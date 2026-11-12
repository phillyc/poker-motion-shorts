# Tooling comparison — programmatic motion graphics for shorts

Scope: what an *agent* can drive to produce punchy 9:16 kinetic typography, ranked
by token/effort cost per finished second. Prices checked Nov 2026; verify before
committing budget.

## The four families

| family | examples | what you get | what it costs you |
|---|---|---|---|
| Code frameworks (self-hosted) | **Remotion**, Motion Canvas, Revideo | full control, components, data-driven frames, your own render farm | React/TS skill, npm/bundler, headless browser per frame, license at scale |
| Declarative + custom compositor | **this repo** (JSON + Pillow/NumPy), FFmpeg filters, GSAP-to-frames | total control over typography, tiny dependency surface, deterministic, fast to author for a fixed template | you build and maintain the primitives; no preview UI |
| Managed render APIs | Creatomate, Shotstack, JSON2Video, Bannerbear, Plainly | template + JSON in, MP4 URL out, zero infra | per-render credits, ceiling on arbitrary layout/animation |
| Timeline apps | After Effects (+Templater), CapCut, Canva | best craft per pixel, presets, stock | not agent-drivable at the frame level; manual time |

## Head-to-head on the things that matter here

### Remotion — https://www.remotion.dev
React components render frames in headless Chromium, then FFmpeg encodes.
`useCurrentFrame()` + `interpolate()`/`spring()`, a real Studio preview, and
Lambda/Cloud Run fan-out for batch.

- **License:** free for individuals and companies ≤3 people; Company License
  $25/seat/month for creators, "$0.01 per render, $100/mo minimum" for automators,
  Enterprise from $500/mo.
- **Agent fit:** good once a project exists — TypeScript is well represented in
  training data and the API is small. Costs: `create-video` scaffold, node_modules,
  bundler step, and slow first renders; every styling change is code, so a "text
  card" is 20–40 lines instead of 4 JSON keys.
- **Use it when:** you need interactive preview, data-driven charts/ranges, or
  components reused across many formats. **Don't** use it just to slam words on a
  background — that is the expensive path to the same pixels.

### Motion Canvas — https://motioncanvas.io
TypeScript generator functions (`yield*`) drive a scene graph with a strong
authoring editor. Beautiful for hand-choreographed explainers; it is
authoring-first, so headless batch rendering needs care.

### Revideo — https://midrender.com/revideo
Fork of Motion Canvas adding headless rendering, audio and a library API; MIT.
Important caveat: the team now develops primarily in **Midrender**, and recent
changes are not upstreamed. Viable, but treat the OSS repo as feature-frozen.

### Managed APIs
- **Creatomate** — template editor + JSON API, from ~$54/month with render credits.
  Fastest "working endpoint" if your layout fits its boxes; custom kinetic type
  choreography hits the ceiling quickly.
- **Shotstack** — JSON timeline (tracks/clips/transitions) rendered server-side,
  credit-per-minute pricing (commonly cited around $0.30/min; check current tiers).
  Excellent for stitching/trimming/overlays, weaker for typographic motion design.
- **JSON2Video / Bannerbear / Plainly** — template-fill and AE-automation flavours;
  good for personalized variants, not for designing a motion language.

### After Effects / CapCut / Canva
Still the quality ceiling and still the right tool for a hero brand film. Not
agent-drivable frame-by-frame; use them to *design* a look that the code then
reproduces at volume (which is what this repo's design system encodes).

## What this experiment actually showed

Same 12.9 s short, two agent paths:

| | JSON timeline + Pillow engine | Remotion (estimated) |
|---|---|---|
| authoring surface | ~110 lines of JSON, 4 keys per card | 300–600 lines TSX + config |
| environment | 3 pip packages, no Node | Node + npm + bundler + Chromium |
| render | 124 s CPU, 3.1 fps, deterministic | seconds-to-minutes per render, browser-bound |
| iteration | render stills at timestamps | Studio scrub (better for choreography) |
| license | none | free ≤3 people, then $25/seat/mo |

Cold-start to three finished videos: 82 min, $0.23 of model spend, 189 tool calls.
Once the engine existed, each additional short cost ~$0.03 and ~10 minutes.

**Recommendation.** Keep the JSON/engine pipeline for the templated series
(one leak, one number, one verdict), and keep Remotion in the toolbox for the
minority of shorts that genuinely need components, charts or a preview loop. If
you ever want zero infrastructure and fixed templates, Creatomate/Shotstack are
the escape hatch — at the cost of the custom kinetic-typography control that makes
these feel like a brand.
