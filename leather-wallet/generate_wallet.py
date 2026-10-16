#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
薄型二つ折り財布（立体ポケット＋上部ファスナー小銭入れ）設計図ジェネレータ

出力（このスクリプトと同じフォルダ）:
  dxf/wallet_A4_1～6_*.dxf   A4横・実寸 1/1 の図面6枚（1～3：型紙、4～6：組立図）
  wallet_A4_all.pdf          上の6枚をまとめた印刷用PDF（matplotlib がある場合）
  preview/page1～6.png       プレビュー画像

DXF は Jw_cad で読み込める AutoCAD R12 形式（ASCII・Shift-JIS・CRLF）。
座標原点 (0,0) は A4 用紙の中心（Jw_cad の原点＝用紙中心に合わせている）。

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
W = 113.0            # 片側の幅（閉じたときの横幅）。開いた全幅は 2W
                     # カードの左端が小銭入れの左の壁 FL にそろう幅（W − T − 0.8 − 0.5 − 85.6 ≒ FL）
H = 100.0            # 高さ
R_OUT = 6.0          # 外周コーナー R
SM = 3.0             # コバから縫い線までの距離

# 右側ユニット（②台座＋③前胴＋⑤裏ポケット布＋⑧③の裏地）
# 外装には右辺と下辺で縫い付ける。上辺と左辺は開いていて、下にお札の右半分が入る
UL = 14.0            # ユニットの左端（中心からの距離）＝折り代。閉じたとき自然に閉じる余裕
ZT = 2.0             # ユニットの上端（ここにファスナーの務歯が乗り、外装の上端とほぼ揃う）
R_UNIT_TOP = 4.0     # ユニット右上の角 R（外装の R6 の内側に収まる）

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

# 斜めライン（中心線に対して左右対称）。u + K_AB * v = 一定 の直線（45°）
#   A: 左＝札押さえベルトの上辺 / 右＝カード窓の上辺
#   B: 左＝札押さえベルトの下辺 / 右＝カード窓の下辺（③に一体化した角押さえの斜辺）
K_AB = 1.0                       # 傾き du/dv（45°。窓の角が鈍角 135° になる）
A_EDGE_V, B_EDGE_V = 53.0, 70.0  # 外装の側面での位置（ベルトの幅 約12）
WIN_CLEAR = 1.5                  # 窓をベルトより片側この分だけ広げる（手作りの誤差の逃げ）
C_A = W + K_AB * A_EDGE_V        # ベルト上辺
C_B = W + K_AB * B_EDGE_V        # ベルト下辺
CW_A = C_A - WIN_CLEAR * math.hypot(1, K_AB)   # 窓の上辺（③のカード面）
CW_B = C_B + WIN_CLEAR * math.hypot(1, K_AB)   # 窓の下辺（③の角押さえ）

# カード差込口（③前胴左の斜め辺）: カードポケット上端で u=D_TOP_U、底で u=D_BOT_U
D_TOP_U, D_BOT_U = 25.0, 42.0

# ⑤裏ポケット（布・上から入れる2段）。完成時の上端は斜め：(左端 u=UL での v, 右端 u=W での v)
POCKETS = ((30.0, 22.0), (42.0, 34.0))   # ⑤a（奥・②側）, ⑤b（手前・外装側）
FOLD_ALLOW = 6.0                 # 上端の折り返し代
FABRIC_INSET = 0.5               # 布の端を革のコバより内側に下げる量

# ⑥裏地（外装の内側全面・布）と ⑦芯材（左側だけ）
CORE_IN = 2.0                    # 芯材を縫い線から離す量
CORE_FOLD = UL + 2.0             # 芯材の中心側の端（中心からの距離）。折り目には入れない

# ファスナー（3号コイル）
ZIP_TAPE_U0, ZIP_TAPE_U1 = UL + 1.0, W - 2.0   # テープの左右端
ZIP_TAPE_IN = 12.0   # 務歯から内側へ入るテープの幅
ZIP_TEETH = FR - FL  # 務歯の長さ（止め金具の間）
ZIP_LEN = ZIP_TEETH + 11.0   # 買うときのテープ長の目安

# 収納物（参考線）
CARD_W, CARD_H, CARD_R = 85.6, 54.0, 3.0
BILL_W, BILL_H = 160.0, 76.0     # 一万円札（折らずに入れる）
BILL_U0 = -(W - 23.0)            # お札の左端（右半分がユニットの下に入る位置。左下の角が④に入る）
LEATHER_T = 0.8                  # 壁の革厚（内寸の計算用）


def u_on(c, v):
    """斜めライン（u + K_AB*v = c）上で、高さ v の点の u"""
    return c - K_AB * v


def v_on(c, u):
    return (c - u) / K_AB


A_BOT_U = u_on(C_A, H)           # ベルト上辺が外装の下辺と交わる位置（中心から）
B_BOT_U = u_on(C_B, H)


def u_on_D(v):
    return D_TOP_U + (D_BOT_U - D_TOP_U) * (v - KT) / (KB - KT)


def pocket_top_v(idx, u):
    """⑤の完成時の上端（斜め）の高さ"""
    vl, vr = POCKETS[idx]
    return vl + (vr - vl) * (u - UL) / (W - UL)


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
#   「展開」= 型紙（平らに置いた形）。③は壁とタブの分だけ大きい
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


def unit_attach_stitch(top=R_OUT):
    """ユニットを外装に縫い付ける線：下辺（ユニット左端から）＋右下の角＋右辺"""
    return [
        L((UL, H - SM), (W - R_OUT, H - SM)),
        arc_deg((W - R_OUT, H - R_OUT), R_OUT - SM, 90, 0),
        L((W - SM, H - R_OUT), (W - SM, top)),
    ]


def left_seam(top=ZT + 2):
    """ユニット左端の縦の縫い線：③左タブ＋②＋⑤a＋⑤b（裏ポケットの左側も閉じる）"""
    return [L((UL + SM, top), (UL + SM, H - SM))]


def base_outline():  # ② 台座
    return rounded_polygon([(UL, ZT), (W, ZT), (W, H), (UL, H)], [0, R_UNIT_TOP, R_OUT, 0])


def pocket_outline(idx):
    """⑤ 裏ポケット布（上端は斜め。折り返し代つき）"""
    i, a = FABRIC_INSET, FOLD_ALLOW
    t = lambda u: pocket_top_v(idx, u)
    return rounded_polygon(
        [
            (UL + i + 1, t(UL + i + 1) - a), (W - i - 1, t(W - i - 1) - a),
            (W - i - 1, t(W - i - 1) - 1), (W - i, t(W - i)),
            (W - i, H - i), (UL + i, H - i), (UL + i, t(UL + i)), (UL + i + 1, t(UL + i + 1) - 1),
        ],
        [0, 0, 0, 0, R_OUT - i, 0, 0, 0],
    )


def pocket_fold(idx):
    u0, u1 = UL + FABRIC_INSET, W - FABRIC_INSET
    return [L((u0, pocket_top_v(idx, u0)), (u1, pocket_top_v(idx, u1)))]


def pocket_top_stitch(idx):
    """折り返しを押さえる縫い（任意。ミシンでも手縫いでも）"""
    u0, u1 = UL + SM + 2, W - SM - 2
    return [L((u0, pocket_top_v(idx, u0) + 3), (u1, pocket_top_v(idx, u1) + 3))]


def lining_outline():  # ⑥ 裏地（外装の内側全面）
    i = FABRIC_INSET
    return rounded_polygon([(-W + i, i), (W - i, i), (W - i, H - i), (-W + i, H - i)], [R_OUT - i] * 4)


