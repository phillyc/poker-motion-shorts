# "Same Hand. Two Seats." — tools & QA

**Output:** `same-hand-two-seats-1080x1920.mp4` — 45.0 s, 1080x1920 (9:16), 30 fps, 1350 frames,
h264 High@4.2 (CRF 17, ~7.2 Mbps), AAC 192k stereo, -14.4 LUFS integrated, 40.6 MB, faststart.

## Tools (all local, no After Effects/Blender on this box)
- **Python 3.11 + Pillow + NumPy** — procedural motion-graphics compositor written for this job
  (`core.py` primitives, `render.py` 20 beats wired to the storyboard's frame numbers).
- **Spring/easing engine** — same motion tokens as the spec (stiffness 320, damping 22/26):
  slamIn / riseIn / snapOut / dealCard / countUp / wordStagger, frame-exact.
- **Living-frame pass** (`encode_v2.py`) — drifting 1350-frame-period key light, breathing
  1.000→1.0035 push-in, fine grain. Kills static holds (longest dead frame went 78 → 0).
- **edge-tts** (`vo.py`, en-US-AndrewMultilingualNeural, +12%, loudnorm-consistent) — 20 VO lines,
  auto-trimmed, tempo-fitted into each beat window (atempo where a line ran long).
- **NumPy synth** (`audio.py`) — 90 BPM dark pulse bed, sub-hits, card flicks, rising seat ticks,
  riser, chime, and the scripted music drop at 38.5–39.5 s; bed auto-ducks 9.4 dB under VO.
- **ffmpeg** — rawvideo pipe → h264, two-pass-style loudnorm to -14 LUFS / -1.5 dBTP, faststart.

## QA (`qa_check.py`, machine-checked on the encoded file)
| check | result |
|---|---|
| duration 45.0 s / 1080x1920 / 30 fps / 1350 frames | PASS |
| AAC stereo audio present | PASS |
| nothing readable outside the y 250–1440 safe band | PASS (0 violations, all 1350 frames) |
| loop closure SSIM(frame 0, frame 1349) | 0.9988 (spec: > 0.98) |
| no frozen holds > 20 frames | PASS (was 17 holds / 78 frames before the living-frame pass) |
| integrated loudness | -14.4 LUFS, peak -1.2 dBFS |

Manual stills QA (22-frame contact sheet across all six scenes) caught and fixed: white type over
white cards in S2.2 (cards now lift 106 px on the spring), chips crossing the table-ring arc in
S4.3, undersized BLIND/INFORMED column labels in S5.1.
