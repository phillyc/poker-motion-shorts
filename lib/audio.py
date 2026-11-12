"""Sound design for the kinetic-typography shorts.

`build(spec, out)` synthesises a music bed (kick / snare / hats / sub bass / pad)
plus an SFX map derived automatically from the timeline: every slam gets a sub
impact, every pop a snap, every kicker a whoosh, every counter a tick, and the
final verdict gets a riser + chime. Everything is NumPy, 48 kHz stereo.
"""
import json
import math
import os
import wave

import numpy as np

SR = 48000


# ------------------------------------------------------------------ helpers
def env_exp(n, decay, attack=0.004, curve=1.0):
    t = np.arange(n) / SR
    e = np.exp(-t / decay) * curve
    a = max(1, int(attack * SR))
    e[:a] *= np.linspace(0, 1, a)
    return e.astype(np.float32)


def sine(f, n, phase=0.0):
    t = np.arange(n, dtype=np.float32) / SR
    return np.sin(2 * np.pi * f * t + phase).astype(np.float32)


def noise(n, seed=3):
    return np.random.default_rng(seed).normal(0, 1, n).astype(np.float32)


def lp(x, cutoff):
    a = float(np.exp(-2 * np.pi * cutoff / SR))
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def hp(x, cutoff):
    return x - lp(x, cutoff)


# ------------------------------------------------------------------ instruments
def kick(strong=1.0):
    n = int(0.42 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f = 44 + (105 - 44) * np.exp(-t / 0.040)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.20)
    beater = hp(noise(n), 2600) * np.exp(-t / 0.005) * 0.20
    return ((body + beater) * strong).astype(np.float32)


