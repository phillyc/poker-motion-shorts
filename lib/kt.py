"""kt.py -- a small declarative kinetic-typography engine.

A short is a JSON timeline of elements; the engine turns it into frames:

    {"id": "pot-odds", "fps": 30, "duration": 12.9,
     "palette": {"bg": "#08110E", "ink": "#F4EFE6", "accent": "#E8B44A"},
     "elements": [
        {"kind": "kicker", "text": "LIVE $1/$2  POT ODDS", "t0": 0.0, "t1": 3.0, "y": 560},
        {"kind": "text", "text": "$50", "t0": 0.15, "t1": 3.0, "y": 760, "size": 260,
         "preset": "slam", "font": "display", "color": "ink"},
        {"kind": "counter", "to": 25, "suffix": "%", "t0": 4.0, "t1": 6.2, "y": 900},
        {"kind": "bar", "t0": 4.2, "t1": 6.2, "y": 1050, "pct": 0.25, "label": "25%"},
        {"kind": "verdict", "text": "CALL", "t0": 6.6, "t1": 9.0, "color": "good"}
     ]}

Design rules baked in: everything is composed inside the 250-1440 vertical safe
band, type is supersampled 2x, entrances use springs (no linear fades), every
hold gets a micro-drift so nothing is frozen.
"""
import json
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import (  # noqa: E402
    A_BLACK, DEJA, FPS, H, INTER, SPRING, W, arc_img, blit, circle_img, clamp01,
    disc_img, ease_in_out, ease_out_back, ease_out_cubic, ease_out_quint, font,
    mix, rgb, rgba, ring_img, rrect_img, text_img,
)

# Anton is the condensed display face used for the big kinetic lines.
ANTON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts", "Anton-Regular.ttf")
if not os.path.exists(ANTON):
    ANTON = A_BLACK

FONT_FILES = {"display": A_BLACK, "slam": ANTON, "ui": INTER}
SAFE_TOP, SAFE_BOT = 250, 1440


# ------------------------------------------------------------------ palette
def palette(spec):
    p = {
        "bg": (8, 17, 14),
        "bg2": (24, 74, 56),
        "ink": (244, 239, 230),
        "dim": (150, 165, 158),
        "accent": (232, 180, 74),
        "good": (53, 225, 196),
        "bad": (255, 77, 61),
    }
    for k, v in (spec.get("palette") or {}).items():
        p[k] = rgb(v)
    return p


# ------------------------------------------------------------------ background
def build_bg(spec, accent):
    """Radial felt light + vignette + a faint accent bloom. Pure NumPy-free so it
    stays fast on small boxes (Pillow gradients are enough at 1080x1920)."""
    import numpy as np
    p = palette(spec)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W * 0.5, H * 0.44
    dx = (xx - cx) / (W * 0.78)
    dy = (yy - cy) / (H * 0.70)
    d = np.sqrt(dx * dx + dy * dy)
    g = np.clip(1.0 - d, 0, 1) ** 1.5
    inner = np.array(p["bg2"], dtype=np.float32)
    outer = np.array(p["bg"], dtype=np.float32)
    if spec.get("palette", {}).get("bg2") is None:
        inner = inner * 0.16
        outer = outer * 0.35
    img = outer[None, None, :] + (inner - outer)[None, None, :] * g[..., None]
    # top sheen
    sheen = np.clip(1.0 - yy / (H * 0.55), 0, 1)[..., None] ** 2.2 * 7.0
    img = img + sheen
    # vignette
    vx = (xx - cx) / (W * 0.62)
    vy = (yy - H * 0.5) / (H * 0.58)
    vig = np.clip(np.sqrt(vx * vx + vy * vy) - 0.62, 0, 1.5) ** 1.4
    img = img * (1.0 - 0.55 * vig[..., None])
    # accent bloom bottom-right, very low frequency
    bx, by = W * 0.92, H * 0.10
    bl = np.exp(-(((xx - bx) / (W * 0.55)) ** 2 + ((yy - by) / (H * 0.35)) ** 2))
    img = img + np.array(accent, dtype=np.float32)[None, None, :] * (bl[..., None] * 0.10)
    rng = np.random.default_rng(5)
    img = img + rng.normal(0, 1.0, img.shape)
    return Image.fromarray(np.clip(img, 0, 255).astype("uint8"), "RGB").convert("RGBA")


# ------------------------------------------------------------------ type
_line_cache = {}
_shadow_cache = {}


def _line(text, size, color, font_key="slam", tracking=0.0, axes=None, weight=None, ss=2):
    key = (text, size, color, font_key, round(tracking, 4), axes, weight)
    hit = _line_cache.get(key)
    if hit is not None:
        return hit
    path = FONT_FILES[font_key]
    ax = axes
    if font_key == "ui" and ax is None:
        ax = (14, weight or 600)
    f = font(path, int(size), ax)
    im = text_img(text, f, color, tracking=tracking, ss=ss)
    _line_cache[key] = im
    return im


