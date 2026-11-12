"""Core drawing/motion library for the poker short."""
import math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), "assets", "fonts")
if not os.path.isdir(FONTS):
    FONTS = os.path.join(HERE, "fonts")

C = {
    "felt900": (8, 17, 14),
    "felt700": (18, 59, 46),
    "ivory": (244, 239, 230),
    "early": (255, 77, 61),
    "late": (53, 225, 196),
    "chip": (232, 180, 74),
    "mute": (110, 124, 119),
    "cardRed": (216, 50, 60),
    "black": (0, 0, 0),
}

def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))

def rgba(c, a):
    return (c[0], c[1], c[2], max(0, min(255, int(a * 255))))

# ---------------------------------------------------------------- easing
def clamp01(x):
    return 0.0 if x < 0 else (1.0 if x > 1 else x)

def ease_out_cubic(t):
    t = clamp01(t); return 1 - (1 - t) ** 3

def ease_out_quint(t):
    t = clamp01(t); return 1 - (1 - t) ** 5

def ease_in_cubic(t):
    t = clamp01(t); return t ** 3

def ease_in_out(t):
    t = clamp01(t)
    return 4 * t * t * t if t < .5 else 1 - (-2 * t + 2) ** 3 / 2

def ease_out_back(t, s=1.70158):
    t = clamp01(t); t -= 1
    return 1 + t * t * ((s + 1) * t + s)

class Spring:
    def __init__(self, stiffness=320, damping=22, mass=0.9):
        self.w0 = math.sqrt(stiffness / mass)
        self.z = damping / (2 * math.sqrt(stiffness * mass))
        self.wd = self.w0 * math.sqrt(max(1e-6, 1 - self.z ** 2))

    def __call__(self, frames):
        t = frames / FPS
        if t <= 0: return 0.0
        if self.z >= 1:
            return 1 - math.exp(-self.w0 * t) * (1 + self.w0 * t)
        e = math.exp(-self.z * self.w0 * t)
        return 1 - e * (math.cos(self.wd * t) + (self.z * self.w0 / self.wd) * math.sin(self.wd * t))

SPRING = Spring(320, 22, 0.9)
SPRING_DEAL = Spring(320, 26, 0.9)

# ---------------------------------------------------------------- shapes (AA via supersampled tiles)
def _down(tile, w, h):
    return tile.resize((w, h), Image.LANCZOS)

