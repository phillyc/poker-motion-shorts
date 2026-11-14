#!/usr/bin/env python3
"""Score the legacy October 2026 *monthly* recap with the real Artlist bank.

`out/october2026_monthly_results.mp4` is the last demo in the NAS gallery that
still carries its original all-NumPy placeholder score.  It has no spec in the
repo, so it could not be re-cut with `tools/recut_audio.py` — this tool closes
that gap.

The motion spec now lives at `shorts/recaps/october-2026-monthly.json` (written
by the storyboard task, recovered from the kanban attachment).  Every cue below
is frame-locked to that spec, so the audio stays in sync with the pixels without
re-rendering the video: the H.264 stream is copied, only the audio is rebuilt.

    python tools/score_monthly.py                     # build + mux + measure
    python tools/score_monthly.py --wav-only          # just build the mix
    python tools/score_monthly.py --music danny-shields-guest-house --offset 50

Cue map (spec `frames` at 30 fps):

    0      sub-hit                     -> impact-bomb
    420-535 one tick per bar growth    -> synth tick (rising pitch; no asset)
    500    sub-hit (bar 3 lands)       -> impact-bomb
    640-720 card-flick x5              -> cards-shuffle x5 (5 frames apart)
    750-795 near-silence               -> bed mute (the silence is the punctuation)
    795    sub-hit + gold chime        -> impact-bomb + cash-register
    900-924 ring-sweep whoosh          -> whoosh-air-slicer (tail lands on 924)
    1290-1312 odometer ticks x2        -> synth tick
    1330-1390 riser                    -> synth riser into 1390
    1390   riser-resolve + sub-hit     -> impact-bomb
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import wave

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "lib"))
os.chdir(REPO)

import audio as A          # noqa: E402  (Mix, riser, tick_sfx, write_wav)
import soundbank as SB     # noqa: E402

SR = A.SR

SPEC = "shorts/recaps/october-2026-monthly.json"
SRC = "out/_source/october2026_monthly_results.mp4"
OUT = "out/october2026_monthly_results.mp4"
ID = "october2026_monthly_results"

# The spec asks for "minimal dark pulse, minor key, no triumphant resolve".
# `ian-post-never-gonna-get-me` is the one licensed bed not already used by
# another short on the gallery page, and 60 + 51 s sits well inside its 196 s,
# so the bed never has to be looped (no fade-to-silence seam).
DEFAULT_MUSIC = "ian-post-never-gonna-get-me"
DEFAULT_OFFSET = 60.0
BED_RMS_DB = -21.0
DUCK = 0.70
LOUDNORM = "loudnorm=I=-14:TP=-1.5:LRA=9"


def load_spec(path=SPEC):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def vo_lines(spec):
    """Scene voSegments -> the `vo` list `lib/vo.py` expects (t / slot / text)."""
    fps = float(spec["composite"]["fps"])
    lines = []
    for scene in spec["scenes"]:
        for seg in scene.get("voSegments") or []:
            t0, t1 = seg["inFrame"] / fps, seg["outFrame"] / fps
            lines.append({"t": round(t0, 3), "slot": round(t1 - t0, 3),
                          "text": seg["text"], "scene": scene["id"]})
    lines.sort(key=lambda ln: ln["t"])
    return lines


def sfx_cues(spec, cfg):
    """Place the real hits. Frames are the spec's; the semantic mapping is ours."""
    fps = float(spec["composite"]["fps"])
    f = lambda n: n / fps                    # noqa: E731  frames -> seconds
    mix = A.Mix(float(spec["composite"]["durationSeconds"]))
    placed = []

    def hit(slug, t, gain, pan=0.0, dur=None, offset=0.0, peak_db=-6.0,
            fade_in=0.002, fade_out=0.10, align="start"):
        x = SB.normalise_peak(SB.sfx(slug, cfg.get("root")), peak_db)
        x = SB.clip(x, dur, offset, fade_in, fade_out)
        at = t - len(x) / SR if align == "end" else t
        mix.add(x, max(0.0, at), gain, pan)
        placed.append({"asset": slug, "t": round(max(0.0, at), 3), "gain": gain})
        return len(x) / SR

    # 0 — hook sub-hit
    hit("impact-bomb", f(0), 0.80, dur=1.5, fade_in=0.001, fade_out=0.5)
    # 420-535 — one low tick per bar growth, pitch rising up-chart
    for k, fr in enumerate(range(420, 536, 23)):
        mix.add(A.tick_sfx(1050 + 70 * k), f(fr), 0.30, pan=0.1)
    placed.append({"asset": "synth-tick", "t": round(f(420), 3), "n": 6})
    # 500 — bar 3 lands (the −$2,000 night)
    hit("impact-bomb", f(500), 0.60, dur=0.8, offset=0.02,
        fade_in=0.001, fade_out=0.3)
    # 640-720 — card flicks, 5 frames apart
    for fr in range(640, 721, 16):
        hit("cards-shuffle", f(fr), 0.42, pan=-0.12, dur=0.30, peak_db=-11)
    # 795 — high hand: sub-hit + gold chime
    hit("impact-bomb", f(795), 0.70, dur=1.1, fade_in=0.001, fade_out=0.35)
    hit("cash-register", f(795) + 0.02, 0.55, pan=0.12, dur=1.9, fade_out=0.45)
    # 900-924 — ring-sweep whoosh, tail landing on the cut at 924
    hit("whoosh-air-slicer", f(924), 0.70, pan=-0.15, dur=0.80,
        fade_in=0.02, fade_out=0.10, align="end")
    # 1290-1312 — odometer ticks
    for fr in (1290, 1312):
        mix.add(A.tick_sfx(1500), f(fr), 0.30, pan=0.15)
    placed.append({"asset": "synth-tick", "t": round(f(1290), 3), "n": 2})
    # 1330-1390 — riser into the verdict, resolved by the sub-hit at 1390
    riser = A.riser(f(1390) - f(1330))
    mix.add(riser, f(1330), 0.50)
    hit("impact-bomb", f(1390), 0.70, dur=1.3, fade_in=0.001, fade_out=0.45)

    # 750-795 — the scored silence. Nothing is placed there on purpose.
    return mix, placed