def _shadow(im, color=(0, 0, 0), blur=18, alpha=0.55):
    key = (id(im), color, blur, alpha)
    hit = _shadow_cache.get(key)
    if hit is not None:
        return hit
    a = im.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
    a = a.point(lambda v: int(v * alpha))
    sh = Image.new("RGBA", im.size, color + (0,))
    sh.putalpha(a)
    _shadow_cache[key] = sh
    return sh


def rich_width(runs, size, tracking, font_key="slam", weight=None):
    total = 0
    for r in runs:
        im = _line(r["text"], size, (255, 255, 255), font_key, tracking,
                   weight=weight)
        total += im.width + r.get("gap", 0)
    return total


# ------------------------------------------------------------------ motion
def _spring01(frames):
    return clamp01(SPRING(max(0, frames)))


def state(el, t):
    """Return (alpha, dx, dy, scale, rot, reveal, squeeze)."""
    t0 = el.get("t0", 0.0)
    t1 = el.get("t1", 1e9)
    preset = el.get("preset", "rise")
    dur = el.get("in", 0.40)
    p = clamp01((t - t0) / max(0.001, dur))
    sf = int(round((t - t0) * FPS))
    alpha, dx, dy, scale, rot, reveal, sq = 1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 1.0
    if t < t0:
        return (0.0, 0, 0, 1, 0, 0, 1)

    if preset == "slam":              # large -> settle, hard cut in
        alpha = clamp01(p * 3.2)
        scale = 1.0 + 0.55 * (1.0 - _spring01(sf))
        dy = -10 * (1.0 - _spring01(sf))
    elif preset == "rise":
        s = _spring01(sf)
        alpha = clamp01(p * 1.6)
        dy = 54 * (1.0 - s)
        scale = 0.985 + 0.015 * s
    elif preset == "drop":
        s = _spring01(sf)
        alpha = clamp01(p * 1.8)
        dy = -70 * (1.0 - s)
    elif preset == "pop":
        alpha = clamp01(p * 2.6)
        scale = 0.55 + 0.45 * ease_out_back(p, 2.2)
        rot = -3.2 * (1.0 - p)
    elif preset == "wipe":
        reveal = ease_out_quint(p)
        alpha = 1.0
    elif preset == "slide_left":
        alpha = clamp01(p * 2.0)
        dx = 90 * (1.0 - ease_out_quint(p))
    elif preset == "slide_right":
        alpha = clamp01(p * 2.0)
        dx = -90 * (1.0 - ease_out_quint(p))
    elif preset == "blur_in":
        alpha = clamp01(p * 1.4)
        scale = 1.10 - 0.10 * ease_out_cubic(p)
        dy = 12 * (1.0 - p)
    elif preset == "none":
        alpha = 1.0
    # exit
    if t > t1:
        q = clamp01((t - t1) / max(0.001, el.get("out", 0.26)))
        alpha *= 1.0 - ease_out_cubic(q)
        if el.get("exit") == "snap":
            scale *= 1.0 + 0.06 * ease_out_cubic(q)
        elif el.get("exit") == "sink":
            dy += 22 * ease_out_cubic(q)
        elif el.get("exit") == "lift":
            dy -= 26 * ease_out_cubic(q)
    # living micro-drift so nothing is ever frozen
    if el.get("drift", True):
        dy += 1.6 * math.sin(2 * math.pi * (t / 7.3) + hash(el.get("id", "x")) % 7)
    return (alpha, dx, dy, scale, rot, reveal, sq)


