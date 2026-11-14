"""Build the 45 s audio bed + frame-locked SFX map for 'Same Hand. Two Seats.'

Real Artlist audio (bed, impacts, card shuffle, record-stop, cash chime) with
two synthesised voices kept for the cues the asset bucket has no sample for:
the 2.5 s riser and the tick/metronome family. Cue times are frame-locked to
hero/render.py (30 fps).  Writes build/audio.wav.

    python hero/audio.py build/audio.wav [--audio-root DIR]
"""
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "lib"))
import audio as A          # noqa: E402  (riser/tick/build helpers)
import soundbank as SB     # noqa: E402

SR = 48000
DUR = 45.0
N = int(SR * DUR)
FPS = 30
PROJECT = "same-hand-two-seats"

L = np.zeros(N, dtype=np.float32)
R = np.zeros(N, dtype=np.float32)


def add(sig, t_start, gain=1.0, pan=0.0):
    i = int(t_start * SR)
    if i >= N:
        return
    sig = np.asarray(sig, dtype=np.float32)
    stereo = sig.ndim == 2
    if i < 0:
        sig = sig[-i:]
        i = 0
    seg = sig[: N - i]
    gl = gain * min(1.0, 1.0 - pan) ** 0.5
    gr = gain * min(1.0, 1.0 + pan) ** 0.5
    if stereo:
        L[i:i + len(seg)] += seg[:, 0] * gl
        R[i:i + len(seg)] += seg[:, 1] * gr
    else:
        L[i:i + len(seg)] += seg * gl
        R[i:i + len(seg)] += seg * gr


def env(n, a=0.005, d=0.2, curve=4.0):
    t = np.arange(n) / SR
    e = np.exp(-t / d) * curve
    at = int(a * SR)
    if at > 0:
        e[:at] *= np.linspace(0, 1, at)
    return e


def sine(f, n, phase=0.0):
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t + phase).astype(np.float32)


def noise(n):
    return np.random.default_rng(11).normal(0, 1, n).astype(np.float32)


def lp(x, cutoff):
    """one-pole lowpass"""
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def hp(x, cutoff):
    return x - lp(x, cutoff)


# ---------------------------------------------------------------- synth voices kept
def tick(freq=1400.0):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    return (sine(freq, n) * np.exp(-t / 0.022) * 0.5 +
            hp(noise(n), 3000) * np.exp(-t / 0.006) * 0.25).astype(np.float32)


def riser(dur=2.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = t / dur
    f = 180 * (7.0 ** p)
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) * 0.25 + np.sin(ph * 2.01) * 0.10
    nz = hp(noise(n), 900) * (0.10 + 0.4 * p ** 2)
    e = (p ** 1.6)
    return ((tone + nz) * e).astype(np.float32)


def low_drone():
    t = np.arange(N) / SR
    dr = (np.sin(2 * np.pi * 41.2 * t) * 0.06 + np.sin(2 * np.pi * 82.4 * t) * 0.025).astype(np.float32)
    lfo = (0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * t)).astype(np.float32)
    return (dr * lfo).astype(np.float32)


# ---------------------------------------------------------------- real-audio helpers
def cfg():
    spec = {"id": PROJECT, "duration": DUR}
    root = None
    if "--audio-root" in sys.argv:
        root = sys.argv[sys.argv.index("--audio-root") + 1]
    c = A.load_config(spec, root=root)
    return c


def hit(slug, t, gain=1.0, dur=None, offset=0.0, peak_db=-6.0,
        fade_in=0.002, fade_out=0.05, pan=0.0, c=None, align="start"):
    x = SB.sfx(slug, c.get("root"))
    x = SB.normalise_peak(x, peak_db)
    x = SB.clip(x, dur, offset, fade_in, fade_out)
    at = t - len(x) / SR if align == "end" else t
    add(x, max(0.0, at), gain * float(c.get("sfx_gain", 1.0)), pan)


def F(fr):
    return fr / FPS


