#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
薄型二つ折り財布（立体ポケット＋上部ファスナー小銭入れ）設計図ジェネレータ

出力（このスクリプトと同じフォルダ）:
  wallet_pattern_A3.dxf    型紙（実寸 1/1・A3横）
  wallet_assembly_A3.dxf   組立図（完成状態の展開図・重なり確認・断面図）
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
# 完成状態を内側から見た座標（投影）: u = 中心（折り線）から右が＋、v = 上端から下が＋
# =============================================================================
W = 105.0            # 片側の幅（閉じたときの横幅）。開いた全幅は 2W
H = 100.0            # 高さ
R_OUT = 6.0          # 外周コーナー R
SM = 3.0             # コバから縫い線までの距離

# 右側ユニット（②台座＋③前胴＋⑤カード押さえ＋⑥裏ポケット板）
# 外装には右端（ヒンジ）だけで縫い付ける → めくれて、下にお札の右半分が入る
UL = 12.0            # ユニットの左端（中心からの距離）
ZT = 2.0             # ユニットの上端（ここにファスナーの務歯が乗り、外装の上端とほぼ揃う）
R_UNIT_TOP = 4.0     # ユニット右上の角 R（外装の R6 の内側に収まる）
BACK_TOP = 30.0      # ⑥裏ポケット板の上端

# ③前胴の立体（箱）: タブを縫い付け、壁を手前に折り上げる
T = 6.0              # タブ（縫い付ける部分）の幅
G = 6.0              # 壁（マチ）の高さ ＝ 手前に折り上げる幅
GAP = 4.0            # 小銭入れとカードポケットの間の谷（平らに縫う部分）の幅
CB = 33.0            # 小銭入れの底の折り線
KT = CB + GAP        # カードポケット上の折り線
KB = H - T           # カードポケット底の折り線
FL = UL + T          # 小銭入れの左の壁
FR = W - T           # 右の壁
SEP_V = CB + GAP / 2  # 仕切り（谷）の縫い線
ZIP_ST = ZT + 2.5    # ファスナーテープを縫う線

# 斜めライン（中心線に対して左右対称）
#   A: 左＝札押さえベルトの上辺 / 右＝カード窓の上辺（前胴の右下辺）
#   B: 左＝札押さえベルトの下辺 / 右＝カード窓の下辺（カード押さえの斜辺）
A_EDGE_V, A_BOT_U = 44.0, 63.0   # 外装の側面で v=44、下辺で |u|=63
B_EDGE_V, B_BOT_U = 68.0, 81.0   # 外装の側面で v=68、下辺で |u|=81
# カード差込口（前胴左の斜め辺）: カードポケット上端で u=27、底で u=50
D_TOP_U, D_BOT_U = 27.0, 50.0

# ファスナー（3号コイル）
ZIP_TAPE_U0, ZIP_TAPE_U1 = UL + 1.0, W - 2.0   # テープの左右端
ZIP_TAPE_IN = 12.0   # 務歯から内側へ入るテープの幅

# 収納物（参考線）
CARD_W, CARD_H, CARD_R = 85.6, 54.0, 3.0
BILL_W, BILL_H = 160.0, 76.0     # 一万円札（折らずに入れる）
BILL_U0 = -82.0                  # お札の左端（右半分がユニットの下に入る位置）
LEATHER_T = 0.8                  # 壁の革厚（内寸の計算用）

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
    return D_TOP_U + (D_BOT_U - D_TOP_U) * (v - KT) / (KB - KT)


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
# 部品形状
#   「投影」= 完成状態を内側から見た位置（財布座標）
#   「展開」= 型紙（革を平らに置いた形）。③⑤は壁とタブの分だけ大きい
# =============================================================================
def body_outline():  # ① 外装
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


def hinge_stitch(v0=R_OUT, v1=H - R_OUT):
    """右辺の縫い線＝ヒンジ（外装とユニットを一緒に縫う唯一の縫い目）"""
    return [L((W - SM, v0), (W - SM, v1))]


def unit_bottom_stitch(u0=UL):
    return [
        L((u0, H - SM), (W - R_OUT, H - SM)),
        arc_deg((W - R_OUT, H - R_OUT), R_OUT - SM, 90, 0),
    ]


def base_outline():  # ② 台座
    return rounded_polygon([(UL, ZT), (W, ZT), (W, H), (UL, H)], [0, R_UNIT_TOP, R_OUT, 0])


def back_outline():  # ⑥ 裏ポケット板
    return rounded_polygon([(UL, BACK_TOP), (W, BACK_TOP), (W, H), (UL, H)], [0, 0, R_OUT, 0])


def band_outline():  # ④ 札押さえベルト
    return rounded_polygon(
        [(-W, A_EDGE_V), (-A_BOT_U, H), (-B_BOT_U, H), (-W, B_EDGE_V)], [0, 0, 0, 0]
    )


def band_stitch():
    return [
        L((-W + SM, v_on_A(W - SM)), (-W + SM, v_on_B(W - SM))),
        L((-u_on_A(H - SM), H - SM), (-u_on_B(H - SM), H - SM)),
    ]


# ---- ③ 前胴：展開（型紙） ----
# 小銭入れ部は 展開＝投影。カード部は 谷（壁2枚）の分だけ下へ 2G ずれる。
CARD_DY = 2 * G


