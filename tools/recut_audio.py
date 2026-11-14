#!/usr/bin/env python3
"""Re-cut the delivered shorts with the real Artlist audio.

Video is stream-copied from `out/_source/` (the existing deliveries) — only the
audio is rebuilt — so this is a fast, lossless-visual replacement:

    python tools/recut_audio.py                 # all projects
    python tools/recut_audio.py pot-odds hero   # subset
    python tools/recut_audio.py --audio-root /home/ubuntu/pokerfx-audio-assets

Each output is written to `out/<name>.mp4` with AAC 192k / 48 kHz and a single
loudnorm pass to -14 LUFS / -1.5 dBTP, then measured and reported.
"""
import argparse
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "lib"))
os.chdir(REPO)

PROJECTS = {
    "pot-odds": {"spec": "shorts/pot-odds.json", "src": "out/_source/pot-odds.mp4", "id": "pot-odds"},
    "limp-trap": {"spec": "shorts/limp-trap.json", "src": "out/_source/limp-trap.mp4", "id": "limp-trap"},
    "october2026_session": {"spec": "shorts/recaps/october2026_session.json",
                            "src": "out/_source/october2026_session.mp4", "id": "october2026_session"},
    "october-2026-session": {"spec": "shorts/recaps/october-2026-session.spec.json",
                            "src": "out/_source/october-2026-session.mp4", "id": "october-2026-session"},
    # the hero bed is a hard-clipped tanh bus: the AAC encoder overshoots ~2 dB on
    # it, so it needs a lower limiter ceiling to land at a legal true peak.
    "hero": {"src": "out/_source/same-hand-two-seats.mp4", "id": "same-hand-two-seats",
             "hero": True, "limit": 0.60},
}
LOUDNORM = "loudnorm=I=-14:TP=-1.5:LRA=9"


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def build_audio(job, root, engine):
    spec_path = job.get("spec")
    wav = os.path.join("build", "audio", job["id"] + ".wav")
    if job.get("hero"):
        run([sys.executable, "hero/audio.py", "build/audio.wav"] + (["--audio-root", root] if root else []))
        env = dict(os.environ)
        if root:
            env["POKERFX_AUDIO_ROOT"] = root
        run([sys.executable, "hero/vo.py"], env=env)
        wav = "build/audio_vo.wav"
    else:
        import audio as A
        spec = json.load(open(spec_path))
        spec.setdefault("fps", 30)
        os.makedirs("build/audio", exist_ok=True)
        A.build(spec, wav, with_vo=True, root=root, engine=engine)
    return wav


def remux(src, wav, out, limit=0.75):
    """Two-stage: loudnorm+limit to a PCM master, then a clean AAC encode.

    Applying the filters in the same ffmpeg pass as the AAC encoder produces
    inter-sample overshoots up to +3.5 dBTP; normalising to a PCM intermediate
    first keeps the delivered true peak at the loudnorm target.
    """
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    norm = os.path.join("build", "audio", "_norm.wav")
    os.makedirs(os.path.dirname(norm), exist_ok=True)
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", wav,
         "-af", LOUDNORM + ",alimiter=level=false:limit=%s:attack=5:release=80" % limit,
         "-c:a", "pcm_s16le", "-ar", "48000", norm])
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-i", src, "-i", norm,
         "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-af", "apad", "-shortest",
         "-movflags", "+faststart", out])


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("projects", nargs="*", default=None)
    ap.add_argument("--audio-root", default=None)
    ap.add_argument("--audio-engine", choices=["artlist", "synth"], default=None)
    ap.add_argument("--no-build", action="store_true", help="reuse existing wavs")
    args = ap.parse_args()

    names = args.projects or list(PROJECTS)
    rows = []
    for name in names:
        job = PROJECTS[name]
        if not os.path.exists(job["src"]):
            print("SKIP %-22s missing source %s" % (name, job["src"]))
            continue
        wav = build_audio(job, args.audio_root, args.audio_engine) if not args.no_build else (
            "build/audio_vo.wav" if job.get("hero") else os.path.join("build", "audio", job["id"] + ".wav"))
        out = os.path.join("out", job["id"] + ".mp4")
        remux(job["src"], wav, out, limit=job.get("limit", 0.75))
        m = measure(out)
        rows.append((name, out, m))
        print("%-22s -> %-34s %s" % (name, out, m), flush=True)

    with open("out/audio_recut_report.json", "w") as fh:
        json.dump([{"project": n, "file": o, **m} for n, o, m in rows], fh, indent=2)
    print("\nwrote out/audio_recut_report.json")


if __name__ == "__main__":
    main()