def core_outline():  # ⑦ 芯材（左側だけ。縫い線と折り目にかけない）
    u0, u1 = -(W - SM - CORE_IN), -CORE_FOLD
    v0, v1 = SM + CORE_IN, H - SM - CORE_IN
    return rounded_polygon([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], [4.0, 2.0, 2.0, 4.0])


def core_outline_box():
    return (-(W - SM - CORE_IN), -CORE_FOLD, SM + CORE_IN, H - SM - CORE_IN)


# 閉じたときの厚みの目安（カード部）[mm]
_T_FIXED = 1.0 * 2 + 0.2 * 2 + 0.4 + 0.2 * 2 + 0.8 + G   # ①×2＋⑥×2＋⑦＋⑤×2＋②＋③の箱
THICK = {"min": round(_T_FIXED + 0.2, 1),                # お札1～2枚
         "max": round(_T_FIXED + 1.0 + 2 * 0.76, 1)}     # お札10枚程度＋裏ポケットにカード各1枚


def offset_convex(pts, dists):
    """凸多角形の各辺を内側へ dists[i] だけ平行移動した多角形（辺 i は pts[i]→pts[i+1]）"""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    sgn = 1 if area > 0 else -1
    lines = []
    for i in range(n):
        p, q = pts[i], pts[(i + 1) % n]
        d = unit(sub(q, p))
        nrm = (-d[1] * sgn, d[0] * sgn)       # 内向きの法線
        lines.append((add(p, mul(nrm, dists[i])), d))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        den = d1[0] * d2[1] - d1[1] * d2[0]
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
        out.append(add(p1, mul(d1, t)))
    return out


def band_outline():  # ④ 札押さえベルト
    return rounded_polygon(
        [(-W, A_EDGE_V), (-A_BOT_U, H), (-B_BOT_U, H), (-W, B_EDGE_V)], [0, 0, 0, 0]
    )


def band_stitch():
    return [
        L((-W + SM, v_on(C_A, W - SM)), (-W + SM, v_on(C_B, W - SM))),
        L((-u_on(C_A, H - SM), H - SM), (-u_on(C_B, H - SM), H - SM)),
    ]


# ---- ③ 前胴：展開（型紙） ----
# 小銭入れ部は 展開＝投影。カード部は谷（壁2枚）の分だけ下へ 2G ずれる。
CARD_DY = 2 * G


def front_flat_outline():
    """③ 外形。カード部の右下の角押さえ（旧カード押さえ）は右タブ・下タブでつながった一体形"""
    xr = FR + G + T          # 右タブの外側
    xl = FL - G - T          # 左タブの外側
    yb = KB + CARD_DY        # カード面の底（展開）
    return rounded_polygon(
        [
            (xl, ZT),
            (xr, ZT),
            (xr, CB),
            (FR, CB),
            (FR, KT + CARD_DY),
            (xr, KT + CARD_DY),
            (xr, yb),                    # 右タブは角まで続く
            (FR, yb),                    # 角の切り欠き（壁どうしが当たらないように）
            (FR, yb + G),
            (W, yb + G),
            (W, yb + G + T),             # 角は外装と同じ R6
            (u_on_D(H), yb + G + T),     # 下タブの左端は差込口の線の延長
            (u_on_D(KB), yb + G),
            (u_on_D(KB), yb),
            (u_on_D(KT), KT + CARD_DY),
            (u_on_D(KT), KT + G),
            (FL, KT + G),
            (FL, CB),
            (xl, CB),
        ],
        [0, R_UNIT_TOP, 1.0, 1.5, 1.5, 1.0, 1.0, 1.0, 1.0, 0, R_OUT, 0, 0, 0, 0, 1.5, 1.0, 1.5, 1.5],
    )


def front_flat_window():
    """③ のカード窓（くり抜き）。左右の斜辺はベルトの線＋片側1.5mm"""
    dy = CARD_DY
    return rounded_polygon(
        [
            (FR, v_on(CW_A, FR) + dy),
            (u_on(CW_A, KB), KB + dy),
            (u_on(CW_A, KB), KB + dy + G),
            (u_on(CW_B, KB), KB + dy + G),
            (u_on(CW_B, KB), KB + dy),
            (FR, v_on(CW_B, FR) + dy),
            (FR + G, v_on(CW_B, FR) + dy),
            (FR + G, v_on(CW_A, FR) + dy),
        ],
        [1.0] * 8,
    )


def front_flat_mountain():
    """山折り（革の表から見て山）＝面と壁の境"""
    dy = CARD_DY
    return [
        L((FL, ZT), (FL, CB)),
        L((FR, ZT), (FR, CB)),
        L((FL, CB), (FR, CB)),
        L((u_on_D(KT), KT + dy), (FR, KT + dy)),
        L((FR, KT + dy), (FR, v_on(CW_A, FR) + dy)),
        L((FR, v_on(CW_B, FR) + dy), (FR, KB + dy)),
        L((u_on_D(KB), KB + dy), (u_on(CW_A, KB), KB + dy)),
        L((u_on(CW_B, KB), KB + dy), (FR, KB + dy)),
    ]


def front_flat_valley():
    """谷折り＝壁とタブ（または仕切りの谷）の境"""
    dy = CARD_DY
    return [
        L((FL - G, ZT), (FL - G, CB)),
        L((FR + G, ZT), (FR + G, CB)),
        L((FL, CB + G), (FR, CB + G)),
        L((u_on_D(KT), KT + G), (FR, KT + G)),
        L((FR + G, KT + dy), (FR + G, v_on(CW_A, FR) + dy)),
        L((FR + G, v_on(CW_B, FR) + dy), (FR + G, KB + dy)),
        L((u_on_D(KB), KB + dy + G), (u_on(CW_A, KB), KB + dy + G)),
        L((u_on(CW_B, KB), KB + dy + G), (FR, KB + dy + G)),
    ]


def front_flat_stitch():
    xh = FR + G + SM                       # 右辺（投影 u=W-3）
    yb = KB + CARD_DY + G + SM             # 下辺（投影 v=H-3）
    return [
        L((FL + 1.5, ZIP_ST), (FR - 1.5, ZIP_ST)),                    # ファスナー
        L((FL - G - T + SM, ZT + 2), (FL - G - T + SM, CB - 1.5)),     # 左タブ
        L((xh, R_OUT + 0.5), (xh, CB - 2)),                            # 右タブ（小銭）
        L((xh, KT + CARD_DY + 2), (xh, KB + CARD_DY - 1.5)),           # 右タブ（カード）
        L((FL + 2, SEP_V + G), (FR - 2, SEP_V + G)),                   # 仕切りの谷
        L((u_on_D(H - SM) + 1.5, yb), (FR, yb)),                       # 下タブ
        arc_deg((FR, KB + CARD_DY + G), SM, 90, 0),
    ]


def card_face_proj():
    """③ カード面（窓より上・左の部分）の投影形"""
    return [(u_on_D(KT), KT), (FR, KT), (FR, v_on(CW_A, FR)), (u_on(CW_A, KB), KB), (u_on_D(KB), KB)]


def front_lining_flat():
    """⑧ ③の裏地：カード面の裏に貼る布。折り線から0.5mm、自由辺から1mm内側"""
    pts = offset_convex(card_face_proj(), [0.5, 0.5, 1.0, 0.5, 1.0])
    return rounded_polygon([(u, v + CARD_DY) for (u, v) in pts], [1.0] * len(pts))


def zip_tape_on_front():
    return rect(FL, ZT, FR, ZT + ZIP_TAPE_IN)


