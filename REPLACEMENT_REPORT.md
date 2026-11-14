# Replacement report — real Artlist audio in the demo shorts

Task `t_7a93c2cc`. Inputs: the s3://pokerfx-audio inventory (`t_17ec7f18`) and the
demo audio audit (`t_8519500f`).

Before this change the repo contained **zero audio assets**: every bed and every
SFX was synthesised in NumPy by `lib/audio.py:build_bed` / `build_sfx` and
`hero/audio.py`. Those placeholder voices are now replaced by the 15 real
licensed Artlist files from S3. Nothing in the visuals changed — the six
delivered MP4s (five shorts plus the monthly recap) were re-scored with the video
stream copied, so frame timing is byte-identical to the previous cut.

---

## 1. What changed

| File | Change |
|---|---|
| `assets/audio/manifest.json` | **new** — 15 assets: slug → local path → S3 key, plus codec, rate, channels, bytes, duration, LUFS-I, true peak |
| `assets/audio/{music,sfx}/` | **new** — byte-identical copies of the 15 S3 objects (gitignored; `LICENSES.md`) |
| `lib/soundbank.py` | **new** — slug resolution, ffmpeg decode to 48 kHz stereo float32, cached; shaping helpers (`fit`, `clip`, `normalise_rms`, `normalise_peak`, `fade`) |
| `lib/audio.py` | two engines behind one cue grammar: `artlist` (default) and `synth` (legacy, kept as `--audio-engine synth`). `Mix.add` now accepts stereo signals; the SFX map is driven by real samples |
| `hero/audio.py` | hero bed/SFX map points at the same sound bank; frame-locked cue times unchanged |
| `config/audio.json` | **new** — per-project music choice, `music_offset`, bed level, duck depth, extra hand-placed SFX |
| `shorts/recaps/october-2026-monthly.json` | **new** — the missing motion spec for the legacy monthly recap (frame-locked cue map recovered from the storyboard attachment; 1530 frames @ 30 fps) |
| `tools/score_monthly.py` | **new** — re-scores `out/october2026_monthly_results.mp4` from that spec, video stream copied |
| `web/index.html` | synced with the deployed NAS gallery (adds the monthly recap card; the repo copy had drifted) |
| `render.py` | `--audio-root` and `--audio-engine` flags |
| `tools/recut_audio.py` | **new** — re-score an existing MP4 (video stream-copied, audio rebuilt) |
| `tools/fetch_audio.py` | **new** — re-materialise the licensed bank from S3, size-verified |
| `.gitignore` | excludes the licensed media (`assets/audio/{music,sfx}/`, `*.mp3`, `*.aac`) |
| `LICENSES.md` | **new** — Artlist terms, why the masters are not in a public repo |
| `README.md` | audio section, two-engine docs, 5-deliverable table, fetch step |

**Licensing decision.** `github.com/phillyc/poker-motion-shorts` is public and
Artlist licenses *use in a production*, not redistribution of the source audio.
So the 22.4 MiB of masters are deliberately **not** committed — only the manifest
is. `python tools/fetch_audio.py` restores the bank from S3 and checks every byte
count against the manifest. This is why the diff shows new code but no new media.

---

## 2. Placeholder → real asset mapping

| Placeholder (old) | Where it was | Now |
|---|---|---|
| `build_bed()` — NumPy kick/snare/hat/bass/pad loop | `lib/audio.py` | real Artlist music bed, `SB.music(slug)` + offset loop |
| `sub_impact()` | `lib/audio.py` | `impact-bomb` — BOOM Library ICE Bomb Hit |
| `snap_sfx()` | `lib/audio.py` | `pop-notification` — Ni Sound Popping Bubble Notification |
| `whoosh()` (kicker) | `lib/audio.py` | `whoosh-air-slicer` — Chroma Air Slicers Short Dirty Woosh (tail ends on the cut) |
| `whoosh()` (rule) | `lib/audio.py` | `whoosh-foil` — Eiravaein Fencing Foil Whoosh |
| `chime()` (final verdict) | `lib/audio.py` | `cash-register` — 2496 Retro Machines Cha Ching Bell |
| hero bed | `hero/audio.py` | `steven-beddall-pocket-money` @ 70 s |
| hero drop accent | `hero/audio.py` | `record-stop` — Heewon Oh DJ Turntable Record Stop |
| hero card shuffles | `hero/audio.py` | `cards-shuffle` — TeaSound Shuffling Cards Quick (two offsets from one 1.55 s sample) |
| `tick_sfx()` counters/bars | `lib/audio.py` | **still synthesised** — no tick asset in the bucket |
| `riser()` verdict build | `lib/audio.py`, `hero/audio.py` | **still synthesised** — no riser asset in the bucket |

