"""Timeline renderer for 'Same Hand. Two Seats.' (1080x1920, 30fps, 1350 frames)."""
import math, os, sys, time
import numpy as np
from collections import OrderedDict
from PIL import Image, ImageDraw, ImageFilter
from core import *

CX = 540
RING_C = (540, 1050)
RING_R = 300
IVORY = C["ivory"]
EARLY = C["early"]
LATE = C["late"]
CHIP = C["chip"]
MUTE = C["mute"]
SAFE_W = 900

HOOK, CLAIM, SUB = 140, 112, 96

# ---------------------------------------------------------------- background
def build_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = (xx - CX) / (W * 0.74)
    dy = (yy - 950) / (H * 0.64)
    d = np.sqrt(dx * dx + dy * dy)
    g = np.clip(1.0 - d, 0, 1) ** 1.35
    inner = np.array((26, 78, 58), dtype=np.float32)
    outer = np.array((5, 11, 9), dtype=np.float32)
    img = outer[None, None, :] + (inner - outer)[None, None, :] * g[..., None]
    sheen = np.clip(1.0 - yy / (H * 0.50), 0, 1)[..., None] ** 2.0 * 12.0
    img = img + sheen
    vx = (xx - CX) / (W * 0.66); vy = (yy - H * 0.5) / (H * 0.60)
    vig = np.clip(np.sqrt(vx * vx + vy * vy) - 0.60, 0, 1.6) ** 1.5
    img = img * (1.0 - 0.50 * vig[..., None])
    rng = np.random.default_rng(7)
    img = img + rng.normal(0, 0.9, img.shape)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

# ---------------------------------------------------------------- ring + seats
SEAT_N = 9
ROT_HOLD = 12.0

def seat_angle(i, rot):
    return -90.0 - rot + (i - 1) * (360.0 / SEAT_N)

def seat_pos(i, rot):
    a = math.radians(seat_angle(i, rot))
    return (RING_C[0] + math.cos(a) * RING_R, RING_C[1] + math.sin(a) * RING_R)

def _build_ring(rot, bright):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    r = RING_R
    # felt surface inside the rail so the ring reads as a table, not a wireframe
    lay.alpha_composite(disc_img(r - 2, (20, 66, 50), alpha=0.72 * bright, ss=3),
                        (int(CX - r + 2), int(RING_C[1] - r + 2)))
    # rail: dark outline + warm ivory edge
    lay.alpha_composite(ring_img(r, 7, (3, 8, 6), 0.45 * bright), (int(CX - r - 7), int(RING_C[1] - r - 7)))
    lay.alpha_composite(ring_img(r, 3, IVORY, 0.22 * bright), (int(CX - r - 3), int(RING_C[1] - r - 3)))
    lay.alpha_composite(ring_img(r - 1, 1, IVORY, 0.38 * bright), (int(CX - r), int(RING_C[1] - r)))
    # inner rail shadow
    lay.alpha_composite(ring_img(r - 9, 4, (0, 0, 0), 0.20 * bright), (int(CX - r + 7), int(RING_C[1] - r + 7)))
    for i in range(1, SEAT_N + 1):
        x, y = seat_pos(i, rot)
        lay.alpha_composite(disc_img(13, (10, 24, 19), alpha=0.55 * bright), (int(x - 14), int(y - 14)))
        lay.alpha_composite(disc_img(12, IVORY, alpha=0.62 * bright), (int(x - 13), int(y - 13)))
        a_rad = math.radians(seat_angle(i, rot))
        nx, ny = x + math.cos(a_rad) * 32, y + math.sin(a_rad) * 32
        n = text_img(str(i), font(INTER, 24, (14, 700)), IVORY, 0.0)
        lay.alpha_composite(alpha_mul(n, 0.30 * bright), (int(nx - n.width / 2), int(ny - n.height / 2 + 1)))
    return lay

