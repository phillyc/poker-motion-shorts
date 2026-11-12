# Short-Form Poker Education Formats — Research Brief

**Task:** t_02765fc1 · **Scope:** Texas Hold'em, live low-stakes cash ($1/$2, $1/$3), YouTube Shorts + Instagram Reels, kinetic typography / motion-graphics-first
**Date of research:** November 2026. View/like counts are snapshots from that date, not live numbers.

---

## TL;DR — recommended slate

Five formats, ordered by (reach ceiling × fit for motion graphics × cheapness to produce):

1. **"The Spot" — one-decision hand breakdown** (30–45s)
2. **"Don't Do This" — common low-stakes mistake** (20–35s)
3. **"Poker Math in Motion" — one rule of thumb, animated** (15–25s)
4. **"Chalkboard Coach" — recurring mascot explains one concept** (25–40s)
5. **"Table Read" — live footage + kinetic lower-thirds exploit tip** (25–40s)

Optional sixth, best used as a weekly engagement play: **"Call It" — pause-and-answer quiz** (15–20s).

The first three are the strongest fits for a POC built around Remotion-style programmatic animation: they need almost no footage, are fully deterministic (cards, board, pot, math are data), and the "kinetic typography" IS the content rather than decoration on top of it.

---

## What the data says (cross-cutting patterns)

