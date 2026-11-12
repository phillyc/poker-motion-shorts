# poker-motion-shorts

Agent-built kinetic-typography shorts for a $1/$2–$1/$3 live-cash poker audience.
Vertical 1080×1920, 30 fps, -14 LUFS, YouTube Shorts + Instagram Reels safe.

Three finished examples live in `out/`:

| id | file | length | concept |
|---|---|---|---|
| `same-hand-two-seats` | `out/same-hand-two-seats.mp4` | 45.0 s | position: same hand, two seats (hero piece, 20 beats, VO + custom score) |
| `pot-odds` | `out/pot-odds.mp4` | 12.9 s | pot odds: 3:1 → 25%, flush draw 35%, then a 40% price you must fold |
| `limp-trap` | `out/limp-trap.mp4` | 10.8 s | misconception: limping "feels safe", 7-way pot, raise-or-fold fix |

## Why this instead of Remotion

Remotion is the right tool for component-shaped, data-driven video with a live
preview. These shorts are a *template*: a fixed brand system and a beat sheet.
For that job a declarative JSON timeline + a ~450-line Pillow/NumPy compositor is
faster for an agent to author (no npm install, no bundler, no browser per frame),
fully deterministic, license-free, and renders a 13 s short in ~2 minutes on one
small CPU box. See `docs/tooling-comparison.md` for the full decision and when to
reach for Remotion instead.

## Quick start

```bash
uv venv --python 3.12 .venv
uv pip install pillow numpy edge-tts      # edge-tts only needed for voiceover

.venv/bin/python render.py shorts/pot-odds.json out/pot-odds.mp4
.venv/bin/python render.py shorts/limp-trap.json out/limp-trap.mp4 --no-vo
.venv/bin/python render.py shorts/pot-odds.json out/stills --stills 1.6 5.2 7.6 11.8
.venv/bin/python render.py shorts/pot-odds.json --qa
```

`ffmpeg`/`ffprobe` must be on PATH. Rendering is CPU-only; expect ~3.4 fps at
1080×1920 on a 4-vCPU instance (~2 min for a 13 s short).

## Layout

```
render.py              CLI: timeline -> frames -> x264/AAC
lib/kt.py              declarative kinetic-typography engine (elements + motion presets)
lib/core.py            drawing primitives, springs/easings, supersampled text
lib/audio.py           NumPy music bed + SFX map derived from the timeline
lib/vo.py              edge-tts voiceover, trimmed/fitted per line, auto-ducked
shorts/*.json          the shorts themselves (this is what you edit)
hero/                  the 45 s hero piece's original 20-beat renderer + spec notes
docs/                  POC report, tooling comparison, format research
out/                   rendered MP4s (not the source of truth)
```

## Timeline format

```json
{
  "id": "pot-odds", "fps": 30, "duration": 12.9, "bpm": 100, "y_offset": 90,
  "palette": {"bg": "#05100C", "bg2": "#12402F", "ink": "#F4EFE6",
              "dim": "#94A79F", "accent": "#E8B44A", "good": "#35E1C4", "bad": "#FF4D3D"},
  "vo": [{"t": 0.25, "text": "Fifty to call, into a hundred and fifty."}],
  "elements": [
    {"kind": "kicker", "text": "LIVE $1/$2 · POT ODDS", "t0": 0.04, "t1": 3.0, "y": 468},
    {"kind": "text", "text": "$50", "t0": 0.12, "t1": 3.0, "y": 690,
     "size": 250, "preset": "slam", "color": "ink"},
    {"kind": "counter", "to": 25, "suffix": "%", "t0": 3.24, "t1": 6.2, "y": 700, "size": 300},
    {"kind": "bar", "t0": 4.05, "t1": 6.2, "y": 1052, "pct": 0.25, "label": "25%",
     "ticks": [[0, "0%"], [0.5, "50%"], [1, "100%"]]},
    {"kind": "rule", "t0": 8.86, "t1": 10.8, "y": 812, "width": 640}
  ]
}
```

Element kinds: `text`, `kicker`, `counter`, `bar`, `rule`, `badge`, `card`.
Motion presets: `slam`, `rise`, `drop`, `pop`, `wipe`, `slide_left`,
`slide_right`, `blur_in`, `none`; exits: `snap`, `sink`, `lift`, `none`.
All times are seconds; `t1` is when the exit animation starts.
Rich lines use `runs: [{text, color, scale, gap}]` for per-word colour and stagger.

## Design rules (baked in)

- **Safe band y 250–1440**: platform chrome eats the rest. `--qa` fails an
  element that pokes outside it or is wider than 940 px.
- **≤ 5 words per card**, one idea per beat, verdict last.
- **Nothing is ever frozen**: every element gets a sub-pixel drift and the whole
  frame gets a drifting key light + breathing push-in + fine grain.
- Type is supersampled 2× — big Anton/Archivo stays crisp.
- Audio: bed at −24ish under VO, ducked 62%, final loudnorm −14 LUFS / −1.5 dBTP.