# ---- ③ 前胴：投影（完成状態の位置。②への貼り位置・組立図用） ----
def front_proj_outline():
    return rounded_polygon(
        [
            (UL, ZT), (W, ZT), (W, CB), (FR, CB), (FR, KT), (W, KT), (W, H),
            (u_on_D(H), H), (u_on_D(KT), KT), (FL, KT), (FL, CB), (UL, CB),
        ],
        [0, R_UNIT_TOP, 0, 0, 0, 0, R_OUT, 0, 0, 0, 0, 0],
    )


def front_proj_window():
    return rounded_polygon(
        [(FR, v_on(CW_A, FR)), (u_on(CW_A, KB), KB), (u_on(CW_B, KB), KB), (FR, v_on(CW_B, FR))],
        [0, 0, 0, 0],
    )


def front_proj_walls():
    return [
        L((FL, ZT), (FL, CB)),
        L((FR, ZT), (FR, CB)),
        L((FL, CB), (FR, CB)),
        L((u_on_D(KT), KT), (FR, KT)),
        L((FR, KT), (FR, v_on(CW_A, FR))),
        L((FR, v_on(CW_B, FR)), (FR, KB)),
        L((u_on_D(KB), KB), (u_on(CW_A, KB), KB)),
        L((u_on(CW_B, KB), KB), (FR, KB)),
    ]


# ---- 収納物（参考） ----
def card_rect():
    u1 = FR - LEATHER_T - 0.5
    v1 = KB - LEATHER_T - 0.3
    return rect(u1 - CARD_W, v1 - CARD_H, u1, v1, CARD_R)


def bill_rect():
    v1 = H - SM - 0.5
    return rect(BILL_U0, v1 - BILL_H, BILL_U0 + BILL_W, v1)


COINS = [((36.5, 17.5), 26.5, "500円"), ((67.0, 18.0), 22.6, "100円"), ((94.0, 18.0), 20.0, "1円")]

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
    ("芯材・裏地", 2, "CONTINUOUS"),
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

SHEET_W, SHEET_H = 297.0, 210.0   # A4 横
FRAME_M = 10.0


def text_width(s, h):
    w = 0.0
    for ch in s:
        o = ord(ch)
        w += h * (0.5 if o < 0x80 or 0xFF61 <= o <= 0xFF9F else 1.0)
    return w


class Sheet:
    """A4 用紙1枚分の図面。座標は用紙中心原点・mm・Y上向き"""

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
        tx0, ty1 = x1 - 110, y0 + 21
        self.polyline([(tx0, y0), (tx0, ty1), (x1, ty1)], "図枠")
        self.line((tx0, y0 + 14), (x1, y0 + 14), "図枠")
        self.line((tx0, y0 + 7), (x1, y0 + 7), "図枠")
        self.text((tx0 + 2, y0 + 15.8), "薄型二つ折り財布（ファスナー小銭入れ付き）", 3.0)
        self.text((tx0 + 2, y0 + 8.8), subtitle, 3.0)
        self.text((tx0 + 2, y0 + 2.2), scale_note, 2.3)
        return x0, y0, x1, y1

    def scale_bar(self, x, y):
        self.line((x, y), (x + 100, y), "図枠")
        for i in range(11):
            t = 3.0 if i % 5 == 0 else 1.5
            self.line((x + i * 10, y), (x + i * 10, y + t), "図枠")
        self.text((x, y + 4.5), "倍率確認用 100mm（実寸で100mmならOK）", 2.3)
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
# 図面ページ（A4横 × 6枚。1～3：型紙、4～6：組立図）
# =============================================================================
PAGE_TOTAL = 6
DATE = "2026-10-16"


def new_page(no, subtitle, assembly=False):
    s = Sheet(subtitle)
    note = ("単位 mm / 縮尺 1:1（断面図の厚み方向は誇張）/ A4横" if assembly
            else "単位 mm / 縮尺 1:1（実寸）/ A4横 / " + DATE)
    box = s.frame(f"{no}/{PAGE_TOTAL}  {subtitle}", note)
    return s, box


PATTERN_LEGEND = [
    ("切断線", None, "切断線"),
    ("縫い線", None, "縫い線"),
    ("山折り", None, "山折り"),
    ("谷折り", None, "谷折り・折り返し"),
    ("中心線", None, "中心（折り）"),
    ("貼り位置", None, "貼り位置"),
    ("ファスナー", "HIDDEN", "ファスナーテープ"),
    ("芯材・裏地", None, "芯材・裏地の線"),
]


def draw_body_pattern(s):
    """① 外装（⑦芯材・⑥裏地の切り線入り）。place 済みの座標に描く"""
    s.path(body_outline(), "切断線")
    s.path(perimeter_stitch(), "縫い線")
    s.path([L((0, -4), (0, H + 4))], "中心線")
    s.path([L((UL, 0), (UL, H))], "貼り位置")
    s.path([L((-W, A_EDGE_V), (-A_BOT_U, H)), L((-W, B_EDGE_V), (-B_BOT_U, H))], "貼り位置")
    s.path(core_outline(), "芯材・裏地")
    s.path(lining_outline(), "芯材・裏地", "HIDDEN")
    s.ltext((-W / 2, 30), "① 外装  ×1", 6.0, align="c")
    s.ltext((-W / 2, 38), "牛革 1.0mm（内側＝床面から見た図）", 3.0, align="c")
    s.ltext((-W / 2, 44), "←  革の伸びにくい方向  →", 3.0, align="c")
    s.ltext((1.2, 36), "中心（折り線）", 2.5, rot=-90)
    s.ltext((-W + 22, 64), "← ④ベルト貼り位置", 2.5)
    s.ltext((-W + SM + CORE_IN + 2, SM + CORE_IN + 4.5), "⑦芯材（左側だけ）は黄色の実線で切る", 2.4)
    s.ltext((UL + 2, 30), "右側ユニット（②③⑤）の左端", 2.5)
    s.ltext((W / 2 + 6, 48), "ユニットは右辺と下辺で縫い付ける", 3.0, align="c")
    s.ltext((W / 2 + 6, 53), "（接着は縫い代だけ）", 3.0, align="c")
    s.ltext((W / 2 + 6, 59), "上辺・左辺は開いていて", 3.0, align="c")
    s.ltext((W / 2 + 6, 64), "下にお札の右半分を入れる", 3.0, align="c")
    s.ltext((W / 2 + 6, 77), "⑥裏地布：黄色の破線（0.5mm内側）で", 2.6, align="c")
    s.ltext((W / 2 + 6, 81.5), "切り、内側全面に貼る（両側）", 2.6, align="c")
    s.ldim_h(-W, 0, W, 0, -7, fmt(2 * W))
    s.ldim_v(-W, 0, -W, H, -W - 8, fmt(H))
    s.ldim_v(-W, 0, -W, A_EDGE_V, -W - 3.5)
    s.ldim_v(-W, A_EDGE_V, -W, B_EDGE_V, -W - 3.5)
    s.ldim_v(-W, B_EDGE_V, -W, H, -W - 3.5)
    s.ldim_h(-W, H, -B_BOT_U, H, H + 5)
    s.ldim_h(-B_BOT_U, H, -A_BOT_U, H, H + 5)
    s.ldim_h(-A_BOT_U, H, 0, H, H + 5)
    s.ldim_h(0, H, UL, H, H + 5)
    s.ldim_h(UL, H, W, H, H + 5)
    s.ltext((-W + 1.0, 7.5), "R6", 2.5)


