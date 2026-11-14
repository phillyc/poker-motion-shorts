"""Render all frames with a 'living frame' pass (drifting key light + breathing
zoom + fine grain) and pipe straight into ffmpeg. render_frame() stays untouched."""
import subprocess, sys, time
import numpy as np
from PIL import Image
import render as R

W, H = 1080, 1920
TOTAL = 1350
LW, LH = W // 8, H // 8
_gx, _gy = np.meshgrid(np.arange(LW, dtype=np.float32), np.arange(LH, dtype=np.float32))
_rng = np.random.default_rng(7)
_grain = _rng.normal(0, 1, (LH, LW)).astype(np.float32)


def offset_field(f):
    """tiny int image of additive light + grain, upscaled to full frame."""
    p = f / TOTAL
    cx = LW * (0.5 + 0.26 * np.sin(2 * np.pi * p))
    cy = LH * (0.42 + 0.16 * np.cos(2 * np.pi * p + 0.7))
    sig = LW * (0.45 + 0.05 * np.sin(2 * np.pi * p * 2.0))
    field = np.exp(-((_gx - cx) ** 2 + (_gy - cy) ** 2) / (2 * sig * sig))
    light = field / field.max() * 10.0
    g = np.roll(_grain, f * 7 % LH, axis=0)
    g = np.roll(g, f * 11 % LW, axis=1) * 1.1
    if f in (0, TOTAL - 1):
        g = 0.0
    off = np.clip(light + g, 0, 255).astype(np.uint8)
    return np.array(Image.fromarray(off).resize((W, H), Image.BILINEAR), dtype=np.uint16)


def living(im, f):
    s = 1.0 + 0.0035 * (0.5 - 0.5 * np.cos(2 * np.pi * f / 150.0))
    if s > 1.0004:                      # subtle breathing push-in
        nw, nh = int(round(W * s)), int(round(H * s))
        im = im.resize((nw, nh), Image.BILINEAR)
        x0, y0 = (nw - W) // 2, (nh - H) // 2
        im = im.crop((x0, y0, x0 + W, y0 + H))
    a = np.asarray(im, dtype=np.uint16) + offset_field(f)[:, :, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "build/same_hand_v2.mp4"
    audio = sys.argv[2] if len(sys.argv) > 2 else "build/audio_vo.wav"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "30", "-i", "pipe:0",
           "-i", audio,
           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-maxrate", "14M", "-bufsize", "20M",
           "-profile:v", "high", "-level", "4.2", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=9",
           "-shortest", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    R.BG = R.build_bg()
    for f in range(TOTAL):
        p.stdin.write(living(R.render_frame(f).convert("RGB"), f).convert("RGB").tobytes())
        if f % 90 == 0:
            el = time.time() - t0
            print("frame %4d/%d  %.1fs  (%.1f fps)" % (f, TOTAL, el, (f + 1) / max(el, .01)), flush=True)
    p.stdin.close()
    print("ffmpeg rc=%s total %.1fs" % (p.wait(), time.time() - t0))


if __name__ == "__main__":
    main()
