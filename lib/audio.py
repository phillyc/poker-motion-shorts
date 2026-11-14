"""Sound design for the kinetic-typography shorts.

Two engines, same cue grammar:

* ``artlist`` (default) — real licensed audio from ``assets/audio/`` (see
  ``lib/soundbank.py``): a music bed plus real impact / whoosh / pop / cash
  hits, placed at the cue points derived from the timeline. Only the voices the
  bucket has no asset for (riser, tick, bar tick) stay synthesised — see
  ``config/audio.json:synth_voices``.
* ``synth`` — the original all-NumPy score. Kept as an offline fallback and as
  the regression path (``--audio-engine synth``).

Both engines are 48 kHz stereo and go through the same VO duck, peak
normalisation and ffmpeg ``loudnorm`` stage in ``render.py``.
"""
import json
import math
import os
import wave

import numpy as np

import soundbank as SB

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CONFIG = os.path.join(REPO, "config", "audio.json")


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


# ------------------------------------------------------------------ config
def load_config(spec, root=None, engine=None):
    """defaults <- config/audio.json projects[id] <- spec['audio'] <- CLI args."""
    cfg = {}
    try:
        with open(CONFIG, encoding="utf-8") as fh:
            doc = json.load(fh)
        cfg.update(doc.get("defaults", {}))
        cfg.update(doc.get("projects", {}).get(spec.get("id", ""), {}))
    except FileNotFoundError:
        pass
    cfg.update(spec.get("audio") or {})
    if engine:
        cfg["engine"] = engine
    cfg.setdefault("engine", "artlist")
    cfg["root"] = root or os.environ.get("POKERFX_AUDIO_ROOT") or SB.BUILTIN_ROOT
    return cfg


# ------------------------------------------------------------------ mixing
class Mix:
    def __init__(self, dur):
        self.n = int(dur * SR)
        self.L = np.zeros(self.n, dtype=np.float32)
        self.R = np.zeros(self.n, dtype=np.float32)

    def add(self, sig, at, gain=1.0, pan=0.0):
        """Add a mono (n,) or stereo (n,2) signal at `at` seconds."""
        i = int(round(at * SR))
        if i >= self.n:
            return
        sig = np.asarray(sig, dtype=np.float32)
        stereo = sig.ndim == 2
        if i < 0:
            sig = sig[-i:]
            i = 0
        seg = sig[: self.n - i]
        if stereo:
            gl = gain * min(1.0, 1.0 - pan) ** 0.5
            gr = gain * min(1.0, 1.0 + pan) ** 0.5
            self.L[i:i + len(seg)] += seg[:, 0] * gl
            self.R[i:i + len(seg)] += seg[:, 1] * gr
        else:
            gl = gain * min(1.0, 1.0 - pan) ** 0.5
            gr = gain * min(1.0, 1.0 + pan) ** 0.5
            self.L[i:i + len(seg)] += seg * gl
            self.R[i:i + len(seg)] += seg * gr

    def stereo(self):
        return np.stack([self.L, self.R], axis=1)