def page1():
    s, (x0, y0, x1, y1) = new_page(1, "型紙 ① 外装（⑥裏地・⑦芯材）")
    s.place(-14.0, 72.0)
    draw_body_pattern(s)
    s.place(0, 0)
    s.text((x1 - 34, y1 - 6), "凡例", 3.4)
    s.legend(x1 - 34, y1 - 13, PATTERN_LEGEND, h=2.0, gap=4.4)
    s.note_lines(x0 + 4, -42.0, [
        "・⑥裏地は布（ナイロンツイル0.2mm等）。①と同じ形を0.5mm内側で切る（または2～3mm大きく切って、貼ってから切り落とす。3/6参照）",
        "・⑦芯材はボンテックス0.4mm。左側だけ。縫い線から2mm、中心から16mm離して、縫い目と折り目にかけない",
        "・貼る順番：①の床面に⑦を貼る → ⑥を全面に貼る → ④ベルトを⑥の上に貼る",
    ], h=2.4, gap=4.0)
    s.scale_bar(x0 + 8, y0 + 14)
    return s


def page2():
    s, (x0, y0, x1, y1) = new_page(2, "型紙 ③ 前胴（立体）・② 台座")
    # ---------------- ③ 前胴（立体の展開図） ----------------
    xl, xr = FL - G - T, FR + G + T
    yb = KB + CARD_DY + G + T
    s.place(-129.0 - xl, 78.0 + ZT)
    s.path(front_flat_outline(), "切断線")
    s.path(front_flat_window(), "切断線")
    s.path(front_flat_mountain(), "山折り")
    s.path(front_flat_valley(), "谷折り")
    s.path(front_flat_stitch(), "縫い線")
    s.path(zip_tape_on_front(), "ファスナー", "HIDDEN")
    s.path(front_lining_flat(), "芯材・裏地")
    s.ltext(((FL + FR) / 2, 22.5), "小銭入れの面", 3.0, align="c")
    s.ltext(((FL + FR) / 2, 27.5), "上端にファスナー（裏に下側テープ）", 2.3, align="c")
    s.ltext((FL + 1.0, ZT + ZIP_TAPE_IN + 3.0), "緑破線＝テープ", 2.0)
    s.ltext((u_on_D(KT + 4) + 1.0, KT + CARD_DY + 4.0), "↑ 壁・谷・壁（谷の縫い線で②と縫う）", 2.2)
    cx = (u_on_D(KB) + FR) / 2
    s.ltext((cx, 66), "③ 前胴 ×1", 5.0, align="c")
    s.ltext((cx, 72), "牛革 0.6～0.8mm（柔らかめ）", 2.7, align="c")
    s.ltext((cx, 80), "カードポケットの面", 3.0, align="c")
    s.ltext((cx, 84.5), "（6枚程度）", 2.5, align="c")
    s.ltext((u_on_D(78) + 3.0, 78 + CARD_DY - 10), "差込口", 2.4, rot=-73)
    s.ltext((u_on_D(88) + 3, 88 + CARD_DY), "⑧裏地（布）", 2.2)
    s.ltext((u_on(CW_A, 80) - 1, 80 + CARD_DY), "窓（くり抜き）", 2.2, rot=-45)
    s.ltext((FR - 9, KB + CARD_DY - 2), "角押さえ", 2.0)
    s.ltext((xl + 0.6, 20), "タブ", 2.0, rot=-90)
    s.ltext((FL - G + 0.6, 20), "壁", 2.0, rot=-90)
    s.ltext((FR + 0.6, 20), "壁", 2.0, rot=-90)
    s.ltext((FR + G + 0.6, 22), "タブ", 2.0, rot=-90)
    s.ltext((FR - 9.5, CB - 1.0), "R1.5", 1.8)
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
    s.ldim_v(xr, ZT, xr, CB, xr + 4)
    s.ldim_v(xr, CB, xr, KT + CARD_DY, xr + 4)
    s.ldim_v(xr, KT + CARD_DY, xr, v_on(CW_A, FR) + CARD_DY, xr + 4)
    s.ldim_v(xr, v_on(CW_A, FR) + CARD_DY, xr, v_on(CW_B, FR) + CARD_DY, xr + 4)
    s.ldim_v(xr, v_on(CW_B, FR) + CARD_DY, xr, KB + CARD_DY, xr + 4)
    s.ldim_v(xr, KB + CARD_DY, xr, yb, xr + 4)
    s.ldim_h(xl, yb, u_on_D(KT), KT + CARD_DY, yb + 5)
    s.ldim_h(u_on_D(KT), KT + CARD_DY, u_on_D(KB), yb, yb + 5)
    s.ldim_h(u_on_D(KB), yb, u_on(CW_A, KB), yb, yb + 5)
    s.ldim_h(u_on(CW_A, KB), yb, u_on(CW_B, KB), yb, yb + 5)
    s.ldim_h(u_on(CW_B, KB), yb, FR, yb, yb + 5)
    s.ldim_h(FR, yb, xr, yb, yb + 5)

    # ---------------- ② 台座 ----------------
    s.place(-3.0 - UL, 80.0)
    s.path(base_outline(), "切断線")
    s.path(front_proj_outline(), "貼り位置")
    s.path(front_proj_walls(), "貼り位置")
    s.path(front_proj_window(), "貼り位置")
    s.path(rect(ZIP_TAPE_U0, ZT, ZIP_TAPE_U1, ZT + ZIP_TAPE_IN), "ファスナー", "HIDDEN")
    s.path([L((FL + 1.5, ZIP_ST), (FR - 1.5, ZIP_ST))], "縫い線")
    s.path(left_seam(), "縫い線")
    s.path([L((FL + 2, SEP_V), (FR - 2, SEP_V))], "縫い線")
    s.path(unit_attach_stitch(R_OUT + 0.5), "縫い線")
    bx = (UL + W) / 2
    s.ltext((bx, 63), "② 台座 ×1", 4.5, align="c")
    s.ltext((bx, 68.5), "牛革 0.8mm", 2.6, align="c")
    s.ltext((bx, 73.5), "裏に⑤a・⑤bを重ねる", 2.4, align="c")
    s.ltext((bx, 22), "上側テープ（表に貼る）", 2.3, align="c")
    s.ltext((bx, 88), "桃色破線＝③の貼り位置", 2.2, align="c")
    s.ldim_h(UL, ZT, W, ZT, ZT - 5, fmt(W - UL))
    s.ldim_v(UL, ZT, UL, H, UL - 5, fmt(H - ZT))

    s.place(0, 0)
    s.text((x1 - 37, y1 - 6), "凡例", 3.4)
    s.legend(x1 - 37, y1 - 13, PATTERN_LEGEND, h=2.2, gap=4.4)
    s.note_lines(x1 - 37, y1 - 54, [
        "③は立体の型紙。",
        "タブを②に縫い、",
        "壁を手前に折り",
        "上げる（マチ6mm）。",
        "折り線の床面に",
        "溝を入れるか漉く。",
        "",
        "⑧（黄線）は",
        "カード面の裏に",
        "貼る布。",
        "",
        "ファスナー：",
        "3号コイル",
        f"務歯{fmt(ZIP_TEETH)}mm",
        f"テープ約{fmt(ZIP_LEN)}mm",
        "内側へ12mm残す",
    ], h=2.2, gap=3.6)
    s.scale_bar(x0 + 8, y0 + 14)
    return s


