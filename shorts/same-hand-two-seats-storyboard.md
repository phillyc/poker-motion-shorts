# Storyboard & Script — "Same Hand. Two Seats."

**Task:** t_d6979582 · **Series:** Poker Shorts (kinetic typography) · **Format:** "Don't Do This" hook + "The Spot" structure (research formats 1 & 2)
**Concept:** Position in Texas Hold'em — why the same hand is worth more from the button
**Audience:** live low-stakes cash, $1/$2–$1/$3, rec players
**Runtime:** 45.0 s · **30 fps** · **1350 frames** · **1080 × 1920 (9:16)**
**Platforms:** YouTube Shorts + Instagram Reels (single master serves both)

---

## 1. The one idea

> **Same two cards. Sit last, and you know more before you decide.**

No chart, no range, no solver. One sentence a $1/$2 player can repeat at the table tonight.

Why this concept first (from the research brief):
- Position is the single highest-EV *free* adjustment at low stakes — it costs nothing and applies every hand.
- It is a **native diagram**: nine seats in a ring is literally the layout, so the motion graphics *are* the lesson, not decoration on it.
- Visually it gives a clean binary (early = red / blind, late = cyan / informed) — a reusable red/green state machine the rest of the series can inherit.

**Deliberately excluded:** any invented win-rate statistic. The short argues from *structure* (how many decisions you see before you act), which is verifiable at the table and can't age into being wrong.

---

## 2. Design system (lock this before animating)

### Canvas & safe areas
| Item | Value |
|---|---|
| Resolution | 1080 × 1920 |
| Frame rate | 30 fps, 1350 frames |
| Duration | 45.0 s |
| **Top safe margin** | y ≤ 250 px — platform UI / search bar. Nothing readable above this. |
| **Bottom safe margin** | y ≥ 1440 px — Reels caption/CTA UI + Shorts action rail. Keep clear. |
| **Live content band** | y = 250 → 1440 (1190 px tall) |
| Caption baseline | y = 1380 (bottom-anchored inside safe band) |
| Horizontal margin | 110 px each side → 860 px type width, max |

> Rule of thumb: if text is within 100 px of y=1440 or y=250, it will get covered by platform chrome on one of the two apps. Both apps are tested, not just YouTube.

### Palette
| Token | Hex | Use |
|---|---|---|
| `felt900` | `#08110E` | Background base (near-black green) |
| `felt700` | `#123B2E` | Table ring fill, subtle radial |
| `ivory` | `#F4EFE6` | Primary type |
| `early` (red) | `#FF4D3D` | UTG / early position / "guessing" |
| `late` (cyan) | `#35E1C4` | Button / late position / "informed" |
| `chip` (gold) | `#E8B44A` | Chips, rule card hairline, numerals |
| `mute` | `#6E7C77` | Desaturated/eliminated states |
| `card-red` | `#D8323C` | Hearts/diamonds pips only |

Two-accent discipline: **red means blind, cyan means informed.** Never use red or cyan for decoration, or the semantic shortcut dies on frame 3.

### Typography
| Role | Face (free, Google Fonts) | Size | Treatment |
|---|---|---|---|
| Hook / stamp | **Archivo Black** (or Anton) | 148 px | UPPERCASE, tracking −2%, line-height 0.92 |
| Claim | Archivo Black | 96 px | UPPERCASE, max 3 lines |
| Label / kicker | **Inter 800** | 44 px | UPPERCASE, tracking +8% |
| Caption | Inter 700 | 40 px | Sentence case |
| Micro | Inter 600 | 28 px | tracking +4%, `mute` |

Numerals: tabular, gold. Max **5 words per text card.** If a card needs 6, it's two cards.

### Motion language
Reusable spring — this is the whole "punchy" feel, so keep it identical everywhere:

```json
{ "type": "spring", "stiffness": 320, "damping": 22, "mass": 0.9 }
```

| Move | Spec | Notes |
|---|---|---|
| **Slam-in** (hooks, stamps) | scale 1.14 → 1.00, opacity 0 → 1, 9 frames on the spring | the signature move; never ease this, spring it |
| **Rise-in** (supporting text) | y +26 → 0, opacity 0 → 1, 10 frames | follows the slam by 4–6 frames |
| **Stagger** (word-by-word) | 3 frames per word, same spring | only for the S5.3 build, use sparingly |
| **Snap-out** | opacity → 0 in 4 frames, y −20 | hard, no easing — reads as a cut, not a fade |
| **Card deal** | y −160 → 0 with 8° rotation settling to 0, spring ×1.4 stiffness | 12 frames |
| **Chip count-up** | 18 frames, ease-out, tabular numerals | |
| **Seat pulse** | ring 1.0 → 1.35 scale, opacity 0.9 → 0, 14 frames, loops 2× | marks "this seat, right now" |
| **Shake** | ±10 px x, 2 px frames, 3 frames total | only on S3.4, maximum once per short |
| **Split wipe** | hard vertical edge, 6 frames, no feather | S5.1 |
| **White flash** | 2 frames of `ivory` at 12% over everything | exactly once, at S5.2 |