# ------------------------------------------------------------------ beds
def build_bed_synth(spec, mix):
    dur = spec.get("duration", 12.0)
    bpm = spec.get("bpm", 100)
    beat = 60.0 / bpm
    bar = beat * 4
    mood = spec.get("mood", "dark")
    roots = [55.0, 55.0, 43.65, 49.0]
    pad_freqs = [220.0, 261.63, 329.63] if mood == "dark" else [196.0, 233.08, 293.66]

    n_bars = int(math.ceil(dur / bar)) + 1
    for b in range(n_bars):
        t0 = b * bar
        if t0 > dur:
            break
        root = roots[b % len(roots)]
        for k in range(4):
            tb = t0 + k * beat
            if k in (0, 2):
                mix.add(kick(1.0 if k == 0 else 0.75), tb, 0.55)
            if k in (1, 3):
                mix.add(snare(), tb, 0.20, pan=0.06)
            mix.add(hat(open_=(k == 3)), tb + beat / 2, 0.55, pan=-0.25)
            mix.add(hat(), tb + beat / 4, 0.30, pan=0.22)
            mix.add(hat(), tb + 3 * beat / 4, 0.26, pan=0.22)
        mix.add(bass_note(root, beat * 0.9), t0, 0.42)
        mix.add(bass_note(root * 1.5, beat * 0.45), t0 + 2.5 * beat, 0.30)
        for f in pad_freqs:
            n = int(bar * SR)
            t = np.arange(n, dtype=np.float32) / SR
            lfo = 0.55 + 0.45 * np.sin(2 * np.pi * t / (bar * 2) + f)
            det = (np.sin(2 * np.pi * f * t) + 0.7 * np.sin(2 * np.pi * (f * 1.004) * t + 1.2))
            e = np.minimum(1.0, t / 0.5) * np.exp(-t / (bar * 0.9))
            sig = lp((det * lfo * e * 0.035).astype(np.float32), 900)
            mix.add(sig, t0, 1.0, pan=-0.3 if f == pad_freqs[0] else 0.3)
    return mix


def build_bed_artlist(spec, mix, cfg):
    dur = float(spec.get("duration", 12.0))
    slug = cfg["music"]
    bed = SB.music(slug, cfg.get("root"))
    offset = float(cfg.get("music_offset", 0.0))
    bed = SB.clip(bed, None, offset, 0.0, 0.0)
    bed = SB.fit(bed, dur, loop=bool(cfg.get("music_loop", True)),
                 fade_out=float(cfg.get("music_fade_out", 0.45)))
    bed = SB.normalise_rms(bed, float(cfg.get("bed_rms_db", -27.0)))
    fi = float(cfg.get("music_fade_in", 0.05))
    if fi > 0:
        n = int(fi * SR)
        bed[:n] *= np.linspace(0.0, 1.0, n, dtype=np.float32)[:, None]
    mix.add(bed, 0.0, 1.0)
    return mix


def build_bed(spec, mix, cfg):
    if cfg.get("engine", "artlist") == "synth":
        return build_bed_synth(spec, mix)
    return build_bed_artlist(spec, mix, cfg)


# ------------------------------------------------------------------ SFX
def _hit(mix, slug, t, *, cfg, gain=1.0, pan=0.0, dur=None, offset=0.0,
         peak_db=None, fade_in=0.003, fade_out=0.05, align="start"):
    """Place a real SFX: normalise its peak, trim, then add at `t` (or end at `t`)."""
    peak_db = float(cfg.get("sfx_peak_db", -6.0)) if peak_db is None else float(peak_db)
    x = SB.sfx(slug, cfg.get("root"))
    x = SB.normalise_peak(x, peak_db)
    x = SB.clip(x, dur, offset, fade_in, fade_out)
    at = t - len(x) / SR if align == "end" else t
    mix.add(x, max(0.0, at), gain * float(cfg.get("sfx_gain", 1.0)), pan)
    return len(x) / SR