def front_flat_outline():
    xr = FR + G + T          # 右タブの外側
    xl = FL - G - T          # 左タブの外側
    ya = v_on_A(FR) + CARD_DY
    return rounded_polygon(
        [
            (xl, ZT),
            (xr, ZT),
            (xr, CB),
            (FR, CB),
            (FR, KT + CARD_DY),
            (xr, KT + CARD_DY),
            (xr, v_on_A(W) + CARD_DY),               # 右タブの下端は A の延長
            (FR + G, ya),
            (FR, ya),
            (u_on_A(KB), KB + CARD_DY),
            (u_on_A(KB), KB + CARD_DY + G),
            (u_on_A(H), KB + CARD_DY + G + T),       # 下タブの右端は A の延長
            (u_on_D(H), KB + CARD_DY + G + T),       # 下タブの左端は D の延長
            (u_on_D(KB), KB + CARD_DY + G),
            (u_on_D(KB), KB + CARD_DY),
            (u_on_D(KT), KT + CARD_DY),
            (u_on_D(KT), KT + G),
            (FL, KT + G),
            (FL, CB),
            (xl, CB),
        ],
        [0, R_UNIT_TOP, 1.0, 1.5, 1.5, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.5, 1.0, 1.5, 1.5],
    )


def front_flat_mountain():
    """山折り（革の表から見て山）＝面と壁の境"""
    ya = v_on_A(FR) + CARD_DY
    return [
        L((FL, ZT), (FL, CB)),
        L((FR, ZT), (FR, CB)),
        L((FL, CB), (FR, CB)),
        L((u_on_D(KT), KT + CARD_DY), (FR, KT + CARD_DY)),
        L((FR, KT + CARD_DY), (FR, ya)),
        L((u_on_D(KB), KB + CARD_DY), (u_on_A(KB), KB + CARD_DY)),
    ]


def front_flat_valley():
    """谷折り＝壁とタブ（または仕切りの谷）の境"""
    ya = v_on_A(FR) + CARD_DY
    return [
        L((FL - G, ZT), (FL - G, CB)),
        L((FR + G, ZT), (FR + G, CB)),
        L((FL, CB + G), (FR, CB + G)),
        L((u_on_D(KT), KT + G), (FR, KT + G)),
        L((FR + G, KT + CARD_DY), (FR + G, ya)),
        L((u_on_D(KB), KB + CARD_DY + G), (u_on_A(KB), KB + CARD_DY + G)),
    ]


def front_flat_stitch():
    xh = FR + G + SM                       # ヒンジ（投影 u=W-3）
    ya = v_on_A(FR) + CARD_DY
    yb = KB + CARD_DY + G + SM             # 下タブ（投影 v=H-3）
    return [
        L((FL + 1.5, ZIP_ST), (FR - 1.5, ZIP_ST)),                 # ファスナー
        L((FL - G - T + SM, ZT + 2), (FL - G - T + SM, BACK_TOP - 2)),  # 左タブ
        L((xh, R_OUT + 0.5), (xh, CB - 2)),                         # 右タブ（ヒンジ）
        L((xh, KT + CARD_DY + 2), (xh, v_on_A(W - SM) + CARD_DY - 2)),  # 右タブ（ヒンジ）
        L((FL + 2, SEP_V + G), (FR - 2, SEP_V + G)),                # 仕切りの谷
        L((u_on_D(H - SM) + 1.5, yb), (u_on_A(H - SM) - 1.5, yb)),  # 下タブ
    ]


def zip_tape_on_front():
    return rect(FL, ZT, FR, ZT + ZIP_TAPE_IN)


# ---- ③ 前胴：投影（完成状態の位置。②への貼り位置・組立図用） ----
def front_proj_outline():
    return rounded_polygon(
        [
            (UL, ZT), (W, ZT), (W, CB), (FR, CB), (FR, KT), (W, KT), (W, A_EDGE_V),
            (A_BOT_U, H), (u_on_D(H), H), (u_on_D(KT), KT), (FL, KT), (FL, CB), (UL, CB),
        ],
        [0, R_UNIT_TOP] + [0] * 11,
    )


def front_proj_walls():
    return [
        L((FL, ZT), (FL, CB)),
        L((FR, ZT), (FR, CB)),
        L((FL, CB), (FR, CB)),
        L((u_on_D(KT), KT), (FR, KT)),
        L((FR, KT), (FR, v_on_A(FR))),
        L((u_on_D(KB), KB), (u_on_A(KB), KB)),
    ]


# ---- ⑤ カード押さえ：展開・投影 ----
def holder_flat_outline():
    xr = FR + G + T
    return rounded_polygon(
        [
            (FR, v_on_B(FR)),
            (FR + G, v_on_B(FR)),
            (xr, B_EDGE_V),                 # 右タブの上端は B の延長
            (xr, KB),
            (FR, KB),
            (FR, KB + G),
            (W, KB + G),
            (W, KB + G + T),
            (B_BOT_U, KB + G + T),          # 下タブの左端は B の延長
            (u_on_B(KB), KB + G),
            (u_on_B(KB), KB),
        ],
        [0, 0, 0, 1.0, 1.0, 1.0, 0, R_OUT, 0, 0, 0],
    )


def holder_flat_mountain():
    return [L((FR, v_on_B(FR)), (FR, KB)), L((u_on_B(KB), KB), (FR, KB))]


def holder_flat_valley():
    return [L((FR + G, v_on_B(FR)), (FR + G, KB)), L((u_on_B(KB), KB + G), (FR, KB + G))]


def holder_flat_stitch():
    yb = KB + G + SM
    return [
        L((FR + G + SM, v_on_B(W - SM) + 2), (FR + G + SM, KB - 1.5)),
        L((u_on_B(H - SM) + 1.5, yb), (FR, yb)),
        arc_deg((FR, KB + G), SM, 90, 0),
    ]


def holder_proj_outline():
    return rounded_polygon(
        [(W, B_EDGE_V), (W, H), (B_BOT_U, H)],
        [0, R_OUT, 0],
    )


