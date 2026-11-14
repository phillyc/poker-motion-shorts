"""Synthesise per-beat voiceover from short-spec.json, fit it to the beat windows,
duck the existing music/SFX bed under it, and write build/audio_vo.wav."""
import asyncio, json, os, subprocess, sys, wave
import numpy as np
import edge_tts

SR = 48000
FPS = 30
# committed copy of the storyboard spec (was an ephemeral scratch attachment)
SPEC = os.environ.get(
    "HERO_SPEC",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "hero", "spec", "short-spec.json"))
VOICE = "en-US-AndrewMultilingualNeural"
RATE = "+12%"
OUTDIR = "build/vo"
BED = "build/audio.wav"
OUT = "build/audio_vo.wav"


def load_beats():
    spec = json.load(open(SPEC))
    beats = []
    for sc in spec["scenes"]:
        for b in sc["beats"]:
            txt = (b.get("vo") or "").strip()
            if txt:
                beats.append(dict(id=b["id"], inF=b["inFrame"], outF=b["outFrame"], text=txt))
    return beats


def dur_of(path):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).strip())


async def synth(beats):
    os.makedirs(OUTDIR, exist_ok=True)
    for b in beats:
        p = f"{OUTDIR}/{b['id']}.mp3"
        if os.path.exists(p) and dur_of(p) > 0.2:
            b["path"] = p
            continue
        for attempt in range(3):
            try:
                await edge_tts.Communicate(b["text"], VOICE, rate=RATE).save(p)
                break
            except Exception as e:
                print("retry", b["id"], e)
                await asyncio.sleep(2)
        b["path"] = p
    return beats


def read_wav(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR and w.getnchannels() == 2, w.getparams()
        n = w.getnframes()
        a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    return a.reshape(-1, 2)


def load_clip(path, fit):
    """decode mp3 -> stereo 48k float; trim pad; time-stretch to `fit` seconds if needed."""
    tmp = "/tmp/_vo_raw.wav"
    tmp2 = "/tmp/_vo_fit.wav"
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", path,
                          "-ar", str(SR), "-ac", "2", tmp])
    a = read_wav(tmp)
    d = len(a) / SR
    # trim leading/trailing near-silence (edge-tts pads ~0.1-0.3s each side)
    mono = np.abs(a).mean(axis=1)
    thr = max(1e-3, mono.max() * 0.02)
    idx = np.nonzero(mono > thr)[0]
    if len(idx) > 10:
        a = a[max(0, idx[0] - int(0.01 * SR)): min(len(a), idx[-1] + int(0.03 * SR))]
    cur = len(a) / SR
    if fit and cur > fit * 0.98:
        tempo = min(1.42, cur / (fit * 0.98))
        data = (np.clip(a, -1, 1) * 32767).astype(np.int16)
        with wave.open(tmp2, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes(data.tobytes())
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", tmp2,
                              "-filter:a", f"atempo={tempo:.4f}",
                              "-ar", str(SR), "-ac", "2", tmp])
        a = read_wav(tmp)
    return a, d


def main():
    beats = load_beats()
    beats = asyncio.run(synth(beats))
    bed = read_wav(BED)
    N = len(bed)
    vo = np.zeros_like(bed)
    duck = np.ones(N, dtype=np.float32)
    att, rel = int(0.06 * SR), int(0.12 * SR)

    placements = []
    for i, b in enumerate(beats):
        start = b["inF"] / FPS + 0.03
        # window: until next beat starts, keeping >= 2 frames of clearance
        nxt = beats[i + 1]["inF"] / FPS if i + 1 < len(beats) else 45.0
        win = max(0.4, nxt - start - 0.06)
        clip, raw = load_clip(b["path"], win)
        i0 = int(start * SR)
        seg = clip[: max(0, N - i0)]
        vo[i0:i0 + len(seg)] += seg
        used = len(seg) / SR
        placements.append((b["id"], b["text"], round(start, 2), round(raw, 2), round(used, 2), round(win, 2)))

        # duck envelope under this VO line
        j0 = max(0, i0 - att)
        j1 = min(N, i0 + len(seg) + rel)
        env = np.ones(j1 - j0, dtype=np.float32)
        a0 = min(att, j1 - j0)
        env[:a0] = np.linspace(1, 0.34, a0)
        env[: len(seg) + rel if j1 - j0 > len(seg) + rel else len(env)] *= 0.34
        env = np.minimum(env, 1.0)
        # flat 0.34 across the body, ramps at both ends
        body_start = i0 - j0
        body_end = min(j1 - j0, body_start + len(seg))
        env[body_start:body_end] = np.minimum(env[body_start:body_end], 0.34)
        if j1 - j0 > body_end:
            env[body_end:] = np.linspace(0.34, 1.0, j1 - j0 - body_end)
        duck[j0:j1] = np.minimum(duck[j0:j1], env)

    mix = bed * duck[:, None] * 1.0 + vo * 0.92
    peak = float(np.max(np.abs(mix)))
    mix = np.tanh(mix * 1.1)
    mix = mix / float(np.max(np.abs(mix))) * 0.93
    mix[-int(0.12 * SR):] *= np.linspace(1, 0, int(0.12 * SR))[:, None]
    data = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(OUT, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data.tobytes())

    print(f"{'beat':6} {'start':>6} {'raw':>5} {'used':>5} {'win':>5}  text")
    for p in placements:
        flag = "  <-- TIGHT" if p[4] > p[5] - 0.05 else ""
        print(f"{p[0]:6} {p[2]:6.2f} {p[3]:5.2f} {p[4]:5.2f} {p[5]:5.2f}  {p[1]}{flag}")
    print("wrote", OUT, "peak", round(peak, 3))


if __name__ == "__main__":
    main()