`config/audio.json:synth_voices` records that these two families are intentional
synth, so a future bucket addition can be swapped in one place.

---

## 3. Per-project score sheet

| project | music bed | offset | bed RMS | real SFX placed |
|---|---|---|---|---|
| `pot-odds` | Steven Beddall — Pocket Money | 70 s | −24 dBFS | 16 hits: impact ×6, air-slicer ×4, pop ×4, cash ×1, shuffle ×1 |
| `limp-trap` | Danny Shields — This Way | 5 s | −24 dBFS | 12 hits: impact ×5, air-slicer ×2, pop ×2, foil ×1, cash ×1, shuffle ×1 |
| `october2026_session` | Danny Shields — Guest House | 60.86 s | −19 dBFS | 24 hits: impact ×11, air-slicer ×9, foil ×1, cash ×1, money-counter ×1, shuffle ×1 |
| `october-2026-session` | Ian Post — Never Gonna Get Me | 100 s | −20 dBFS | 22 hits: impact ×10, air-slicer ×8, foil ×1, cash ×1, money-counter ×1, shuffle ×1 |
| `october2026_monthly_results` | Ian Post — Never Gonna Get Me | 60 s | −21 dBFS | 12 hits: impact ×4, shuffle ×6, air-slicer ×1, cash ×1 (+ synth ticks/riser, bed mute 25.0–26.5 s) |
| `same-hand-two-seats` (hero) | Steven Beddall — Pocket Money | 70 s | −20 dBFS | impact ×4, shuffle ×2, record-stop ×1, cash ×1 (+ synth ticks/riser) |

Ingest constraints from the inventory, all honoured:

- The six 44.1 kHz SFX are resampled to 48 kHz by the `soundbank` decoder before
  mixing, so nothing lands off-grid.
- Hot masters (−7.2 … −9.4 LUFS-I, up to +1.0 dBTP) are **not** compressed; they
  are gained down to the bed level and the final mix is normalised once.
- The `… Lips Pop Bubbly .aac` stray-space key is only present in the manifest;
  the local filename is slugged, so no quoting hazard remains in the build path.

---

## 4. Verification

**Asset integrity** — all 15 local files SHA-256 match the local S3 mirror, and
`tools/fetch_audio.py --check` passes (15/15, sizes match the manifest).

**Audio actually replaced** — normalised cross-correlation of each delivered
MP4's audio against (a) the newly built WAV and (b) the previous delivery's
audio. A lag scan is used because AAC adds a 240-sample (5 ms) encoder delay.

| project | vs new build | lag | vs old delivery |
|---|---|---|---|
| `pot-odds` | **+0.9968** | −240 | +0.0114 |
| `limp-trap` | **+0.9939** | −240 | −0.0165 |
| `october2026_session` | **+0.9990** | 0 | −0.0149 |
| `october-2026-session` | **+0.9962** | −240 | +0.0015 |
| `same-hand-two-seats` | **+0.9895** | −240 | +0.0039 |
| `october2026_monthly_results` | **+0.9989** | 0 | (new; no previous re-score) |

Every MP4 is the new score; none carries the old audio. The new WAVs in turn
correlate ~+0.60 with the source MP3 at the configured offsets (0.60 not 1.0
because the bed is ducked, gained and mixed with VO/SFX), which confirms the
synthesised bed is gone rather than merely re-labelled.

**Delivery spec** (`out/audio_recut_report.json`, measured with `ebur128`):