def holder_proj_walls():
    return [L((FR, v_on_B(FR)), (FR, KB)), L((u_on_B(KB), KB), (FR, KB))]


# ---- 収納物（参考） ----
def card_rect():
    u1 = FR - LEATHER_T - 0.5
    v1 = KB - LEATHER_T - 0.3
    return rect(u1 - CARD_W, v1 - CARD_H, u1, v1, CARD_R)


def bill_rect():
    v1 = H - SM - 0.5
    return rect(BILL_U0, v1 - BILL_H, BILL_U0 + BILL_W, v1)


COINS = [((34.0, 17.5), 26.5, "500円"), ((63.0, 18.0), 22.6, "100円"), ((87.0, 18.0), 20.0, "1円")]


# =============================================================================
# 図面（エンティティ）とレイヤ
# =============================================================================
# (名前, 色(ACI), 既定線種)
LAYERS = [
    ("切断線", 7, "CONTINUOUS"),
    ("縫い線", 1, "DASHED"),
    ("山折り", 4, "CENTER"),
    ("谷折り", 4, "HIDDEN"),
    ("中心線", 4, "CENTER"),
    ("貼り位置", 6, "HIDDEN"),
    ("ファスナー", 3, "CONTINUOUS"),
    ("カード", 5, "PHANTOM"),
    ("お札", 6, "PHANTOM"),
    ("小銭", 2, "PHANTOM"),
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
    "HIDDEN": ("Hidden _ _ _ _", [1.2, -0.8]),
    "CENTER": ("Center ____ _ ____", [6.0, -1.2, 1.0, -1.2]),
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
    x0, y0, x1, y1 = s.frame("型紙（実寸）  部品 ①～⑥",
                             "単位 mm / 縮尺 1:1 / 用紙 A3横 / 2026-10-15")

    # ---------------- ① 外装 ----------------
    s.place(-85.0, 124.0)
    s.path(body_outline(), "切断線")
    s.path(perimeter_stitch(), "縫い線")
    s.path([L((0, -4), (0, H + 4))], "中心線")
    s.path([L((UL, 0), (UL, H))], "貼り位置")
    s.path([L((-W, A_EDGE_V), (-A_BOT_U, H)), L((-W, B_EDGE_V), (-B_BOT_U, H))], "貼り位置")
    s.ltext((-W / 2, 30), "① 外装  ×1", 6.0, align="c")
    s.ltext((-W / 2, 38), "革厚 1.2～1.4mm（内側＝床面から見た図）", 3.0, align="c")
    s.ltext((-W / 2, 44), "←  革の伸びにくい方向  →", 3.0, align="c")
    s.ltext((1.2, 36), "中心（折り線）", 2.5, rot=-90)
    s.ltext((-W + 22, 62), "← ④ベルト貼り位置", 2.5)
    s.ltext((UL + 2, 30), "右側ユニット（②③⑤⑥）の左端", 2.5)
    s.ltext((W / 2 + 4, 52), "ユニットは右辺（ヒンジ）だけで", 3.0, align="c")
    s.ltext((W / 2 + 4, 57), "縫い付ける（接着もしない）", 3.0, align="c")
    s.ltext((W / 2 + 4, 63), "→ めくって下にお札を入れる", 3.0, align="c")
    s.ltext((W - 4.5, 50), "ヒンジ", 2.5, rot=-90)
    s.ldim_h(-W, 0, W, 0, -7, "210")
    s.ldim_v(-W, 0, -W, H, -W - 8, "100")
    s.ldim_v(-W, 0, -W, A_EDGE_V, -W - 3.5)
    s.ldim_v(-W, A_EDGE_V, -W, B_EDGE_V, -W - 3.5)
    s.ldim_v(-W, B_EDGE_V, -W, H, -W - 3.5)
    s.ldim_h(-W, H, -B_BOT_U, H, H + 5)
    s.ldim_h(-B_BOT_U, H, -A_BOT_U, H, H + 5)
    s.ldim_h(-A_BOT_U, H, 0, H, H + 5)
    s.ldim_h(0, H, UL, H, H + 5)
    s.ldim_h(UL, H, W, H, H + 5)
    s.ltext((-W + 1.0, 7.5), "R6", 2.5)

    # ---------------- ③ 前胴（立体の展開図） ----------------
    xl, xr = FL - G - T, FR + G + T
    yb = KB + CARD_DY + G + T
    s.place(32.0 - xl, 124.0 + ZT)
    s.path(front_flat_outline(), "切断線")
    s.path(front_flat_mountain(), "山折り")
    s.path(front_flat_valley(), "谷折り")
    s.path(front_flat_stitch(), "縫い線")
    s.path(zip_tape_on_front(), "ファスナー", "HIDDEN")
    s.ltext(((FL + FR) / 2, 22.5), "小銭入れの面", 3.0, align="c")
    s.ltext(((FL + FR) / 2, 27.5), "上端にファスナー（裏に下側テープ）", 2.3, align="c")
    s.ltext((FL + 1.0, ZT + ZIP_TAPE_IN + 3.0), "緑破線＝テープ", 2.0)
    s.ltext((70, 64), "③ 前胴 ×1", 5.0, align="c")
    s.ltext((70, 70), "革厚 0.8mm（柔らかめ）", 2.7, align="c")
    s.ltext((70, 78), "カードポケットの面", 3.0, align="c")
    s.ltext((70, 82.5), "（6枚程度）", 2.5, align="c")
    s.ltext((u_on_D(80) + 3.0, 80 + CARD_DY - 10), "差込口", 2.4, rot=-68)
    s.ltext((FL + 2, KT + CARD_DY + 4.0), "↑ 壁・谷・壁（谷の縫い線で②⑥と縫う）", 2.2)
    s.ltext((xl + 0.6, 20), "タブ", 2.0, rot=-90)
    s.ltext((FL - G + 0.6, 20), "壁", 2.0, rot=-90)
    s.ltext((FR + 0.6, 20), "壁", 2.0, rot=-90)
    s.ltext((FR + G + 0.6, 22), "タブ", 2.0, rot=-90)
    # 寸法
    s.ldim_h(xl, ZT, xr, ZT, ZT - 10, fmt(xr - xl))
    s.ldim_h(xl, ZT, FL - G, ZT, ZT - 5)
    s.ldim_h(FL - G, ZT, FL, ZT, ZT - 5)
    s.ldim_h(FL, ZT, FR, ZT, ZT - 5)
    s.ldim_h(FR, ZT, FR + G, ZT, ZT - 5)
    s.ldim_h(FR + G, ZT, xr, ZT, ZT - 5)
    s.ldim_v(xl, ZT, xl, CB, xl - 4)
    s.ldim_v(xl, CB, xl, CB + G, xl - 4)
    s.ldim_v(xl, CB + G, xl, KT + G, xl - 4)
    s.ldim_v(xl, KT + G, xl, KT + CARD_DY, xl - 4)
    s.ldim_v(xl, KT + CARD_DY, xl, KB + CARD_DY, xl - 4)
    s.ldim_v(xl, KB + CARD_DY, xl, KB + CARD_DY + G, xl - 4)
    s.ldim_v(xl, KB + CARD_DY + G, xl, yb, xl - 4)
    s.ldim_v(xr, KT + CARD_DY, xr, v_on_A(W) + CARD_DY, xr + 4)
    s.ldim_v(xr, v_on_A(W) + CARD_DY, xr, v_on_A(FR) + CARD_DY, xr + 4)
    s.ldim_v(xr, ZT, xr, CB, xr + 4)
    s.ldim_v(xr, CB, xr, KT + CARD_DY, xr + 4)
    s.ldim_h(xl, yb, u_on_D(KT), KT + CARD_DY, yb + 5)
    s.ldim_h(u_on_D(KT), KT + CARD_DY, u_on_D(KB), yb, yb + 5)
    s.ldim_h(u_on_D(KB), yb, u_on_A(KB), yb, yb + 5)
    s.ldim_h(u_on_A(KB), yb, FR, yb, yb + 5)
    s.ldim_h(FR, yb, xr, yb, yb + 5)
    s.ltext((FR - 9.5, CB - 1.0), "R1.5", 1.8)

    # ---------------- 凡例 ----------------
    s.place(0, 0)
    lx, ly = 150.0, 128.0
    s.text((lx, ly - 3), "凡例", 4.0)
    s.legend(lx, ly - 10, [
        ("切断線", None, "切断線"),
        ("縫い線", None, "縫い線（3mmピッチ）"),
        ("山折り", None, "山折り（面と壁の境）"),
        ("谷折り", None, "谷折り（壁とタブの境）"),
        ("中心線", None, "中心（外装の折り）"),
        ("貼り位置", None, "貼り位置ガイド"),
        ("ファスナー", "HIDDEN", "ファスナーテープ"),
    ], h=2.6, gap=5.0)
    s.note_lines(lx, ly - 50, [
        "③⑤は「立体」の型紙。",
        "タブを②に縫い付け、",
        "壁を手前に折り上げると",
        "高さ6mmの箱になる。",
        "折り線の床面は漉くか",
        "溝を入れると折りやすい。",
        "（山＝表側が山、谷＝表側が谷）",
    ], h=2.5, gap=4.2)

    # ---------------- ② 台座 ----------------
    s.place(-190.0 - UL, -6.0)
    s.path(base_outline(), "切断線")
    s.path(front_proj_outline(), "貼り位置")
    s.path(front_proj_walls(), "貼り位置")
    s.path(holder_proj_outline(), "貼り位置")
    s.path(rect(ZIP_TAPE_U0, ZT, ZIP_TAPE_U1, ZT + ZIP_TAPE_IN), "ファスナー", "HIDDEN")
    s.path([L((FL + 1.5, ZIP_ST), (FR - 1.5, ZIP_ST))], "縫い線")
    s.path([L((UL + SM, ZT + 2), (UL + SM, BACK_TOP - 2))], "縫い線")
    s.path([L((FL + 2, SEP_V), (FR - 2, SEP_V))], "縫い線")
    s.path(unit_bottom_stitch(), "縫い線")
    s.path(hinge_stitch(), "縫い線")
    s.ltext((62, 63), "② 台座 ×1", 4.5, align="c")
    s.ltext((62, 68.5), "革厚 0.8～1.0mm", 2.6, align="c")
    s.ltext((62, 22), "上側テープ（表に貼る）", 2.3, align="c")
    s.ltext((UL + 1.0, 46), "左端は裏ポケットの入口", 2.3, rot=-90)
    s.ldim_h(UL, ZT, W, ZT, ZT - 5, fmt(W - UL))
    s.ldim_v(UL, ZT, UL, H, UL - 5, fmt(H - ZT))

    # ---------------- ⑥ 裏ポケット板 ----------------
    s.place(-84.0 - UL, -8.0 + BACK_TOP)
    s.path(back_outline(), "切断線")
    s.path([L((FL + 2, SEP_V), (FR - 2, SEP_V))], "縫い線")
    s.path(unit_bottom_stitch(), "縫い線")
    s.path(hinge_stitch(BACK_TOP + 2), "縫い線")
    s.ltext((58, 56), "⑥ 裏ポケット板 ×1", 4.0, align="c")
    s.ltext((58, 62), "革厚 0.8～1.0mm", 2.6, align="c")
    s.ltext((58, 68), "②の裏に重ねる（間が裏ポケット）", 2.4, align="c")
    s.ltext((58, 72.5), "上端・左端は先にコバ仕上げ", 2.4, align="c")
    s.ldim_h(UL, BACK_TOP, W, BACK_TOP, BACK_TOP - 5, fmt(W - UL))
    s.ldim_v(UL, BACK_TOP, UL, H, UL - 5, fmt(H - BACK_TOP))

    # ---------------- ④ 札押さえベルト ----------------
    s.place(20.0 + W, -12.0 + A_EDGE_V)
    s.path(band_outline(), "切断線")
    s.path(band_stitch(), "縫い線")
    s.ltext((-W + 1, H + 10), "④ 札押さえベルト ×1", 3.2)
    s.ltext((-W + 1, H + 14.5), "革厚 1.0mm／斜め2辺は先に磨く", 2.3)
    s.ldim_v(-W, A_EDGE_V, -W, B_EDGE_V, -W - 4)
    s.ldim_h(-B_BOT_U, H, -A_BOT_U, H, H + 5)
    s.ldim_h(-W, A_EDGE_V, -A_BOT_U, A_EDGE_V, A_EDGE_V - 4)
    s.ldim_v(-A_BOT_U, A_EDGE_V, -A_BOT_U, H, -A_BOT_U + 4)

    # ---------------- ⑤ カード押さえ（立体の展開図） ----------------
    s.place(70.0 - B_BOT_U, -12.0 + B_EDGE_V)
    s.path(holder_flat_outline(), "切断線")
    s.path(holder_flat_mountain(), "山折り")
    s.path(holder_flat_valley(), "谷折り")
    s.path(holder_flat_stitch(), "縫い線")
    s.ltext((B_BOT_U - 1, KB + G + T + 10), "⑤ カード押さえ ×1", 3.2)
    s.ltext((B_BOT_U - 1, KB + G + T + 14.5), "革厚 0.8mm／斜辺は先に磨く", 2.3)
    s.ldim_h(B_BOT_U, KB + G + T, FR + G + T, KB, KB + G + T + 5)
    s.ldim_v(FR + G + T, B_EDGE_V, FR + G + T, KB + G + T, FR + G + T + 4)

    # ---------------- 部品表・注意 ----------------
    s.place(0, 0)
    tx, ty = 112.0, 2.0
    s.text((tx, ty - 3.5), "部品表", 4.0)
    rows = [
        ("No.", "部品名", "数", "革厚"),
        ("①", "外装", "1", "1.2～1.4"),
        ("②", "台座（小銭・カードの背面）", "1", "0.8～1.0"),
        ("③", "前胴（立体：小銭入れ＋カード）", "1", "0.8"),
        ("④", "札押さえベルト", "1", "1.0"),
        ("⑤", "カード押さえ（立体）", "1", "0.8"),
        ("⑥", "裏ポケット板", "1", "0.8～1.0"),
    ]
    cols = [tx, tx + 7, tx + 60, tx + 66, tx + 82]
    rh = 5.5
    top = ty - 6.0
    for i, r in enumerate(rows):
        yy = top - (i + 1) * rh
        for j, c in enumerate(r):
            s.text((cols[j] + 1.0, yy + 1.6), c, 2.5)
    for i in range(len(rows) + 1):
        s.line((cols[0], top - i * rh), (cols[-1], top - i * rh), "図枠")
    for c in cols:
        s.line((c, top), (c, top - len(rows) * rh), "図枠")
    s.note_lines(tx, top - len(rows) * rh - 6, [
        "副資材",
        "・3号コイルファスナー 1本：務歯 81mm（止め金具の間）",
        "　テープ長 約90mm、内側へ12mm残してカット",
        "・ロウ引き糸 0.45～0.55mm 約5m",
        "注意",
        "・すべて実寸。下のスケールで印刷倍率を確認。",
        "・①は内側（床面）から、②～⑥は表から見た図。",
        "・③⑤の角の小さなRは、折ったときの裂け防止。",
        "・ユニット（②③⑤⑥）と①は接着しない。",
    ], h=2.5, gap=4.1)

    s.scale_bar(x0 + 8, y0 + 14)
    return s


# =============================================================================
# 組立図シート
# =============================================================================
class Sec:
    """断面模式図用。a=横方向の位置[mm]、k=層の高さ（厚み方向は誇張）"""

    def __init__(self, s, ox, oy, step=2.5):
        self.s, self.ox, self.oy, self.step = s, ox, oy, step

    def P(self, a, k):
        return (self.ox + a, self.oy + k * self.step)

    def h(self, a0, a1, k, layer="断面図", lt=None):
        self.s.line(self.P(a0, k), self.P(a1, k), layer, lt)

    def v(self, a, k0, k1, layer="断面図", lt=None):
        self.s.line(self.P(a, k0), self.P(a, k1), layer, lt)

    def box(self, a0, a1, k0, k1, layer, lt=None):
        self.s.polyline([self.P(a0, k0), self.P(a1, k0), self.P(a1, k1), self.P(a0, k1)],
                        layer, closed=True, ltype=lt)

    def t(self, a, k, txt, h=2.2, align="c"):
        self.s.text(self.P(a, k), txt, h, align=align)


K_BODY, K_BILL, K_BACK, K_BASE, K_TAB, K_FACE = 0.0, 0.7, 1.5, 2.6, 2.95, 5.4


def draw_assembly_sheet():
    s = Sheet("組立図")
    x0, y0, x1, y1 = s.frame("組立図（完成状態）・重なり確認・断面模式図",
                             "単位 mm / 縮尺 1:1（断面図の厚み方向は誇張）/ A3横")

    # ---------------- 展開図（完成状態を内側から） ----------------
    OX, OY = -80.0, 120.0
    s.place(OX, OY)
    s.text((OX - W, OY + 13), "完成状態を開いて内側から見た図", 4.0)
    s.path(body_outline(), "切断線")
    s.path(perimeter_stitch(), "縫い線")
    s.path([L((0, -4), (0, H + 4))], "中心線")
    s.path(band_outline(), "切断線")
    s.path([L((UL, CB), (UL, H))], "切断線")
    s.path(front_proj_outline(), "切断線")
    s.path(front_proj_walls(), "切断線")
    s.path(holder_proj_outline(), "切断線")
    s.path(holder_proj_walls(), "切断線")
    s.path(rect(FL, 0.0, FR, ZT), "ファスナー")
    s.path([L((UL + SM, ZT + 2), (UL + SM, BACK_TOP - 2))], "縫い線")
    s.path([L((FL + 2, SEP_V), (FR - 2, SEP_V))], "縫い線")
    s.path([L((FL + 1.5, ZIP_ST), (FR - 1.5, ZIP_ST))], "縫い線")
    s.path(card_rect(), "カード")
    s.path(bill_rect(), "お札")
    for (c, d, _) in COINS:
        s.circle(s.T(c), d / 2, "小銭")
    s.ltext((-W / 2 - 2, 45), "お札（折らずに入れる）", 3.0, align="c")
    s.ltext((-W / 2 - 2, 50), "右半分は右側ユニットの下へ", 2.5, align="c")
    s.ltext((-W / 2 - 2, 54.5), "左下の角をベルトに差し込む", 2.5, align="c")
    s.ltext((-W + 23, 93), "④ベルト", 2.4)
    s.ltext((56, 12.5), "小銭入れ（マチ6）", 2.6, align="c")
    s.ltext((70, 62), "カード 6枚程度", 3.0, align="c")
    s.ltext((70, 66.5), "（マチ6）", 2.4, align="c")
    s.ltext((FL - 1, -1.2), "ファスナー（上端）", 2.3, align="l")
    s.ltext((u_on_D(80) - 9.0, 86), "差込口", 2.4)
    s.ltext((W - 9.0, 73), "窓", 2.5)
    s.ltext((W - 6.0, 92), "⑤", 2.5)
    s.ltext((UL - 0.8, 60), "裏ポケット入口", 2.2, rot=-90, valign="t")
    s.ltext((W + 1.2, 12), "ヒンジ（右辺だけ縫う）", 2.2, rot=-90)
    # 寸法
    s.ldim_h(-W, 0, W, 0, -9, "210（閉じると 105×100）")
    s.ldim_h(0, 0, UL, 0, -3.5)
    s.ldim_v(-W, 0, -W, H, -W - 4, "100")
    s.ldim_v(-W, 0, -W, A_EDGE_V, -W - 9)
    s.ldim_v(-W, A_EDGE_V, -W, B_EDGE_V, -W - 9)
    s.ldim_v(-W, B_EDGE_V, -W, H, -W - 9)
    s.ldim_v(W, 0, W, CB, W + 8)
    s.ldim_v(W, CB, W, KT, W + 8)
    s.ldim_v(W, KT, W, KB, W + 8)
    s.ldim_v(W, KB, W, H, W + 8)
    s.ldim_h(-B_BOT_U, H, -A_BOT_U, H, H + 5)
    s.ldim_h(-A_BOT_U, H, 0, H, H + 5)
    s.ldim_h(0, H, u_on_D(H), H, H + 5)
    s.ldim_h(u_on_D(H), H, A_BOT_U, H, H + 5)
    s.ldim_h(A_BOT_U, H, B_BOT_U, H, H + 5)

    # ---------------- 重なり確認（右半分＋左のベルトを折り返し） ----------------
    CX, CY = 60.0, 120.0
    s.place(CX, CY)
    s.text((CX - 2, CY + 13), "閉じたときの重なり（右半分）", 4.0)
    s.path(body_right_half(), "切断線")
    s.path([L((0, -4), (0, H + 4))], "中心線")
    s.path([L((UL, CB), (UL, H))], "切断線")
    s.path(front_proj_outline(), "切断線")
    s.path(front_proj_walls(), "切断線")
    s.path(holder_proj_outline(), "切断線")
    s.path(card_rect(), "カード")
    s.path(mirror_u(band_outline()), "お札", "HIDDEN")
    s.ltext((W / 2 + 8, 44), "桃色破線＝左の④ベルトを", 2.5, align="c")
    s.ltext((W / 2 + 8, 48.5), "中心で折り返した位置", 2.5, align="c")
    s.ltext((W / 2 + 8, 54), "→ 窓とぴったり重なる", 2.5, align="c")
    s.ldim_v(W, A_EDGE_V, W, B_EDGE_V, W + 5)

    # ---------------- 断面模式図 ----------------
    def sec_common(sc, items, notes, stitches):
        sc.h(-W, W, K_BODY)
        for it in items:
            if it[0] == "h":
                sc.h(*it[1:])
            elif it[0] == "v":
                sc.v(*it[1:])
            else:
                sc.box(*it[1:])
        for (a, k0, k1) in stitches:
            sc.v(a, k0, k1, "縫い線")
        for (a, k, txt, al) in notes:
            sc.t(a, k, txt, 2.1, al)
        sc.v(0, -0.6, K_FACE + 0.6, "中心線")

    # A-A：小銭入れ
    va = 22.0
    sa = Sec(s, OX, -18.0)
    s.text(sa.P(-W, K_FACE + 1.6), f"断面 A-A（上端から {fmt(va)}mm：小銭入れ）", 3.3)
    sec_common(sa, [
        ("h", BILL_U0, BILL_U0 + BILL_W, K_BILL, "お札", "CONTINUOUS"),
        ("h", UL, W, K_BASE),
        ("h", UL, FL, K_TAB), ("h", FR, W, K_TAB),
        ("v", FL, K_BASE, K_FACE), ("v", FR, K_BASE, K_FACE),
        ("h", FL, FR, K_FACE),
        ("b", 20.8, 47.3, K_TAB, K_TAB + 0.5, "小銭"),
        ("b", 51.7, 74.3, K_TAB, K_TAB + 0.5, "小銭"),
    ], [
        (-W + 1, -1.5, "①外装", "l"),
        (-40, K_BILL + 0.25, "お札", "c"),
        (45, K_BILL + 0.25, "お札の右半分（めくって入れる）", "c"),
        (57, K_TAB + 0.9, "小銭", "c"),
        (57, K_FACE + 0.3, "③小銭入れ（高さ6）", "c"),
        (UL - 1, K_BASE - 0.3, "②", "r"),
        (W + 1, K_TAB, "ヒンジ", "l"),
    ], [(-W + SM, -0.4, 0.4), (W - SM, -0.4, K_TAB + 0.4), (UL + SM, K_BASE - 0.4, K_TAB + 0.4)])

    # B-B：カード・窓・ベルト
    vb = 85.0
    sb = Sec(s, OX, -52.0)
    s.text(sb.P(-W, K_FACE + 1.6), f"断面 B-B（上端から {fmt(vb)}mm：カード・窓・ベルト）", 3.3)
    c0, c1 = FR - LEATHER_T - 0.5 - CARD_W, FR - LEATHER_T - 0.5
    sec_common(sb, [
        ("h", BILL_U0, BILL_U0 + BILL_W, K_BILL, "お札", "CONTINUOUS"),
        ("h", -u_on_B(vb), -u_on_A(vb), K_BACK),
        ("h", UL, W, K_BACK),
        ("h", UL, W, K_BASE),
        ("b", c0, c1, K_TAB, K_FACE - 0.35, "カード", "CONTINUOUS"),
        ("h", u_on_D(vb), u_on_A(vb), K_FACE),
        ("h", u_on_B(vb), FR, K_FACE),
        ("v", FR, K_BASE, K_FACE),
        ("h", FR, W, K_TAB),
    ], [
        (-W + 1, -1.5, "①外装", "l"),
        (-30, K_BILL + 0.25, "お札", "c"),
        (-(u_on_A(vb) + u_on_B(vb)) / 2, K_BACK + 0.3, "④", "c"),
        (UL + 3, K_BACK + 0.3, "裏ポケット", "l"),
        (UL - 1, K_BACK - 0.3, "⑥", "r"),
        (UL - 1, K_BASE - 0.1, "②", "r"),
        (28, K_TAB + 0.6, "カード×6", "c"),
        ((u_on_D(vb) + u_on_A(vb)) / 2, K_FACE + 0.3, "③", "c"),
        ((u_on_A(vb) + u_on_B(vb)) / 2, K_FACE + 0.3, "窓", "c"),
        ((u_on_B(vb) + FR) / 2, K_FACE + 0.3, "⑤", "c"),
    ], [(-W + SM, -0.4, 0.4), (W - SM, -0.4, K_TAB + 0.4)])
    for uu in (u_on_A(vb), u_on_B(vb)):
        sb.v(uu, -0.6, K_FACE + 0.8, "中心線", "HIDDEN")
        sb.v(-uu, -0.6, K_FACE + 0.8, "中心線", "HIDDEN")
    s.text(sb.P(-W, -3.2), "※ 水色破線：閉じると ④ベルト（左）が 窓（右）にちょうど重なる", 2.3)

    # C-C：縦断面（u=60）
    sc = Sec(s, -185.0, -96.0)
    s.text(sc.P(0, K_FACE + 1.6), "断面 C-C（中心から60mmの縦断面：左が上端）", 3.3)
    sc.h(0, H, K_BODY)
    sc.h(H - SM - 0.5 - BILL_H, H - SM - 0.5, K_BILL, "お札", "CONTINUOUS")
    sc.h(BACK_TOP, H, K_BACK)
    sc.h(ZT, H, K_BASE)
    sc.box(-0.3, ZT, K_BASE, K_FACE, "ファスナー")
    sc.h(ZT, ZT + ZIP_TAPE_IN, K_BASE + 0.15, "ファスナー")
    sc.h(ZT, ZT + ZIP_TAPE_IN, K_FACE - 0.15, "ファスナー")
    sc.h(ZT, CB, K_FACE)
    sc.v(CB, K_BASE, K_FACE)
    sc.h(CB, KT, K_TAB)
    sc.v(KT, K_BASE, K_FACE)
    sc.h(KT, KB, K_FACE)
    sc.v(KB, K_BASE, K_FACE)
    sc.h(KB, H, K_TAB)
    sc.box(KB - LEATHER_T - 0.3 - CARD_H, KB - LEATHER_T - 0.3, K_TAB, K_FACE - 0.35, "カード", "CONTINUOUS")
    sc.box(4.25, 30.75, K_TAB, K_TAB + 0.5, "小銭")
    for (a, k0, k1) in [(ZIP_ST, K_BASE - 0.4, K_BASE + 0.5), (ZIP_ST, K_FACE - 0.5, K_FACE + 0.4),
                        (SEP_V, K_BACK - 0.4, K_TAB + 0.4), (H - SM, K_BACK - 0.4, K_TAB + 0.4),
                        (SM, -0.4, 0.4), (H - SM, -0.4, 0.4)]:
        sc.v(a, k0, k1, "縫い線")
    sc.t(-1, K_FACE + 0.3, "ファスナー", 2.1, "r")
    sc.t(17.5, K_FACE + 0.3, "小銭入れ", 2.1, "c")
    sc.t(SEP_V, K_FACE + 0.3, "仕切り", 2.1, "c")
    sc.t(66, K_FACE + 0.3, "カードポケット", 2.1, "c")
    sc.t(66, K_TAB + 0.6, "カード", 2.1, "c")
    sc.t(66, K_BACK + 0.3, "裏ポケット", 2.1, "c")
    sc.t(17.5, K_BILL + 0.25, "お札", 2.1, "c")
    sc.t(H + 1, K_BASE - 0.4, "②", 2.1, "l")
    sc.t(H + 1, K_BACK - 0.5, "⑥", 2.1, "l")
    sc.t(H + 1, K_BODY - 0.5, "①", 2.1, "l")

    # 閉じた状態を上から見た図（模式）
    tv = Sec(s, -180.0, -133.0, 2.2)
    s.text(tv.P(-5, 10.8), "閉じた状態を上から見た図（模式）", 3.3)
    tv.h(0, W, 0)
    tv.h(0, W, 8.6)
    s.arc(tv.P(0, 4.3), 4.3 * 2.2, 90, 270, "断面図")
    tv.h(UL, W, K_BASE - 0.6)
    tv.box(FL, FR, K_BASE - 0.6, K_FACE - 0.6, "ファスナー")
    tv.h(FL, FR, K_FACE - 0.6)
    tv.box(FL + 2, FL + 9, K_FACE - 0.6, K_FACE + 1.2, "ファスナー")
    tv.h(UL, W, K_BACK - 0.6, "断面図", "HIDDEN")
    tv.h(0, BILL_U0 + BILL_W, 0.6, "お札", "CONTINUOUS")
    tv.h(0, -BILL_U0, 7.6, "お札", "CONTINUOUS")
    s.arc(tv.P(0, 4.1), 3.5 * 2.2, 90, 270, "お札")
    tv.t(W + 4, 6.0, "ファスナーは上端に出ているので、", 2.6, "l")
    tv.t(W + 4, 4.2, "財布を閉じたまま開けて小銭を出せる。", 2.6, "l")
    tv.t(W + 4, 2.4, "（開けて両端を軽く押すと口が開く）", 2.4, "l")
    tv.t(W / 2, 8.9, "外装（左半分）", 2.1, "c")
    tv.t(W / 2, -1.8, "外装（右半分）", 2.1, "c")
    tv.t(FL + 10, K_FACE + 0.1, "引手", 2.1, "l")

    # ---------------- 仕様・手順 ----------------
    s.place(0, 0)
    nx = 48.0
    s.text((nx, 6.0), "仕様", 4.0)
    s.note_lines(nx, -1.0, [
        "・サイズ：開き 210×100mm／閉じ 105×100mm、厚み約14mm",
        "・お札：折らずに入れる。右半分は右側ユニットの下（めくって入れる）",
        "・小銭入れ：上端にファスナー。閉じたままでも上から開けられる",
        "　（高さ6mmの箱。開けて両端を軽く押すと口が開く）",
        "・カード：6枚程度。左の差込口から入れ、右下の窓で滑らせて出す",
        "・裏ポケット：②と⑥の間（入口は左端）。約88×60mmまで",
    ], h=2.5, gap=4.1)
    s.text((nx, -30.0), "作り方の順序", 4.0)
    s.note_lines(nx, -37.0, [
        "1. 裁断・床面処理。③⑤の折り線に溝を入れ、自由辺のコバを仕上げる",
        "2. ファスナー：下側テープを③の上端の裏、上側テープを②の上端の表に貼り、",
        "　 それぞれ上端から2.5mmで縫う（務歯は②③の上端の間に出す）",
        "3. ③のタブと谷を②に貼り、左タブ（中心から15mm）を縫う",
        "4. ⑥を②の裏に重ね、仕切りの谷を ③＋②＋⑥ まとめて縫う",
        "5. ③⑤の下タブ・右タブを②に貼る（カード3枚ほど入れて壁を立てる）",
        "6. 下端（③⑤の下タブ＋②＋⑥）を縫う → ユニット完成",
        "7. ①に④を貼り、外周を右辺以外すべて縫う",
        "8. ユニットを①の右に重ね、右辺（ヒンジ）を全部まとめて縫う",
        "9. 右辺のコバを仕上げ、中心に折り癖を付ける",
    ], h=2.4, gap=3.9)
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
        "外周（ヒンジ含む）": path_length(perimeter_stitch()),
        "ユニット下端": path_length(unit_bottom_stitch()),
        "ファスナー×2": 2 * (FR - FL - 3.0),
        "左タブ": BACK_TOP - ZT - 4,
        "仕切り": FR - FL - 4,
    }
    total = sum(stitches.values())
    print("縫い線の長さ:", {k: round(v, 1) for k, v in stitches.items()},
          "合計", round(total), "mm / 糸の目安(×4):", round(total * 4 / 1000, 2), "m")
    for name, sheet in (("pattern", draw_pattern_sheet()), ("assembly", draw_assembly_sheet())):
        check_cp932(sheet)
        dxf = os.path.join(OUT_DIR, f"wallet_{name}_A3.dxf")
        write_dxf(sheet, dxf)
        render(sheet, os.path.join(OUT_DIR, f"wallet_{name}_A3.pdf"),
               os.path.join(OUT_DIR, f"preview_{name}.png"))
        print("wrote", dxf, len(sheet.ents), "entities")


if __name__ == "__main__":
    main()