def circle_img(r, color, alpha=1.0, ss=3):
    w = int(2 * r + 2); 
    t = Image.new("RGBA", (w * ss, w * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    d.ellipse([ss, ss, w * ss - ss - 1, w * ss - ss - 1], fill=rgba(color, alpha))
    return _down(t, w, w)

def ring_img(r, width, color, alpha=1.0, ss=3):
    w = int(2 * r + 2 + width)
    t = Image.new("RGBA", (w * ss, w * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    o = width / 2 * ss
    d.ellipse([ss + o, ss + o, w * ss - ss - 1 - o, w * ss - ss - 1 - o],
              outline=rgba(color, alpha), width=max(1, int(width * ss)))
    return _down(t, w, w)

def disc_img(r, fill, ring=None, ringw=2, ringalpha=1.0, alpha=1.0, ss=3):
    w = int(2 * r + 2)
    t = Image.new("RGBA", (w * ss, w * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    if fill:
        d.ellipse([ss, ss, w * ss - ss - 1, w * ss - ss - 1], fill=rgba(fill, alpha))
    if ring:
        o = ringw / 2 * ss
        d.ellipse([ss + o, ss + o, w * ss - ss - 1 - o, w * ss - ss - 1 - o],
                  outline=rgba(ring, ringalpha * alpha), width=max(1, int(ringw * ss)))
    return _down(t, w, w)

def arc_img(r, a0, a1, width, color, alpha=1.0, ss=3, head=False):
    """angles in degrees, clockwise from 3 o'clock (PIL convention)."""
    w = int(2 * r + 2 + width)
    t = Image.new("RGBA", (w * ss, w * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    o = width / 2 * ss
    bb = [ss + o, ss + o, w * ss - ss - 1 - o, w * ss - ss - 1 - o]
    if abs(a1 - a0) > 0.4:
        d.arc(bb, a0, a1, fill=rgba(color, alpha), width=max(1, int(width * ss)))
    if head and abs(a1 - a0) > 1:
        hx = w * ss / 2 + math.cos(math.radians(a1)) * (r + width / 2) * ss
        hy = w * ss / 2 + math.sin(math.radians(a1)) * (r + width / 2) * ss
        rr = width * 0.95 * ss
        d.ellipse([hx - rr, hy - rr, hx + rr, hy + rr], fill=rgba(color, alpha))
    return _down(t, w, w)

def rrect_img(w, h, radius, fill=None, stroke=None, sw=2, alpha=1.0, ss=3):
    t = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    bb = [0, 0, w * ss - 1, h * ss - 1]
    if fill:
        d.rounded_rectangle(bb, radius=radius * ss, fill=fill)
    if stroke:
        d.rounded_rectangle(bb, radius=radius * ss, outline=rgba(stroke, alpha), width=max(1, int(sw * ss)))
    return _down(t, w, h)

# ---------------------------------------------------------------- text
_font_cache = {}
_txt_cache = {}
SUIT = {"spades": "\u2660", "hearts": "\u2665", "diamonds": "\u2666", "clubs": "\u2663"}

def font(path, size, axes=None):
    key = (path, size, tuple(axes) if axes else None)
    f = _font_cache.get(key)
    if f is None:
        f = ImageFont.truetype(path, size)
        if axes:
            try: f.set_variation_by_axes(axes)
            except Exception: pass
        _font_cache[key] = f
    return f

A_BLACK = os.path.join(FONTS, "ArchivoBlack-Regular.ttf")
INTER = os.path.join(FONTS, "Inter[opsz,wght].ttf")
DEJA = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def text_img(text, tfont, color, tracking=0.0, alpha=1.0, ss=1):
    """Render a single line (no newlines) tightly cropped, AA, with tracking in em.

    `ss` supersamples: glyphs are rasterised at ss x the target size then downscaled,
    so big display type keeps clean edges instead of halving in size.
    """
    key = (text, id(tfont), color, tracking, alpha, ss)
    hit = _txt_cache.get(key)
    if hit is not None: return hit
    px = tfont.size
    fs = int(round(px * ss))
    f = tfont if fs == px else tfont.font_variant(size=fs)
    try:
        asc, desc = f.getmetrics()
    except Exception:
        asc, desc = fs, 0
    track = tracking * fs
    adv = [f.getlength(ch) for ch in text]
    total = sum(adv) + track * max(0, len(text) - 1)
    pad = int(round(px * 0.30 * ss)) + 4
    w = int(math.ceil(total)) + pad * 2
    h = int(asc + desc) + pad * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = pad
    fill = rgba(color, alpha)
    if abs(track) < 0.5:
        # draw in one pass so kerning/ligatures survive (matters for big display type)
        d.text((x, pad), text, font=f, fill=fill)
    else:
        for ch, a in zip(text, adv):
            d.text((x, pad), ch, font=f, fill=fill)
            x += a + track
    if ss != 1:
        img = img.resize((max(1, w // ss), max(1, h // ss)), Image.LANCZOS)
    # trim to ink bbox
    bb = img.getbbox()
    if bb: img = img.crop(bb)
    else: img = img.crop((0, 0, 1, 1))
    _txt_cache[key] = img
    return img

def fit_size(text, path, size, maxw, tracking=0.0, axes=None, min_size=20):
    while size > min_size:
        f = font(path, int(size), axes)
        w = sum(f.getlength(ch) for ch in text) + tracking * int(size) * max(0, len(text) - 1)
        if w <= maxw: return int(size)
        size -= 2
    return int(min_size)

def blit(base, img, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    """Composite img centered at (cx,cy)."""
    if alpha <= 0.003: return
    im = img
    if abs(scale - 1.0) > 0.002:
        nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
        im = im.resize((nw, nh), Image.LANCZOS)
    if abs(rot) > 0.2:
        im = im.rotate(-rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.997:
        im = im.copy()
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im.putalpha(a)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def alpha_mul(img, a):
    if a >= 0.997: return img
    im = img.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im