# ---------------------------------------------------------------- music bed
C = cfg()
DROP_A, DROP_B = 1155 / FPS, 1185 / FPS      # music drop (dead air before rule card)

bed = SB.music(C["music"], C.get("root"))
bed = SB.clip(bed, None, float(C.get("music_offset", 0.0)), 0.0, 0.0)
bed = SB.fit(bed, DUR, loop=bool(C.get("music_loop", True)),
             fade_out=float(C.get("music_fade_out", 0.45)))
bed = SB.normalise_rms(bed, float(C.get("bed_rms_db", -24.0)))

# drop the music to silence for the rule card (30 ms ramps), then bring it back
g = np.ones(N, dtype=np.float32)
ia, ib = int(DROP_A * SR), int(DROP_B * SR)
k = int(0.03 * SR)
g[ia:ib] = 0.0
g[ia - k:ia] = np.linspace(1, 0, k)
g[ib:ib + k] = np.linspace(0, 1, k)
bed = bed * g[:, None]
add(bed, 0.0, 1.0)

# record-stop at the drop, so the music does not just vanish
hit(C.get("drop_sfx", "record-stop"), DROP_A, gain=0.55, dur=1.0,
    peak_db=-6.0, fade_in=0.002, fade_out=0.15, c=C)

# low drone under everything, also muted through the drop
add(low_drone() * g, 0.0, 0.5)

# ---------------------------------------------------------------- SFX map (frame-locked)
hit("impact-bomb", F(0), gain=0.80, dur=1.5, fade_in=0.001, fade_out=0.5, c=C)

# the hole cards: two shuffle flicks, different slices of the same take
hit("cards-shuffle", F(135), gain=0.45, dur=0.30, offset=0.02, peak_db=-8,
    fade_in=0.002, fade_out=0.06, pan=-0.25, c=C)
hit("cards-shuffle", F(145), gain=0.45, dur=0.30, offset=0.72, peak_db=-8,
    fade_in=0.002, fade_out=0.06, pan=0.25, c=C)

for i in range(8):                       # rising tick per seat (no asset — synth)
    add(tick(900 * (1.11 ** i)), F(345) + i * (66 / 30.0) / 8.0, 0.30, -0.4 + 0.1 * i)
add(tick(1700), F(428), 0.18)
for i in range(8):                       # ? pops
    add(tick(1200 * (1.05 ** i)), F(428) + i * 5 / FPS, 0.10, 0.3)
hit("impact-bomb", F(500), gain=0.70, dur=0.9, fade_in=0.001, fade_out=0.3, c=C)
for k in range(8):                       # S4 travelling dots
    add(tick(1100 * (1.04 ** k)), F(646) + k * 6 / FPS, 0.13, -0.3 + 0.08 * k)
add(riser(990 / 30.0 - 915 / 30.0), F(915), 0.42)          # no asset — synth
hit("impact-bomb", F(990), gain=0.85, dur=1.6, fade_in=0.001, fade_out=0.5, c=C)
hit("cash-register", F(1185) + 0.02, gain=0.55, dur=2.0, peak_db=-6,
    fade_in=0.002, fade_out=0.45, c=C)
hit("impact-bomb", F(1185), gain=0.30, dur=0.6, fade_in=0.001, fade_out=0.25, c=C)

# ---------------------------------------------------------------- mix
mix = np.stack([L, R], axis=1)
mix = np.tanh(mix * 1.15) * 0.95          # gentle glue / soft clip on the bus
peak = float(np.max(np.abs(mix))) or 1.0
mix = mix / peak * 0.89
mix = np.clip(mix, -1, 1)
tail = int(0.12 * SR)
mix[-tail:] *= np.linspace(1, 0, tail)[:, None]

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "build/audio.wav"
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
data = (mix * 32767).astype(np.int16)
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(data.tobytes())
print("wrote audio: %s  %.1fs  peak(pre-norm)=%.2f  music=%s" % (out, DUR, peak, C["music"]))