_ring_cache = OrderedDict()
def draw_ring(base, f, rot, alpha, bright=1.0):
    if alpha <= 0.004: return
    key = (round(rot, 0) if f < 135 else round(rot, 1), round(bright, 2), round(alpha, 2))
    lay = _ring_cache.get(key)
    if lay is None:
        base_lay = _build_ring(key[0], key[1])
        lay = alpha_mul(base_lay, key[2])
        _ring_cache[key] = lay
        if len(_ring_cache) > 7:
            _ring_cache.popitem(last=False)
    else:
        _ring_cache.move_to_end(key)
    base.alpha_composite(lay)

def seat_mark(base, i, rot, color, alpha=1.0, radius=0, glow=True):
    x, y = seat_pos(i, rot)
    if glow and radius > 0 and alpha > 0.01:
        base.alpha_composite(ring_img(radius, 2, color, 0.85 * alpha), (int(x - radius - 1), int(y - radius - 1)))
    base.alpha_composite(disc_img(13, color, alpha=alpha), (int(x - 14), int(y - 14)))

# ---------------------------------------------------------------- playing cards
_card_cache = {}
def card_img(rank, suit, w, h, face=(250, 248, 243)):
    key = (rank, suit, w, h, face)
    if key in _card_cache: return _card_cache[key]
    ss = 2
    card = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    rad = max(3, int(w * 0.055))
    d.rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=rad * ss, fill=face + (255,))
    d.rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=rad * ss,
                        outline=(0, 0, 0, 40), width=max(1, int(w * 0.012 * ss)))
    card = card.resize((w, h), Image.LANCZOS)
    sh = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    sh.paste(Image.new("RGBA", (w, h), (0, 0, 0, 120)), (20, 22), card.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(max(4, int(w * 0.045))))
    out = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    out.alpha_composite(sh)
    out.alpha_composite(card, (20, 20))
    ink = C["felt900"] if suit in ("spades", "clubs") else C["cardRed"]
    fs = int(h * 0.29)
    r_im = text_img(rank, font(A_BLACK, fs), ink, -0.04)
    s_im = text_img(SUIT[suit], font(DEJA, int(h * 0.20)), ink, 0.0)
    ox = int(w * 0.10); oy = int(h * 0.055)
    out.alpha_composite(r_im, (20 + ox, 20 + oy))
    out.alpha_composite(s_im, (20 + ox + int(w * 0.01), 20 + oy + int(r_im.height * 0.90)))
    big = text_img(SUIT[suit], font(DEJA, int(h * 0.34)), ink, 0.0)
    out.alpha_composite(alpha_mul(big, 0.90), (20 + (w - big.width) // 2, 20 + int(h * 0.64) - big.height // 2))
    _card_cache[key] = out
    return out

def draw_card(base, rank, suit, w, h, cx, cy, alpha=1.0, scale=1.0, rot=0.0):
    if alpha <= 0.004: return
    blit(base, card_img(rank, suit, w, h), cx, cy, scale=scale, alpha=alpha, rot=rot)

def card_pair(base, cx, cy, w, h, spread=118, rot=7.0, alpha=1.0, scale=1.0, dy=0.0):
    draw_card(base, "A", "spades", w, h, cx - spread * scale, cy + dy, alpha=alpha, scale=scale, rot=-rot)
    draw_card(base, "J", "spades", w, h, cx + spread * scale, cy + dy, alpha=alpha, scale=scale, rot=rot)

# ---------------------------------------------------------------- chips
_chip_cache = {}
def chip_img(r, color=CHIP):
    key = (r, color)
    if key in _chip_cache: return _chip_cache[key]
    ss = 3
    w = int(2 * r + 4)
    t = Image.new("RGBA", (w * ss, w * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    bb = [ss, ss, w * ss - ss - 1, w * ss - ss - 1]
    d.ellipse(bb, fill=color + (255,))
    d.ellipse(bb, outline=(0, 0, 0, 70), width=max(1, int(r * 0.10 * ss)))
    o = r * 0.24 * ss
    d.ellipse([ss + o, ss + o, w * ss - ss - 1 - o, w * ss - ss - 1 - o],
              outline=(0, 0, 0, 46), width=max(1, int(r * 0.09 * ss)))
    for k in range(6):
        a0 = k * 60 + 6
        d.arc(bb, a0, a0 + 24, fill=(255, 255, 255, 200), width=max(1, int(r * 0.19 * ss)))
    t = t.resize((w, w), Image.LANCZOS)
    _chip_cache[key] = t
    return t

def chip_stack(base, cx, base_y, n, r=30, alpha=1.0):
    for k in range(n):
        blit(base, chip_img(r), cx, base_y - k * (r * 0.52), alpha=alpha)

# ---------------------------------------------------------------- motion
def slam(f, t0, dur=9):
    p = SPRING(max(0, f - t0))
    return 1.16 - 0.16 * clamp01(p), clamp01(p * 2.0)

def rise(f, t0, dur=10, dist=26):
    p = ease_out_cubic((f - t0) / dur) if f >= t0 else 0.0
    return dist * (1 - p), p

def snap(f, t1, dist=20):
    p = clamp01((f - (t1 - 4)) / 4.0)
    return -dist * p, 1 - p

def put_line(base, text, tf, y, color, scale=1.0, dy=0.0, alpha=1.0, cx=CX, tracking=0.0, shadow=True):
    if alpha <= 0.004: return
    im = text_img(text, tf, color, tracking)
    if shadow:
        blit(base, alpha_mul(text_img(text, tf, (0, 0, 0), tracking), 0.30 * alpha), cx + 2, y + dy + 6, scale=scale)
    blit(base, im, cx, y + dy, scale=scale, alpha=alpha)

def line_alpha(f, t0, t1, preset="slam"):
    sc, dy, a = 1.0, 0.0, 1.0
    if preset == "slam":
        sc, a = slam(f, t0)
    elif preset == "rise":
        dy, a = rise(f, t0, 10)
    if t1 is not None and f > t1 - 4:
        sdy, sa = snap(f, t1); dy += sdy; a *= sa
    return sc, dy, a

def big_line(base, text, f, t0, y, color=IVORY, size=CLAIM, t1=None, preset="slam", alpha=1.0, cx=CX):
    if f < t0 or (t1 is not None and f > t1 + 1): return
    sc, dy, a = line_alpha(f, t0, t1, preset)
    sz = fit_size(text, A_BLACK, size, SAFE_W)
    put_line(base, text, font(A_BLACK, sz), y, color, scale=sc, dy=dy, alpha=a * alpha, cx=cx)

def kicker(base, text, y, color, f, t0, t1=None, alpha=1.0):
    if f < t0 or (t1 is not None and f > t1 + 1): return
    dy, a = rise(f, t0, 10, 18)
    if t1 is not None and f > t1 - 4:
        sdy, sa = snap(f, t1); dy += sdy; a *= sa
    put_line(base, text, font(INTER, 42, (14, 800)), y, color, dy=dy, alpha=a * alpha, tracking=0.075)

def micro(base, text, y, color, f, t0, alpha=0.95, tracking=0.10, size=28, t1=None):
    if f < t0: return
    dy, a = rise(f, t0, 10, 12)
    if t1 is not None and f > t1 - 4:
        sdy, sa = snap(f, t1); dy += sdy; a *= sa
    put_line(base, text, font(INTER, size, (14, 600)), y, color, dy=dy, alpha=a * alpha, tracking=tracking, shadow=False)

def dim_overlay(base, amount):
    if amount <= 0.002: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, int(255 * clamp01(amount))))
    base.alpha_composite(lay)

_tint_cache = {}
def tint_half(base, color, side, alpha):
    if alpha <= 0.004: return
    key = (color, side, round(alpha, 2))
    if key not in _tint_cache:
        if len(_tint_cache) > 60: _tint_cache.clear()
        _tint_cache[key] = Image.new("RGBA", (W // 2, H), color + (int(255 * alpha),))
    base.alpha_composite(_tint_cache[key], (0 if side == "left" else W // 2, 0))

def vline(base, x, y0, y1, color, alpha, w=2):
    if y1 <= y0 or alpha <= 0.004: return
    lay = Image.new("RGBA", (w, int(y1 - y0)), color + (int(255 * alpha),))
    base.alpha_composite(lay, (int(x - w / 2), int(y0)))

# ---------------------------------------------------------------- scenes
def morph_line(base, text, f, t0, y0, y1, s0, s1, color=IVORY, t1=None):
    """shrink-and-rise morph from a hook size to a claim size (stays crisp at rest)."""
    if f < t0: return
    p = clamp01(SPRING(f - t0))
    s_final = fit_size(text, A_BLACK, s1, SAFE_W)
    sc0 = fit_size(text, A_BLACK, s0, SAFE_W) / s_final
    y = y0 + (y1 - y0) * p
    a = 1.0
    if t1 is not None and f > t1 - 4:
        _, a = snap(f, t1); y += -20 * clamp01((f - (t1 - 4)) / 4.0)
    blit(base, text_img(text, font(A_BLACK, s_final), color), CX, y,
         scale=1 + (sc0 - 1) * (1 - p), alpha=a)

def scene1(base, f):
    # 1.1 SAME HAND -> shrinks up at 45
    if f < 48:
        sc, a = slam(f, 0)
        put_line(base, "SAME HAND.", font(A_BLACK, fit_size("SAME HAND.", A_BLACK, HOOK, SAFE_W)),
                 880, IVORY, scale=sc, alpha=a)
    elif f < 97:
        morph_line(base, "SAME HAND.", f, 45, 880, 790, HOOK, CLAIM, t1=95)
    # 1.2 TWO SEATS -> shrinks up at 92
    if 45 <= f < 50:
        big_line(base, "TWO SEATS.", f, 45, 930, IVORY, HOOK)
    elif 50 <= f < 140:
        if f < 92:
            big_line(base, "TWO SEATS.", f, 45, 930, IVORY, HOOK)
        else:
            morph_line(base, "TWO SEATS.", f, 92, 930, 800, HOOK, CLAIM)
    # 1.3 TWO RESULTS
    if 90 <= f < 135:
        big_line(base, "TWO RESULTS.", f, 90, 940, IVORY, HOOK, t1=134)
        p = clamp01((f - 92) / 10.0)
        tint_half(base, EARLY, "left", 0.075 * p)
        tint_half(base, LATE, "right", 0.075 * p)
        vline(base, CX, 960 - 380 * p, 960 + 380 * p, IVORY, 0.26 * p)

def scene2(base, f, rot):
    if f < 198:
        for k, (rank, t0, dx) in enumerate((("A", 135, -150), ("J", 145, 150))):
            p = SPRING_DEAL(max(0, f - t0))
            draw_card(base, rank, "spades", 288, 408, CX + dx, 866 - 200 * (1 - p),
                      alpha=clamp01(p * 2.4), rot=(7 if k else -7) * (1 - p))
        if f >= 150:
            kicker(base, "THE SAME TWO CARDS", 1150, IVORY, f, 150, 198, alpha=0.92)
    if 197 <= f < 252:
        p = SPRING(max(0, f - 197))
        # lift the pair off the type so the white-on-white collision never forms
        card_pair(base, CX, 866 - 106 * p, 288, 408, spread=150 + 46 * p, rot=7 + 3 * p)
        tint_half(base, EARLY, "left", 0.05 * p)
        tint_half(base, LATE, "right", 0.05 * p)
        big_line(base, "ONE HAND.", f, 202, 1090, IVORY, CLAIM, t1=250)
        big_line(base, "TWO SEATS.", f, 208, 1200, IVORY, CLAIM, t1=250)
    if f >= 246:
        p = ease_out_cubic((f - 246) / 18)
        out = 1 - clamp01((f - 276) / 8.0)
        for k, (rank, ddx) in enumerate((("A", -34), ("J", 34))):
            draw_card(base, rank, "spades", max(8, int(288 - 150 * p)), max(8, int(408 - 212 * p)),
                      CX + ddx * (0.5 + 0.5 * p), 760 + (1235 - 760) * p, alpha=0.95 * out,
                      rot=(-2 if k == 0 else 2))
        if f < 300:
            pr = ease_in_out(clamp01((f - 244) / 34))
            if pr > 0:
                lay = arc_img(RING_R, -90, -90 + 300 * pr, 3, CHIP, alpha=0.95 * out, head=True)
                base.alpha_composite(lay, (int(CX - RING_R - 3), int(RING_C[1] - RING_R - 3)))
        micro(base, "POSITION = WHEN YOU ACT", 1372, MUTE, f, 246, alpha=0.95, size=30, tracking=0.10, t1=284)

def scene3(base, f, rot):
    if f >= 285:
        seat_mark(base, 1, rot, EARLY, alpha=1.0, radius=32)
    if 285 <= f <= 352:
        kicker(base, "UNDER THE GUN", 452, EARLY, f, 285, 352)
        big_line(base, "FIRST TO ACT", f, 287, 578, IVORY, CLAIM, t1=352)
    if 345 <= f <= 428:
        p = clamp01((f - 345) / 66.0)
        n = int(round(1 + 7 * ease_out_cubic(p)))
        big_line(base, f"{n} PLAYERS", f, 345, 560, IVORY, CLAIM, t1=428)
        big_line(base, "BEHIND YOU", f, 351, 674, IVORY, CLAIM, t1=428)
        for i in range(9):
            t0 = 348 + i * 8.0
            if f >= t0:
                seat_mark(base, ((i + 1) % 9) + 1, rot, EARLY, alpha=clamp01((f - t0) / 4.0) * 0.7, glow=False)
    if 420 <= f <= 510:
        big_line(base, "NO IDEA", f, 420, 498, IVORY, CLAIM, t1=510)
        big_line(base, "WHAT'S COMING", f, 426, 612, IVORY, CLAIM, t1=510)
        for i in range(1, 10):
            t0 = 428 + (i - 1) * 5
            if f >= t0:
                aa = clamp01((f - t0) / 6.0) * 0.62
                if f > 490: aa *= 1 - clamp01((f - 490) / 10.0) * 0.35
                qx, qy = seat_pos(i, rot)
                ar = math.radians(seat_angle(i, rot))
                blit(base, text_img("?", font(A_BLACK, 56), EARLY),
                     qx + math.cos(ar) * 46, qy + math.sin(ar) * 46, alpha=aa)
    if f >= 500:
        sc, a = slam(f, 500)
        sh = 0.0
        if 500 <= f < 507:
            sh = 11 * (1 - (f - 500) / 7) * math.sin((f - 500) * 8.0)
        put_line(base, "GUESSING.", font(A_BLACK, fit_size("GUESSING.", A_BLACK, HOOK, SAFE_W)),
                 880, EARLY, scale=sc, alpha=a, cx=CX + sh)
        if f >= 508:
            micro(base, "WORST INFORMATION AT THE TABLE", 1006, IVORY, f, 508, alpha=0.62, size=28, tracking=0.09, t1=584)

def scene4(base, f, rot):
    bx, by = seat_pos(6, rot)
    if f >= 585:
        p = SPRING_DEAL(max(0, f - 585))
        blit(base, ring_img(34, 6, CHIP, 1.0), bx, by - 24 * (1 - p), alpha=clamp01(p * 2), scale=0.5 + 0.5 * p)
        seat_mark(base, 6, rot, LATE, alpha=1.0, radius=36)
    if 585 <= f <= 652:
        kicker(base, "ON THE BUTTON", 452, LATE, f, 585, 652)
        big_line(base, "LAST TO ACT", f, 587, 578, IVORY, CLAIM, t1=652)
    if 640 <= f <= 730:
        p = clamp01((f - 640) / 44.0)
        n = int(round(8 * ease_out_cubic(p)))
        big_line(base, f"{n} DECISIONS", f, 640, 560, LATE, CLAIM, t1=730)
        big_line(base, "BEFORE YOURS", f, 646, 674, LATE, CLAIM, t1=730)
        for k in range(8):
            t0 = 646 + k * 6.0
            if f >= t0:
                pr = ease_in_out(clamp01((f - t0) / 20.0))
                a0 = seat_angle(k + 1, rot)
                ang = math.radians(a0 + (seat_angle(6, rot) - a0) * min(1, pr))
                px = RING_C[0] + math.cos(ang) * RING_R
                py = RING_C[1] + math.sin(ang) * RING_R
                al = 0.9 * (1 - clamp01((pr - 0.88) / 0.12))
                blit(base, disc_img(7, LATE), px, py, alpha=al)
    if 720 <= f <= 830:
        rows = (("FOLDED", "5", IVORY, 1024, 72, 44), ("LIMPED", "2", IVORY, 1114, 72, 44),
                ("RAISED", "$15", CHIP, 1204, 92, 44))
        for k, (lab, val, col, yy, szv, szl) in enumerate(rows):
            t0 = 720 + k * 12
            if f >= t0:
                d, a = rise(f, t0, 12, 26)
                li = text_img(lab, font(INTER, szl, (14, 800)), IVORY, 0.14)
                vi = text_img(val, font(A_BLACK, szv), col, -0.01)
                blit(base, li, 312 + li.width / 2, yy + d, alpha=a * 0.95)
                blit(base, vi, 768 - vi.width / 2, yy + d, alpha=a)
                lay = Image.new("RGBA", (466, 2), (255, 255, 255, int(255 * 0.12 * a)))
                base.alpha_composite(lay, (308, yy + 44 + int(d)))
        if f >= 726:
            cp = clamp01((f - 726) / 18.0)
            for cxx, n in ((486, 3), (540, 4), (594, 2)):
                chip_stack(base, cxx, 1392, max(1, int(round(n * cp))), r=26, alpha=0.55 * cp)
    if f >= 820:
        if f < 870:
            big_line(base, "YOU'RE NOT", f, 820, 578, IVORY, CLAIM, t1=870)
            big_line(base, "GUESSING.", f, 826, 700, IVORY, HOOK, t1=870)
        else:
            big_line(base, "YOU'RE", f, 866, 578, IVORY, CLAIM)
            sc, a = slam(f, 866)
            put_line(base, "RESPONDING.", font(A_BLACK, fit_size("RESPONDING.", A_BLACK, HOOK, SAFE_W)),
                     700, LATE, scale=sc, alpha=a)
            pw = clamp01((f - 876) / 6.0)
            if pw > 0:
                wd = int(600 * pw)
                lay = Image.new("RGBA", (max(1, wd), 4), LATE + (255,))
                base.alpha_composite(lay, (CX - wd // 2, 774))

def scene5(base, f, rot):
    if 915 <= f < 1185:
        pw = clamp01((f - 915) / 6.0)
        tint_half(base, EARLY, "left", 0.07 * pw)
        tint_half(base, LATE, "right", 0.07 * pw)
        vline(base, CX, 966 - 330 * pw, 966 + 330 * pw, IVORY, 0.20 * pw)
    if 915 <= f <= 995:
        for ccx, lab, col in ((288, "BLIND", EARLY), (792, "INFORMED", LATE)):
            for k, (rank, ddx) in enumerate((("A", -96), ("J", 96))):
                draw_card(base, rank, "spades", 186, 264, ccx + ddx, 742, alpha=1.0,
                          rot=(-5 if k == 0 else 5))
            li = text_img(lab, font(INTER, 46, (14, 800)), col, 0.14)
            blit(base, li, ccx, 950, alpha=1.0)
    if 990 <= f <= 1090:
        if 990 <= f < 993:
            lay = Image.new("RGBA", (W, H), IVORY + (int(255 * 0.12 * (1 - (f - 990) / 3)),))
            base.alpha_composite(lay)
        big_line(base, "POSITION", f, 991, 770, IVORY, HOOK, t1=1090)
        big_line(base, "IS FREE.", f, 997, 900, IVORY, HOOK, t1=1090)
    if f >= 1080:
        lines = (("IT DOESN'T CHANGE", 676, IVORY), ("YOUR CARDS.", 774, IVORY),
                 ("IT CHANGES", 902, LATE), ("WHAT YOU KNOW.", 1000, LATE))
        size = 84
        gap = 24
        for k, (txt, yy, col) in enumerate(lines):
            words = txt.split(" ")
            imgs = [text_img(w, font(A_BLACK, size), col, -0.02) for w in words]
            total = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
            x = CX - total / 2
            acc = 0
            for j, im in enumerate(imgs):
                start = 1080 + k * 6 + j * 3
                if f >= start:
                    p = ease_out_cubic((f - start) / 9.0)
                    blit(base, im, x + acc + im.width / 2, yy + 20 * (1 - p),
                         alpha=p, scale=1 + 0.05 * (1 - p))
                acc += im.width + gap

def scene6(base, f, rot):
    if 1185 <= f < 1336:
        p = ease_out_cubic((f - 1185) / 10.0)
        q = 1 - clamp01((f - 1328) / 7.0)
        s = 0.96 + 0.04 * p
        pw, ph = int(940 * s), int(480 * s)
        panel = rrect_img(pw, ph, 24, fill=C["felt700"], stroke=CHIP, sw=1.5, alpha=0.55)
        panel = alpha_mul(panel, p * q)
        base.alpha_composite(panel, (CX - pw // 2, 880 - ph // 2))
        fa = q
        if f >= 1192:
            sc, a = slam(f, 1192)
            put_line(base, "TIGHT UP FRONT.", font(A_BLACK, 76), 830, IVORY, scale=sc, alpha=a * fa)
        if f >= 1204:
            sc, a = slam(f, 1204)
            put_line(base, "WIDE ON THE BUTTON.", font(A_BLACK, fit_size("WIDE ON THE BUTTON.", A_BLACK, 76, 820)),
                     940, LATE, scale=sc, alpha=a * fa)
    if 1260 <= f < 1336:
        d, a = rise(f, 1260, 10, 12)
        a *= 1 - clamp01((f - 1328) / 8.0)
        put_line(base, "THE CHEAPEST EDGE AT $1/$2", font(INTER, 28, (14, 700)), 1176,
                 IVORY, dy=d, alpha=a * 0.62, tracking=0.10, shadow=False)
        hd = text_img("NOFACE POKER", font(INTER, 24, (14, 700)), MUTE, 0.16)
        blit(base, hd, 130 + hd.width / 2, 1392 + d, alpha=a * 0.8)

# ---------------------------------------------------------------- assembly
BG = None

def ring_alpha(f):
    a = 0.95 * clamp01(f / 20.0)
    if f < 135: a *= 0.62
    if 1185 <= f < 1332: a *= 0.42
    if f > 1326:
        a *= 1 - clamp01((f - 1326) / 23.0)
    return a

def ring_rot(f):
    if f < 135: return 0.0
    return ROT_HOLD * ease_in_out(clamp01((f - 135) / 26.0))

def render_frame(f):
    global BG
    if BG is None: BG = build_bg()
    base = BG.copy()
    rot = ring_rot(f)
    if 135 <= f < 285:  bright = 0.55
    elif 285 <= f < 585: bright = 0.80
    else: bright = 1.0
    draw_ring(base, f, rot, ring_alpha(f), bright)

    if f < 135:
        scene1(base, f)
    elif f < 285:
        scene2(base, f, rot)
    elif f < 585:
        scene3(base, f, rot)
        if f >= 500:
            dim_overlay(base, 0.34 * clamp01((f - 500) / 12.0))
    elif f < 915:
        scene4(base, f, rot)
    elif f < 1185:
        scene5(base, f, rot)
    else:
        scene6(base, f, rot)
    return base

def save_png(f, path):
    render_frame(f).convert("RGB").save(path, compress_level=1)

def make_sheet(paths, out, cols=4, scale=0.30):
    ims = [Image.open(p) for p in paths]
    w, h = int(W * scale), int(H * scale)
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (w * cols, h * rows), (12, 12, 12))
    for i, im in enumerate(ims):
        sh.paste(im.resize((w, h), Image.LANCZOS), ((i % cols) * w, (i // cols) * h))
    sh.save(out, compress_level=1)
    return out

if __name__ == "__main__":
    t = time.time()
    save_png(int(sys.argv[1]) if len(sys.argv) > 1 else 0, "build/probe2.png")
    print("%.2fs" % (time.time() - t))
