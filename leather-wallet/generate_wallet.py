#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
薄型二つ折り財布（ファスナー小銭入れ付き）設計図ジェネレータ

出力（このスクリプトと同じフォルダ）:
  wallet_pattern_A3.dxf    型紙（実寸 1/1・A3横）
  wallet_assembly_A3.dxf   組立図・重なり確認図・断面模式図（1/1・A3横）
  wallet_pattern_A3.pdf / wallet_assembly_A3.pdf   印刷・確認用（matplotlib がある場合）
  preview_pattern.png / preview_assembly.png       プレビュー画像

DXF は Jw_cad で読み込める AutoCAD R12 形式（ASCII・Shift-JIS・CRLF）。
座標原点 (0,0) は A3 用紙の中心（Jw_cad の原点＝用紙中心に合わせている）。

寸法を変えたいときは「設計寸法」の定数を書き換えて再実行する:
  python3 generate_wallet.py
"""
import math
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# 設計寸法 [mm]
# 財布座標: u = 中心（折り線）から右が＋、v = 上端から下が＋（内側から見た向き）
# =============================================================================
W = 102.0            # 片側の幅（閉じたときの横幅）。開いた全幅は 2W
H = 100.0            # 高さ
R_OUT = 6.0          # 外周コーナー R
SM = 3.0             # コバから縫い線までの距離
GLUE = 5.0           # 接着しろの幅（縫い代部分）

UNIT_L = 12.0        # 台座・前胴の左端（中心からの距離）＝裏ポケット入口
SEAM_U = UNIT_L + SM  # 小銭入れ左側の縫い線
SEP_V = 40.0         # 小銭入れ／カードポケット仕切りの縫い線
L_R = 6.0            # 仕切り縫い線の角 R（小銭が角に溜まりにくくする）

# 斜めライン（中心線に対して左右対称）
#   A: 左＝札押さえベルトの上辺 / 右＝カード窓の上辺（前胴の右下辺）
#   B: 左＝札押さえベルトの下辺 / 右＝カード窓の下辺（カード押さえの斜辺）
A_EDGE_V, A_BOT_U = 52.0, 68.0   # 側面で v=52、下辺で |u|=68
B_EDGE_V, B_BOT_U = 76.0, 85.0   # 側面で v=76、下辺で |u|=85

# 前胴 左側の斜め辺（カード差込口）: u = D_BOT_U - D_SLOPE * (H - v)
D_BOT_U = 48.0
D_SLOPE = 0.4
STEP_V = SEP_V + SM  # 前胴の段（仕切り縫い線から 3mm 下）
STEP_R_CONVEX = SM + L_R  # 9  : 段の外R（仕切り縫い線の R と同心）
STEP_R_CONCAVE = 4.0      # 段から斜め辺へつながる内R

# ファスナー窓（3号コイル想定。窓幅はスライダーに合わせて 6〜8mm で調整）
WIN_V0, WIN_V1 = 9.0, 16.0       # 窓幅 7mm
WIN_U0, WIN_U1 = 21.5, 92.5      # 窓長 71mm（両端 R3.5 = φ7 ポンチ）
ZIP_ELEM_W = 4.0                 # エレメント（務歯）幅
ZIP_TAPE_U0, ZIP_TAPE_U1 = 16.5, 97.5   # テープ長 81mm
ZIP_TAPE_V0, ZIP_TAPE_V1 = 4.0, 25.5    # 上側テープは v=4 でカット

# 収納物（参考線）
CARD_W, CARD_H, CARD_R = 85.6, 54.0, 3.0
BILL_W, BILL_H = 80.0, 76.0      # 一万円札（160x76）を二つ折り

K_AB = (W - A_BOT_U) / (H - A_EDGE_V)   # 斜めラインの傾き du/dv
assert abs(K_AB - (W - B_BOT_U) / (H - B_EDGE_V)) < 1e-9, "A と B は平行にする"


def u_on_A(v):
    return W - K_AB * (v - A_EDGE_V)


def v_on_A(u):
    return A_EDGE_V + (W - u) / K_AB


def u_on_B(v):
    return W - K_AB * (v - B_EDGE_V)


def v_on_B(u):
    return B_EDGE_V + (W - u) / K_AB


def u_on_D(v):
    return D_BOT_U - D_SLOPE * (H - v)


# =============================================================================
# 幾何ユーティリティ
# =============================================================================
def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def mul(a, s):
    return (a[0] * s, a[1] * s)


def length(a):
    return math.hypot(a[0], a[1])


def unit(a):
    n = length(a)
    return (a[0] / n, a[1] / n)


def L(p, q):
    return ("L", p, q)


def A(c, r, p0, p1, pm):
    """円弧: 中心 c, 半径 r, 始点 p0 → 終点 p1（pm は弧上の途中の点）"""
    return ("A", c, r, p0, p1, pm)


def arc_pt(c, r, deg):
    """財布座標（v 下向き）での角度 deg の点。0°=+u, 90°=+v"""
    t = math.radians(deg)
    return (c[0] + r * math.cos(t), c[1] + r * math.sin(t))


def arc_deg(c, r, d0, d1):
    return A(c, r, arc_pt(c, r, d0), arc_pt(c, r, d1), arc_pt(c, r, (d0 + d1) / 2))


def rounded_polygon(pts, radii, closed=True):
    """頂点列と各頂点のフィレット半径から線分・円弧の列を作る"""
    n = len(pts)
    t_in, t_out, arcs = [], [], []
    for i in range(n):
        p = pts[i]
        r = radii[i]
        if r <= 0 or (not closed and (i == 0 or i == n - 1)):
            t_in.append(p)
            t_out.append(p)
            arcs.append(None)
            continue
        d1 = unit(sub(pts[i - 1], p))
        d2 = unit(sub(pts[(i + 1) % n], p))
        half = math.acos(max(-1.0, min(1.0, d1[0] * d2[0] + d1[1] * d2[1]))) / 2
        t = r / math.tan(half)
        c = add(p, mul(unit(add(d1, d2)), r / math.sin(half)))
        a0 = add(p, mul(d1, t))
        a1 = add(p, mul(d2, t))
        pm = add(c, mul(unit(sub(p, c)), r))
        t_in.append(a0)
        t_out.append(a1)
        arcs.append(A(c, r, a0, a1, pm))
    segs = []
    last = n if closed else n - 1
    for i in range(last):
        j = (i + 1) % n
        if arcs[i]:
            segs.append(arcs[i])
        if length(sub(t_in[j], t_out[i])) > 1e-9:
            segs.append(L(t_out[i], t_in[j]))
    return segs


def stadium(u0, u1, v0, v1):
    """横長の長円（両端半円）"""
    r = (v1 - v0) / 2
    vc = (v0 + v1) / 2
    c1, c2 = (u0 + r, vc), (u1 - r, vc)
    return [
        L((c1[0], v0), (c2[0], v0)),
        A(c2, r, (c2[0], v0), (c2[0], v1), (u1, vc)),
        L((c2[0], v1), (c1[0], v1)),
        A(c1, r, (c1[0], v1), (c1[0], v0), (u0, vc)),
    ]


def rect(u0, v0, u1, v1, r=0.0):
    return rounded_polygon([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], [r] * 4)


def mirror_u(segs):
    out = []
    for s in segs:
        if s[0] == "L":
            out.append(L((-s[1][0], s[1][1]), (-s[2][0], s[2][1])))
        else:
            _, c, r, p0, p1, pm = s
            f = lambda p: (-p[0], p[1])
            out.append(A(f(c), r, f(p0), f(p1), f(pm)))
    return out


# =============================================================================
# 部品形状（財布座標）
# =============================================================================
def body_outline():
    return rounded_polygon([(-W, 0), (W, 0), (W, H), (-W, H)], [R_OUT] * 4)


def body_right_half():
    c1, c2 = (W - R_OUT, R_OUT), (W - R_OUT, H - R_OUT)
    return [
        L((0, 0), (W - R_OUT, 0)),
        arc_deg(c1, R_OUT, -90, 0),
        L((W, R_OUT), (W, H - R_OUT)),
        arc_deg(c2, R_OUT, 0, 90),
        L((W - R_OUT, H), (0, H)),
    ]


def perimeter_stitch():
    return rounded_polygon(
        [(-W + SM, SM), (W - SM, SM), (W - SM, H - SM), (-W + SM, H - SM)],
        [R_OUT - SM] * 4,
    )


def base_outline():  # ② 台座
    return rounded_polygon([(UNIT_L, 0), (W, 0), (W, H), (UNIT_L, H)], [0, R_OUT, R_OUT, 0])


def front_outline():  # ③ 前胴
    return rounded_polygon(
        [
            (UNIT_L, 0),
            (W, 0),
            (W, A_EDGE_V),
            (A_BOT_U, H),
            (D_BOT_U, H),
            (u_on_D(STEP_V), STEP_V),
            (UNIT_L, STEP_V),
        ],
        [0, R_OUT, 0, 0, 0, STEP_R_CONCAVE, STEP_R_CONVEX],
    )


def front_free_edges():
    """前胴の輪郭のうち、台座・外装の外周と重ならない辺（左の段〜斜め辺、右下の斜め辺）"""
    out = []
    for s in front_outline():
        pts = [s[1], s[2]] if s[0] == "L" else [s[3], s[4]]
        on_edge = any(
            all(abs(p[k] - val) < 1e-6 for p in pts)
            for k, val in ((0, UNIT_L), (1, 0.0), (1, H), (0, W))
        )
        if s[0] == "A" and abs(s[1][0] - (W - R_OUT)) < 1e-6:
            on_edge = True
        if not on_edge:
            out.append(s)
    return out


def card_holder_outline():  # ⑤ カード押さえ（三角）
    return rounded_polygon([(W, B_EDGE_V), (W, H), (B_BOT_U, H)], [0, R_OUT, 0])


def band_outline():  # ④ 札押さえベルト
    return rounded_polygon(
        [(-W, A_EDGE_V), (-A_BOT_U, H), (-B_BOT_U, H), (-W, B_EDGE_V)], [0, 0, 0, 0]
    )


def window_cut():
    return stadium(WIN_U0, WIN_U1, WIN_V0, WIN_V1)


def window_stitch():
    return stadium(WIN_U0 - SM, WIN_U1 + SM, WIN_V0 - SM, WIN_V1 + SM)


def l_seam():
    """小銭入れの左側〜仕切りの縫い線（前胴＋台座を縫う）"""
    c = (SEAM_U + L_R, SEP_V - L_R)
    return [
        L((SEAM_U, SM), (SEAM_U, SEP_V - L_R)),
        arc_deg(c, L_R, 180, 90),
        L((SEAM_U + L_R, SEP_V), (W - SM, SEP_V)),
    ]


def corner_stitch_tr():
    return arc_deg((W - R_OUT, R_OUT), R_OUT - SM, -90, 0)


def corner_stitch_br():
    return arc_deg((W - R_OUT, H - R_OUT), R_OUT - SM, 0, 90)


def base_stitch():
    return [
        L((UNIT_L, SM), (W - R_OUT, SM)),
        corner_stitch_tr(),
        L((W - SM, R_OUT), (W - SM, H - R_OUT)),
        corner_stitch_br(),
        L((W - R_OUT, H - SM), (UNIT_L, H - SM)),
    ]


def front_stitch():
    return [
        L((UNIT_L, SM), (W - R_OUT, SM)),
        corner_stitch_tr(),
        L((W - SM, R_OUT), (W - SM, v_on_A(W - SM))),
        L((u_on_D(H - SM), H - SM), (u_on_A(H - SM), H - SM)),
    ]


def card_holder_stitch():
    return [
        L((W - SM, v_on_B(W - SM)), (W - SM, H - R_OUT)),
        corner_stitch_br(),
        L((W - R_OUT, H - SM), (u_on_B(H - SM), H - SM)),
    ]


def band_stitch():
    return [
        L((-W + SM, v_on_A(W - SM)), (-W + SM, v_on_B(W - SM))),
        L((-u_on_A(H - SM), H - SM), (-u_on_B(H - SM), H - SM)),
    ]


def card_rect():
    u1 = W - SM - 0.5
    v1 = H - SM - 0.5
    return rect(u1 - CARD_W, v1 - CARD_H, u1, v1, CARD_R)


def bill_rect():
    u0 = -W + SM + 0.5
    v1 = H - SM - 0.5
    return rect(u0, v1 - BILL_H, u0 + BILL_W, v1)


def path_length(segs):
    total = 0.0
    for s in segs:
        if s[0] == "L":
            total += length(sub(s[2], s[1]))
        else:
            _, c, r, p0, p1, pm = s
            a0 = math.atan2(p0[1] - c[1], p0[0] - c[0])
            a1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
            am = math.atan2(pm[1] - c[1], pm[0] - c[0])
            sw = (a1 - a0) % (2 * math.pi)
            if (am - a0) % (2 * math.pi) > sw:
                sw = 2 * math.pi - sw
            total += r * sw
    return total


# =============================================================================
# 図面（エンティティ）とレイヤ
# =============================================================================
# (名前, 色(ACI), 既定線種)
LAYERS = [
    ("切断線", 7, "CONTINUOUS"),
    ("縫い線", 1, "DASHED"),
    ("折り線", 4, "CENTER"),
    ("貼り位置", 4, "HIDDEN"),
    ("ファスナー", 3, "CONTINUOUS"),
    ("カード", 5, "PHANTOM"),
    ("お札", 6, "PHANTOM"),
    ("寸法", 7, "CONTINUOUS"),
    ("文字", 7, "CONTINUOUS"),
    ("断面図", 7, "CONTINUOUS"),
    ("図枠", 7, "CONTINUOUS"),
]
LAYER_PROPS = {n: (c, lt) for n, c, lt in LAYERS}

# 線種（Jw_cad はピッチ未指定だと実線になるため、パターン長を明示）
LTYPES = {
    "CONTINUOUS": ("Solid line", []),
    "DASHED": ("Dashed __ __ __", [2.0, -1.0]),
    "HIDDEN": ("Hidden _ _ _ _", [1.5, -1.0]),
    "CENTER": ("Center ____ _ ____", [8.0, -1.5, 1.0, -1.5]),
    "PHANTOM": ("Phantom ____ _ _ ____", [8.0, -1.2, 1.0, -1.2, 1.0, -1.2]),
}

SHEET_W, SHEET_H = 420.0, 297.0   # A3 横
FRAME_M = 10.0


def text_width(s, h):
    w = 0.0
    for ch in s:
        o = ord(ch)
        w += h * (0.5 if o < 0x80 or 0xFF61 <= o <= 0xFF9F else 1.0)
    return w


class Sheet:
    """A3 用紙1枚分の図面。座標は用紙中心原点・mm・Y上向き"""

    def __init__(self, title):
        self.title = title
        self.ents = []
        self.place(0, 0)

    # ---- 財布座標 → 用紙座標 ----
    def place(self, ox, oy):
        self.ox, self.oy = ox, oy

    def T(self, p):
        return (self.ox + p[0], self.oy - p[1])

    # ---- 用紙座標で直接描く ----
    def line(self, p, q, layer, ltype=None, color=None):
        self.ents.append(dict(t="LINE", p=p, q=q, layer=layer, lt=ltype, c=color))

    def arc(self, c, r, a0, a1, layer, ltype=None, color=None):
        self.ents.append(dict(t="ARC", c=c, r=r, a0=a0 % 360, a1=a1 % 360, layer=layer, lt=ltype, c_=color))

    def circle(self, c, r, layer, ltype=None, color=None):
        self.ents.append(dict(t="CIRCLE", c=c, r=r, layer=layer, lt=ltype, c_=color))

    def text(self, p, s, h, layer="文字", align="l", valign="b", rot=0.0, color=None):
        w = text_width(s, h)
        dx = {"l": 0.0, "c": -w / 2, "r": -w}[align]
        dy = {"b": 0.0, "m": -h / 2, "t": -h}[valign]
        t = math.radians(rot)
        x = p[0] + dx * math.cos(t) - dy * math.sin(t)
        y = p[1] + dx * math.sin(t) + dy * math.cos(t)
        self.ents.append(dict(t="TEXT", p=(x, y), s=s, h=h, rot=rot, layer=layer, c=color))

    def polyline(self, pts, layer, closed=False, ltype=None):
        n = len(pts)
        for i in range(n if closed else n - 1):
            self.line(pts[i], pts[(i + 1) % n], layer, ltype)

    # ---- 財布座標の線分・円弧列を描く ----
    def path(self, segs, layer, ltype=None):
        for s in segs:
            if s[0] == "L":
                self.line(self.T(s[1]), self.T(s[2]), layer, ltype)
            else:
                _, c, r, p0, p1, pm = s
                C, P0, P1, PM = self.T(c), self.T(p0), self.T(p1), self.T(pm)
                ang = lambda P: math.degrees(math.atan2(P[1] - C[1], P[0] - C[0])) % 360
                a0, a1, am = ang(P0), ang(P1), ang(PM)
                if (am - a0) % 360 < (a1 - a0) % 360:
                    self.arc(C, r, a0, a1, layer, ltype)
                else:
                    self.arc(C, r, a1, a0, layer, ltype)

    def ltext(self, p, s, h, **kw):
        """財布座標で文字"""
        self.text(self.T(p), s, h, **kw)

    # ---- 寸法 ----
    def _arrow(self, tip, d, layer):
        for sgn in (1, -1):
            a = math.atan2(d[1], d[0]) + sgn * math.radians(18)
            self.line(tip, (tip[0] + 2.2 * math.cos(a), tip[1] + 2.2 * math.sin(a)), layer)

    def dim_h(self, x1, y1, x2, y2, yd, label=None, h=2.5):
        """水平寸法: 点(x1,y1)(x2,y2) の x 方向距離を y=yd に記入（用紙座標）"""
        lay = "寸法"
        for x, y in ((x1, y1), (x2, y2)):
            s = 1 if yd > y else -1
            self.line((x, y + s * 1.0), (x, yd + s * 1.5), lay)
        self.line((x1, yd), (x2, yd), lay)
        d = 1 if x2 > x1 else -1
        self._arrow((x1, yd), (d, 0), lay)
        self._arrow((x2, yd), (-d, 0), lay)
        if label is None:
            label = fmt(abs(x2 - x1))
        self.text(((x1 + x2) / 2, yd + 0.8), label, h, layer=lay, align="c")

    def dim_v(self, x1, y1, x2, y2, xd, label=None, h=2.5):
        """垂直寸法: y 方向距離を x=xd に記入（用紙座標）"""
        lay = "寸法"
        for x, y in ((x1, y1), (x2, y2)):
            s = 1 if xd > x else -1
            self.line((x + s * 1.0, y), (xd + s * 1.5, y), lay)
        self.line((xd, y1), (xd, y2), lay)
        d = 1 if y2 > y1 else -1
        self._arrow((xd, y1), (0, d), lay)
        self._arrow((xd, y2), (0, -d), lay)
        if label is None:
            label = fmt(abs(y2 - y1))
        self.text((xd - 0.8, (y1 + y2) / 2), label, h, layer=lay, align="c", rot=90)

    def ldim_h(self, u1, v1, u2, v2, vd, label=None):
        P1, P2 = self.T((u1, v1)), self.T((u2, v2))
        self.dim_h(P1[0], P1[1], P2[0], P2[1], self.oy - vd, label)

    def ldim_v(self, u1, v1, u2, v2, ud, label=None):
        P1, P2 = self.T((u1, v1)), self.T((u2, v2))
        self.dim_v(P1[0], P1[1], P2[0], P2[1], self.ox + ud, label)

    def leader(self, p_text, p_target, s, h=2.8, align="l"):
        """引出線付き注記（用紙座標）"""
        self.line(p_text, p_target, "寸法")
        self.circle(p_target, 0.5, "寸法")
        if not s:
            return
        dy = 0.8
        self.text((p_text[0] + (1.0 if align == "l" else -1.0), p_text[1] + dy - (h / 2)), s, h, align=align)

    # ---- 図枠・表題欄 ----
    def frame(self, subtitle, scale_note):
        x0, y0 = -SHEET_W / 2 + FRAME_M, -SHEET_H / 2 + FRAME_M
        x1, y1 = SHEET_W / 2 - FRAME_M, SHEET_H / 2 - FRAME_M
        self.polyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "図枠", closed=True)
        # 表題欄（右下）
        tx0, ty1 = x1 - 120, y0 + 30
        self.polyline([(tx0, y0), (tx0, ty1), (x1, ty1)], "図枠")
        self.line((tx0, y0 + 20), (x1, y0 + 20), "図枠")
        self.line((tx0, y0 + 10), (x1, y0 + 10), "図枠")
        self.text((tx0 + 3, y0 + 23), "薄型二つ折り財布（ファスナー小銭入れ付き）", 4.0)
        self.text((tx0 + 3, y0 + 13), subtitle, 4.0)
        self.text((tx0 + 3, y0 + 3.5), scale_note, 3.0)
        return x0, y0, x1, y1

    def scale_bar(self, x, y):
        self.line((x, y), (x + 100, y), "図枠")
        for i in range(11):
            t = 3.0 if i % 5 == 0 else 1.5
            self.line((x + i * 10, y), (x + i * 10, y + t), "図枠")
        self.text((x, y + 4.5), "印刷倍率の確認用スケール 100mm（実寸で100mmになっていればOK）", 2.5)
        self.text((x, y - 4.0), "0", 2.5, align="c")
        self.text((x + 50, y - 4.0), "50", 2.5, align="c")
        self.text((x + 100, y - 4.0), "100", 2.5, align="c")

    def legend(self, x, y, items, h=3.0, gap=6.0):
        for i, (layer, lt, label) in enumerate(items):
            yy = y - i * gap
            self.line((x, yy + h * 0.35), (x + 14, yy + h * 0.35), layer, lt)
            self.text((x + 17, yy), label, h)

    def note_lines(self, x, y, lines, h=3.0, gap=None):
        gap = gap or h * 1.6
        for i, s in enumerate(lines):
            self.text((x, y - i * gap), s, h)


def fmt(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


# =============================================================================
# DXF 出力（AutoCAD R12 ASCII / Shift-JIS）
# =============================================================================
def write_dxf(sheet, path):
    rows = []

    def g(code, val):
        if isinstance(val, float):
            val = f"{val:.6f}".rstrip("0").rstrip(".") if abs(val) > 1e-12 else "0.0"
            if "." not in val:
                val += ".0"
        rows.append(f"{code:>3}")
        rows.append(str(val))

    xs, ys = [], []
    for e in sheet.ents:
        for k in ("p", "q", "c"):
            if k in e and isinstance(e[k], tuple):
                xs.append(e[k][0])
                ys.append(e[k][1])
    # HEADER
    g(0, "SECTION"); g(2, "HEADER")
    g(9, "$ACADVER"); g(1, "AC1009")
    g(9, "$DWGCODEPAGE"); g(3, "ANSI_932")
    g(9, "$INSBASE"); g(10, 0.0); g(20, 0.0); g(30, 0.0)
    g(9, "$EXTMIN"); g(10, float(min(xs))); g(20, float(min(ys))); g(30, 0.0)
    g(9, "$EXTMAX"); g(10, float(max(xs))); g(20, float(max(ys))); g(30, 0.0)
    g(9, "$LIMMIN"); g(10, -SHEET_W / 2); g(20, -SHEET_H / 2)
    g(9, "$LIMMAX"); g(10, SHEET_W / 2); g(20, SHEET_H / 2)
    g(9, "$LTSCALE"); g(40, 1.0)
    g(9, "$TEXTSTYLE"); g(7, "STANDARD")
    g(9, "$CLAYER"); g(8, "0")
    g(9, "$LUNITS"); g(70, 2)
    g(9, "$LUPREC"); g(70, 2)
    g(0, "ENDSEC")
    # TABLES
    g(0, "SECTION"); g(2, "TABLES")
    g(0, "TABLE"); g(2, "LTYPE"); g(70, len(LTYPES))
    for name, (desc, pat) in LTYPES.items():
        g(0, "LTYPE"); g(2, name); g(70, 0); g(3, desc); g(72, 65)
        g(73, len(pat)); g(40, float(sum(abs(x) for x in pat)))
        for x in pat:
            g(49, float(x))
    g(0, "ENDTAB")
    g(0, "TABLE"); g(2, "LAYER"); g(70, len(LAYERS) + 1)
    g(0, "LAYER"); g(2, "0"); g(70, 0); g(62, 7); g(6, "CONTINUOUS")
    for name, color, lt in LAYERS:
        g(0, "LAYER"); g(2, name); g(70, 0); g(62, color); g(6, lt)
    g(0, "ENDTAB")
    g(0, "TABLE"); g(2, "STYLE"); g(70, 1)
    g(0, "STYLE"); g(2, "STANDARD"); g(70, 0); g(40, 0.0); g(41, 1.0); g(50, 0.0)
    g(71, 0); g(42, 2.5); g(3, "txt"); g(4, "")
    g(0, "ENDTAB")
    g(0, "ENDSEC")
    # BLOCKS（空）
    g(0, "SECTION"); g(2, "BLOCKS"); g(0, "ENDSEC")
    # ENTITIES
    g(0, "SECTION"); g(2, "ENTITIES")
    for e in sheet.ents:
        lcolor, lltype = LAYER_PROPS[e["layer"]]
        color = e.get("c") if e["t"] in ("LINE", "TEXT") else e.get("c_")
        color = color if isinstance(color, int) else lcolor
        lt = e.get("lt") or lltype
        if e["t"] == "LINE":
            g(0, "LINE"); g(8, e["layer"]); g(6, lt); g(62, color)
            g(10, float(e["p"][0])); g(20, float(e["p"][1])); g(30, 0.0)
            g(11, float(e["q"][0])); g(21, float(e["q"][1])); g(31, 0.0)
        elif e["t"] == "ARC":
            g(0, "ARC"); g(8, e["layer"]); g(6, lt); g(62, color)
            g(10, float(e["c"][0])); g(20, float(e["c"][1])); g(30, 0.0)
            g(40, float(e["r"])); g(50, float(e["a0"])); g(51, float(e["a1"]))
        elif e["t"] == "CIRCLE":
            g(0, "CIRCLE"); g(8, e["layer"]); g(6, lt); g(62, color)
            g(10, float(e["c"][0])); g(20, float(e["c"][1])); g(30, 0.0)
            g(40, float(e["r"]))
        elif e["t"] == "TEXT":
            g(0, "TEXT"); g(8, e["layer"]); g(62, color)
            g(10, float(e["p"][0])); g(20, float(e["p"][1])); g(30, 0.0)
            g(40, float(e["h"])); g(1, e["s"])
            if e["rot"]:
                g(50, float(e["rot"]))
            g(7, "STANDARD")
    g(0, "ENDSEC")
    g(0, "EOF")
    data = "\r\n".join(rows) + "\r\n"
    with open(path, "wb") as f:
        f.write(data.encode("cp932"))  # Jw_cad は Shift-JIS


# =============================================================================
# 型紙シート
# =============================================================================
def draw_pattern_sheet():
    s = Sheet("型紙")
    x0, y0, x1, y1 = s.frame("型紙（実寸）  ①外装 ②台座 ③前胴 ④ベルト ⑤カード押さえ",
                             "単位 mm / 縮尺 1:1 / 用紙 A3横 / 2026-10-15")

    # ---------------- ① 外装 ----------------
    s.place(-85.0, 126.0)
    s.path(body_outline(), "切断線")
    s.path(perimeter_stitch(), "縫い線")
    s.path([L((0, -4), (0, H + 4))], "折り線")
    s.path([L((UNIT_L, 0), (UNIT_L, H))], "貼り位置")
    s.path([L((-W, A_EDGE_V), (-A_BOT_U, H)), L((-W, B_EDGE_V), (-B_BOT_U, H))], "貼り位置")
    s.path([L((W, B_EDGE_V), (B_BOT_U, H))], "貼り位置")
    s.ltext((-W / 2, 30), "① 外装  ×1", 6.0, align="c")
    s.ltext((-W / 2, 39), "革厚 1.2～1.4mm（内側＝床面から見た図）", 3.0, align="c")
    s.ltext((-W / 2, 45), "←  革の伸びにくい方向  →", 3.0, align="c")
    s.ltext((1.2, 38), "中心（折り線）", 2.5, rot=-90)
    s.ltext((UNIT_L + 2, 62), "②台座の左端", 2.5)
    s.ltext((UNIT_L + 2, 66), "（ここが裏ポケット入口）", 2.5)
    s.ltext((-W + 6, 44), "④ベルト", 2.5)
    s.ltext((-W + 6, 48), "貼り位置 ↓", 2.5)
    s.ltext((W - 4, 88), "⑤", 2.5, align="r")
    s.ltext((W / 2 + 6, 30), "右半分：②③⑤を重ねる", 3.0, align="c")
    s.ltext((W / 2 + 6, 36), "（外周の縫い代だけ接着）", 3.0, align="c")
    # 寸法
    s.ldim_h(-W, 0, W, 0, -7, "204")
    s.ldim_v(-W, 0, -W, H, -W - 8, "100")
    s.ldim_v(-W, 0, -W, A_EDGE_V, -W - 3.5)
    s.ldim_v(-W, A_EDGE_V, -W, B_EDGE_V, -W - 3.5)
    s.ldim_v(-W, B_EDGE_V, -W, H, -W - 3.5)
    s.ldim_h(-W, H, -B_BOT_U, H, H + 5)
    s.ldim_h(-B_BOT_U, H, -A_BOT_U, H, H + 5)
    s.ldim_h(-A_BOT_U, H, 0, H, H + 5)
    s.ldim_h(0, H, UNIT_L, H, H + 5)
    s.ldim_h(UNIT_L, H, B_BOT_U, H, H + 5)
    s.ldim_h(B_BOT_U, H, W, H, H + 5)
    s.ldim_v(W, 0, W, B_EDGE_V, W + 4)
    s.ldim_v(W, B_EDGE_V, W, H, W + 4)
    s.ltext((-W + 1.0, 7.5), "R6", 2.5)
    s.ltext((-W + 4.5, 12.5), "縫い線はコバから3mm", 2.5)

    # ---------------- ② 台座 ----------------
    s.place(-199.0, 0.0)    # u=12 → X=-187
    s.path(base_outline(), "切断線")
    s.path(base_stitch(), "縫い線")
    s.path(l_seam(), "縫い線")
    s.path(front_free_edges(), "貼り位置")
    s.path([L((W, B_EDGE_V), (B_BOT_U, H))], "貼り位置")
    cx = (UNIT_L + W) / 2
    s.ltext((cx + 6, 26), "② 台座  ×1", 5.0, align="c")
    s.ltext((cx + 6, 32), "革厚 0.8～1.0mm", 3.0, align="c")
    s.ltext((38, 58), "破線＝③前胴・⑤の", 2.5)
    s.ltext((38, 61.5), "　　　貼り位置", 2.5)
    s.ltext((UNIT_L + 1.5, 78), "← 裏ポケット入口", 2.5)
    s.ltext((UNIT_L + 1.5, 81.5), "（先にコバ磨き）", 2.5)
    s.ltext((cx + 6, 10.5), "小銭入れ（背面）", 2.5, align="c")
    s.ldim_h(UNIT_L, 0, W, 0, -6, "90")
    s.ldim_v(UNIT_L, 0, UNIT_L, H, UNIT_L - 5, "100")

    # ---------------- ③ 前胴 ----------------
    s.place(-97.0, 0.0)     # u=12 → X=-85
    s.path(front_outline(), "切断線")
    s.path(window_cut(), "切断線")
    s.path(front_stitch(), "縫い線")
    s.path(window_stitch(), "縫い線")
    s.path(l_seam(), "縫い線")
    zc = (WIN_V0 + WIN_V1) / 2
    s.path(rect(ZIP_TAPE_U0, ZIP_TAPE_V0, ZIP_TAPE_U1, ZIP_TAPE_V1), "ファスナー", "HIDDEN")
    s.ltext((66, 56), "③ 前胴  ×1", 5.0, align="c")
    s.ltext((66, 61.5), "革厚 0.8～1.0mm", 3.0, align="c")
    s.ltext((66, 70), "カードポケット", 3.0, align="c")
    s.ltext((66, 74.5), "（6枚程度）", 2.5, align="c")
    s.ltext((57, 32.0), "小銭入れ（前面）", 3.0, align="c")
    s.ltext((60, 21.2), "緑破線＝ファスナーテープ位置（裏）", 2.2, align="c")
    s.ltext((57, zc + 0.9), "ファスナー窓（φ7ポンチ＋直線カット）", 2.0, align="c")
    s.ltext((u_on_D(62) + 3.5, 62), "カード差込口", 2.5, rot=-68.2)
    s.ltext((UNIT_L + 9.5, STEP_V + 2.0), "R9", 2.2)
    s.ltext((u_on_D(STEP_V) + 3.5, STEP_V + 4.0), "R4", 2.2)
    s.ldim_h(UNIT_L, 0, W, 0, -11, "90")
    s.ldim_h(UNIT_L, 0, WIN_U0, WIN_V0, -5.5)
    s.ldim_h(WIN_U0, WIN_V0, WIN_U1, WIN_V0, -5.5)
    s.ldim_h(WIN_U1, WIN_V0, W, 0, -5.5)
    s.ldim_v(UNIT_L, 0, WIN_U0, WIN_V0, UNIT_L - 4)
    s.ldim_v(WIN_U0, WIN_V0, WIN_U0, WIN_V1, UNIT_L - 4)
    s.ldim_v(UNIT_L, WIN_V1, UNIT_L, STEP_V, UNIT_L - 4)
    s.ldim_v(UNIT_L, STEP_V, D_BOT_U, H, UNIT_L - 4)
    s.ldim_v(W, 0, W, A_EDGE_V, W + 4)
    s.ldim_v(W, A_EDGE_V, A_BOT_U, H, W + 4)
    s.ldim_h(UNIT_L, STEP_V, D_BOT_U, H, H + 5)
    s.ldim_h(D_BOT_U, H, A_BOT_U, H, H + 5)
    s.ldim_h(A_BOT_U, H, W, A_EDGE_V, H + 5)

    # ---------------- ④ 札押さえベルト ----------------
    s.place(122.0, 52.0)    # u=-102 → X=20, v=52 → Y=0
    s.path(band_outline(), "切断線")
    s.path(band_stitch(), "縫い線")
    s.ltext((-W + 2, 113), "④ 札押さえベルト ×1", 3.5)
    s.ltext((-W + 2, 117.5), "革厚 1.0mm", 2.5)
    s.ltext((-W + 2, 121.5), "斜め2辺は先にコバ磨き", 2.5)
    s.ldim_v(-W, A_EDGE_V, -W, B_EDGE_V, -W - 4)
    s.ldim_h(-B_BOT_U, H, -A_BOT_U, H, H + 5)
    s.ldim_v(-A_BOT_U, A_EDGE_V, -A_BOT_U, H, -A_BOT_U + 4, "48")
    s.ldim_h(-W, A_EDGE_V, -A_BOT_U, A_EDGE_V, A_EDGE_V - 4, "34")
    s.ltext((-W + 14, 70), "幅約14", 2.2, rot=-54.7)

    # ---------------- ⑤ カード押さえ ----------------
    s.place(-15.0, 76.0)    # u=85 → X=70, v=76 → Y=0
    s.path(card_holder_outline(), "切断線")
    s.path(card_holder_stitch(), "縫い線")
    s.ltext((B_BOT_U - 4, 113), "⑤ カード押さえ ×1", 3.5)
    s.ltext((B_BOT_U - 4, 117.5), "革厚 0.8～1.0mm", 2.5)
    s.ltext((B_BOT_U - 4, 121.5), "斜辺は先にコバ磨き", 2.5)
    s.ldim_v(W, B_EDGE_V, W, H, W + 4)
    s.ldim_h(B_BOT_U, H, W, H, H + 5)
    s.ltext((W - 6.5, H - 7.5), "R6", 2.2)

    # ---------------- 凡例・注意 ----------------
    s.place(0, 0)
    lx, ly = 32.0, 133.0
    s.text((lx, ly - 3), "凡例", 4.0)
    s.legend(lx, ly - 11, [
        ("切断線", None, "切断線（裁断・コバ）"),
        ("縫い線", None, "縫い線（菱目打ち 3mmピッチ推奨）"),
        ("折り線", None, "中心・折り線"),
        ("貼り位置", None, "貼り位置ガイド（他パーツの位置）"),
        ("ファスナー", "HIDDEN", "ファスナーテープ（前胴の裏側）"),
    ], h=3.0, gap=5.5)
    s.text((lx, ly - 44), "注意", 4.0)
    s.note_lines(lx, ly - 51, [
        "・すべて実寸（1:1）。印刷後、下のスケールで倍率を確認。",
        "・①外装は内側（床面）から見た図。②～⑤は表（銀面）から見た図。",
        "　床面側に型紙を写すときは②～⑤を裏返して使う。",
        "・ファスナー窓の両端は φ7mm ポンチで抜き、間を直線カット。",
        "　窓幅7mmは3号コイル想定。スライダーが通らなければ8mmに。",
        "・②台座を外装に貼るのは外周の縫い代（幅5mm）だけ。",
        "　内側を接着すると裏ポケットがふさがるので注意。",
        "・④ベルトと③前胴下部は、お札・カードを挟んだ状態で",
        "　縫い代を接着すると、ほどよいゆとりができる。",
        "・④の斜め2辺、③の窓・差込口・右下斜辺、⑤の斜辺、",
        "　②の左端は、組み立て前にコバを仕上げておく。",
    ], h=2.8, gap=4.6)

    # 部品表
    tx, ty = 108.0, 2.0
    s.text((tx, ty - 3.5), "部品表", 4.0)
    rows = [
        ("No.", "部品名", "数", "革厚"),
        ("①", "外装", "1", "1.2～1.4"),
        ("②", "台座（裏ポケット／小銭・カードの背面）", "1", "0.8～1.0"),
        ("③", "前胴（小銭入れ前面＋カードポケット）", "1", "0.8～1.0"),
        ("④", "札押さえベルト", "1", "1.0"),
        ("⑤", "カード押さえ（三角）", "1", "0.8～1.0"),
    ]
    cols = [tx, tx + 8, tx + 68, tx + 75, tx + 90]
    rh = 6.0
    top = ty - 6.0
    for i, r in enumerate(rows):
        yy = top - (i + 1) * rh
        for j, c in enumerate(r):
            s.text((cols[j] + 1.2, yy + 1.8), c, 2.7)
    for i in range(len(rows) + 1):
        s.line((cols[0], top - i * rh), (cols[-1], top - i * rh), "図枠")
    for c in cols:
        s.line((c, top), (c, top - len(rows) * rh), "図枠")
    s.note_lines(tx, top - len(rows) * rh - 6, [
        "副資材",
        "・3号コイルファスナー 1本（テープ幅約26mm）",
        "　テープ長 81mm／窓長 71mm に合わせて止め金具を付ける",
        "・ロウ引き糸 0.45～0.55mm 約4m（外周＋窓＋仕切り）",
        "・接着剤（ゴム系 or 水性）、トコノール等",
    ], h=2.7, gap=4.4)

    s.scale_bar(x0 + 8, y0 + 14)
    return s


# =============================================================================
# 組立図シート
# =============================================================================
def draw_assembly_sheet():
    s = Sheet("組立図")
    x0, y0, x1, y1 = s.frame("組立図・重なり確認図・断面模式図",
                             "単位 mm / 縮尺 1:1（断面図の厚み方向は誇張）/ A3横")

    # ---------------- 展開図（内側） ----------------
    OX, OY = -75.0, 118.0
    s.place(OX, OY)
    s.text((OX - W, OY + 13), "展開図（開いて内側から見た図）", 4.0)
    s.path(body_outline(), "切断線")
    s.path(perimeter_stitch(), "縫い線")
    s.path([L((0, -4), (0, H + 4))], "折り線")
    s.path(band_outline(), "切断線")
    s.path([L((UNIT_L, 0), (UNIT_L, H))], "切断線")
    s.path(front_free_edges(), "切断線")
    s.path([L((W, B_EDGE_V), (B_BOT_U, H))], "切断線")
    s.path(window_cut(), "切断線")
    s.path(window_stitch(), "縫い線")
    s.path(l_seam(), "縫い線")
    zc = (WIN_V0 + WIN_V1) / 2
    s.path(rect(WIN_U0 + 1, zc - ZIP_ELEM_W / 2, WIN_U1 - 1, zc + ZIP_ELEM_W / 2), "ファスナー")
    s.path(rect(ZIP_TAPE_U0, ZIP_TAPE_V0, ZIP_TAPE_U1, ZIP_TAPE_V1), "ファスナー", "HIDDEN")
    s.path(card_rect(), "カード")
    s.path(bill_rect(), "お札")
    # 注記
    s.ltext((-W / 2 + 1, 50), "お札（二つ折り 80×76）", 3.0, align="c")
    s.ltext((-W / 2 + 1, 55), "札押さえベルトに角を差し込む", 2.5, align="c")
    s.ltext((-W + 22, 93), "④ベルト", 2.5)
    s.ltext((62, 28.5), "小銭入れ（3号ファスナー）", 2.6, align="c")
    s.ltext((56, 37.5), "仕切り縫い（③＋②）", 2.4, align="c")
    s.ltext((64, 68), "カード 6枚程度", 3.0, align="c")
    s.ltext((64, 72.5), "（85.6×54）", 2.5, align="c")
    s.ltext((UNIT_L - 0.8, 52), "裏ポケット入口", 2.3, rot=-90, valign="t")
    s.ltext((W - 9.5, 73.5), "窓", 2.5)
    s.ltext((W - 7.5, 95), "⑤", 2.5)
    s.ltext((u_on_D(80) - 9.5, 88), "差込口", 2.5)
    # 寸法
    s.ldim_h(-W, 0, W, 0, -9, "204（閉じると 102×100）")
    s.ldim_h(0, 0, UNIT_L, 0, -3.5)
    s.ldim_v(-W, 0, -W, H, -W - 5, "100")
    s.ldim_v(W, 0, W, SEP_V, W + 4)
    s.ldim_v(W, SEP_V, W, A_EDGE_V, W + 4)
    s.ldim_v(W, A_EDGE_V, W, B_EDGE_V, W + 4)
    s.ldim_v(W, B_EDGE_V, W, H, W + 4)
    s.ldim_h(0, H, D_BOT_U, H, H + 5)
    s.ldim_h(D_BOT_U, H, A_BOT_U, H, H + 5)
    s.ldim_h(A_BOT_U, H, B_BOT_U, H, H + 5)
    s.ldim_h(-A_BOT_U, H, 0, H, H + 5)
    s.ldim_h(-B_BOT_U, H, -A_BOT_U, H, H + 5)
    s.ldim_v(-W, 0, -W, A_EDGE_V, -W - 11)
    s.ldim_v(-W, A_EDGE_V, -W, B_EDGE_V, -W - 11)
    s.ldim_v(-W, B_EDGE_V, -W, H, -W - 11)

    # ---------------- 重なり確認図（右半分＋左ベルトを折り返し） ----------------
    CX, CY = 75.0, 118.0
    s.place(CX, CY)
    s.text((CX - 2, CY + 13), "閉じたときの重なり確認（右半分）", 4.0)
    s.path(body_right_half(), "切断線")
    s.path([L((0, -4), (0, H + 4))], "折り線")
    s.path([L((UNIT_L, 0), (UNIT_L, H))], "切断線")
    s.path(front_free_edges(), "切断線")
    s.path([L((W, B_EDGE_V), (B_BOT_U, H))], "切断線")
    s.path(window_cut(), "切断線")
    s.path(card_rect(), "カード")
    s.path(mirror_u(band_outline()), "お札", "HIDDEN")
    s.ltext((W / 2 + 6, 47), "桃色破線＝左側の④ベルトを", 2.6, align="c")
    s.ltext((W / 2 + 6, 51.5), "中心で折り返した位置", 2.6, align="c")
    s.ltext((W / 2 + 6, 58), "→ 右下のカード窓と", 2.6, align="c")
    s.ltext((W / 2 + 6, 62.5), "　ぴったり重なる（左右対称）", 2.6, align="c")
    s.leader(s.T((W + 9, 64)), s.T((u_on_A(70) + 6, 70)), "", 2.5)
    s.ltext((W + 3, 60), "ベルト", 2.5)
    s.ltext((W + 3, 64), "＝窓", 2.5)
    s.ldim_v(W, A_EDGE_V, W, B_EDGE_V, W + 13)

    # ---------------- 断面模式図 ----------------
    STEP = 4.0   # 層の間隔（厚み方向は誇張）

    def section(oy, title, items, stitches, notes):
        """items: (u0, u1, 層番号k, レイヤ, 線種) / notes: (u, 隙間番号g, 文字, 揃え)"""
        s.place(OX, oy)
        s.text(s.T((-W, -4.2 * STEP - 1.5)), title, 3.5)
        s.line(s.T((-W, 0)), s.T((W, 0)), "断面図")    # ①外装
        s.text(s.T((-W, 3.6)), "①外装", 2.3)
        for (u0, u1, k, layer, lt) in items:
            yy = -k * STEP
            s.line(s.T((u0, yy)), s.T((u1, yy)), layer, lt)
        for (u, k0, k1) in stitches:
            s.line(s.T((u, -k0 * STEP + 1.0)), s.T((u, -k1 * STEP - 1.0)), "縫い線")
        for (u, gi, txt, al) in notes:
            s.text(s.T((u, -gi * STEP - 0.8)), txt, 2.3, align=al)
        s.path([L((0, 2.5), (0, -3.8 * STEP))], "折り線")

    # A-A：ファスナーの高さ
    va = (WIN_V0 + WIN_V1) / 2
    section(-20.0, f"断面 A-A（上端から {fmt(va)}mm：ファスナー・小銭入れの位置）", [
        (UNIT_L, W, 1, "断面図", None),                        # ②台座
        (ZIP_TAPE_U0, ZIP_TAPE_U1, 2.75, "ファスナー", None),  # テープ
        (UNIT_L, WIN_U0, 3, "断面図", None),                   # ③前胴
        (WIN_U1, W, 3, "断面図", None),
        (WIN_U0 + 1, WIN_U1 - 1, 3, "ファスナー", None),       # エレメント
    ], [(-W + SM, 0, 0), (W - SM, 0, 3), (SEAM_U, 1, 3)], [
        (-W / 2, 0, "（この高さはお札なし）", "c"),
        (UNIT_L + 4.5, 0, "裏ポケット（①と②の間）", "l"),
        (57, 1, "小銭入れ（②と③の間）", "c"),
        (57, 3, "③前胴の窓 ＋ ファスナー", "c"),
        (UNIT_L + 4.5, 1, "L字縫い", "l"),
    ])
    # B-B：カード・窓・ベルトの高さ
    vb = 85.0
    section(-55.0, f"断面 B-B（上端から {fmt(vb)}mm：カード・窓・ベルトの位置）", [
        (-W + SM + 0.5, -W + SM + 0.5 + BILL_W, 1, "お札", "CONTINUOUS"),
        (-u_on_B(vb), -u_on_A(vb), 2, "断面図", None),          # ④ベルト
        (UNIT_L, W, 1, "断面図", None),                         # ②台座
        (W - SM - 0.5 - CARD_W, W - SM - 0.5, 2, "カード", "CONTINUOUS"),
        (u_on_D(vb), u_on_A(vb), 3, "断面図", None),            # ③前胴
        (u_on_B(vb), W, 3, "断面図", None),                     # ⑤
    ], [(-W + SM, 0, 0), (W - SM, 0, 3)], [
        (-W / 2 + 10, 1, "お札（二つ折り）", "c"),
        (-(u_on_A(vb) + u_on_B(vb)) / 2, 2, "④", "c"),
        (UNIT_L + 4.5, 0, "裏ポケット", "l"),
        (27, 2, "カード×6", "c"),
        ((u_on_D(vb) + u_on_A(vb)) / 2, 3, "③前胴", "c"),
        ((u_on_A(vb) + u_on_B(vb)) / 2, 2.25, "窓", "c"),
        ((u_on_B(vb) + W) / 2, 3, "⑤", "c"),
    ])
    for uu in (u_on_A(vb), u_on_B(vb)):
        s.line(s.T((uu, 2.0)), s.T((uu, -3.8 * STEP)), "貼り位置")
        s.line(s.T((-uu, 2.0)), s.T((-uu, -3.8 * STEP)), "貼り位置")
    s.text(s.T((-W, 7.5)), "※ 水色破線：中心で折ると ④ベルト（左）が 窓（右）にちょうど重なる（左右対称）", 2.5)

    # ---------------- 仕様・手順 ----------------
    s.place(0, 0)
    nx = 50.0
    s.text((nx, 3.0), "仕様", 4.0)
    s.note_lines(nx, -4.0, [
        "・サイズ：開き 204×100mm／閉じ 102×100mm",
        "・厚み目安：約12mm（カード6枚・お札数枚・小銭数枚）",
        "・お札：二つ折り（80×76）をベルトで角留め",
        "・カード：1ポケットに6枚程度。左の差込口から出し入れ、",
        "　右下の窓に指をかけて左へスライドさせて取り出す",
        "・小銭入れ：3号コイルファスナー、開口 約71mm",
        "・裏ポケット：②台座と外装の間（入口は中心から12mm）",
        "　標準カード（85.6×54）横入れ、大きめのカードは縦入れで",
        "　約55×90mm まで",
    ], h=2.7, gap=4.4)
    s.text((nx, -46.0), "作り方の順序", 4.0)
    s.note_lines(nx, -53.0, [
        "1. 裁断 → 床面処理 → 自由辺（窓・差込口・斜辺・②左端・④）のコバ仕上げ",
        "2. ③前胴の裏にファスナーを貼り、窓のまわりを縫う",
        "3. ③前胴と②台座を重ね、L字の縫い線（小銭入れ左＋仕切り）を縫う",
        "4. ⑤と③下部の縫い代を②に接着（カードを3枚ほど挟んでゆとりを作る）",
        "5. ②③⑤のユニットを外装右側に、外周の縫い代だけで接着",
        "6. ④ベルトを外装左下に接着（お札を挟んでゆとりを作る）",
        "7. 外周を一周縫う → 外周のコバ仕上げ → 中心に折り癖を付ける",
    ], h=2.6, gap=4.3)
    return s


# =============================================================================
# プレビュー（PDF/PNG）
# =============================================================================
ACI_RGB = {1: "#d00000", 2: "#c8a000", 3: "#00902a", 4: "#0090c0", 5: "#1040e0", 6: "#d000c0", 7: "#000000"}
LW_MM = {"切断線": 0.35, "断面図": 0.4, "縫い線": 0.25, "図枠": 0.35}


def render(sheet, pdf_path, png_path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        from matplotlib.patches import Arc, Circle
    except ImportError:
        print("matplotlib が無いのでプレビューを省略")
        return
    matplotlib.rcParams["lines.scale_dashes"] = False
    font_path = None
    for cand in ("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
                 "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
                 "C:/Windows/Fonts/msgothic.ttc"):
        if os.path.exists(cand):
            font_path = cand
            break
    fp = font_manager.FontProperties(fname=font_path) if font_path else None
    mm2pt = 72 / 25.4
    fig = plt.figure(figsize=(SHEET_W / 25.4, SHEET_H / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-SHEET_W / 2, SHEET_W / 2)
    ax.set_ylim(-SHEET_H / 2, SHEET_H / 2)
    ax.set_aspect("equal")
    ax.axis("off")

    def style(e):
        lcolor, lltype = LAYER_PROPS[e["layer"]]
        color = e.get("c") if e["t"] in ("LINE", "TEXT") else e.get("c_")
        color = ACI_RGB[color if isinstance(color, int) else lcolor]
        lt = e.get("lt") or lltype
        pat = LTYPES[lt][1]
        ls = "-" if not pat else (0, [abs(x) * mm2pt for x in pat])
        lw = LW_MM.get(e["layer"], 0.18) * mm2pt
        return color, ls, lw

    for e in sheet.ents:
        if e["t"] == "TEXT":
            color, _, _ = style(e)
            ax.text(e["p"][0], e["p"][1], e["s"], fontsize=e["h"] * mm2pt, rotation=e["rot"],
                    rotation_mode="anchor", ha="left", va="baseline", color=color,
                    fontproperties=fp)
            continue
        color, ls, lw = style(e)
        if e["t"] == "LINE":
            ax.plot([e["p"][0], e["q"][0]], [e["p"][1], e["q"][1]], color=color, lw=lw,
                    linestyle=ls, solid_capstyle="round")
        elif e["t"] == "ARC":
            ax.add_patch(Arc(e["c"], 2 * e["r"], 2 * e["r"], theta1=e["a0"], theta2=e["a1"],
                             color=color, lw=lw, linestyle=ls))
        elif e["t"] == "CIRCLE":
            ax.add_patch(Circle(e["c"], e["r"], fill=False, color=color, lw=lw, linestyle=ls))
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=150, facecolor="white")
    plt.close(fig)


def check_cp932(sheet):
    for e in sheet.ents:
        if e["t"] == "TEXT":
            e["s"].encode("cp932")  # 変換できない文字があればここで例外
    for n, _, _ in LAYERS:
        n.encode("cp932")


def main():
    stitches = {
        "外周": path_length(perimeter_stitch()),
        "ファスナー窓": path_length(window_stitch()),
        "L字（小銭入れ左＋仕切り）": path_length(l_seam()),
    }
    print("縫い線の長さ:", {k: round(v, 1) for k, v in stitches.items()},
          "糸の目安(×4):", round(sum(stitches.values()) * 4 / 1000, 2), "m")
    for name, sheet in (("pattern", draw_pattern_sheet()), ("assembly", draw_assembly_sheet())):
        check_cp932(sheet)
        dxf = os.path.join(OUT_DIR, f"wallet_{name}_A3.dxf")
        write_dxf(sheet, dxf)
        render(sheet, os.path.join(OUT_DIR, f"wallet_{name}_A3.pdf"),
               os.path.join(OUT_DIR, f"preview_{name}.png"))
        print("wrote", dxf, len(sheet.ents), "entities")


if __name__ == "__main__":
    main()