def snare():
    n = int(0.24 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    nz = hp(noise(n, 9), 1400) * np.exp(-t / 0.055)
    tone = sine(196, n) * np.exp(-t / 0.045) * 0.30
    return (nz * 0.34 + tone).astype(np.float32)


def hat(open_=False):
    n = int((0.12 if open_ else 0.045) * SR)
    t = np.arange(n, dtype=np.float32) / SR
    return (hp(noise(n, 21), 7000) * np.exp(-t / (0.035 if open_ else 0.009)) * 0.16).astype(np.float32)


def bass_note(f, dur):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    raw = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    e = np.minimum(1.0, t / 0.012) * np.exp(-t / (dur * 0.55))
    return (lp(raw.astype(np.float32), 220) * e * 0.5).astype(np.float32)


def sub_impact(gain=1.0):
    n = int(1.0 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    f = 34 + (120 - 34) * np.exp(-t / 0.05)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.34)
    crack = hp(noise(n), 2200) * np.exp(-t / 0.010) * 0.30
    return ((body + crack) * gain).astype(np.float32)


def snap_sfx(gain=1.0):
    n = int(0.13 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    return (hp(noise(n, 5), 2600) * np.exp(-t / 0.014) * gain + sine(2400, n) * np.exp(-t / 0.010) * 0.18 * gain).astype(np.float32)


def tick_sfx(f=1800.0):
    n = int(0.06 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    return (sine(f, n) * np.exp(-t / 0.016) * 0.30 + hp(noise(n, 8), 5000) * np.exp(-t / 0.004) * 0.12).astype(np.float32)


def whoosh(dur=0.45):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    p = t / dur
    nz = hp(noise(n, 12), 700) * (np.sin(np.pi * p) ** 1.4)
    return (nz * 0.10).astype(np.float32)


def riser(dur=1.6):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    p = t / dur
    f = 150 * (9.0 ** p)
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = (np.sin(ph) * 0.16 + np.sin(ph * 2.01) * 0.06) * (p ** 1.8)
    nz = hp(noise(n, 4), 900) * (p ** 2.2) * 0.10
    return (tone + nz).astype(np.float32)


def chime(base=784.0, dur=1.8):
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    out = np.zeros(n, dtype=np.float32)
    for mult, amp, dec in ((1.0, 0.42, 1.1), (2.0, 0.20, 0.7), (2.76, 0.12, 0.5), (5.4, 0.05, 0.3)):
        out += (np.sin(2 * np.pi * base * mult * t) * amp * np.exp(-t / dec)).astype(np.float32)
    a = int(0.004 * SR)
    out[:a] *= np.linspace(0, 1, a)
    return out


# ------------------------------------------------------------------ mixing
class Mix:
    def __init__(self, dur):
        self.n = int(dur * SR)
        self.L = np.zeros(self.n, dtype=np.float32)
        self.R = np.zeros(self.n, dtype=np.float32)

    def add(self, sig, at, gain=1.0, pan=0.0):
        i = int(at * SR)
        if i >= self.n:
            return
        if i < 0:
            sig = sig[-i:]
            i = 0
        seg = sig[: self.n - i]
        gl = gain * min(1.0, 1.0 - pan) ** 0.5
        gr = gain * min(1.0, 1.0 + pan) ** 0.5
        self.L[i:i + len(seg)] += seg * gl
        self.R[i:i + len(seg)] += seg * gr

    def stereo(self):
        return np.stack([self.L, self.R], axis=1)


def build_bed(spec, mix):
    dur = spec.get("duration", 12.0)
    bpm = spec.get("bpm", 100)
    beat = 60.0 / bpm
    bar = beat * 4
    mood = spec.get("mood", "dark")
    # minor progression roots (Hz): A1, A1, F1, G1
    roots = [55.0, 55.0, 43.65, 49.0]
    pad_freqs = [220.0, 261.63, 329.63] if mood == "dark" else [196.0, 233.08, 293.66]

    n_bars = int(math.ceil(dur / bar)) + 1
    for b in range(n_bars):
        t0 = b * bar
        if t0 > dur:
            break
        root = roots[b % len(roots)]
        # drums
        for k in range(4):
            tb = t0 + k * beat
            if k in (0, 2):
                mix.add(kick(1.0 if k == 0 else 0.75), tb, 0.55)
            if k in (1, 3):
                mix.add(snare(), tb, 0.20, pan=0.06)
            mix.add(hat(open_=(k == 3)), tb + beat / 2, 0.55, pan=-0.25)
            mix.add(hat(), tb + beat / 4, 0.30, pan=0.22)
            mix.add(hat(), tb + 3 * beat / 4, 0.26, pan=0.22)
        # bass: root on 1 and the "and" of 3
        mix.add(bass_note(root, beat * 0.9), t0, 0.42)
        mix.add(bass_note(root * 1.5, beat * 0.45), t0 + 2.5 * beat, 0.30)
        # pad: one slow chord per bar, heavily low-passed, wide
        for f in pad_freqs:
            n = int(bar * SR)
            t = np.arange(n, dtype=np.float32) / SR
            lfo = 0.55 + 0.45 * np.sin(2 * np.pi * t / (bar * 2) + f)
            det = (np.sin(2 * np.pi * f * t) + 0.7 * np.sin(2 * np.pi * (f * 1.004) * t + 1.2))
            e = np.minimum(1.0, t / 0.5) * np.exp(-t / (bar * 0.9))
            sig = lp((det * lfo * e * 0.035).astype(np.float32), 900)
            mix.add(sig, t0, 1.0, pan=-0.3 if f == pad_freqs[0] else 0.3)
    return mix


def build_sfx(spec, mix):
    els = spec.get("elements", [])
    verdict_done = False
    for el in els:
        t0 = el.get("t0", 0)
        kind = el.get("kind", "text")
        preset = el.get("preset", "")
        size = el.get("size", 0)
        if kind == "kicker":
            mix.add(whoosh(), max(0.0, t0 - 0.18), 0.9, pan=-0.15)
        if preset == "slam":
            mix.add(sub_impact(1.0 if size >= 150 else 0.55), t0, 0.50)
        elif preset in ("pop", "drop"):
            mix.add(snap_sfx(), t0, 0.45, pan=0.1)
        if kind == "counter":
            for k in range(4):
                mix.add(tick_sfx(1600 + 120 * k), t0 + 0.10 * k, 0.35, pan=0.15)
        if kind == "bar":
            mix.add(tick_sfx(1200), t0 + el.get("in", 1.0), 0.35)
        if kind == "rule" and not verdict_done:
            mix.add(whoosh(0.30), t0, 0.5, pan=0.2)
    # final verdict: riser into the last big slam, then a chime
    slams = [e for e in els if e.get("preset") == "slam" and e.get("size", 0) >= 150]
    if slams:
        last = max(slams, key=lambda e: e.get("t1", 0) if e.get("t1", 0) < 1e8 else 0)
        mix.add(riser(1.4), max(0.0, last["t0"] - 1.4), 0.55)
        mix.add(chime(), last["t0"] + 0.05, 0.35, pan=0.1)
    return mix


def write_wav(path, stereo, sr=SR):
    data = np.clip(stereo, -1.0, 1.0)
    peak = float(np.max(np.abs(data))) or 1.0
    data = data / peak * 0.89
    pcm = (data * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def build(spec, out, with_vo=True):
    dur = spec.get("duration", 12.0)
    mix = Mix(dur)
    build_bed(spec, mix)
    build_sfx(spec, mix)
    bed = mix.stereo()
    if with_vo and spec.get("vo"):
        from vo import voice_track
        voice = voice_track(spec, out.replace(".wav", "_vo.wav"))
        if voice is not None:
            voice = voice[: len(bed)]
            # duck the bed under the voice (smoothed envelope follower)
            env = np.abs(voice).mean(axis=1)
            k = int(0.09 * SR)
            kern = np.ones(k, dtype=np.float32) / k
            env = np.convolve(env, kern, mode="same")
            env = np.clip(env / (env.max() + 1e-9) * 2.2, 0, 1)
            duck = 1.0 - 0.62 * env
            bed = bed * duck[:, None] + voice * 1.0
    write_wav(out, bed)
    return out


if __name__ == "__main__":
    import sys
    spec = json.load(open(sys.argv[1]))
    print(build(spec, sys.argv[2]))