FABRIC_NOTES = [
    "⑥裏地（外装の内側全面）の貼り方と仕上げ",
    "1. 布は①の型紙より2～3mm大きく切る（型紙の黄色破線＝0.5mm内側で切ってもよい）",
    "2. ①の床面の左側に⑦芯材を貼る。芯の縁は軽くやすって段差をなだらかにする",
    "3. ①（芯の上も）と布の両方にゴム系接着剤を薄く塗り、半乾きで中央から外へ空気を抜きながら貼る",
    "4. 中心の折り目は、①を閉じる方向に軽く曲げた状態で貼る（閉じたときにシワが出にくい）",
    "5. 乾いたら①の縁に沿って布を切り落とす。刃を少し内側に倒すと、布がコバより0.3～0.5mm内側で切れる",
    "6. 布の切り口はほつれ止め（ナイロンはライター等で軽く溶かす／ほつれ止め液）",
    "7. 菱目打ちは①と布を重ねたまま打ち、そのまま縫う（布は縫い線の外側に約2.5mm残る）",
    "8. コバは革だけを磨く（布は内側に下がっているので削れない）。コバ塗料を使うと段差も目立たない",
    "※ ⑤a・⑤b・⑧も同じ要領。⑤の入口は折り返し代6mmを内側へ折って貼る",
]


def page3():
    s, (x0, y0, x1, y1) = new_page(3, "型紙 ⑤a・⑤b 裏ポケット布・④ ベルト・部品表")
    # ---------------- ⑤a / ⑤b 裏ポケット布 ----------------
    for idx, (ox, label, depth_note) in enumerate([
        (-130.0, "⑤a 裏ポケット布（奥） ×1", "②のすぐ裏"),
        (-23.0, "⑤b 裏ポケット布（手前） ×1", "⑤aの上に重ねる"),
    ]):
        tl = pocket_top_v(idx, UL + FABRIC_INSET)
        tr = pocket_top_v(idx, W - FABRIC_INSET)
        tm = pocket_top_v(idx, 60)
        s.place(ox - UL - FABRIC_INSET, 82.0 + min(tl, tr) - FOLD_ALLOW)
        s.path(pocket_outline(idx), "切断線")
        s.path(pocket_fold(idx), "谷折り")
        s.path(pocket_top_stitch(idx), "縫い線", "HIDDEN")
        s.path(left_seam(tl + 1.5), "縫い線")
        s.path(unit_attach_stitch(tr + 1.5), "縫い線")
        cy = (tm + H) / 2
        s.ltext((60, cy - 6), label, 3.4, align="c")
        s.ltext((60, cy), "布 0.2mm（ナイロンツイル等）", 2.4, align="c")
        s.ltext((60, cy + 5), depth_note, 2.3, align="c")
        s.ltext((60, cy + 10), f"深さ 左{fmt(H - SM - pocket_top_v(idx, UL))}／右{fmt(H - SM - pocket_top_v(idx, W))}mm", 2.3, align="c")
        s.ltext((60, tm - 2.0), "↓折り返し代（内側へ折って貼る）", 2.0, align="c",
                rot=-math.degrees(math.atan2(tr - tl, W - UL)))
        s.ltext((60, tm + 7), "押さえ縫い（任意）", 2.0, align="c")
        s.ldim_v(UL + FABRIC_INSET, tl - FOLD_ALLOW, UL + FABRIC_INSET, tl, UL - 4)
        s.ldim_v(UL + FABRIC_INSET, tl, UL + FABRIC_INSET, H - FABRIC_INSET, UL - 4)
        s.ldim_h(UL + FABRIC_INSET, H - FABRIC_INSET, W - FABRIC_INSET, H - FABRIC_INSET, H + 4.5)

    # ---------------- ④ 札押さえベルト ----------------
    s.place(85.0 + W, 82.0 + A_EDGE_V)
    s.path(band_outline(), "切断線")
    s.path(band_stitch(), "縫い線")
    s.ltext((-W + 20, A_EDGE_V + 6), "④ 札押さえベルト ×1", 3.0)
    s.ltext((-W + 22, A_EDGE_V + 10.5), "牛革 0.8mm", 2.3)
    s.ltext((-W + 24, A_EDGE_V + 14.5), "斜め2辺は先に磨く", 2.3)
    s.ldim_v(-W, A_EDGE_V, -W, B_EDGE_V, -W - 4)
    s.ldim_h(-B_BOT_U, H, -A_BOT_U, H, H + 5)

    # ---------------- 部品表 ----------------
    s.place(0, 0)
    tx, ty = 76.0, 26.0
    s.text((tx, ty), "部品表", 3.4)
    rows = [
        ("No.", "部品名", "数", "素材・厚み"),
        ("①", "外装", "1", "牛革1.0"),
        ("②", "台座", "1", "牛革0.8"),
        ("③", "前胴（立体）", "1", "牛革0.6～0.8"),
        ("④", "札押さえベルト", "1", "牛革0.8"),
        ("⑤a", "裏ポケット布（奥）", "1", "布0.2"),
        ("⑤b", "裏ポケット布（手前）", "1", "布0.2"),
        ("⑥", "裏地（①の内側全面）", "1", "布0.2"),
        ("⑦", "芯材（左側だけ）", "1", "ボンテックス0.4"),
        ("⑧", "裏地（③カード面の裏）", "1", "布0.2"),
    ]
    cols = [tx, tx + 6, tx + 32, tx + 36, tx + 59]
    rh = 4.2
    top = ty - 2.0
    for i, r in enumerate(rows):
        yy = top - (i + 1) * rh
        for j, c in enumerate(r):
            s.text((cols[j] + 0.6, yy + 1.3), c, 2.1)
    for i in range(len(rows) + 1):
        s.line((cols[0], top - i * rh), (cols[-1], top - i * rh), "図枠")
    for c in cols:
        s.line((c, top), (c, top - len(rows) * rh), "図枠")
    s.note_lines(tx, top - len(rows) * rh - 5, [
        "副資材：3号コイルファスナー",
        f"（務歯{fmt(ZIP_TEETH)}／テープ約{fmt(ZIP_LEN)}mm）、",
        "ロウ引き糸0.45～0.55mm 約5m、",
        "ゴム系接着剤、ほつれ止め",
    ], h=2.2, gap=3.6)

    s.text((x0 + 4, -14.0), FABRIC_NOTES[0], 3.2)
    s.note_lines(x0 + 4, -20.5, FABRIC_NOTES[1:], h=2.2, gap=3.5)
    s.scale_bar(x0 + 8, y0 + 14)
    return s


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


K_BODY, K_CORE, K_LIN, K_BILL, K_PB, K_PA, K_BASE, K_TAB, K_FLIN, K_FACE = (
    0.0, 0.3, 0.6, 1.0, 1.5, 2.05, 2.6, 2.95, 5.15, 5.4)