def build_bed(spec, cfg):
    """Bed, with the spec's 750-795 frame music drop applied as a gain envelope."""
    fps = float(spec["composite"]["fps"])
    dur = float(spec["composite"]["durationSeconds"])
    slug = cfg["music"]
    bed = SB.music(slug, cfg.get("root"))
    off = float(cfg["music_offset"])
    total = len(bed) / SR
    if off + dur + 2.0 > total:
        raise SystemExit(
            "bed overrun: %s offset %.2f + %.2f s > track %.2f s — move the in-point"
            % (slug, off, dur, total))
    bed = SB.clip(bed, None, off)                 # from the in-point to the end
    bed = SB.fit(bed, dur, loop=False, fade_out=0.45)
    bed = SB.normalise_rms(bed, BED_RMS_DB)
    fi = int(0.05 * SR)
    bed[:fi] *= np.linspace(0.0, 1.0, fi, dtype=np.float32)[:, None]

    # music drop for the "near-silence" beat: 0.25 s ramps, floor at -60 dB
    a, b = int(750 / fps * SR), int(795 / fps * SR)
    ramp = int(0.25 * SR)
    env = np.ones(len(bed), dtype=np.float32)
    env[max(0, a - ramp):a] = np.linspace(1.0, 0.001, len(env[max(0, a - ramp):a]))
    env[a:b] = 0.001
    env[b:b + ramp] = np.linspace(0.001, 1.0, len(env[b:b + ramp]))
    return bed * env[:, None], {"bed_mute": [round(750 / fps, 3), round(795 / fps, 3)]}


def build_mix(spec, cfg, wav_out):
    dur = float(spec["composite"]["durationSeconds"])
    bed, notes = build_bed(spec, cfg)
    sfx, placed = sfx_cues(spec, cfg)
    mix = bed + sfx.stereo()

    lines = vo_lines(spec)
    from vo import voice_track
    voice = voice_track({**spec, "id": ID, "duration": dur, "vo": lines},
                        wav_out.replace(".wav", "_vo.wav"))
    if voice is not None:
        voice = voice[: len(bed)]
        env = np.abs(voice).mean(axis=1)
        k = int(0.09 * SR)
        env = np.convolve(env, np.ones(k, dtype=np.float32) / k, mode="same")
        env = np.clip(env / (env.max() + 1e-9) * 2.2, 0, 1)
        duck = 1.0 - DUCK * env
        mix = bed * duck[:, None] + sfx.stereo() + voice

    peak = float(np.max(np.abs(mix)))
    if peak > 0.98:
        mix = mix * (0.98 / peak)
    A.write_wav(wav_out, mix)
    notes.update({"vo_lines": len(lines), "sfx": placed})
    return wav_out, notes


