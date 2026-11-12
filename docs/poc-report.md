# POC report — agentic motion graphics for poker shorts

**Question:** can an agent produce punchy, on-brand, platform-ready kinetic
typography for a $1/$2 live-cash audience — and what does it cost in time, tokens
and complexity compared with Remotion-style tooling?

**Answer:** yes for a templated series. Three shorts were built end-to-end
(research → script → storyboard → render → QA → delivery) in **82 minutes wall
clock** and **$0.23** of model spend, and the third one was authored as a **150-line
JSON file**. Remotion is still the better tool when a short needs custom
component logic or live preview; it is not the cheapest way to make beat-sheet
typography.

---

## 1. What shipped

| short | length | frames | file | concept | how it was made |
|---|---|---|---|---|---|
| **Same Hand. Two Seats.** | 45.0 s | 1350 | 39 MB | position: same hand, two seats, 6 scenes / 20 beats | bespoke 20-beat renderer + score + 20 VO lines |
| **Pot Odds** | 12.9 s | 387 | 12 MB | 3:1 → need 25% → draw is 35% → call; then a 40% price → fold | 20-element JSON timeline on the shared engine |
| **The Limp Trap** | 10.8 s | 324 | 9.1 MB | limping "feels safe" → 7-way pot, top pair, no read → raise or fold | 14-element JSON timeline on the shared engine |

All three: 1080×1920, 30 fps, h264 High (CRF 17, ~7.2 Mbps), AAC 192k,
−14 LUFS / ≈−1 dBTP, faststart. Type, cards and bars stay inside the
y 250–1440 safe band so Shorts/Reels chrome never covers them.

Rendered output is in `out/`; the timelines are in `shorts/`.

## 2. Measured metrics

### Wall clock (three agent runs, no human in the loop)

| phase | task | duration |
|---|---|---|
| Format research (19 Shorts + 5 Reels verified) | t_02765fc1 | 7.3 min |
| Storyboard + script + machine-readable spec (45 s) | t_d6979582 | 4.6 min |
| Hero render, "living frame" pass, audio, QA + 3 defect fixes | t_fc833dee | 48.9 min |
| Two new shorts (engine generalisation, 2 timelines, 2 renders) + packaging | root | ~20 min |
| **Total, cold start → three delivered videos** | | **~82 min** |

Render throughput on a 4-vCPU box: **2.8–3.4 fps** at 1080×1920
(hero 485 s; pot-odds 124 s; limp-trap 102 s, including audio synthesis).

### Token spend (DeepSeek v4.1 flash, provider-reported usage)

| run | input | output | cache read | est. cost |
|---|---|---|---|---|
| research | 198,172 | 17,641 | 1.36 M | $0.044 |
| storyboard | 45,790 | 31,224 | 1.06 M | $0.029 |
| hero render | 198,803 | 36,061 | 4.34 M | $0.064 |
| new shorts + packaging | 377,933 | 44,780 | 3.74 M | $0.095 |
| **total** | **820,698** | **129,706** | **10.5 M** | **$0.2325** |

189 tool calls and 355 messages for the whole experiment.

**Marginal cost of a new short once the template exists: ~$0.02–0.04 and
~10 minutes**, most of it render time. The expensive part is inventing the look,
not producing the next episode.

### Effort comparison (same 12.9 s short, two ways)

| | JSON timeline + this engine | Remotion (estimate) |
|---|---|---|
| agent-authored lines | ~110 lines JSON + ~20 lines VO | 300–600 lines TSX across components + config |
| setup | `uv pip install pillow numpy edge-tts` | `npx create-video`, npm install, bundler, headless Chromium |
| render | 124 s, CPU only, deterministic | typically 2–6× realtime on first run; Chromium per frame |
| preview | stills at any timestamp (`--stills`) | full scrub-able Studio (real advantage) |
| reuse | new short = new JSON | new short = new composition + props |
| license | none | free for individuals/≤3-person companies, paid above |

Estimates, not measurements — see `tooling-comparison.md` for the sources.

## 3. Architecture

```
timeline JSON  ──►  kt.py (elements + springs)  ──►  living-frame pass  ──►  x264 + AAC
                        │                                   │
                        └── auto SFX map ──► audio.py ──────┘  (edge-tts VO, ducked)
```

- **Declarative beats.** Each element has `t0/t1`, a motion preset (`slam`, `pop`,
  `rise`, `wipe`, `drop`, `slide_*`, `blur_in`), colour role, font role and a `y`
  in the safe band. No per-frame code per short.
- **Springs, not tweens.** Entrances are damped-spring solutions (stiffness 320,
  damping 22/26), so slams settle with real overshoot; exits are 0.26 s cubic fades.
- **Living frame.** Drifting key light, breathing 1.000→1.0035 push-in, 0.9σ grain,
  plus sub-pixel drift on each element — kills "PowerPoint hold" frames.
- **Sound is derived, not hand-placed.** Slams get sub impacts, pops get snaps,
  kickers get whooshes, counters get ticks, the last big slam gets a riser + chime;
  a 90–100 BPM bed sits under it and ducks 62% under VO.
- **QA in the loop.** `--qa` rejects type outside the safe band, lines wider than
  940 px, and micro-type; every render is probed for duration/fps/loudness.

## 4. What is good enough to post, and what isn't

**Good:** hook, hierarchy, pacing, verdict clarity, safe areas, loudness, loop-friendly
end cards, visual consistency across the three, and the fact that a new episode is a
JSON edit.

**Not yet production grade:**
- **Voice** is edge-tts (Andrew multilingual), not Phil. It reads well but it is
  clearly synthetic; record real VO and drop the mp3s in `out/vo_<id>/` to replace.
- **Music** is NumPy-synthesised placeholder. Swap in a licensed bed (Epidemic/
  Artlist) — the engine already ducks whatever WAV you give it.
- **No live preview UI.** Iteration is still-render → look → adjust, which is fine
  for typography but slow for complex choreography. That is exactly where Remotion
  Studio earns its keep.
- **No captions/burned subtitles** for silent autoplay (the on-screen type is the
  message, but a real series should add a word-level caption track).
- **Card and table drawings** are competent-but-flat; the hero piece has them, the
  two new shorts deliberately stay type-only.

## 5. Recommended next steps

1. **Pick a format and commit to 8–10 episodes** of 12–15 s ("one leak, one number,
   one verdict"). The template is the moat; the topic is the variable.
2. **Record real VO** for one episode and A/B it against edge-tts before scaling.
3. **License one music bed** and one SFX pack; drop the synth placeholders.
4. **Add a caption track** (word-level) and test silent-first retention.
5. **Keep this engine for the series**, and stand up Remotion only for the
   occasional "data-viz" short (equity curves, range grids) where components and
   preview pay for themselves.
6. If volume grows past ~3 shorts/week, move rendering to a tiny queue
   (one worker, same code, ffmpeg unchanged) — it is already CPU-only and deterministic.
