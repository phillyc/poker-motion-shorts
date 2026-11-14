"""Real-audio sound bank (Artlist assets shipped in `assets/audio/`).

Every placeholder voice in `lib/audio.py` / `hero/audio.py` maps to a slug in
`assets/audio/manifest.json`.  This module resolves a slug to a file, decodes
it with ffmpeg to 48 kHz stereo float32 (so the 44.1 kHz AAC SFX and 44.1 kHz
MP3 beds land on the same timeline), and cache the result.

Asset root resolution (first hit wins):
  1. explicit `root=` argument (from `render.py --audio-root`)
  2. $POKERFX_AUDIO_ROOT
  3. `assets/audio/` inside the repo

An external root is resolved through the *original* S3 keys recorded in the
manifest, so pointing at a raw mirror of the bucket (e.g.
`/home/ubuntu/pokerfx-audio-assets`) works without renaming anything.
"""
from __future__ import annotations

import functools
import json
import os
import subprocess
import sys

import numpy as np

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BUILTIN_ROOT = os.path.join(REPO, "assets", "audio")
MANIFEST = os.path.join(BUILTIN_ROOT, "manifest.json")


class MissingAsset(RuntimeError):
    """Raised when a requested slug/file cannot be found under the asset root."""


@functools.lru_cache(maxsize=1)
def manifest():
    with open(MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


@functools.lru_cache(maxsize=None)
def _index():
    """slug -> {'file': rel, 's3_key': key, 'group': 'music'|'sfx', ...}"""
    idx = {}
    m = manifest()
    for group in ("music", "sfx"):
        for entry in m[group]:
            e = dict(entry)
            e["group"] = group
            idx[e["slug"]] = e
    return idx


def root(explicit: str | None = None) -> str:
    return os.path.abspath(explicit or os.environ.get("POKERFX_AUDIO_ROOT") or BUILTIN_ROOT)


def groups():
    idx = _index()
    return {g: [s for s, e in idx.items() if e["group"] == g] for g in ("music", "sfx")}


def resolve(ref: str, root_dir: str | None = None) -> str:
    """Resolve a slug (preferred), a repo-relative path, or an absolute path."""
    root_dir = root(root_dir)
    if os.path.isabs(ref) and os.path.exists(ref):
        return ref
    entry = _index().get(ref)
    if entry:
        for cand in (os.path.join(root_dir, entry["file"]),
                     os.path.join(root_dir, entry["s3_key"])):
            if os.path.exists(cand):
                return cand
        raise MissingAsset(
            "asset %r not found under %s (looked for %s and %s)"
            % (ref, root_dir, entry["file"], entry["s3_key"]))
    for cand in (os.path.join(root_dir, ref),
                 os.path.join(root_dir, "music", ref),
                 os.path.join(root_dir, "sfx", ref)):
        if os.path.exists(cand):
            return cand
    raise MissingAsset(
        "unknown asset %r — known slugs: %s" % (ref, ", ".join(sorted(_index()))))


def _decode(path: str) -> np.ndarray:
    """ffmpeg -> float32 stereo @ 48 kHz. Works for MP3 and raw ADTS (.aac)."""
    raw = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-nostdin", "-i", path,
         "-f", "f32le", "-acodec", "pcm_f32le", "-ac", "2", "-ar", str(SR), "-"],
        stderr=subprocess.PIPE)
    x = np.frombuffer(raw, dtype="<f4").astype(np.float32)
    if x.size % 2:
        x = x[:-1]
    return x.reshape(-1, 2).copy()


@functools.lru_cache(maxsize=32)
def _load_cached(path: str, mtime: float) -> np.ndarray:
    x = _decode(path)
    x.setflags(write=False)
    return x


def load(ref: str, root_dir: str | None = None, sr: int = SR) -> np.ndarray:
    """Decoded stereo float32 array, read-only and cached per file+mtime."""
    if sr != SR:
        raise ValueError("soundbank decodes at %d Hz; resample elsewhere" % SR)
    path = resolve(ref, root_dir)
    x = _load_cached(path, os.path.getmtime(path))
    return x


def music(slug: str, root_dir: str | None = None) -> np.ndarray:
    return load(slug, root_dir)


def sfx(slug: str, root_dir: str | None = None) -> np.ndarray:
    return load(slug, root_dir)


# ------------------------------------------------------------------ shaping
def db(x: np.ndarray, gain_db: float) -> np.ndarray:
    return (x * (10.0 ** (gain_db / 20.0))).astype(np.float32)


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x, dtype=np.float64))) + 1e-12)