def remux(src, wav, out, limit=0.75):
    """loudnorm+limit to PCM, then a separate clean AAC pass (no overshoot)."""
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    norm = os.path.join("build", "audio", "_norm_monthly.wav")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", wav,
                    "-af", LOUDNORM + ",alimiter=level=false:limit=%s:attack=5:release=80" % limit,
                    "-c:a", "pcm_s16le", "-ar", "48000", norm], check=True)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", src, "-i", norm,
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-af", "apad", "-shortest", "-movflags", "+faststart", out], check=True)


def measure(path):
    probe = json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_type,codec_name,sample_rate,channels,bit_rate:format=duration",
         "-of", "json", path]))
    a = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    v = next(s for s in probe["streams"] if s["codec_type"] == "video")
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                          "-map", "0:a", "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    i = lra = peak = None
    for line in err.splitlines():
        s = line.strip()
        if s.startswith("I:"):
            i = float(s.split()[1])
        elif s.startswith("LRA:") and lra is None:
            lra = float(s.split()[1])
        elif s.startswith("Peak:") and peak is None:
            peak = float(s.split()[1])
    return {"video": v["codec_name"], "audio": a["codec_name"], "sr": int(a["sample_rate"]),
            "ch": int(a["channels"]), "kbps": int(a.get("bit_rate", 0)) // 1000,
            "duration": round(float(probe["format"]["duration"]), 2),
            "lufs": i, "lra": lra, "true_peak": peak}


def update_report(row):
    path = os.path.join("out", "audio_recut_report.json")
    rows = []
    if os.path.exists(path):
        try:
            rows = json.load(open(path))
        except ValueError:
            rows = []
    rows = [r for r in rows if r.get("project") != ID] + [row]
    with open(path, "w") as fh:
        json.dump(rows, fh, indent=2)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=SPEC)
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--music", default=DEFAULT_MUSIC)
    ap.add_argument("--offset", type=float, default=DEFAULT_OFFSET)
    ap.add_argument("--audio-root", default=None)
    ap.add_argument("--wav-only", action="store_true")
    ap.add_argument("--no-build", action="store_true")
    args = ap.parse_args()

    spec = load_spec(args.spec)
    cfg = {"music": args.music, "music_offset": args.offset,
           "root": args.audio_root or os.environ.get("POKERFX_AUDIO_ROOT") or SB.BUILTIN_ROOT}
    wav = os.path.join("build", "audio", ID + ".wav")
    os.makedirs(os.path.dirname(wav), exist_ok=True)

    notes = {}
    if not args.no_build:
        wav, notes = build_mix(spec, cfg, wav)
        print("mix ->", wav, {k: notes[k] for k in ("vo_lines",) if k in notes})
    if args.wav_only:
        return
    if not os.path.exists(args.src):
        raise SystemExit("missing source video %s (fetch it from the NAS out/ tree)" % args.src)

    remux(args.src, wav, args.out)
    m = measure(args.out)
    row = {"project": ID, "file": args.out, **m}
    update_report(row)
    side = os.path.join("out", ID + ".audio.json")
    with open(side, "w") as fh:
        json.dump({"music": args.music, "music_offset": args.offset,
                   "bed_rms_db": BED_RMS_DB, "duck": DUCK, "measured": m,
                   "cue_map": notes}, fh, indent=2)
    print("%-24s -> %s\n%s" % (ID, args.out, json.dumps(m)))
    print("sidecar:", side)
    # hard checks
    bad = []
    if m["lufs"] is None or abs(m["lufs"] + 14.0) > 1.2:
        bad.append("LUFS %s off target" % m["lufs"])
    if m["true_peak"] is None or m["true_peak"] > -0.5:
        bad.append("true peak %s too hot" % m["true_peak"])
    if abs(m["duration"] - float(spec["composite"]["durationSeconds"])) > 0.05:
        bad.append("duration %s != spec" % m["duration"])
    if bad:
        raise SystemExit("FAILED checks: " + "; ".join(bad))
    print("checks OK")


if __name__ == "__main__":
    main()