**Hard rule:** audio-off comprehension. Every spoken word that carries meaning must also exist as type on screen. There is **no separate subtitle track** — the kinetic type *is* the caption. That's the reason this format travels on muted feeds.

### Audio
- Music: minimal 90 BPM dark pulse, ducked −14 dB under VO; no melody competing with type.
- SFX map: sub-hit on each hook word · card flick on deal · single tick per seat count (rising pitch) · riser 2 s into S5 · **1 s of near-silence** before the rule card (the drop is the punchline) · soft chime on rule card.
- VO: warm, flat, conversational — 175 wpm max, ~115 words total. Not an announcer. Barely any smile.

---

## 3. Shot-by-shot storyboard

Legend: **IN/OUT** in frames @30fps (seconds in parens). `▸` = on-screen type. `VO` = voiceover. `FX` = animation note.

---

### S1 — HOOK · 0.0 → 4.5 s (f0–f135)

**Visual:** Black. A faint 9-seat table ring fades up at 20% opacity, camera pulled back so the ring reads as a diagram, not a table. Behind everything, `felt700` radial.

| Beat | Time | On screen | VO / FX |
|---|---|---|---|
| **S1.1** | 0.00–1.50 (f0–45) | ▸ **SAME HAND.** — 148 px, ivory, centred at y=780 | VO: "Same two cards." · FX: slam-in on f0, **no logo, no greeting, no fade from black**. Sub-hit at f0. |
| **S1.2** | 1.50–3.00 (f45–90) | ▸ **TWO SEATS.** — stacks below at y=940; previous line rises to y=700 and shrinks to 96 px | VO: "Two seats." · FX: seat 1 (left of ring) pulses `early`; seat 6 (bottom right) pulses `late`. Pulse offset 8 frames so they don't read as simultaneous. |
| **S1.3** | 3.00–4.50 (f90–135) | ▸ **TWO RESULTS.** — third line, y=1080, keeps the column | VO: "Two completely different results." · FX: thin vertical hairline splits the frame; left half gains 8% red tint, right 8% cyan. Ring brightens to 45%. |

**Read at a glance:** the whole thesis is legible by f90 with sound off.

---

### S2 — THE HAND · 4.5 → 9.5 s (f135–285)

**Visual:** The hook text snaps out in one move. Table ring rotates 12° so seat 1 sits at top-left (standard 9-handed orientation), then holds for the rest of the video.

| Beat | Time | On screen | VO / FX |
|---|---|---|---|
| **S2.1** | 4.50–6.50 (f135–195) | ▸ Card pair **A♠ J♠** deals into centre (each 260×370 px, ivory face, 6 px radius, 2 px `felt700` stroke); ▸ label under: **THE SAME TWO CARDS** (44 px, tracking +8%) | VO: "Ace-jack suited. Everyone gets this hand." · FX: two cards deal one after another, 10 frames apart, spring overshoot then settle. Card flick ×2. |
| **S2.2** | 6.50–8.00 (f195–240) | ▸ The pair **duplicates** — one copy slides left and tints `early`, one slides right and tints `late`; ▸ centre text: **ONE HAND. TWO SEATS.** | VO: "Where you sit decides what it's worth." · FX: duplicate at 40% opacity crossfading to 100%; slide on spring, 14 frames. |
| **S2.3** | 8.00–9.50 (f240–285) | ▸ Card copies shrink to 120×170 and park at y=1290 as a persistent HUD; ▸ micro caption: **POSITION = WHEN YOU ACT** | FX: a 3 px `chip` arc draws around the ring clockwise over 30 frames (stroke dashoffset animation). This arc is a recurring motif — it comes back in S3 and reverses in S4. |

---

### S3 — EARLY POSITION (the problem) · 9.5 → 19.5 s (f285–585)

**Visual:** Everything dims to 30%. Seat 1 lights `early`. This is the "bad line" act — same treatment the research brief's "Don't Do This" format uses.