| file | dur | LUFS-I | LRA | true peak |
|---|---|---|---|---|
| `pot-odds.mp4` | 12.90 | −13.8 | 2.2 | −2.3 |
| `limp-trap.mp4` | 10.79 | −14.7 | 1.0 | −2.4 |
| `october2026_session.mp4` | 51.99 | −14.2 | 3.2 | −2.0 |
| `october-2026-session.mp4` | 44.99 | −14.7 | 2.5 | −2.3 |
| `same-hand-two-seats.mp4` | 45.00 | −14.4 | 2.5 | −3.1 |
| `october2026_monthly_results.mp4` | 51.00 | −14.3 | 3.1 | −2.3 |

All within ±1 LU of the −14 LUFS target, all true peaks legal (< −0.5 dBTP),
AAC-LC 192 kbps / 48 kHz stereo, H.264 video stream-copied.

**Loop-seam fix (`october2026_session`).** The first pass put the bed at 75 s on a
123.55 s track, so only 48.55 s remained for a 52 s short: `fit()` tiled the
segment, and because "Guest House" self-fades to digital silence by 123 s the
delivery had 101 ms of true zeros at 48.00–48.55 s and a hard, full-level
re-entry at 48.549 s. Moved the in-point to 60.86 s (an 81 BPM downbeat; 112.86 s
total, 10.69 s clear of the fade) so nothing is tiled. Class-level guards added
so it cannot recur: `soundbank.fits_track()` + a `check_beds()` pre-flight in
`tools/recut_audio.py` refuse an overrunning in-point, `fit()` crossfades any
remaining seam equal-power over 0.30 s, and a TP retry loop lowers the limiter
ceiling until the *decoded* true peak is legal. Post-fix: no zero runs, min
400 ms RMS −19.5 dBFS between 44–52 s, bed lag 0.00 s in every window.

Two-stage normalisation matters: applying `loudnorm` in the same ffmpeg pass as
the AAC encoder produced inter-sample overshoots up to +3.5 dBTP, so the filter
chain writes a PCM master first and the AAC encode is a separate clean pass.
The hero needed a lower limiter ceiling (`0.60`) because its tanh bus overshoots.

---

## 5. Gaps and follow-ups

1. **`out/october2026_monthly_results.mp4` is now re-scored (was gap 1).** It
   exists in the NAS delivery tree (51.0 s, 1080×1920, AAC 48 kHz) but had no
   spec anywhere — so it kept its original all-NumPy score. Recovered the spec
   from the storyboard attachment, wrote `shorts/recaps/october-2026-monthly.json`
   (1530 frames @ 30 fps) and `tools/score_monthly.py`, and re-scored it with
   `ian-post-never-gonna-get-me` @ 60 s (never looped) plus the frame-locked cue
   map. Delivered: −14.3 LUFS-I / −2.3 dBTP, audio matches the rebuilt mix at
   r = 0.9989 (lag 0), H.264 stream byte-identical to `out/_source`, deployed to
   the gallery with MD5 local == served.
2. **No tick, riser, chip, or ambience assets exist in the bucket.** Counters and
   bars keep synthesised ticks, and both verdict risers stay synth. Adding one
   tick sample and one riser to `s3://pokerfx-audio/sfx/` would retire the last
   synthetic voices — the swap is a one-line manifest entry plus a
   `config/audio.json` cue change.
3. **NAS delivery is updated — six files.** The live gallery at
   `http://100.91.93.22/poker-motion-shorts/` serves the re-scored MP4s.
   Files were tar-streamed over ssh (`docs/poc-report.md` §6) after copying
   the previous versions to `out/.bak-20261114-preaurescore/` (five) and
   `out/.bak-20261114-premonthly/` (monthly) on the NAS. MD5 of every deployed
   file matches the local render, all answer HTTP 206 with `video/mp4`, and a
   full download decodes cleanly.
4. Loudness on `pot-odds` (−13.8) sits ~0.2 LU off target — well inside platform
   tolerance, noted only so it is not mistaken for drift.

## 6. Reproducing

```bash
python tools/fetch_audio.py                      # restore the licensed bank
python tools/recut_audio.py                      # re-score all five
python tools/recut_audio.py pot-odds hero        # subset
python tools/recut_audio.py --audio-engine synth # legacy A/B
python tools/score_monthly.py                    # sixth short (monthly recap)
python tools/fetch_audio.py --check              # integrity only
```