- **Length.** YouTube Shorts allows up to 3 minutes ([YouTube Help](https://support.google.com/youtube/answer/10059070?hl=en)); Instagram Reels specs are 9:16, ≥720px, ≥30fps ([Instagram Help](https://help.instagram.com/1038071743007909)). Independent 2026 analyses converge on **45–60s as the engagement sweet spot for Reels**, with sub-30s used for single-idea hits ([MoonB](https://www.moonb.io/blog/instagram-reel-length), [WaveVision](https://www.wavevision.io/blog/instagram-reels-length-what-performs-best-in-2026)). For poker education, the winning pattern is **one idea per short**, 20–45s.
- **Hook is the whole game.** Top performers open on the claim or the mistake, not on a greeting or a logo. Every 7-figure short sampled here has its thesis legible in frame 1 (`STEP 1: PLAY YOUR POSITION NOT YOUR CARDS`, `only DUMMIES make this mistake`, `BEGINNER MISTAKE!`).
- **Text carries the audio-off viewer.** Big, high-contrast, 3–5 words per card, one idea per card. This is exactly what kinetic typography is for — and most of the poker niche does it badly with default Captions presets, which is the opening.
- **Talking heads underperform relative to effort in this niche.** Negreanu's low-stakes advice short sits at 329K with a studio setup; a mascot + chalkboard + card graphics short does 10M. Production value ≠ reach; *clarity of the single claim* does.
- **Recurring visual IP compounds.** Channels that reuse one character/graphic system (hungry horse poker's dealer mascot, BlackRain79's overhead felt layout, TryBluff's black-card template) get brand recall from a 12px thumbnail.
- **Save/send is the real currency for education.** "Keep this for your next session" framing drives saves, and saves are what the algorithms treat as durable value.

---

## Format 1 — "The Spot": one-decision hand breakdown

**What it is:** A single street, a single decision. Board, stacks, pot, and hero's cards are laid out as a graphic; the video walks the decision tree and lands on one answer.

**Hook formula (0–2s):** "You're in the BB with 9♠7♠, $240 deep. Flop comes 8♠6♦2♣. What's your play?" — question in text, cards on screen, no preamble.

**Beat sheet (≈35s):**
- 0–3s: cards + board + pot fly in, question stamped on screen
- 3–10s: the two candidate actions appear as two columns
- 10–25s: one candidate is eliminated with an animated reason (equity %, range, texture)
- 25–33s: answer locks in with a hard cut + sound hit
- 33–35s: one-line takeaway held for the loop

**Motion treatment:** cards deal in on a spring curve; chips count up; equity bar fills; eliminated option desaturates and slides out. Everything on a 9:16 safe-area grid, 2 lines max per text block.

**Proven examples:**
- Casino King — *Poker Strategy for LATE Position* — ~998K views — https://www.youtube.com/shorts/HVCc1hSxYUk — first-person live footage, yellow `STEP 1:` headline, green caption bar, exactly the "one concept, three text beats" structure. (Hashtagged #pokerstars, but the uploader is Casino King.)
- WPT — *every card makes this poker hand crazier* — 4,900 likes on IG — https://www.instagram.com/reel/DfjBtXot_Jt/ — pure hand-breakdown captioning, street-by-street.
- Jonathan Little / PokerCoaching — *How are you playing this marginal hand in a cash game?* — https://www.instagram.com/reel/DZsomS8tBD5/ — question-first, $1/$3 specific, ties to a course.
- hungry horse poker — *why ACES are the 2ND best hand* — ~5.2M — https://www.youtube.com/shorts/tfOFK9S67rc — same skeleton, meme energy.

**Why it works for low-stakes live cash:** Rec players at $1/$3 don't have a range model — they have a *hand memory*. Abstract theory ("c-bet 33% on dry boards") bounces off; a concrete spot they recognise from last Saturday sticks. Live cash also produces the same 20 spots over and over (limped pots, BB defence, top pair on wet boards), so the format is infinitely repeatable without repeating content.

**Production notes:** Fully data-driven — one JSON per spot (stacks, board, cards, pot, actions) renders the whole short. Cheapest format to scale in Remotion. No footage licensing, no talent.

---

## Format 2 — "Don't Do This": the common low-stakes mistake

**What it is:** Name the leak in the first second, show the bad line, show the cost, show the fix. Negative framing ("mistake", "leak", "stop doing this") consistently outperforms positive framing in this niche.

**Hook formula (0–2s):** "This is why you're stuck at $1/$2." / "Only dummies make this mistake." / "the BIGGEST mistake new poker players make."

**Beat sheet (≈25s):**
- 0–2s: red slash / X stamp over the bad play, claim in 6 words
- 2–8s: the bad line plays out in graphics (chips sliding away, equity collapsing)
- 8–15s: the cost stated as a number ("this costs you ~$18/hour at $1/$3")
- 15–22s: the correct line animates in, side-by-side with a green check
- 22–25s: rule stated once, hold, loop

**Motion treatment:** red/green semantic system; shake or glitch on the mistake beat; the number should be the biggest type on screen. This is the format where a strong kinetic-type system pays off most — the joke *is* the timing of the text.

**Proven examples:**
- hungry horse poker — *only DUMMIES make this mistake* — ~7.6M — https://www.youtube.com/shorts/uTSm4P1s1N4 — mascot + chalkboard + hand graphic + pot readout.
- BlackRain79Poker — *3 Hands EVERY Beginner Plays Wrong!* — ~658K — https://www.youtube.com/shorts/tm5BmqoKaLI — overhead felt, cards and chips only, zero face, pure low-stakes authority.
- *the BIGGEST mistake new poker players make* — ~10M — https://www.youtube.com/shorts/EnwMtX4JR0Y — mistake framed as a fish, not a spot.
- BlackRain79Poker — *3 AMATEUR Hour Mistakes!* — ~11K — https://www.youtube.com/shorts/vfFz8r23o1Q — series naming ("3 X mistakes") is itself a format.

**Why it works for low-stakes live cash:** The audience's self-image is "I'm decent, the table is soft." A mistake format validates that while handing them a fix, and the mistakes that actually cost money at $1/$3 (limping, over-calling, paying off nits, no 3-betting) are unglamorous and never covered well by solver-content channels. That's whitespace.

**Production notes:** Needs almost no footage. One reusable "mistake versus correct" layout with a red/green state machine = a series template.

---

## Format 3 — "Poker Math in Motion": one rule of thumb, animated

**What it is:** A single piece of arithmetic — pot odds, rule of 4 and 2, equity needed, break-even bluff frequency — animated as an equation that builds itself. 15–25 seconds.

**Hook formula (0–2s):** "You're getting 3-to-1. You need to win this 25% of the time. Here's how to know in 3 seconds."

**Beat sheet (≈20s):**
- 0–3s: the situation + the number you need to beat
- 3–12s: the equation assembles term by term, each term landing on a beat and replaced in place
- 12–18s: the numbers resolve; the answer is the largest element on screen
- 18–20s: the shortcut restated as a single rule card

**Motion treatment:** This is the purest kinetic typography play in the slate. Dark background, enormous type, one accent colour, arithmetic operators that snap in. No cards required, though a card pair anchors the frame.

**Proven examples:**
- TryBluff — *Pot Odds Explained in 30 Seconds* — https://www.youtube.com/shorts/PLxDD37Q7sM — black card, `Call 100. Pot becomes 300. 100 ÷ 300`, green result. This is the template to beat.
- UpswingPoker — rule of 4 and 2 explainer reel — https://www.instagram.com/reel/Ddej5EhRB82/
- eFX Effects — *The Rule of 4: Poker Odds in Two Seconds* — https://www.youtube.com/shorts/-E3tL1K64lU — proves the topic travels even with weak production.
- Phil Galfond — *The #1 Low Stakes Poker HACK!* — ~49K — https://www.youtube.com/shorts/_I16i3Pa7EY — talking head + bold subtitle treatment; the weak version of this format.

**Why it works for low-stakes live cash:** Live low-stakes players get *no* HUD and no time bank. A mental-math shortcut they can execute in 5 seconds at the table is the single most actionable thing you can hand them, and it's inherently visual — numbers are easier to animate than concepts.

**Production notes:** Deterministic and templatable; the same composition can render a whole series by swapping variables. Lowest token/effort cost per finished short. Risk: maths content is a smaller audience than gossip/hand drama — treat these as the "saves" pillar, not the "reach" pillar.

---

## Format 4 — "Chalkboard Coach": recurring mascot, one concept

**What it is:** A single illustrated character (a dealer, a fish, a cartoon pro) stands at a chalkboard or card table and teaches one concept per episode. Serialised, instantly recognisable.

**Hook formula (0–2s):** Character points at the board; a handwritten line appears: "THIS JUST ISN'T A BLUFF IN A THOUSAND YEARS."

**Beat sheet (≈30s):**
- 0–4s: character enters/settles, board scribbles the claim
- 4–12s: hand graphic assembles below (hero/villain cards, pot)
- 12–22s: one turn of the concept — character reacts, text stamps a label
- 22–28s: rule of thumb written out
- 28–30s: character's sign-off gesture → loop point

**Motion treatment:** hand-drawn/wobbly type, chalk texture, squash-and-stretch on the character. The looseness is the point — it reads as "friend explaining", not "course".

**Proven examples:**
- hungry horse poker — *only DUMMIES make this mistake* (~7.6M, https://www.youtube.com/shorts/uTSm4P1s1N4), *poker pros use THIS secret* (~2.5M, https://www.youtube.com/shorts/ZGKJUAoXaZw), *my FAVORITE bluffing tip* (~1M, https://www.youtube.com/shorts/uTjNCWfPFmM) — same mascot, same chalkboard, same card+pot overlay across all of them.
- Brantzen Poker — *This Poker SECRET is all you need to win* — ~19M — https://www.youtube.com/shorts/FstIrEXHsDE — human version of the same idea: one recurring personality, one claim, giant type.

**Why it works for low-stakes live cash:** Low-stakes players learn from people, not from charts. A recurring character also solves the "who is this channel" problem in a niche where most accounts are anonymous clip farms, and it lets you say blunt things ("you're the fish") without the audience feeling attacked.

**Production notes:** Highest upfront design cost (character rig or a small library of illustrated poses), lowest marginal cost after that — one character, N boards. If the character is a vector asset, Remotion/Lottie can drive it; no voice actor needed if text carries it.

---

## Format 5 — "Table Read": live footage + kinetic lower-thirds exploit tip

**What it is:** Real (or recreated) live-table footage — first-person cards, chip stacks, a villain's bet — with animated overlays doing the teaching. The most "native to the platform" of the five.

**Hook formula (0–2s):** Footage already in motion + one stamped claim: "Watch his hands before you call." / "This is a $550 mistake."

**Beat sheet (≈30s):**
- 0–3s: strongest 1 second of footage, claim stamped
- 3–12s: bet sizes / pot / stack appear as live overlays; the read is annotated
- 12–24s: the decision and the result
- 24–30s: the generalisable rule as a clean text card

**Motion treatment:** Overlays must feel like a broadcast graphics package — stack counters, pot ticker, action chips ("RAISE $550"), range bars. Type sits in the lower third; keep the top third clear for the platform UI.

**Proven examples:**
- Casino King — *Poker Strategy for LATE Position* — ~998K — https://www.youtube.com/shorts/HVCc1hSxYUk
- Brantzen Poker — *How to READ Your OPPONENT'S MIND* — ~11M — https://www.youtube.com/shorts/PX4xH0WNDwQ
- Daniel Negreanu — *Negreanu's Advice to Low Stakes Poker Players* — ~329K — https://www.youtube.com/shorts/rDzzWnGB-KA
- hungry horse poker — *5 tips to CRUSH low stakes poker* — ~210K — https://www.youtube.com/shorts/VBy6-VB2LHI — footage + terminal-style typewriter overlay boxes.

**Why it works for low-stakes live cash:** Live cash is the product's context — felt, chips, $1/$3 stacks. Footage gives legitimacy ("this actually happened at a table like yours") that pure graphics can't, and the overlay layer is where your motion-design advantage shows.

**Production notes:** Most expensive format — needs footage capture and colour/sound work, plus graphics. Best used as the *hero* piece once the graphics system exists, not for the first POC.

---

## Optional — "Call It": pause-and-answer quiz

**What it is:** A spot is set up, a 2-second countdown runs, the answer reveals. Built for comments and rewatches.

**Proven examples:** PokerReflex equity quiz series — https://www.youtube.com/shorts/tka5nDjzDEc · GGPoker — *Poker Quiz for $100?!* — ~6.9K — https://www.youtube.com/shorts/KFb_eO9XsYE · PokerOrg chip trivia — ~12K — https://www.youtube.com/shorts/oITM6g_LOug · Galfond — *Why Using Pre-Flop Charts Is Holding You Back* — ~40K — https://www.youtube.com/shorts/y5gNzmKv_jA

**Why it works:** The pause creates a commitment, and commitment creates comments. Weak for teaching depth, strong for reach and for warming an audience toward the longer formats. Note the reach ceiling here is low for most accounts — use as a cadence filler, not a pillar.

---

## Effort vs. reach

| Format | Footage needed | Template-ability | Reach ceiling | Audience value |
|---|---|---|---|---|
| The Spot | none | very high | high | high |
| Don't Do This | none | very high | very high | high |
| Poker Math in Motion | none | highest | medium | very high (saves) |
| Chalkboard Coach | none | high (after character) | very high | medium |
| Table Read | high | low | high | high |
| Call It (quiz) | none | high | medium | medium |

---

## Recommended POC slate for the build phase

Pick three that stress different parts of the animation stack:

1. **"Poker Math in Motion" — pot odds** — proves deterministic, data-driven rendering; cheapest to ship; immediately comparable against the TryBluff benchmark.
2. **"Don't Do This" — limping from EP at $1/$3** — proves the red/green state machine, punch timing, and the hook system; highest reach ceiling of the three.
3. **"The Spot" — BB defence vs a $10 open** — proves card/board/chip layout, spring-based dealing animation, and the 9:16 safe-area grid at full complexity.

Each should be 20–35s, 1080×1920, 30fps, burned-in captions, and silent-readable. If the pipeline can render those three from a JSON input, the rest of the slate is content work, not engineering work.

---

## Sources

YouTube (view counts from Shorts search results, Nov 2026): HVCc1hSxYUk · uTSm4P1s1N4 · tfOFK9S67rc · ZGKJUAoXaZw · uTjNCWfPFmM · tm5BmqoKaLI · EnwMtX4JR0Y · vfFz8r23o1Q · PLxDD37Q7sM · -E3tL1K64lU · FstIrEXHsDE · PX4xH0WNDwQ · rDzzWnGB-KA · VBy6-VB2LHI · _I16i3Pa7EY · y5gNzmKv_jA · tka5nDjzDEc · KFb_eO9XsYE · oITM6g_LOug

Instagram (verified via page metadata, Nov 2026): instagram.com/reel/DZsomS8tBD5 (Jonathan Little / PokerCoaching) · instagram.com/reel/DfjBtXot_Jt (WPT) · instagram.com/reel/DfJ-CFZpVqT (Natural8) · instagram.com/reel/DXcJX9YEVpH (Phil Galfond) · instagram.com/reel/Ddej5EhRB82 (UpswingPoker)

Platform specs: [YouTube Shorts — 3 min max](https://support.google.com/youtube/answer/10059070?hl=en) · [Instagram Reels specs](https://help.instagram.com/1038071743007909)

Length benchmarks: [MoonB — best Reel length 2026](https://www.moonb.io/blog/instagram-reel-length) · [WaveVision — Reels length 2026](https://www.wavevision.io/blog/instagram-reels-length-what-performs-best-in-2026)
