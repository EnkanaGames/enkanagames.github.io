#!/usr/bin/env python3
"""
完成イメージ（CG）を Blender の Python モジュール bpy（Cycles）で描く。
形と寸法は generate_wallet.py の設計値をそのまま使う。

  # Python 3.11
  pip install bpy==4.4.0 "numpy<2"
  python render_wallet.py                       # 開いた状態・右側の寄り・閉じた状態の3枚
  python render_wallet.py open --samples 32 --scale 40   # 試し描き

出力: render/wallet_open.jpg, render/wallet_detail.jpg, render/wallet_closed.jpg
"""
import argparse
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import generate_wallet as gw  # noqa: E402

MM = 0.001

# =============================================================================
# 重なりの高さ w [mm]（外装の外側の面＝0、内側へ＋）
# =============================================================================
W_BODY = (0.0, 1.0)          # ① 外装 1.0
W_LIN = (1.0, 1.2)           # ⑥ 裏地（布）
W_BILL = 1.2                 # お札（1枚 0.1）
W_BAND = (1.45, 2.45)        # ④ ベルト（お札の上）
W_POCKET = ((1.65, 1.85), (1.45, 1.65))   # ⑤a, ⑤b
W_BASE = (1.85, 2.65)        # ② 台座 0.8
Z2 = W_BASE[1]               # ②の表
T3 = 0.8                     # ③の革厚
Z_TAB = Z2 + T3              # ③タブ・谷の表
Z_TOP = Z2 + gw.G            # ③の面の表（箱の高さ＝壁の幅）
CARD_T = 0.76

# =============================================================================
# 形のユーティリティ
# =============================================================================
def poly_from_segs(segs, step_deg=5.0, closed=True):
    pts = []
    for s in segs:
        if s[0] == "L":
            pts.append(tuple(s[1]))
        else:
            _, c, r, p0, p1, pm = s
            a0 = math.atan2(p0[1] - c[1], p0[0] - c[0])
            a1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
            am = math.atan2(pm[1] - c[1], pm[0] - c[0])
            sw = (a1 - a0) % (2 * math.pi)
            if (am - a0) % (2 * math.pi) > sw:
                sw -= 2 * math.pi
            n = max(2, int(math.ceil(abs(math.degrees(sw)) / step_deg)))
            for i in range(n):
                t = a0 + sw * i / n
                pts.append((c[0] + r * math.cos(t), c[1] + r * math.sin(t)))
    if not closed:
        last = segs[-1]
        pts.append(tuple(last[2]) if last[0] == "L" else tuple(last[4]))
    out = []
    for p in pts:
        if not out or math.dist(p, out[-1]) > 1e-6:
            out.append(p)
    if closed and math.dist(out[0], out[-1]) < 1e-6:
        out.pop()
    return out


def area2(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts)))


def inside(pt, poly):
    x, y = pt
    c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def rot2(pts, deg, center):
    t = math.radians(deg)
    cs, sn = math.cos(t), math.sin(t)
    cx, cy = center
    return [(cx + (x - cx) * cs - (y - cy) * sn, cy + (x - cx) * sn + (y - cy) * cs) for x, y in pts]


# =============================================================================
# 折り曲げ（中心の折り目）。右半分は台に平らに置き、左半分を角度 theta だけ起こす
# =============================================================================
class Bend:
    def __init__(self, theta_deg, arc_len):
        self.t = math.radians(theta_deg)
        self.L = arc_len
        self.R = arc_len / self.t

    def __call__(self, u, w):
        h, t, R = self.L / 2, self.t, self.R
        if u >= h:
            sx, sz, nx, nz = u - h, 0.0, 0.0, 1.0
        elif u >= -h:
            f = t * (h - u) / self.L
            sx, sz, nx, nz = -R * math.sin(f), R * (1 - math.cos(f)), math.sin(f), math.cos(f)
        else:
            d = -u - h
            sx = -R * math.sin(t) - d * math.cos(t)
            sz = R * (1 - math.cos(t)) + d * math.sin(t)
            nx, nz = math.sin(t), math.cos(t)
        return sx + w * nx, sz + w * nz