| Beat | Time | On screen | VO / FX |
|---|---|---|---|
| **S3.1** | 9.50–11.50 (f285–345) | ▸ Kicker **UNDER THE GUN** (44 px, `early`) at y=460; ▸ claim **FIRST TO ACT** (96 px, ivory) y=560 | VO: "From under the gun, you're first to act—" · FX: seat 1 slam-pulses; a 2 px `early` ring stays lit. |
| **S3.2** | 11.50–14.00 (f345–420) | ▸ **8 PLAYERS BEHIND YOU** (96 px) replaces claim; the numeral **8** counts up 1→8, each tick lighting the next seat dot in `early` at 25% | VO: "—with eight players behind you." · FX: chevron arrows sweep clockwise from seat 1; 9 frames total, one per seat; tick SFX rising in pitch. This is the most literal "see the seat diagram" beat — hold it. |
| **S3.3** | 14.00–16.67 (f420–500) | ▸ **NO IDEA WHAT'S COMING** (96 px, two lines: "NO IDEA" / "WHAT'S COMING") | VO: "You have no idea what's coming." · FX: a `?` glyph pops on each of the 8 seats in sequence (6 frames each, overlapping), then all collapse to 40% opacity together. |
| **S3.4** | 16.67–19.50 (f500–585) | ▸ **GUESSING.** — 148 px `early`, stamped at y=900 over a dimmed ring; ▸ micro under: **WORST INFORMATION AT THE TABLE** | VO: "So you guess — with the worst information at the table." · FX: everything desaturates to `mute` in 10 frames; stamp slams in; 3-frame shake; sub-hit. **Only shake in the video.** |

---

### S4 — LATE POSITION (the fix) · 19.5 → 30.5 s (f585–915)

**Visual:** Hard cut on the beat. Full colour returns, ring brightens, seat 6 (button) lights `late`. The arc motif from S2.3 now animates **counter-clockwise** — information flowing *into* you instead of decisions flowing *away*.

| Beat | Time | On screen | VO / FX |
|---|---|---|---|
| **S4.1** | 19.50–21.33 (f585–640) | ▸ Kicker **ON THE BUTTON** (`late`), claim **LAST TO ACT** | VO: "On the button, you act last." · FX: hard cut, no crossfade. Button chip icon (gold disc, 90 px) drops onto seat 6 and lands with a spring. |
| **S4.2** | 21.33–24.00 (f640–720) | ▸ **8 DECISIONS BEFORE YOURS** — counter counts 0→8, but every tick is a cyan dot *landing on the button*, not on a seat | VO: "Every player has already decided before you do." · FX: 8 small `late` dots travel seat→button along the arc, 52 frames spread; each landing nudges the button ring 4%. Counter is `late`, tabular. |
| **S4.3** | 24.00–27.33 (f720–820) | ▸ Three stacked readout rows build in sequence (each row = label left, value right, 1 px `felt700` divider):<br>`FOLDED` → `5`<br>`LIMPED` → `2`<br>`RAISED` → `$15` | VO: "You know who folded, who limped, who raised — and how much." · FX: rows at y = **1010 / 1105 / 1200** (95 px pitch, last row clears the y=1440 safe line by 240 px); rise-in 12 frames apart; values count up; the `$15` value is `chip` gold and 20% larger. Chips stack behind the readout, 3 denominations. |
| **S4.4** | 27.33–30.50 (f820–915) | ▸ **YOU'RE NOT GUESSING.** → replaced at f870 by ▸ **YOU'RE RESPONDING.** (slam, `late`) | VO: "You're not guessing. You're responding." · FX: first line rises in ivory, second slams over it in `late` with 2 px `late` underline that draws left-to-right in 6 frames. |

---

### S5 — THE EDGE (the payoff) · 30.5 → 39.5 s (f915–1185)

**Visual:** The frame splits down the middle — the S1.3 hairline returns as a real divider. Left column = the red seat, right column = the cyan seat. Same cards both sides. This is the shot that gets screenshotted.

| Beat | Time | On screen | VO / FX |
|---|---|---|---|
| **S5.1** | 30.50–33.00 (f915–990) | Left (red tint 10%): ▸ **A♠J♠** mini-cards + **BLIND**<br>Right (cyan tint 10%): ▸ **A♠J♠** mini-cards + **INFORMED** | VO: "Same cards. Same opponents. Same board." · FX: split wipe 6 frames; both mini-card pairs land simultaneously — deliberately identical, the sameness *is* the argument. |
| **S5.2** | 33.00–36.00 (f990–1080) | ▸ **POSITION IS FREE.** — 148 px, centred, spanning both halves; the divider dissolves | VO: "The only thing that changed is what you knew." · FX: **2-frame ivory flash at 12%**, then the line slams. Divider lines retract upward in 8 frames. Sub-hit + riser resolves. |
| **S5.3** | 36.00–39.50 (f1080–1185) | ▸ **IT DOESN'T CHANGE YOUR CARDS.** (ivory) / **IT CHANGES WHAT YOU KNOW.** (second line, `late`) — word-by-word build, 3 frames apart | VO: "Position doesn't change your cards. It changes how much you know when you act." · FX: the only staggered build in the short; then 20 frames of **stillness** — nothing moves. Let it land. |

