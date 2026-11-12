"""Synthesise the 45s audio bed + SFX map for 'Same Hand. Two Seats.' (90 BPM)."""
import numpy as np, wave, sys

SR = 48000
DUR = 45.0
N = int(SR * DUR)
FPS = 30

L = np.zeros(N, dtype=np.float32)
R = np.zeros(N, dtype=np.float32)


def add(sig, t_start, gain=1.0, pan=0.0):
    i = int(t_start * SR)
    if i >= N: return
    seg = sig[: N - i]
    gl = gain * min(1.0, 1.0 - pan) ** 0.5
    gr = gain * min(1.0, 1.0 + pan) ** 0.5
    L[i:i + len(seg)] += seg * gl
    R[i:i + len(seg)] += seg * gr


def env(n, a=0.005, d=0.2, curve=4.0):
    t = np.arange(n) / SR
    e = np.exp(-t / d) * curve
    at = int(a * SR)
    if at > 0: e[:at] *= np.linspace(0, 1, at)
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


def sub_hit(dur=0.9, f0=90, f1=38):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.06)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph).astype(np.float32)
    click = noise(n) * np.exp(-t / 0.012) * 0.35
    return (body * np.exp(-t / 0.30) + click).astype(np.float32)


def card_flick():
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    nz = hp(noise(n), 1800)
    e = np.exp(-t / 0.035) * (1 - np.exp(-t / 0.002))
    # a short pitched "whip"
    sw = sine(2200, n) * np.exp(-t / 0.02) * 0.25
    return (nz * e * 0.5 + sw).astype(np.float32)


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
    e = (p ** 1.6) * (1 - 0.0 * p)
    return ((tone + nz) * e).astype(np.float32)


def chime(dur=2.2, base=784.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    parts = [(1.0, 0.55, 1.4), (2.0, 0.28, 0.9), (2.76, 0.16, 0.6), (5.4, 0.07, 0.35)]
    out = np.zeros(n, dtype=np.float32)
    for mult, amp, dec in parts:
        out += (np.sin(2 * np.pi * base * mult * t) * amp * np.exp(-t / dec)).astype(np.float32)
    at = int(0.004 * SR)
    out[:at] *= np.linspace(0, 1, at)
    return out


# ---------------------------------------------------------------- music bed (90 BPM)
BEAT = 60.0 / 90.0            # 0.6667 s
BAR = BEAT * 4
DROP_A, DROP_B = 1155 / FPS, 1185 / FPS   # music drop (dead air before rule card)

music = np.zeros(N, dtype=np.float32)

def kick(strong=True):
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    f = 46 + (95 - 46) * np.exp(-t / 0.045)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.22)
    beater = hp(noise(n), 2500) * np.exp(-t / 0.006) * 0.18
    return ((body * (1.0 if strong else 0.62)) + beater).astype(np.float32)

def hat():
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    return (hp(noise(n), 6500) * np.exp(-t / 0.018) * 0.12).astype(np.float32)

def bass_note(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t) * 0.5 + np.sin(4 * np.pi * f * t) * 0.12)
    e = np.minimum(1, t / 0.01) * np.exp(-t / (dur * 0.7))
    return (x * e).astype(np.float32)

t = 0.0
bar_i = 0
while t < DUR - 0.1:
    in_drop = DROP_A <= t < DROP_B
    if not in_drop:
        g = 1.0 if t < 36.0 else 0.85
        m = kick(strong=(bar_i % 2 == 0))
        add(m, t, 0.55 * g)
        add(kick(False)[: int(0.3 * SR)], t + BEAT * 2, 0.30 * g)
        add(hat(), t + BEAT * 1, 0.5)
        add(hat(), t + BEAT * 3, 0.5)
        if bar_i % 2 == 0:
            add(hat(), t + BEAT * 3.5, 0.35)
        # dark minor-pentatonic bass pulse
        notes = [55.0, 55.0, 61.74, 49.0]
        bn = bass_note(notes[bar_i % 4], BEAT * 1.9)
        add(bn, t, 0.20 * g)
    t += BAR
    bar_i += 1

# low drone, ducks under the drop
dr = (np.sin(2 * np.pi * 41.2 * np.arange(N) / SR) * 0.06 +
      np.sin(2 * np.pi * 82.4 * np.arange(N) / SR) * 0.025).astype(np.float32)
lfo = (0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * np.arange(N) / SR)).astype(np.float32)
dr *= lfo
duck = np.ones(N, dtype=np.float32)
ia, ib = int(DROP_A * SR), int(DROP_B * SR)
duck[ia:ib] = 0.0
# smooth the drop edges (30 ms)
k = int(0.03 * SR)
duck[ia - k:ia] = np.linspace(1, 0, k)
duck[ib:ib + k] = np.linspace(0, 1, k)
add(dr * duck, 0.0, 0.5)

# ---------------------------------------------------------------- SFX map (from spec)
def F(fr): return fr / FPS

add(sub_hit(), F(0), 0.85)
add(card_flick(), F(135), 0.55, -0.25)
add(card_flick(), F(145), 0.55, 0.25)
for i in range(8):                       # rising tick per seat
    add(tick(900 * (1.11 ** i)), F(345) + i * (66 / 30.0) / 8.0, 0.30, -0.4 + 0.1 * i)
add(tick(1700), F(428), 0.18)
for i in range(8):                       # ? pops
    add(tick(1200 * (1.05 ** i)), F(428) + i * 5 / FPS, 0.10, 0.3)
add(sub_hit(0.7, 80, 40), F(500), 0.75)
for k in range(8):                       # S4 travelling dots
    add(tick(1100 * (1.04 ** k)), F(646) + k * 6 / FPS, 0.13, -0.3 + 0.08 * k)
add(riser(990 / 30.0 - 915 / 30.0), F(915), 0.42)
add(sub_hit(1.0, 95, 36), F(990), 0.80)
add(chime(), F(1185) + 0.02, 0.34)
add(sub_hit(0.6, 70, 45), F(1185), 0.30)

# ---------------------------------------------------------------- mix
mix = np.stack([L, R], axis=1)
# gentle bus compression + soft clip
mix = np.tanh(mix * 1.25) * 0.92
peak = np.max(np.abs(mix))
mix = mix / peak * 0.89
mix = np.clip(mix, -1, 1)
# fade the last 4 frames to keep the loop clean
tail = int(0.12 * SR)
mix[-tail:] *= np.linspace(1, 0, tail)[:, None]

data = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[1] if len(sys.argv) > 1 else "build/audio.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(data.tobytes())
print("wrote audio: %.1fs, peak=%.2f" % (DUR, peak))