def build_sfx_artlist(spec, mix, cfg):
    els = spec.get("elements", [])
    verdict_done = False
    for el in els:
        t0 = float(el.get("t0", 0))
        kind = el.get("kind", "text")
        preset = el.get("preset", "")
        size = el.get("size", 0)
        if kind == "kicker":
            # whoosh tail lands on the typographic cut
            _hit(mix, "whoosh-air-slicer", t0, cfg=cfg, gain=0.85, pan=-0.15,
                 dur=0.62, fade_in=0.01, fade_out=0.08, align="end")
        if preset == "slam":
            if size >= 150:
                _hit(mix, "impact-bomb", t0, cfg=cfg, gain=0.80, dur=1.5,
                     fade_in=0.001, fade_out=0.5)
            else:
                _hit(mix, "impact-bomb", t0, cfg=cfg, gain=0.45, dur=0.6,
                     offset=0.02, fade_in=0.001, fade_out=0.25)
        elif preset in ("pop", "drop"):
            _hit(mix, "pop-notification", t0, cfg=cfg, gain=0.60, pan=0.1,
                 dur=0.5, fade_in=0.001, fade_out=0.12)
        if kind == "counter":
            for k in range(4):
                mix.add(tick_sfx(1600 + 120 * k), t0 + 0.10 * k, 0.35, pan=0.15)
        if kind == "bar":
            mix.add(tick_sfx(1200), t0 + el.get("in", 1.0), 0.35)
        if kind == "rule" and not verdict_done:
            _hit(mix, "whoosh-foil", t0, cfg=cfg, gain=0.55, pan=0.2, dur=0.85,
                 fade_in=0.01, fade_out=0.10)
            verdict_done = True
    # final verdict: riser (synth — no asset) into the last big slam, then cash
    slams = [e for e in els if e.get("preset") == "slam" and e.get("size", 0) >= 150]
    if slams:
        last = max(slams, key=lambda e: e.get("t1", 0) if e.get("t1", 0) < 1e8 else 0)
        mix.add(riser(1.4), max(0.0, last["t0"] - 1.4), 0.45)
        _hit(mix, "cash-register", last["t0"] + 0.05, cfg=cfg, gain=0.55, pan=0.1,
             dur=1.9, fade_in=0.002, fade_out=0.45)
    for cue in cfg.get("extra") or []:
        _hit(mix, cue["asset"], float(cue.get("t", 0.0)), cfg=cfg,
             gain=float(cue.get("gain", 0.5)), pan=float(cue.get("pan", 0.0)),
             dur=cue.get("dur"), offset=float(cue.get("offset", 0.0)),
             peak_db=cue.get("peak_db"))
    return mix


def build_sfx_synth(spec, mix):
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
    slams = [e for e in els if e.get("preset") == "slam" and e.get("size", 0) >= 150]
    if slams:
        last = max(slams, key=lambda e: e.get("t1", 0) if e.get("t1", 0) < 1e8 else 0)
        mix.add(riser(1.4), max(0.0, last["t0"] - 1.4), 0.55)
        mix.add(chime(), last["t0"] + 0.05, 0.35, pan=0.1)
    return mix


def build_sfx(spec, mix, cfg):
    if cfg.get("engine", "artlist") == "synth":
        return build_sfx_synth(spec, mix)
    return build_sfx_artlist(spec, mix, cfg)


# ------------------------------------------------------------------ output
def write_wav(path, stereo, sr=SR, peak=0.89):
    data = np.clip(stereo, -1.0, 1.0)
    top = float(np.max(np.abs(data))) or 1.0
    data = data / top * peak
    pcm = (data * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def build(spec, out, with_vo=True, root=None, engine=None):
    """Render the full mix for `spec`: bed + SFX + (VO ducking the bed)."""
    dur = float(spec.get("duration", 12.0))
    cfg = load_config(spec, root=root, engine=engine)

    bed_mix = Mix(dur)
    build_bed(spec, bed_mix, cfg)
    sfx_mix = Mix(dur)
    build_sfx(spec, sfx_mix, cfg)

    bed = bed_mix.stereo()
    mix = bed + sfx_mix.stereo()

    if with_vo and spec.get("vo"):
        from vo import voice_track
        voice = voice_track(spec, out.replace(".wav", "_vo.wav"))
        if voice is not None:
            voice = voice[: len(bed)]
            # duck the bed only — SFX keep their level
            env = np.abs(voice).mean(axis=1)
            k = int(0.09 * SR)
            kern = np.ones(k, dtype=np.float32) / k
            env = np.convolve(env, kern, mode="same")
            env = np.clip(env / (env.max() + 1e-9) * 2.2, 0, 1)
            duck = 1.0 - float(cfg.get("duck", 0.62)) * env
            mix = bed * duck[:, None] + sfx_mix.stereo() + voice

    peak = float(np.max(np.abs(mix)))
    if peak > 0.98:                       # clip guard before write_wav's normalise
        mix = mix * (0.98 / peak)
    write_wav(out, mix)
    return out


if __name__ == "__main__":
    import sys
    spec = json.load(open(sys.argv[1]))
    print(build(spec, sys.argv[2]))