---

### S6 — RULE CARD + LOOP · 39.5 → 45.0 s (f1185–1350)

| Beat | Time | On screen | VO / FX |
|---|---|---|---|
| **S6.1** | 39.50–42.00 (f1185–1260) | Card panel (rounded 24 px, `felt700` fill at 90%, 1 px `chip` hairline, 940×480 px, centred y=880):<br>▸ **TIGHT UP FRONT.** (ivory, 88 px)<br>▸ **WIDE ON THE BUTTON.** (`late`, 88 px) | VO: "Tight up front. Wide on the button." · FX: **1 second of near-silence** before the panel enters (f1155–1185 is dead air + music drop) — the silence is the punctuation. Panel scales 0.96 → 1.00 in 10 frames, then type slams line by line. Chime. |
| **S6.2** | 42.00–44.00 (f1260–1320) | ▸ micro: **THE CHEAPEST EDGE AT $1/$2** under the panel; ▸ handle lower-left inside safe band | VO: "That's it. That's the whole edge." · FX: micro fades up 10 frames. |
| **S6.3** | 44.00–45.00 (f1320–1350) | Panel and type snap out; ring returns dimmed to 20%, seats unlit, background back to `felt900` | FX: **this frame must match frame 0.** The loop is seamless — a rewatch costs the algorithm nothing and the first 3 words land again. |

---

## 4. Voiceover script (clean read)

> Same two cards. Two seats. Two completely different results.
>
> Ace-jack suited. Everyone gets this hand. Where you sit decides what it's worth.
>
> From under the gun, you're first to act — with eight players behind you. You have no idea what's coming. So you guess. With the worst information at the table.
>
> On the button, you act last. Every player has already decided before you do. You know who folded, who limped, who raised — and how much. You're not guessing. You're responding.
>
> Same cards. Same opponents. Same board. The only thing that changed is what you knew.
>
> Position doesn't change your cards. It changes how much you know when you act.
>
> Tight up front. Wide on the button. That's it. That's the whole edge.

**Word count:** 124 words over ~42 s of speaking time (there are ~3 s of intentional silence) ≈ **177 wpm** — deliberate, unhurried, still snappy. If the read comes in long, cut the S5.1 line "Same board." first.

---

## 5. Platform packaging

### Titles (pick one)
1. `Same hand. Two seats. Two different results.`
2. `Why position beats good cards at $1/$2`
3. `You're playing the same hand wrong from early position`

### Description
```
Position isn't about your cards. It's about how many decisions you get to see
before you make yours.

Play tight from early position. Play wide on the button.

#poker #texasholdem #pokerstrategy #cashgame #pokerplayer
```

### Platform notes
- **YouTube Shorts:** upload 1080×1920 / 30 fps / H.264 High, ~12 Mbps, AAC 192 kbps. Title ≤ 60 chars so it doesn't truncate in-feed. Hashtag `#Shorts` in description. Shorts max is 3 min; we're at 45 s, comfortably in the sweet spot.
- **Instagram Reels:** same master. 9:16, ≥720 px, ≥30 fps — compliant. Cover frame: **f96** (the split hook, "TWO RESUL—" mid-fade) — that's the frame with the strongest red/cyan contrast at grid size. Don't use a title card as the cover; the type is the thumbnail.
- **First-frame test:** at 12 px thumbnail size, frame 96 must still read as "two things, opposite colours." That's why the hairline split and the tint land before f135.
- **Caption file:** none needed (type is burned in). Provide `.srt` anyway for accessibility/search if the pipeline can emit it — OCR-indexable text is a real discovery lever on both platforms.

---

## 6. What "done" looks like for the render

Checklist the production task should hold itself to:

- [ ] 1350 frames, exactly 45.000 s, 1080×1920, 30 fps
- [ ] No readable element above y=250 or below y=1440
- [ ] Frame 0 and frame 1349 are visually identical (loop)
- [ ] Every VO line has a matching on-screen card at the same time
- [ ] Red = blind/early, cyan = informed/late, everywhere, no exceptions
- [ ] Exactly one shake (S3.4), one white flash (S5.2), one staggered build (S5.3)
- [ ] Muted playback still teaches the full lesson
- [ ] ≥1 s of silence before the rule card survives the music mix

The frame-accurate version of all of the above is in `short-spec.json` — the render task should consume that file rather than re-deriving timings from this document.