def page4():
    s, (x0, y0, x1, y1) = new_page(4, "組立図：完成状態を開いて内側から見た図", assembly=True)
    s.place(-12.0, 72.0)
    s.path(body_outline(), "切断線")
    s.path(perimeter_stitch(), "縫い線")
    s.path([L((0, -4), (0, H + 4))], "中心線")
    s.path(core_outline(), "芯材・裏地", "HIDDEN")
    s.path(band_outline(), "切断線")
    s.path([L((UL, CB), (UL, H))], "切断線")
    s.path(front_proj_outline(), "切断線")
    s.path(front_proj_walls(), "切断線")
    s.path(front_proj_window(), "切断線")
    s.path(rect(FL, 0.0, FR, ZT), "ファスナー")
    s.path(left_seam(), "縫い線")
    s.path([L((FL + 2, SEP_V), (FR - 2, SEP_V))], "縫い線")
    s.path([L((FL + 1.5, ZIP_ST), (FR - 1.5, ZIP_ST))], "縫い線")
    s.path(card_rect(), "カード")
    s.path(bill_rect(), "お札")
    for (c, d, _) in COINS:
        s.circle(s.T(c), d / 2, "小銭")
    s.ltext((-W / 2 - 2, 45), "お札（折らずに入れる）", 3.0, align="c")
    s.ltext((-W / 2 - 2, 50), "右半分は右側ユニットの下へ", 2.5, align="c")
    s.ltext((-W / 2 - 2, 54.5), "左下の角をベルトに差し込む", 2.5, align="c")
    s.ltext((-W / 2 - 2, 12), "黄破線＝⑦芯材（⑥裏地の下・左側だけ）", 2.4, align="c")
    s.ltext((-A_BOT_U + 4, 93), "← ④ベルト", 2.4)
    s.ltext((58, 12.5), "小銭入れ（マチ6）", 2.6, align="c")
    s.ltext((88, 50), "カード 6枚程度", 3.0, align="c")
    s.ltext((88, 54.5), "（マチ6・面の裏に⑧裏地）", 2.3, align="c")
    s.ltext((FL - 1, -1.2), "ファスナー（上端）", 2.3, align="l")
    s.ltext((u_on_D(80) - 12.0, 86), "差込口", 2.4)
    s.ltext((u_on(CW_A, 80) + 2.5, 82), "窓", 2.5)
    s.ltext((FR - 7.5, KB - 2.5), "角", 2.2)
    s.ltext((UL - 0.8, 40), "②の裏に布ポケット2段", 2.1, rot=-90, valign="t")
    s.ldim_h(-W, 0, W, 0, -9, f"{fmt(2 * W)}（閉じると {fmt(W)}×{fmt(H)}）")
    s.ldim_h(0, 0, UL, 0, -3.5)
    s.ldim_v(-W, 0, -W, H, -W - 4, fmt(H))
    s.ldim_v(-W, 0, -W, A_EDGE_V, -W - 9)
    s.ldim_v(-W, A_EDGE_V, -W, B_EDGE_V, -W - 9)
    s.ldim_v(-W, B_EDGE_V, -W, H, -W - 9)
    s.ldim_v(W, 0, W, CB, W + 6)
    s.ldim_v(W, CB, W, KT, W + 6)
    s.ldim_v(W, KT, W, KB, W + 6)
    s.ldim_v(W, KB, W, H, W + 6)
    s.ldim_v(FR, KT, FR, v_on(CW_A, FR), W + 12)
    s.ldim_v(FR, v_on(CW_A, FR), FR, v_on(CW_B, FR), W + 12)
    s.ldim_v(FR, v_on(CW_B, FR), FR, KB, W + 12)
    s.ldim_h(-B_BOT_U, H, -A_BOT_U, H, H + 5)
    s.ldim_h(-A_BOT_U, H, 0, H, H + 5)
    s.ldim_h(0, H, u_on_D(H), H, H + 5)
    s.ldim_h(u_on_D(H), H, u_on(CW_A, KB), KB, H + 5)
    s.ldim_h(u_on(CW_A, KB), KB, u_on(CW_B, KB), KB, H + 5)
    s.ldim_h(u_on(CW_B, KB), KB, FR, KB, H + 5)
    s.place(0, 0)
    items = [
        ("切断線", None, "革の縁"),
        ("縫い線", None, "縫い線"),
        ("ファスナー", None, "ファスナー"),
        ("カード", None, "カード"),
        ("お札", None, "お札"),
        ("小銭", None, "小銭"),
        ("芯材・裏地", "HIDDEN", "⑦芯材"),
    ]
    s.text((x0 + 4, -64.0), "凡例", 3.4)
    s.legend(x0 + 4, -70.0, items[:4], h=2.2, gap=4.4)
    s.legend(x0 + 48, -70.0, items[4:], h=2.2, gap=4.4)
    s.note_lines(x0 + 4, -44.0, [
        "・右側ユニット（②台座＋③前胴＋⑤a・⑤b）は外装の右辺と下辺だけで縫い付ける。上辺と左辺は開いている",
        "・③は高さ6mmの箱（小銭入れ・カードポケット）。ファスナーは最上部で、閉じたままでも開けられる",
        "・窓は④ベルトと左右対称（45°）で、ベルトより両側1.5mm広い。窓の下の角押さえは③と一体",
        "・カードは左の差込口から入れ、窓に指をかけて左へ滑らせて出す",
    ], h=2.3, gap=3.9)
    return s