# ------------------------------------------------------------------ drawing
def draw_text(base, el, t, pal, cx=540):
    color = pal.get(el.get("color", "ink"), pal["ink"])
    size = el.get("size", 96)
    font_key = el.get("font", "slam")
    tracking = el.get("tracking", 0.0)
    weight = el.get("weight")
    y = el.get("y", 900)
    alpha, dx, dy, scale, rot, reveal, _ = state(el, t)
    if alpha <= 0.004:
        return
    runs = el.get("runs") or [{"text": el.get("text", "")}]
    stagger = el.get("stagger", 0.0)
    total_w = rich_width(runs, size, tracking, font_key, weight)
    if total_w * scale > 1020:            # never let a slam overshoot the frame
        scale = 1020.0 / total_w
    align = el.get("align", "center")
    if align == "center":
        x = cx - total_w / 2
    elif align == "left":
        x = cx - el.get("width", 900) / 2
    else:
        x = cx + el.get("width", 900) / 2 - total_w
    for i, run in enumerate(runs):
        rc = pal.get(run.get("color", el.get("color", "ink")), color)
        rmul = run.get("scale", 1.0)
        im = _line(run["text"], size, rc, font_key, tracking, weight=weight)
        ra = alpha
        rdy = dy + (1.0 - rmul) * size * 0.30
        rscale = scale * rmul
        ralpha = 1.0
        if stagger and i:
            d = i * stagger
            sp = clamp01((t - el.get("t0", 0) - d) / 0.26)
            ra = alpha * sp
            rdy = dy + 34 * (1.0 - _spring01(int((t - el.get("t0", 0) - d) * FPS)))
        if el.get("shadow", True):
            sh = _shadow(im, (0, 0, 0), max(8, size // 9), 0.55)
            blit(base, sh, x + im.width / 2 + 4, y + rdy + max(5, size // 14),
                 rscale, ra * ralpha, rot)
        if reveal < 0.999:
            wpx = max(1, int(im.width * reveal))
            im = im.crop((0, 0, wpx, im.height))
            blit(base, im, x + wpx / 2, y + rdy, rscale, ra, rot)
        else:
            blit(base, im, x + im.width / 2, y + rdy, rscale, ra, rot)
        x += im.width + run.get("gap", 0)


def draw_kicker(base, el, t, pal, cx=540):
    el = dict(el)
    el.setdefault("size", 30)
    el.setdefault("font", "ui")
    el.setdefault("weight", 700)
    el.setdefault("tracking", 0.22)
    el.setdefault("color", "accent")
    el.setdefault("preset", "wipe")
    alpha = state(el, t)[0]
    if alpha <= 0.004:
        return
    # small accent tick before the label
    txt = el.get("text", "")
    im = _line(txt, el["size"], pal.get(el["color"], pal["accent"]), el["font"],
               el["tracking"], weight=el["weight"])
    y = el.get("y", 520)
    _, dx, dy, scale, rot, reveal, _ = state(el, t)
    wpx = max(1, int(im.width * reveal))
    im2 = im.crop((0, 0, wpx, im.height))
    blit(base, im2, cx - im.width / 2 + wpx / 2, y + dy, scale, alpha)
    if el.get("rule", True) and reveal > 0.2:
        rw = int(54 * clamp01((reveal - 0.2) / 0.8))
        lay = rrect_img(max(2, rw), 3, 2, fill=pal["accent"])
        base.alpha_composite(lay, (int(cx - im.width / 2 - 22 - rw), int(y + dy - 2)))


def draw_counter(base, el, t, pal, cx=540):
    t0 = el.get("t0", 0.0)
    dur = el.get("count_dur", 0.9)
    p = ease_out_cubic(clamp01((t - t0) / dur))
    v = el.get("from", 0) + (el.get("to", 0) - el.get("from", 0)) * p
    fmt = el.get("fmt", "{:.0f}")
    txt = fmt.format(v)
    e2 = dict(el)
    e2["text"] = el.get("prefix", "") + txt + el.get("suffix", "")
    e2.setdefault("preset", "none")
    draw_text(base, e2, t, pal, cx)


def draw_bar(base, el, t, pal, cx=540):
    alpha, dx, dy, scale, rot, reveal, _ = state(el, t)
    if alpha <= 0.004:
        return
    w = el.get("width", 760)
    h = el.get("height", 18)
    y = el.get("y", 1050) + dy
    pct = el.get("pct", 0.5) * ease_out_cubic(clamp01((t - el.get("t0", 0)) / el.get("in", 1.0)))
    x0 = cx - w / 2
    trackcol = mix(pal["bg"], pal.get("dim", (120, 130, 125)), 0.34)
    track = rrect_img(w, h, h // 2, fill=trackcol)
    base.alpha_composite(track, (int(x0), int(y - h / 2)))
    fillw = max(2, int(w * pct))
    fcol = pal.get(el.get("color", "accent"), pal["accent"])
    fill = rrect_img(fillw, h, h // 2, fill=fcol)
    base.alpha_composite(fill, (int(x0), int(y - h / 2)))
    if el.get("label"):
        # label floats above the fill head, never over the track
        lab = _line(el["label"], el.get("label_size", 40), pal.get(el.get("color", "accent"), pal["accent"]), "ui", 0.04, weight=800)
        lx = min(x0 + fillw, x0 + w - lab.width / 2)
        blit(base, lab, lx, y - h / 2 - lab.height / 2 - 18, 1.0, alpha)
        tick = rrect_img(3, h + 20, 0, fill=fcol)
        base.alpha_composite(tick, (int(x0 + fillw - 1), int(y - h / 2 - 10)))
    if el.get("ticks"):
        for frac, txt in el["ticks"]:
            tx = x0 + w * frac
            tick = rrect_img(2, 10, 0, fill=mix(pal["bg"], pal["dim"], 0.55))
            base.alpha_composite(tick, (int(tx), int(y + h / 2 + 7)))
            lab = _line(txt, 30, mix(pal["bg"], pal.get("dim", (120, 130, 125)), 0.8), "ui", 0.02, weight=600)
            blit(base, lab, tx, y + h / 2 + 36, 1.0, alpha * 0.95)


def draw_rule(base, el, t, pal, cx=540):
    alpha, dx, dy, scale, rot, reveal, _ = state(el, t)
    if alpha <= 0.004:
        return
    w = el.get("width", 640) * ease_out_quint(clamp01((t - el.get("t0", 0)) / el.get("in", 0.5)))
    h = el.get("height", 5)
    col = pal.get(el.get("color", "accent"), pal["accent"])
    lay = rrect_img(max(2, int(w)), h, h // 2, fill=col)
    base.alpha_composite(lay, (int(cx - w / 2), int(el.get("y", 900) + dy - h / 2)))


def draw_badge(base, el, t, pal, cx=540):
    alpha, dx, dy, scale, rot, reveal, _ = state(el, t)
    if alpha <= 0.004:
        return
    txt = el.get("text", "")
    size = el.get("size", 30)
    im = _line(txt, size, pal.get(el.get("color", "ink"), pal["ink"]), "ui", 0.14, weight=800)
    pw = el.get("pad_x", 30)
    ph = el.get("pad_y", 16)
    bw, bh = im.width + pw * 2, im.height + ph * 2
    box = rrect_img(int(bw), int(bh), el.get("radius", bh // 2),
                    fill=pal.get(el.get("fill", "accent"), pal["accent"]))
    if el.get("stroke"):
        box = rrect_img(int(bw), int(bh), el.get("radius", bh // 2),
                        fill=None, stroke=pal.get(el.get("stroke"), pal["accent"]), sw=3)
    x, y = cx, el.get("y", 800) + dy
    base.alpha_composite(box, (int(x - bw / 2), int(y - bh / 2)))
    blit(base, im, x + dx * 0, y + 1, 1.0, alpha)


def draw_cardface(base, el, t, pal, cx=540):
    """Small playing card (rank/suit) with a deal-in animation."""
    alpha, dx, dy, scale, rot, reveal, _ = state(el, t)
    if alpha <= 0.004:
        return
    w = el.get("cw", 150)
    h = int(w * 1.4)
    face = (250, 248, 243)
    suit = el.get("suit", "spades")
    col = (216, 50, 60) if suit in ("hearts", "diamonds") else (28, 32, 30)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=int(w * 0.09), fill=face + (255,))
    sym = {"spades": "\u2660", "hearts": "\u2665", "diamonds": "\u2666", "clubs": "\u2663"}[suit]
    rf = font(INTER, int(w * 0.30), (14, 800))
    d.text((w * 0.12, h * 0.05), el.get("rank", "A"), font=rf, fill=col)
    sf = font(DEJA, int(w * 0.30))
    d.text((w * 0.12, h * 0.30), sym, font=sf, fill=col)
    big = font(DEJA, int(w * 0.42))
    bb = d.textbbox((0, 0), sym, font=big)
    d.text((w * 0.62 - (bb[2] - bb[0]) / 2, h * 0.52), sym, font=big, fill=col)
    blit(base, im, cx + el.get("x", 0) + dx, el.get("y", 800) + dy, scale, alpha, rot)


DRAW = {
    "text": draw_text,
    "kicker": draw_kicker,
    "counter": draw_counter,
    "bar": draw_bar,
    "rule": draw_rule,
    "badge": draw_badge,
    "card": draw_cardface,
}


# ------------------------------------------------------------------ frame
def render_frame(f, spec, bg, total):
    t = f / float(spec.get("fps", FPS))
    pal = palette(spec)
    base = bg.copy()
    cx = spec.get("cx", 540)
    for el in spec.get("elements", []):
        fn = DRAW.get(el.get("kind", "text"))
        if fn is None:
            continue
        off = spec.get("y_offset", 0)
        if off:
            el = dict(el, y=el.get("y", 900) + off)
        fn(base, el, t, pal, cx)
    # progress hairline (below the platform UI, purely decorative)
    if spec.get("progress", True):
        w = W - 120
        p = clamp01(t / max(0.001, spec.get("duration", total / float(spec.get("fps", FPS)))))
        ImageDraw.Draw(base).rounded_rectangle(
            [60, H - 96, 60 + w, H - 93], radius=2, fill=(255, 255, 255, 26))
        ImageDraw.Draw(base).rounded_rectangle(
            [60, H - 96, 60 + max(2, int(w * p)), H - 93], radius=2,
            fill=pal["accent"] + (200,))
    return base.convert("RGB")
