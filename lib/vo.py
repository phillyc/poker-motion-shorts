"""edge-tts voiceover: synth each line, trim silence, fit it into its slot and
return a full-length stereo track to mix under the bed."""
import asyncio
import os
import subprocess
import wave

import numpy as np

SR = 48000
VOICE = "en-US-AndrewMultilingualNeural"
VOICE_ALT = "en-US-AriaNeural"      # used for the sarcastic short
RATE = "+10%"


def _dur(path):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).strip())


def _read(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR and w.getnchannels() == 2, w.getparams()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return a.reshape(-1, 2)


async def _synth(lines, voice, cache_dir):
    import edge_tts
    os.makedirs(cache_dir, exist_ok=True)
    for i, ln in enumerate(lines):
        p = os.path.join(cache_dir, f"line{i:02d}.mp3")
        ln["path"] = p
        if os.path.exists(p) and _dur(p) > 0.15:
            continue
        for attempt in range(4):
            try:
                await edge_tts.Communicate(ln["text"], voice, rate=RATE).save(p)
                break
            except Exception as e:      # noqa: BLE001 - network flake, retry
                print("  tts retry", i, e)
                await asyncio.sleep(2)


def voice_track(spec, out, voice=None):
    lines = spec.get("vo") or []
    if not lines:
        return None
    voice = voice or spec.get("voice") or VOICE
    cache = os.path.join(os.path.dirname(out), "vo_" + spec.get("id", "short"))
    asyncio.run(_synth(lines, voice, cache))

    dur_total = spec.get("duration", 12.0)
    track = np.zeros((int(dur_total * SR) + SR, 2), dtype=np.float32)
    for i, ln in enumerate(lines):
        raw = "/tmp/_kt_vo_raw.wav"
        fit = "/tmp/_kt_vo_fit.wav"
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", ln["path"],
                               "-ar", str(SR), "-ac", "2", raw])
        a = _read(raw)
        mono = np.abs(a).mean(axis=1)
        thr = max(1e-3, mono.max() * 0.02)
        idx = np.nonzero(mono > thr)[0]
        if len(idx) > 10:
            a = a[max(0, idx[0] - int(0.01 * SR)): min(len(a), idx[-1] + int(0.04 * SR))]
        slot = ln.get("slot")
        cur = len(a) / SR
        if slot and cur > slot * 0.99:
            tempo = min(1.45, cur / (slot * 0.99))
            pcm = (np.clip(a, -1, 1) * 32767).astype("<i2")
            with wave.open(fit, "wb") as w:
                w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
                w.writeframes(pcm.tobytes())
            subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", fit,
                                   "-filter:a", f"atempo={tempo:.3f}",
                                   "-ar", str(SR), "-ac", "2", raw])
            a = _read(raw)
        i0 = int(ln["t"] * SR)
        a = a[: len(track) - i0]
        track[i0:i0 + len(a)] += a * 0.92

    np.save(out.replace(".wav", ".npy"), track)
    _write(out, track)
    return track


def _write(path, stereo):
    data = np.clip(stereo, -1, 1)
    pcm = (data * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