def page5():
    s, (x0, y0, x1, y1) = new_page(5, "組立図：断面模式図", assembly=True)
    fab0, fab1 = UL + FABRIC_INSET, W - FABRIC_INSET
    OX = -14.0

    def base_layers(sc, v):
        sc.h(-W, W, K_BODY)
        c = core_outline_box()
        if c[2] <= v <= c[3]:
            sc.h(c[0], c[1], K_CORE, "芯材・裏地")
        sc.h(-W + FABRIC_INSET, W - FABRIC_INSET, K_LIN, "芯材・裏地", "HIDDEN")
        if H - SM - 0.5 - BILL_H <= v <= H - SM - 0.5:
            sc.h(BILL_U0, BILL_U0 + BILL_W, K_BILL, "お札", "CONTINUOUS")
        for idx, k in ((1, K_PB), (0, K_PA)):
            us = [u for u in (fab0 + i * 0.5 for i in range(int((fab1 - fab0) / 0.5) + 1))
                  if pocket_top_v(idx, u) <= v]
            if us:
                sc.h(min(us), fab1, k, "断面図", "HIDDEN")
        sc.h(UL, W, K_BASE)
        sc.v(0, -0.6, K_FACE + 0.6, "中心線")

    # A-A：小銭入れ
    va = 25.0
    sa = Sec(s, OX, 62.0)
    s.text(sa.P(-W, K_FACE + 1.6), f"断面 A-A（上端から {fmt(va)}mm：小銭入れ）", 3.2)
    base_layers(sa, va)
    for it in [(UL, FL, K_TAB), (FR, W, K_TAB), (FL, FR, K_FACE)]:
        sa.h(*it)
    sa.v(FL, K_BASE, K_FACE)
    sa.v(FR, K_BASE, K_FACE)
    for (c, d, _) in COINS[:2]:
        sa.box(c[0] - d / 2, c[0] + d / 2, K_TAB, K_TAB + 0.5, "小銭")
    for (a, k0, k1) in [(-W + SM, -0.4, K_LIN + 0.4), (W - SM, -0.4, K_TAB + 0.4),
                        (UL + SM, K_BASE - 0.4, K_TAB + 0.4)]:
        sa.v(a, k0, k1, "縫い線")
    for (a, k, txt, al) in [
        (-W + 1, -1.5, "①外装＋⑦芯（左）＋⑥裏地", "l"),
        (-40, K_BILL + 0.2, "お札", "c"),
        (40, K_BILL + 0.2, "お札の右半分（ユニットの下）", "c"),
        (W + 1, K_PA - 0.2, "⑤a", "l"),
        (UL - 1, K_BASE + 0.1, "②", "r"),
        (60, K_TAB + 0.9, "小銭", "c"),
        (60, K_FACE + 0.3, "③小銭入れ（高さ6）", "c"),
    ]:
        sa.t(a, k, txt, 2.1, al)

    # B-B：カード・窓・角押さえ・ベルト
    vb = 85.0
    sb = Sec(s, OX, 24.0)
    s.text(sb.P(-W, K_FACE + 1.6), f"断面 B-B（上端から {fmt(vb)}mm：カード・窓・ベルト）", 3.2)
    base_layers(sb, vb)
    c0, c1 = FR - LEATHER_T - 0.5 - CARD_W, FR - LEATHER_T - 0.5
    sb.h(-u_on(C_B, vb), -u_on(C_A, vb), K_BILL + 0.5)
    sb.box(c0, c1, K_TAB, K_FLIN - 0.3, "カード", "CONTINUOUS")
    sb.h(u_on_D(vb), u_on(CW_A, vb), K_FACE)
    sb.h(u_on_D(vb) + 1, u_on(CW_A, vb) - 1, K_FLIN, "芯材・裏地", "HIDDEN")
    sb.h(u_on(CW_B, vb), FR, K_FACE)
    sb.v(FR, K_BASE, K_FACE)
    sb.h(FR, W, K_TAB)
    for (a, k0, k1) in [(-W + SM, -0.4, K_LIN + 0.4), (W - SM, -0.4, K_TAB + 0.4),
                        (UL + SM, K_PB - 0.4, K_BASE + 0.4)]:
        sb.v(a, k0, k1, "縫い線")
    for uu in (u_on(C_A, vb), u_on(C_B, vb)):
        sb.v(uu, -0.6, K_FACE + 0.8, "中心線", "HIDDEN")
        sb.v(-uu, -0.6, K_FACE + 0.8, "中心線", "HIDDEN")
    for (a, k, txt, al) in [
        (-W + 1, -1.5, "①＋⑦＋⑥", "l"),
        (-40, K_BILL + 0.2, "お札", "c"),
        (-(u_on(C_A, vb) + u_on(C_B, vb)) / 2, K_BILL + 0.8, "④", "c"),
        (UL - 1, K_PB - 0.35, "⑤b", "r"),
        (UL - 1, K_PA - 0.05, "⑤a", "r"),
        (UL - 1, K_BASE + 0.3, "②", "r"),
        (30, K_TAB + 0.6, "カード×6", "c"),
        ((u_on_D(vb) + u_on(CW_A, vb)) / 2, K_FACE + 0.3, "③＋⑧裏地", "c"),
        ((u_on(CW_A, vb) + u_on(CW_B, vb)) / 2, K_FACE + 0.3, "窓", "c"),
        ((u_on(CW_B, vb) + FR) / 2, K_FACE + 0.3, "角", "c"),
    ]:
        sb.t(a, k, txt, 2.1, al)
    s.text(sb.P(-W, -3.2),
           f"※ 水色破線：閉じたときの④ベルトの位置。窓とのすき間は両側 {fmt(WIN_CLEAR)}mm", 2.3)

    # C-C：縦断面（u=60）
    sc = Sec(s, -126.0, -26.0, 3.4)
    s.text(sc.P(0, K_FACE + 1.6), "断面 C-C（中心から60mmの縦断面：左が上端）", 3.2)
    sc.h(0, H, K_BODY)
    sc.h(FABRIC_INSET, H - FABRIC_INSET, K_LIN, "芯材・裏地", "HIDDEN")
    sc.h(H - SM - 0.5 - BILL_H, H - SM - 0.5, K_BILL, "お札", "CONTINUOUS")
    for idx, k in ((1, K_PB), (0, K_PA)):
        top = pocket_top_v(idx, 60)
        sc.h(top, H - FABRIC_INSET, k, "断面図", "HIDDEN")
        sc.h(top, top + FOLD_ALLOW, k + 0.22, "断面図", "HIDDEN")
    sc.h(ZT, H, K_BASE)
    sc.box(-0.3, ZT, K_BASE, K_FACE, "ファスナー")
    sc.h(ZT, ZT + ZIP_TAPE_IN, K_BASE + 0.15, "ファスナー")
    sc.h(ZT, ZT + ZIP_TAPE_IN, K_FACE - 0.15, "ファスナー")
    sc.h(ZT, CB, K_FACE)
    sc.v(CB, K_BASE, K_FACE)
    sc.h(CB, KT, K_TAB)
    sc.v(KT, K_BASE, K_FACE)
    sc.h(KT, KB, K_FACE)
    sc.h(KT + 0.5, KB - 0.5, K_FLIN, "芯材・裏地", "HIDDEN")
    sc.v(KB, K_BASE, K_FACE)
    sc.h(KB, H, K_TAB)
    sc.box(KB - LEATHER_T - 0.3 - CARD_H, KB - LEATHER_T - 0.3, K_TAB, K_FLIN - 0.3, "カード", "CONTINUOUS")
    sc.box(4.25, 30.75, K_TAB, K_TAB + 0.5, "小銭")
    for (a, k0, k1) in [(ZIP_ST, K_BASE - 0.4, K_BASE + 0.5), (ZIP_ST, K_FACE - 0.5, K_FACE + 0.4),
                        (SEP_V, K_BASE - 0.4, K_TAB + 0.4), (H - SM, -0.4, K_TAB + 0.4),
                        (SM, -0.4, K_LIN + 0.4)]:
        sc.v(a, k0, k1, "縫い線")
    sc.t(-1, K_FACE + 0.3, "ファスナー", 2.0, "r")
    sc.t(17.5, K_FACE + 0.3, "小銭入れ", 2.0, "c")
    sc.t(SEP_V, K_FACE + 0.3, "仕切り", 2.0, "c")
    sc.t(66, K_FACE + 0.3, "カードポケット（面の裏に⑧）", 2.0, "c")
    sc.t(66, K_TAB + 0.6, "カード", 2.0, "c")
    sc.t(10.5, K_BILL + 0.15, "お札", 2.0, "c")
    sc.t(H + 1, K_BASE - 0.25, "②", 1.9, "l")
    sc.t(H + 1, K_PA - 0.25, "⑤a", 1.9, "l")
    sc.t(H + 1, K_PB - 0.25, "⑤b", 1.9, "l")
    sc.t(H + 1, K_LIN - 0.25, "⑥", 1.9, "l")
    sc.t(H + 1, K_BODY - 0.45, "①", 1.9, "l")
    sc.t(pocket_top_v(0, 60) - 6, -1.3, "↑⑤a・⑤bの上端（斜め・上から入れる2段）", 2.0, "l")
    sc.t(H + 7, K_BILL, "← 下辺は全層まとめて縫う", 2.0, "l")

    # 閉じた状態を上から見た図（模式）
    tv = Sec(s, -124.0, -80.0, 2.0)
    s.text(tv.P(-2, 10.8), "閉じた状態を上から見た図（模式）", 3.2)
    tv.h(0, W, 0)
    tv.h(0, W, 8.6)
    s.arc(tv.P(0, 4.3), 4.3 * 2.0, 90, 270, "断面図")
    tv.h(UL, W, K_BASE - 0.6)
    tv.box(FL, FR, K_BASE - 0.6, K_FACE - 0.6, "ファスナー")
    tv.h(FL, FR, K_FACE - 0.6)
    tv.box(FL + 2, FL + 9, K_FACE - 0.6, K_FACE + 1.2, "ファスナー")
    tv.h(UL, W, K_PA - 0.6, "断面図", "HIDDEN")
    tv.h(UL, W, K_PB - 0.6, "断面図", "HIDDEN")
    tv.h(0, BILL_U0 + BILL_W, 0.35, "お札", "CONTINUOUS")
    tv.h(0, -BILL_U0, 7.6, "お札", "CONTINUOUS")
    s.arc(tv.P(0, 4.0), 3.6 * 2.0, 90, 270, "お札")
    tv.t(W + 4, 6.0, "ファスナーは上端に出ているので、", 2.4, "l")
    tv.t(W + 4, 4.0, "閉じたまま開けて小銭を出せる", 2.4, "l")
    tv.t(W + 4, 2.0, "（両端を軽く押すと口が開く）", 2.2, "l")
    tv.t(W / 2, 8.9, "外装（左半分・芯と裏地入り）", 2.0, "c")
    tv.t(W / 2, -1.9, "外装（右半分）", 2.0, "c")
    tv.t(FL + 10, K_FACE + 0.1, "引手", 2.0, "l")
    return s


