#!/usr/bin/env python3
"""Render a kinetic-typography short from a JSON timeline.

    python render.py shorts/pot-odds.json out/pot-odds.mp4
    python render.py shorts/pot-odds.json out/pot-odds.mp4 --no-vo
    python render.py shorts/pot-odds.json --stills out/stills 0.5 2.0 4.2
    python render.py shorts/pot-odds.json --qa

Pipeline: Pillow/NumPy compositor -> "living frame" pass (drifting key light,
breathing push-in, fine grain) -> rawvideo pipe -> x264 + AAC, loudness-normalised
to -14 LUFS / -1.5 dBTP (the YouTube / Reels target).
"""
import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
import audio as A          # noqa: E402
import kt                  # noqa: E402
from core import FPS, H, W  # noqa: E402

LW, LH = W // 8, H // 8
_gx, _gy = np.meshgrid(np.arange(LW, dtype=np.float32), np.arange(LH, dtype=np.float32))
_grain = np.random.default_rng(7).normal(0, 1, (LH, LW)).astype(np.float32)


def offset_field(f, total):
    p = f / max(1, total)
    cx = LW * (0.5 + 0.24 * np.sin(2 * np.pi * p))
    cy = LH * (0.44 + 0.14 * np.cos(2 * np.pi * p + 0.7))
    sig = LW * (0.48 + 0.05 * np.sin(2 * np.pi * p * 2.0))
    field = np.exp(-((_gx - cx) ** 2 + (_gy - cy) ** 2) / (2 * sig * sig))
    light = field / field.max() * 8.0
    g = np.roll(_grain, f * 7 % LH, axis=0)
    g = np.roll(g, f * 11 % LW, axis=1) * 1.05
    if f in (0, total - 1):
        g = g * 0
    off = np.clip(light + g, 0, 255).astype(np.uint8)
    return np.array(Image.fromarray(off).resize((W, H), Image.BILINEAR), dtype=np.uint16)


def living(im, f, total):
    s = 1.0 + 0.0035 * (0.5 - 0.5 * np.cos(2 * np.pi * f / 150.0))
    if s > 1.0004:
        nw, nh = int(round(W * s)), int(round(H * s))
        im = im.resize((nw, nh), Image.BILINEAR)
        x0, y0 = (nw - W) // 2, (nh - H) // 2
        im = im.crop((x0, y0, x0 + W, y0 + H))
    a = np.asarray(im, dtype=np.uint16) + offset_field(f, total)[:, :, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def qa_spec(spec):
    """Static checks: every element's ink box must stay inside the safe band and
    inside the frame width; nothing may collide with the top/bottom platform UI."""
    problems = []
    pal = kt.palette(spec)
    for el in spec.get("elements", []):
        if el.get("kind", "text") not in ("text", "counter", "kicker", "badge"):
            continue
        size = el.get("size", 96)
        fk = el.get("font", "slam")
        tr = el.get("tracking", 0.0)
        txt = el.get("text", "")
        if el.get("kind") == "counter":
            txt = el.get("prefix", "") + (el.get("fmt", "{:.0f}").format(el.get("to", 0))) + el.get("suffix", "")
        w = kt.rich_width(el.get("runs") or [{"text": txt}], size, tr, fk, el.get("weight"))
        y = el.get("y", 900) + spec.get("y_offset", 0)
        top, bot = y - size * 0.62, y + size * 0.42
        if top < kt.SAFE_TOP:
            problems.append((el.get("id", txt), "above safe band", round(top)))
        if bot > kt.SAFE_BOT:
            problems.append((el.get("id", txt), "below safe band", round(bot)))
        if w > 940:
            problems.append((el.get("id", txt), "wider than 940px", round(w)))
        if el.get("kind") == "text" and size < 32 and el.get("color", "ink") == "dim":
            problems.append((el.get("id", txt), "micro type under 40px", size))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--no-vo", action="store_true")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--stills", nargs="*", type=float, help="times (s) to dump PNG stills")
    ap.add_argument("--qa", action="store_true")
    args = ap.parse_args()

    spec = json.load(open(args.spec))
    spec.setdefault("fps", FPS)
    dur = spec.get("duration", 12.0)
    total = int(round(dur * spec["fps"]))
    problems = qa_spec(spec)
    print("QA:", "PASS" if not problems else problems)

    os.makedirs(os.path.dirname(os.path.abspath(args.out or "x")), exist_ok=True)
    bg = kt.build_bg(spec, kt.palette(spec)["accent"])

    if args.stills is not None:
        outdir = args.out or "stills"
        os.makedirs(outdir, exist_ok=True)
        for t in args.stills:
            f = int(round(t * spec["fps"]))
            p = os.path.join(outdir, f"{spec['id']}_{t:05.2f}s.png")
            living(kt.render_frame(f, spec, bg, total), f, total).save(p)
            print(p)
        return

    wav = os.path.join(os.path.dirname(os.path.abspath(args.out)), spec["id"] + ".wav")
    if not args.no_audio:
        t0 = time.time()
        A.build(spec, wav, with_vo=(not args.no_vo))
        print("audio built in %.1fs -> %s" % (time.time() - t0, wav))

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(spec["fps"]), "-i", "pipe:0"]
    if not args.no_audio:
        cmd += ["-i", wav]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "17", "-maxrate", "14M", "-bufsize", "20M",
            "-profile:v", "high", "-level", "4.2", "-pix_fmt", "yuv420p"]
    if not args.no_audio:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-shortest"]
    cmd += ["-movflags", "+faststart", args.out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(total):
        p.stdin.write(living(kt.render_frame(f, spec, bg, total), f, total).tobytes())
        if f % 60 == 0:
            el = time.time() - t0
            print("frame %4d/%d  %.1fs  (%.1f fps)" % (f, total, el, (f + 1) / max(el, .01)), flush=True)
    p.stdin.close()
    rc = p.wait()
    print("done rc=%s in %.1fs -> %s" % (rc, time.time() - t0, args.out))


if __name__ == "__main__":
    main()