# =============================================================================
# マテリアル
# =============================================================================
def _nodes(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    return m, nt.nodes, nt.links, nt.nodes["Principled BSDF"]


def _tex(N, kind, scale, **kw):
    n = N.new(kind)
    n.inputs["Scale"].default_value = scale
    for k, v in kw.items():
        n.inputs[k].default_value = v
    return n


def mat_leather(name, base, dark, rough=0.48, grain=0.55):
    m, N, Lk, b = _nodes(name)
    tc = N.new("ShaderNodeTexCoord")
    mot = _tex(N, "ShaderNodeTexNoise", 45.0, Detail=5.0, Roughness=0.55)
    Lk.new(tc.outputs["Object"], mot.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = (*base, 1)
    Lk.new(mot.outputs["Fac"], ramp.inputs["Fac"])
    Lk.new(ramp.outputs["Color"], b.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = rough - 0.15
    rr.inputs["To Max"].default_value = rough + 0.15
    Lk.new(mot.outputs["Fac"], rr.inputs["Value"])
    Lk.new(rr.outputs["Result"], b.inputs["Roughness"])
    # 銀面のしぼ：ボロノイの境界（細かいシワの網目）＋ノイズ
    vor = _tex(N, "ShaderNodeTexVoronoi", 900.0, Randomness=1.0)
    vor.feature = "DISTANCE_TO_EDGE"
    crease = N.new("ShaderNodeMapRange")
    crease.inputs["From Max"].default_value = 0.12
    Lk.new(vor.outputs["Distance"], crease.inputs["Value"])
    fine = _tex(N, "ShaderNodeTexNoise", 2600.0, Detail=8.0, Roughness=0.6)
    Lk.new(tc.outputs["Object"], vor.inputs["Vector"])
    Lk.new(tc.outputs["Object"], fine.inputs["Vector"])
    mix = N.new("ShaderNodeMath")
    mix.operation = "MULTIPLY_ADD"
    mix.inputs[1].default_value = 0.6
    Lk.new(fine.outputs["Fac"], mix.inputs[0])
    Lk.new(crease.outputs["Result"], mix.inputs[2])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = grain
    bump.inputs["Distance"].default_value = 0.00006
    Lk.new(mix.outputs["Value"], bump.inputs["Height"])
    # ゆるい凹凸（革のうねり）
    wav = _tex(N, "ShaderNodeTexNoise", 60.0, Detail=3.0)
    Lk.new(tc.outputs["Object"], wav.inputs["Vector"])
    bump2 = N.new("ShaderNodeBump")
    bump2.inputs["Strength"].default_value = 0.08
    bump2.inputs["Distance"].default_value = 0.0002
    Lk.new(wav.outputs["Fac"], bump2.inputs["Height"])
    Lk.new(bump2.outputs["Normal"], bump.inputs["Normal"])
    Lk.new(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Coat Weight"].default_value = 0.18
    b.inputs["Coat Roughness"].default_value = 0.35
    b.inputs["Sheen Weight"].default_value = 0.08
    return m


def mat_edge(name, color):
    m, N, Lk, b = _nodes(name)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.3
    b.inputs["Coat Weight"].default_value = 0.35
    b.inputs["Coat Roughness"].default_value = 0.2
    tc = N.new("ShaderNodeTexCoord")
    n = _tex(N, "ShaderNodeTexNoise", 1500.0, Detail=6.0)
    Lk.new(tc.outputs["Object"], n.inputs["Vector"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.15
    bump.inputs["Distance"].default_value = 0.00003
    Lk.new(n.outputs["Fac"], bump.inputs["Height"])
    Lk.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_fabric(name, color, sheen=(0.45, 0.55, 0.85)):
    m, N, Lk, b = _nodes(name)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.55
    b.inputs["Sheen Weight"].default_value = 0.4
    b.inputs["Sheen Roughness"].default_value = 0.4
    b.inputs["Sheen Tint"].default_value = (*sheen, 1)
    tc = N.new("ShaderNodeTexCoord")
    wx = N.new("ShaderNodeTexWave")
    wx.bands_direction = "X"
    wy = N.new("ShaderNodeTexWave")
    wy.bands_direction = "Y"
    for w_ in (wx, wy):
        w_.inputs["Scale"].default_value = 160.0
        w_.inputs["Distortion"].default_value = 0.3
        Lk.new(tc.outputs["Object"], w_.inputs["Vector"])
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    Lk.new(wx.outputs["Fac"], mul.inputs[0])
    Lk.new(wy.outputs["Fac"], mul.inputs[1])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.00002
    Lk.new(mul.outputs["Value"], bump.inputs["Height"])
    Lk.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_plain(name, color, rough=0.4, metal=0.0, coat=0.0):
    m, N, Lk, b = _nodes(name)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    return m


def mat_paper(name):
    """お札（参考）：薄い地色に、縁から少し内側へ細かい地紋の帯。実在の紙幣の図柄は使わない"""
    m, N, Lk, b = _nodes(name)
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    Lk.new(tc.outputs["UV"], sep.inputs["Vector"])

    def edge_mm(out, size):
        inv = N.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        Lk.new(out, inv.inputs[1])
        mn = N.new("ShaderNodeMath")
        mn.operation = "MINIMUM"
        Lk.new(out, mn.inputs[0])
        Lk.new(inv.outputs["Value"], mn.inputs[1])
        sc = N.new("ShaderNodeMath")
        sc.operation = "MULTIPLY"
        sc.inputs[1].default_value = size / 20.0
        Lk.new(mn.outputs["Value"], sc.inputs[0])
        return sc.outputs["Value"]

    dmin = N.new("ShaderNodeMath")
    dmin.operation = "MINIMUM"
    Lk.new(edge_mm(sep.outputs["X"], gw.BILL_W), dmin.inputs[0])
    Lk.new(edge_mm(sep.outputs["Y"], gw.BILL_H), dmin.inputs[1])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "LINEAR"
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.66, 0.61, 0.50, 1)
    els[1].position, els[1].color = 1.0, (0.64, 0.59, 0.49, 1)
    for pos, col in [(0.17, (0.66, 0.61, 0.50, 1)), (0.2, (0.42, 0.34, 0.25, 1)),
                     (0.42, (0.47, 0.39, 0.29, 1)), (0.45, (0.64, 0.59, 0.49, 1))]:
        e = els.new(pos)
        e.color = col
    Lk.new(dmin.outputs["Value"], ramp.inputs["Fac"])
    wv = N.new("ShaderNodeTexWave")
    wv.bands_direction = "DIAGONAL"
    wv.inputs["Scale"].default_value = 900.0
    wv.inputs["Distortion"].default_value = 4.0
    Lk.new(tc.outputs["Object"], wv.inputs["Vector"])
    fine = N.new("ShaderNodeMapRange")
    fine.inputs["To Min"].default_value = 0.88
    Lk.new(wv.outputs["Fac"], fine.inputs["Value"])
    mul = N.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    Lk.new(ramp.outputs["Color"], mul.inputs["A"])
    Lk.new(fine.outputs["Result"], mul.inputs["B"])
    Lk.new(mul.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.8
    return m


def mat_backdrop(name):
    m, N, Lk, b = _nodes(name)
    tc = N.new("ShaderNodeTexCoord")
    n = _tex(N, "ShaderNodeTexNoise", 6.0, Detail=6.0, Roughness=0.6)
    Lk.new(tc.outputs["Object"], n.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.36, 0.345, 0.32, 1)
    ramp.color_ramp.elements[1].color = (0.44, 0.425, 0.39, 1)
    Lk.new(n.outputs["Fac"], ramp.inputs["Fac"])
    Lk.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    fine = _tex(N, "ShaderNodeTexNoise", 900.0, Detail=4.0)
    Lk.new(tc.outputs["Object"], fine.inputs["Vector"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.2
    bump.inputs["Distance"].default_value = 0.0001
    Lk.new(fine.outputs["Fac"], bump.inputs["Height"])
    Lk.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def make_materials():
    tan, tan_d = (0.42, 0.18, 0.045), (0.27, 0.10, 0.022)
    M = {
        "leather": mat_leather("leather", tan, tan_d),
        "leather2": mat_leather("leather_inner", (0.45, 0.20, 0.055), (0.30, 0.12, 0.03)),
        "edge": mat_edge("edge", (0.10, 0.04, 0.015)),
        "lining": mat_fabric("lining", (0.012, 0.02, 0.055)),
        "thread": mat_plain("thread", (0.78, 0.69, 0.50), rough=0.42, coat=0.25),
        "paper": mat_paper("paper"),
        "paper_edge": mat_plain("paper_edge", (0.75, 0.72, 0.64), rough=0.8),
        "brass": mat_plain("brass", (0.78, 0.58, 0.32), rough=0.3, metal=1.0),
        "coil": mat_plain("coil", (0.015, 0.02, 0.045), rough=0.35, coat=0.3),
        "card_edge": mat_plain("card_edge", (0.85, 0.85, 0.83), rough=0.35),
        "backdrop": mat_backdrop("backdrop"),
    }
    for i, c in enumerate([(0.85, 0.85, 0.82), (0.45, 0.66, 0.50), (0.70, 0.55, 0.22),
                           (0.02, 0.02, 0.025), (0.03, 0.12, 0.35)]):
        M[f"card{i}"] = mat_plain(f"card{i}", c, rough=0.3, coat=0.25)
    return M


# =============================================================================
# メッシュ
# =============================================================================
OBJS = []


def new_obj(name, bm, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    OBJS.append(ob)
    return ob


def add_bevel(ob, width, seg=3, angle=30):
    md = ob.modifiers.new("bevel", "BEVEL")
    md.width = width
    md.segments = seg
    md.limit_method = "ANGLE"
    md.angle_limit = math.radians(angle)
    return md


def slab(name, pts, w0, w1, mats, cuts=(), bevel=0.3, seg=3, uv=None):
    """平らな部品：外形 pts を w0～w1 の厚みにする。上下面は mats[0]、側面（コバ）は mats[1]"""
    if area2(pts) < 0:
        pts = pts[::-1]
    bm = bmesh.new()
    bot = [bm.verts.new((u, v, w0)) for u, v in pts]
    top = [bm.verts.new((u, v, w1)) for u, v in pts]
    bm.faces.new(top).material_index = 0
    bm.faces.new(bot[::-1]).material_index = 0
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([bot[i], bot[j], top[j], top[i]]).material_index = 1
    for x in cuts:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                               plane_co=(x, 0, 0), plane_no=(1, 0, 0))
    if uv:   # uv = (u0, v0, u1, v1, deg, center)：回転を戻してから 0～1 に
        u0, v0, u1, v1, deg, c = uv
        lay = bm.loops.layers.uv.new()
        for f in bm.faces:
            for lp in f.loops:
                (x, y), = rot2([lp.vert.co[:2]], -deg, c)
                lp[lay].uv = ((x - u0) / (u1 - u0), (y - v0) / (v1 - v0))
    ob = new_obj(name, bm, mats)
    if bevel > 0:
        add_bevel(ob, bevel, seg)
    return ob


def unit_sphere(nu=12, nv=7):
    vs = [(0, 0, -1)]
    for j in range(1, nv):
        ph = -math.pi / 2 + math.pi * j / nv
        for i in range(nu):
            th = 2 * math.pi * i / nu
            vs.append((math.cos(ph) * math.cos(th), math.cos(ph) * math.sin(th), math.sin(ph)))
    vs.append((0, 0, 1))
    fs = []
    for i in range(nu):
        fs.append((0, 1 + (i + 1) % nu, 1 + i))
    for j in range(nv - 2):
        a, b = 1 + j * nu, 1 + (j + 1) * nu
        for i in range(nu):
            i2 = (i + 1) % nu
            fs.append((a + i, a + i2, b + i2, b + i))
    top = len(vs) - 1
    a = 1 + (nv - 2) * nu
    for i in range(nu):
        fs.append((a + i, a + (i + 1) % nu, top))
    return vs, fs


SPHERE = unit_sphere()


def add_ellipsoid(bm, c, ax, ay, az):
    vs, fs = SPHERE
    vv = [bm.verts.new(c + ax * x + ay * y + az * z) for x, y, z in vs]
    for f in fs:
        bm.faces.new([vv[i] for i in f])


# =============================================================================
# 縫い目（手縫いのサドルステッチ。菱目 3mm、斜めに並ぶ）
# =============================================================================
PITCH = 3.0
BAND_POLY = None


def resample(pts, closed, pitch):
    seq = pts + ([pts[0]] if closed else [])
    cum = [0.0]
    for i in range(1, len(seq)):
        cum.append(cum[-1] + math.dist(seq[i - 1], seq[i]))
    total = cum[-1]
    n = max(1, int(round(total / pitch)))
    step = total / n
    out = []
    k, j = 0, 1
    count = n if closed else n + 1
    for k in range(count):
        s = min(k * step, total)
        while j < len(seq) - 1 and cum[j] < s:
            j += 1
        t = (s - cum[j - 1]) / max(1e-9, cum[j] - cum[j - 1])
        p, q = seq[j - 1], seq[j]
        out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    if closed:
        out.append(out[0])
    return out


def unit_tab(u, v):
    if u >= gw.FR - 0.01 and (gw.ZT <= v <= gw.CB or v >= gw.KT):
        return True
    if v >= gw.KB and u >= gw.u_on_D(v):
        return True
    return gw.UL <= u <= gw.FL and v <= gw.CB


def surface_w(u, v):
    """内側の縫い目が乗る面の高さ。None はユニットの下に隠れて見えない"""
    if u > gw.UL - 0.3 and v >= gw.ZT - 0.3:
        if v < 5.0:
            return None
        return Z_TAB if unit_tab(u, v) else Z2
    if inside((u, v), BAND_POLY):
        return W_BAND[1]
    return W_LIN[1]


def add_stitches(bm, holes, wfunc, outer=False, skip=None, slant=22.0):
    up = Vector((0, 0, -1 if outer else 1))
    a = math.radians(-slant if outer else slant)
    for i in range(len(holes) - 1):
        p, q = Vector((*holes[i], 0)), Vector((*holes[i + 1], 0))
        m = (p + q) / 2
        if skip and skip(m.x, m.y):
            continue
        w = 0.0 if outer else wfunc(m.x, m.y)
        if w is None:
            continue
        t = (q - p).normalized()
        n = Vector((-t.y, t.x, 0))
        d = t * math.cos(a) + n * math.sin(a)
        pd = Vector((-d.y, d.x, 0))
        ln = (q - p).length
        c = m + up * 0.1 + Vector((0, 0, w))
        if outer:
            add_ellipsoid(bm, c, d * ln * 0.44, -pd * 0.42, up * 0.3)
        else:
            add_ellipsoid(bm, c, d * ln * 0.44, pd * 0.42, up * 0.3)


def build_stitches(M):
    bm = bmesh.new()
    per = resample(poly_from_segs(gw.perimeter_stitch(), 3.0), True, PITCH)
    add_stitches(bm, per, surface_w)
    add_stitches(bm, per, None, outer=True)
    seam = resample(poly_from_segs(gw.left_seam(), closed=False), False, PITCH)
    add_stitches(bm, seam, lambda u, v: Z_TAB if v < gw.CB else Z2)
    zl = resample([(gw.FL + 1.5, gw.ZIP_ST), (gw.FR - 1.5, gw.ZIP_ST)], False, PITCH)
    add_stitches(bm, zl, lambda u, v: Z_TOP, skip=lambda u, v: 22.0 < u < 29.0)
    vl = resample([(gw.FL + 2, gw.SEP_V), (gw.FR - 2, gw.SEP_V)], False, PITCH)
    add_stitches(bm, vl, lambda u, v: Z_TAB)
    ob = new_obj("stitches", bm, [M["thread"]])
    return ob


# =============================================================================
# 部品
# =============================================================================
def front_shell(M):
    """③ 前胴：面・壁・タブを1枚の革として作り、厚み0.8と折り目の丸みを付ける"""
    FL, FR, UL, W, H = gw.FL, gw.FR, gw.UL, gw.W, gw.H
    ZT, CB, KT, KB = gw.ZT, gw.CB, gw.KT, gw.KB
    uD_KT, uD_KB, uD_H = gw.u_on_D(KT), gw.u_on_D(KB), gw.u_on_D(H)
    vA, vB = gw.v_on(gw.CW_A, FR), gw.v_on(gw.CW_B, FR)
    uA, uB = gw.u_on(gw.CW_A, KB), gw.u_on(gw.CW_B, KB)
    zt, zb = Z_TOP, Z_TAB
    bm = bmesh.new()
    vmap = {}

    def V(p):
        k = tuple(round(c, 4) for c in p)
        if k not in vmap:
            vmap[k] = bm.verts.new(p)
        return vmap[k]

    def F(pts, nrm):
        nx = ny = nz = 0.0
        for i in range(len(pts)):
            x1, y1, z1 = pts[i]
            x2, y2, z2 = pts[(i + 1) % len(pts)]
            nx += (y1 - y2) * (z1 + z2)
            ny += (z1 - z2) * (x1 + x2)
            nz += (x1 - x2) * (y1 + y2)
        if nx * nrm[0] + ny * nrm[1] + nz * nrm[2] < 0:
            pts = pts[::-1]
        bm.faces.new([V(p) for p in pts])

    flat = lambda pts, w: [(u, v, w) for u, v in pts]

    def wall(a, b, nrm):
        F([(a[0], a[1], zt), (b[0], b[1], zt), (b[0], b[1], zb), (a[0], a[1], zb)], nrm)

    up = (0, 0, 1)
    # 小銭入れ
    F(flat([(FL, ZT), (FR, ZT), (FR, CB), (FL, CB)], zt), up)
    wall((FL, ZT), (FL, CB), (-1, 0, 0))
    wall((FR, ZT), (FR, CB), (1, 0, 0))
    wall((FL, CB), (FR, CB), (0, 1, 0))
    F(flat([(UL, ZT), (FL, ZT), (FL, CB), (UL, CB)], zb), up)
    F(flat(poly_from_segs(gw.rounded_polygon([(FR, ZT), (W, ZT), (W, CB), (FR, CB)],
                                             [0, gw.R_UNIT_TOP, 0, 0])), zb), up)
    # 仕切りの谷
    F(flat([(FL, CB), (FR, CB), (FR, KT), (uD_KT, KT), (FL, KT)], zb), up)
    # カードポケット
    wall((uD_KT, KT), (FR, KT), (0, -1, 0))
    F(flat([(uD_KT, KT), (FR, KT), (FR, vA), (uA, KB), (uD_KB, KB)], zt), up)
    wall((FR, KT), (FR, vA), (1, 0, 0))
    wall((uD_KB, KB), (uA, KB), (0, 1, 0))
    F(flat([(FR, KT), (W, KT), (W, KB), (FR, KB), (FR, vB), (FR, vA)], zb), up)
    # 角押さえ
    F(flat([(FR, vB), (FR, KB), (uB, KB)], zt), up)
    wall((FR, vB), (FR, KB), (1, 0, 0))
    wall((uB, KB), (FR, KB), (0, 1, 0))
    bt = poly_from_segs(gw.rounded_polygon(
        [(uD_KB, KB), (uA, KB), (uB, KB), (FR, KB), (W, KB), (W, H), (uD_H, H)],
        [0, 0, 0, 0, 0, gw.R_OUT, 0]))
    F(flat(bt, zb), up)

    ob = new_obj("front", bm, [M["leather2"], M["edge"], M["lining"]])
    sd = ob.modifiers.new("solid", "SOLIDIFY")
    sd.thickness = T3
    sd.offset = -1.0
    sd.use_even_offset = True
    sd.use_quality_normals = True
    sd.material_offset = 2
    sd.material_offset_rim = 1
    add_bevel(ob, 0.4, 4)
    return ob


def build_zipper(M):
    FL, FR = gw.FL, gw.FR
    ZT = gw.ZT
    # テープ（②の表と③の裏）
    for i, (w0, w1) in enumerate([(Z2, Z2 + 0.25), (Z_TOP - T3 - 0.25, Z_TOP - T3)]):
        slab(f"tape{i}", [(FL + 0.5, ZT - 1.3), (FR - 0.5, ZT - 1.3),
                          (FR - 0.5, ZT + gw.ZIP_TAPE_IN), (FL + 0.5, ZT + gw.ZIP_TAPE_IN)],
             w0, w1, [M["coil"], M["coil"]], bevel=0.08, seg=1)
    # コイル（務歯）：上下2列がかみ合う
    bm = bmesh.new()
    lo, hi = Z2 + 0.3, Z_TOP - T3 - 0.3
    mid = (lo + hi) / 2
    pitch = 0.95
    u = FL + 0.6
    k = 0
    while u < FR - 1.0:
        for row, (a, b) in enumerate([(lo, mid + 0.25), (mid - 0.25, hi)]):
            uu = u + (pitch / 2 if row else 0)
            c = Vector((uu, ZT - 0.55, (a + b) / 2))
            add_ellipsoid(bm, c, Vector((0.36, 0, 0)), Vector((0, 0.95, 0)), Vector((0, 0, (b - a) / 2)))
        u += pitch
        k += 1
    new_obj("coil", bm, [M["coil"]])
    # スライダーと引き手（真鍮）
    su0 = FL + 1.5
    slab("slider", poly_from_segs(gw.rect(su0, ZT - 3.6, su0 + 8.5, ZT + 0.4, 1.4)),
         Z2 + 0.15, Z_TOP - T3 - 0.1, [M["brass"], M["brass"]], bevel=0.7, seg=4)
    slab("slider_neck", poly_from_segs(gw.rect(su0 + 3.2, ZT - 3.2, su0 + 5.3, ZT - 0.4, 0.6)),
         Z_TOP - T3 - 0.4, Z_TOP + 0.55, [M["brass"], M["brass"]], bevel=0.4, seg=3)
    pull = poly_from_segs(gw.rect(su0 + 2.0, ZT - 3.4, su0 + 6.5, ZT + 11.5, 2.2))
    slab("pull", pull, Z_TOP + 0.15, Z_TOP + 0.75, [M["brass"], M["brass"]], bevel=0.25, seg=3)


def card_poly(du=0.0, dv=0.0, deg=0.0):
    u1 = gw.FR - T3 - 0.5 + du
    v1 = gw.KB - T3 - 0.3 + dv
    pts = poly_from_segs(gw.rect(u1 - gw.CARD_W, v1 - gw.CARD_H, u1, v1, gw.CARD_R))
    return rot2(pts, deg, (u1 - gw.CARD_W / 2, v1 - gw.CARD_H / 2))


def bill_poly(du=0.0, dv=0.0, deg=0.0):
    v1 = gw.H - gw.SM - 0.5 + dv
    u0 = gw.BILL_U0 + du
    c = (u0 + gw.BILL_W / 2, v1 - gw.BILL_H / 2)
    pts = poly_from_segs(gw.rect(u0, v1 - gw.BILL_H, u0 + gw.BILL_W, v1))
    return rot2(pts, deg, c), (u0, v1 - gw.BILL_H, u0 + gw.BILL_W, v1, deg, c)


def build(M, fold_cuts):
    global BAND_POLY
    BAND_POLY = poly_from_segs(gw.band_outline())
    slab("body", poly_from_segs(gw.body_outline()), *W_BODY, [M["leather"], M["edge"]],
         cuts=fold_cuts, bevel=0.35, seg=3)
    slab("lining", poly_from_segs(gw.lining_outline()), *W_LIN, [M["lining"], M["lining"]],
         cuts=fold_cuts, bevel=0.05, seg=1)
    for i, (du, dv, deg) in enumerate([(0, 0, 0), (-1.6, -0.9, -0.35)]):
        w0 = W_BILL + 0.1 * i
        pts, uv = bill_poly(du, dv, deg)
        slab(f"bill{i}", pts, w0, w0 + 0.09, [M["paper"], M["paper_edge"]],
             cuts=fold_cuts, bevel=0.0, uv=uv)
    slab("band", BAND_POLY, *W_BAND, [M["leather2"], M["edge"]], bevel=0.3)
    # ⑤ 裏ポケット（完成形）
    for idx in (0, 1):
        i = gw.FABRIC_INSET
        t = lambda u: gw.pocket_top_v(idx, u)
        pts = poly_from_segs(gw.rounded_polygon(
            [(gw.UL + i, t(gw.UL + i)), (gw.W - i, t(gw.W - i)), (gw.W - i, gw.H - i), (gw.UL + i, gw.H - i)],
            [0, 0, gw.R_OUT - i, 0]))
        slab(f"pocket{idx}", pts, *W_POCKET[idx], [M["lining"], M["lining"]], bevel=0.05, seg=1)
    slab("base", poly_from_segs(gw.base_outline()), *W_BASE, [M["leather2"], M["edge"]], bevel=0.3)
    front_shell(M)
    build_zipper(M)
    for i, (du, dv, deg) in enumerate([(0, 0, 0), (-1.0, -0.2, 0.15), (-0.3, -0.7, -0.1),
                                       (-1.8, -0.3, 0.1), (-0.7, -0.5, -0.12)]):
        w0 = Z2 + 0.02 + i * CARD_T
        slab(f"card{i}", card_poly(du, dv, deg), w0, w0 + CARD_T - 0.02,
             [M[f"card{i}"], M["card_edge"]], bevel=0.2, seg=2)
    build_stitches(M)


def finalize(bend):
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in OBJS:
        mats = list(ob.data.materials)
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        ob.modifiers.clear()
        old = ob.data
        ob.data = me
        bpy.data.meshes.remove(old)
        if len(me.materials) == 0:
            for m in mats:
                me.materials.append(m)
        # 図面は v が下向き（左手系）なので、Y を反転して面の向きを戻す
        for v in me.vertices:
            x, z = bend(v.co.x, v.co.z)
            v.co = (x * MM, (gw.H / 2 - v.co.y) * MM, z * MM)
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        me.set_sharp_from_angle(angle=math.radians(40))
        me.update()


# =============================================================================
# シーン
# =============================================================================
def area_light(name, loc, target, size, power, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y = size
    ld.energy = power
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def look_at(ob, target):
    d = Vector(target) - Vector(ob.location)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def setup_scene(M, view, samples, scale):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.render.resolution_x, sc.render.resolution_y = 1800, 1200
    sc.render.resolution_percentage = scale
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 92
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    wd = bpy.data.worlds.new("world")
    wd.use_nodes = True
    bg = wd.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.85, 0.87, 0.9, 1)
    bg.inputs["Strength"].default_value = 0.1
    sc.world = wd

    bm = bmesh.new()
    s = 1.5
    vs = [bm.verts.new(p) for p in [(-s, -s, -0.0003), (s, -s, -0.0003), (s, s, -0.0003), (-s, s, -0.0003)]]
    bm.faces.new(vs)
    me = bpy.data.meshes.new("floor")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M["backdrop"])
    fl = bpy.data.objects.new("floor", me)
    sc.collection.objects.link(fl)

    cam = bpy.data.cameras.new("cam")
    cam.lens = 75
    cam.dof.use_dof = True
    co = bpy.data.objects.new("cam", cam)
    sc.collection.objects.link(co)
    sc.camera = co
    if view == "open":
        tgt = (-0.006, -0.004, 0.006)
        co.location = (0.15, -0.45, 0.48)
        cam.dof.aperture_fstop = 11
        area_light("key", (-0.35, 0.30, 0.55), (0, 0, 0), (0.45, 0.35), 7)
        area_light("fill", (0.45, -0.35, 0.25), (0, 0, 0), (0.5, 0.5), 2.2, (1.0, 0.96, 0.9))
        area_light("rim", (0.15, 0.55, 0.18), (0, 0, 0), (0.4, 0.15), 4)
    elif view == "detail":
        tgt = (0.050, -0.006, 0.005)
        co.location = (0.209, -0.215, 0.175)
        cam.lens = 76
        cam.dof.aperture_fstop = 8
        area_light("key", (-0.25, 0.30, 0.45), tgt, (0.35, 0.3), 6)
        area_light("fill", (0.40, -0.30, 0.20), tgt, (0.4, 0.4), 2.0, (1.0, 0.96, 0.9))
        area_light("rim", (0.15, 0.45, 0.15), tgt, (0.3, 0.12), 4)
    else:
        tgt = (0.048, 0.005, 0.004)
        co.location = (-0.12, 0.44, 0.27)
        cam.lens = 85
        cam.dof.aperture_fstop = 11
        area_light("key", (0.40, -0.10, 0.45), (0.04, 0, 0), (0.45, 0.35), 7)
        area_light("fill", (-0.40, 0.35, 0.20), (0.04, 0, 0), (0.5, 0.5), 2.2, (1.0, 0.96, 0.9))
        area_light("rim", (0.0, -0.55, 0.20), (0.04, 0, 0), (0.4, 0.15), 5)
    look_at(co, tgt)
    cam.dof.focus_distance = (Vector(tgt) - co.location).length


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("views", nargs="*", default=["open", "detail", "closed"])
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--scale", type=int, default=100)
    ap.add_argument("--out", default=os.path.join(HERE, "render"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for view in a.views:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        OBJS.clear()
        M = make_materials()
        if view in ("open", "detail"):
            bend = Bend(14.0, 24.0)
        else:
            r = (Z_TOP + 0.75 + W_BAND[1] + 0.3) / 2       # 引き手＋ベルトが当たらない半径
            bend = Bend(180.0, math.pi * r)
        h = bend.L / 2
        cuts = [-h - 0.5 + i * 0.5 for i in range(int((2 * h + 1) / 0.5) + 1)]
        build(M, cuts)
        finalize(bend)
        setup_scene(M, view, a.samples, a.scale)
        path = os.path.join(a.out, f"wallet_{view}.jpg")
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print("wrote", path)


if __name__ == "__main__":
    main()