def normalise_rms(x: np.ndarray, target_db: float) -> np.ndarray:
    """Scale so the whole-file RMS sits at `target_db` dBFS (per-sample, both ch)."""
    cur = 20.0 * np.log10(max(rms(x), 1e-9))
    return db(x, target_db - cur)


def normalise_peak(x: np.ndarray, target_db: float) -> np.ndarray:
    peak = float(np.max(np.abs(x))) or 1e-9
    return db(x, target_db - 20.0 * np.log10(peak))


def fade(x: np.ndarray, fade_in: float = 0.0, fade_out: float = 0.0) -> np.ndarray:
    y = x.copy()
    n = len(y)
    a = min(int(fade_in * SR), n)
    b = min(int(fade_out * SR), n)
    if a > 1:
        y[:a] *= np.linspace(0.0, 1.0, a, dtype=np.float32)[:, None]
    if b > 1:
        y[-b:] *= np.linspace(1.0, 0.0, b, dtype=np.float32)[:, None]
    return y


def clip(x: np.ndarray, dur: float | None = None, offset: float = 0.0,
         fade_in: float = 0.002, fade_out: float = 0.02) -> np.ndarray:
    """Offset/trim a sample to `dur` seconds and de-click both ends."""
    i = max(0, int(offset * SR))
    y = x[i:]
    if dur is not None:
        y = y[: int(dur * SR)]
    return fade(y, fade_in, fade_out)


def track_duration(slug: str) -> float | None:
    """Manifest duration of a music slug in seconds (None if unknown)."""
    entry = _index().get(slug)
    if not entry or entry.get("group") != "music":
        return None
    dur = float(entry.get("duration") or 0.0)
    return dur or None


def fits_track(slug: str, offset: float, dur: float, margin: float = 2.0) -> bool:
    """True when ``offset + dur`` (plus ``margin``) stays inside the track.

    A bed that has to be *looped* to cover the short is a latent defect: if the
    source ends in a fade to silence (as licensed tracks usually do) the loop
    point becomes digital silence followed by a hard, full-level re-entry.  Call
    this before rendering and move the in-point earlier if it returns False.
    """
    total = track_duration(slug)
    if total is None:
        return True
    return offset + dur + margin <= total + 1e-6


def _tile_xfade(x: np.ndarray, n: int, xfade: float = 0.30) -> np.ndarray:
    """Tile `x` to exactly `n` samples with an equal-power crossfade per seam.

    A hard splice at the loop point clicks, and when the tail is fading it also
    dips to silence and then re-enters at full level.  Overlapping each repeat by
    `xfade` seconds and blending the two with cos/sin keeps the seam continuous
    and the perceived level constant (equal power, 3 dB down at the midpoint).
    """
    L = max(0, min(int(round(xfade * SR)), len(x) // 2))
    if L < 2:
        reps = int(np.ceil(n / len(x)))
        return np.tile(x, (reps, 1))[:n].copy()
    t = np.arange(L, dtype=np.float32) / L
    fo = np.cos(t * np.pi / 2)[:, None]          # equal-power fade-out
    fi = np.sin(t * np.pi / 2)[:, None]          # equal-power fade-in
    out = x.copy()
    while len(out) < n + L:
        head = x.copy()
        head[:L] = head[:L] * fi + out[-L:] * fo
        out = np.concatenate([out[:-L], head])
    return out[:n]


def fit(x: np.ndarray, dur: float, loop: bool = True, fade_out: float = 0.35,
        xfade: float = 0.30) -> np.ndarray:
    """Trim or (optionally) loop a music bed to exactly `dur` seconds."""
    n = int(round(dur * SR))
    if len(x) >= n:
        return fade(x[:n], 0.02, fade_out)
    if not loop:
        out = np.zeros((n, 2), dtype=np.float32)
        out[: len(x)] = fade(x, 0.02, fade_out)
        return out
    return fade(_tile_xfade(x, n, xfade), 0.02, fade_out)



if __name__ == "__main__":
    for g, slugs in groups().items():
        print(g, len(slugs))
        for s in slugs:
            try:
                x = load(s)
                print("  %-38s %6.2fs  rms %6.1f dBFS  peak %5.1f dBFS"
                      % (s, len(x) / SR, 20 * np.log10(rms(x)),
                         20 * np.log10(float(np.max(np.abs(x))))))
            except MissingAsset as e:
                print("  %-38s MISSING: %s" % (s, e))
    print("root:", root(), file=sys.stderr)