def page6():
    s, (x0, y0, x1, y1) = new_page(6, "組立図：重なり確認・仕様・作り方", assembly=True)
    CX, CY = -131.0, 76.0
    s.place(CX, CY)
    s.text((CX - 2, CY + 9), "閉じたときの重なり（右半分）", 3.4)
    s.path(body_right_half(), "切断線")
    s.path([L((0, -4), (0, H + 4))], "中心線")
    s.path([L((UL, CB), (UL, H))], "切断線")
    s.path(front_proj_outline(), "切断線")
    s.path(front_proj_walls(), "切断線")
    s.path(front_proj_window(), "切断線")
    s.path(card_rect(), "カード")
    s.path(mirror_u(band_outline()), "お札", "HIDDEN")
    s.ltext((W / 2 + 6, 44), "桃色破線＝左の④ベルトを", 2.4, align="c")
    s.ltext((W / 2 + 6, 48.5), "中心で折り返した位置", 2.4, align="c")
    s.ltext((W / 2 + 6, 54), "→ 窓の中に収まる", 2.4, align="c")
    s.ltext((W / 2 + 6, 58.5), f"（すき間は両側 {fmt(WIN_CLEAR)}mm）", 2.4, align="c")
    s.ltext((W / 2 + 6, 66), "窓の下の角押さえ（③と一体）で", 2.4, align="c")
    s.ltext((W / 2 + 6, 70.5), "カードの右下が飛び出さない", 2.4, align="c")
    s.ldim_v(FR, v_on(CW_A, FR), FR, v_on(CW_B, FR), W + 4,
             "窓 " + fmt(v_on(CW_B, FR) - v_on(CW_A, FR)))
    s.ldim_v(FR, v_on(C_A, FR), FR, v_on(C_B, FR), W + 10,
             "④ " + fmt(v_on(C_B, FR) - v_on(C_A, FR)))

    s.place(0, 0)
    t = THICK
    s.text((x0 + 2, -34.0), "厚みの内訳（閉じた状態・カード部）", 3.0)
    s.note_lines(x0 + 2, -40.0, [
        "①1.0×2＋⑥0.2×2＋⑦0.4＋⑤0.2×2",
        "＋②0.8＋③の箱6.0（カード6枚）",
        f"＝ 約{fmt(t['min'])}mm（お札1～2枚）",
        f"お札10枚＋裏ポケットにカード各1枚で約{fmt(t['max'])}mm",
    ], h=2.3, gap=3.7)

    nx = -2.0
    s.text((nx, 87.0), "仕様", 3.6)
    s.note_lines(nx, 81.0, [
        f"・サイズ：開き {fmt(2 * W)}×{fmt(H)}mm／閉じ {fmt(W)}×{fmt(H)}mm、厚み約{fmt(t['min'])}～{fmt(t['max'])}mm",
        "・お札：折らずに入れる。右半分はユニットの下（上・左から差し込む）",
        "・小銭入れ：上端にファスナー。閉じたままでも開けられる（マチ6mm）",
        "・カード：6枚程度。窓の下の角押さえ（③と一体）で右下を押さえる",
        f"・窓は④ベルトより両側{fmt(WIN_CLEAR)}mm広く、閉じると④が窓に収まる",
        "・裏ポケット：②の裏に布2段・上端は斜め（左が低い）",
        f"・左側は⑦芯材＋⑥裏地で張りを出す。折り代は中心～ユニット左端 {fmt(UL)}mm",
    ], h=2.2, gap=3.5)
    s.text((nx, 52.0), "作り方の順序", 3.6)
    s.note_lines(nx, 46.0, [
        "1. 裁断・床面処理。③の折り線に溝を入れ、窓をくり抜き、自由辺を磨く",
        "2. ①の左側に⑦芯材を貼り、⑥裏地を内側全面に貼る（貼り方は3/6）",
        "3. ④ベルトを⑥の上に貼る。③のカード面の裏に⑧裏地を貼る",
        "4. ファスナー：下側テープを③上端の裏、上側テープを②上端の表に貼り、",
        "　 それぞれ上端から2.5mmで縫う",
        "5. ③のタブと谷を②に貼り、仕切りの谷（③＋②）を縫う",
        "6. ③の右タブ・下タブを②に貼る（カードを3枚ほど入れて壁を立てる）",
        "7. ⑤a・⑤bの上端を折り返して貼り、②の裏に⑤a→⑤bの順に縫い代だけ貼る",
        "8. 左端の縦の線（③左タブ＋②＋⑤a＋⑤b）を縫う → ユニット完成",
        "9. 外周のうち、右辺・右下の角・ユニット部分の下辺以外を縫う（①＋⑥＋④）",
        "10. ユニットを①に重ね、下辺→右下の角→右辺を全層まとめて縫う",
        "11. コバを仕上げ（布は0.5mm内側）、中心に折り癖を付ける",
    ], h=2.2, gap=3.5)
    return s


PAGES = [
    ("1_pattern_body", page1),
    ("2_pattern_front_base", page2),
    ("3_pattern_pockets_band", page3),
    ("4_assembly_inside", page4),
    ("5_assembly_sections", page5),
    ("6_assembly_notes", page6),
]


# =============================================================================
# プレビュー（PDF/PNG）
# =============================================================================
ACI_RGB = {1: "#d00000", 2: "#c8a000", 3: "#00902a", 4: "#0090c0", 5: "#1040e0", 6: "#d000c0", 7: "#000000"}
LW_MM = {"切断線": 0.35, "断面図": 0.4, "縫い線": 0.25, "図枠": 0.35}


def render(sheet, pdf, png_path):
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
    pdf.savefig(fig)
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
        "外周（ユニット部分を含む）": path_length(perimeter_stitch()),
        "ファスナー×2": 2 * (FR - FL - 3.0),
        "ユニット左端": H - SM - ZT - 2,
        "仕切り": FR - FL - 4,
        "布の押さえ縫い×2": 2 * (W - UL - 2 * SM - 4),
    }
    total = sum(stitches.values())
    print("縫い線の長さ:", {k: round(v, 1) for k, v in stitches.items()},
          "合計", round(total), "mm / 糸の目安(×4):", round(total * 4 / 1000, 2), "m")
    print("窓（③の右の壁 u=%.0f）: v=%.2f〜%.2f / 窓（底 v=%.0f）: u=%.2f〜%.2f" % (
        FR, v_on(CW_A, FR), v_on(CW_B, FR), KB, u_on(CW_A, KB), u_on(CW_B, KB)))
    print("ベルト: 側面 v=%.1f〜%.1f, 下辺 u=%.1f〜%.1f / 厚み目安 %s" % (
        A_EDGE_V, B_EDGE_V, A_BOT_U, B_BOT_U, THICK))
    dxf_dir = os.path.join(OUT_DIR, "dxf")
    png_dir = os.path.join(OUT_DIR, "preview")
    os.makedirs(dxf_dir, exist_ok=True)
    os.makedirs(png_dir, exist_ok=True)
    sheets = []
    for name, fn in PAGES:
        sheet = fn()
        check_cp932(sheet)
        dxf = os.path.join(dxf_dir, f"wallet_A4_{name}.dxf")
        write_dxf(sheet, dxf)
        sheets.append((name, sheet))
        print("wrote", dxf, len(sheet.ents), "entities")
    try:
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib.backends.backend_pdf import PdfPages
    except ImportError:
        print("matplotlib が無いので PDF/PNG を省略")
        return
    with PdfPages(os.path.join(OUT_DIR, "wallet_A4_all.pdf")) as pdf:
        for name, sheet in sheets:
            render(sheet, pdf, os.path.join(png_dir, f"page{name.split('_')[0]}.png"))
    print("wrote wallet_A4_all.pdf (%d pages)" % len(sheets))


if __name__ == "__main__":
    main()
