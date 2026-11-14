# Licences

## Audio — Artlist.io

Every music bed and sound effect in the delivered shorts comes from
[Artlist.io](https://artlist.io), licensed to Phil C. under an active Artlist
subscription (Music + SFX). The masters live in the private bucket
`s3://pokerfx-audio` (AWS account `862635396572`) and each MP3 carries the
embedded tag `copyright: Licensed for video by Artlist.io`.

| What | Where |
|---|---|
| Licensed masters | `s3://pokerfx-audio/{music,sfx}/` (private) |
| Local materialisation | `assets/audio/{music,sfx}/` — gitignored |
| Slug ↔ file ↔ S3 key map | `assets/audio/manifest.json` (tracked) |

### What the licence allows

- Use of the tracks in videos published on social platforms and client work,
  monetised or not, for the term of the subscription.
- Altering, trimming, looping and mixing the tracks into a soundtrack.

### What it does not allow — and why the raw files are gitignored

Artlist licenses use *in a production*, not redistribution of the source audio.
This repository is **public**, so committing the MP3/AAC masters would publish
the library itself. That is why:

- `assets/audio/music/` and `assets/audio/sfx/` are gitignored, as are `*.mp3`
  and `*.aac` globally.
- Only `assets/audio/manifest.json` is tracked — slugs, S3 keys, durations,
  loudness stats and byte sizes, no media.
- `python tools/fetch_audio.py` re-materialises the bank from S3 on demand and
  verifies each file against the manifest's recorded size.

Rendered deliverables (`out/*.mp4`) contain the licensed music mixed with
voiceover and are published as finished videos, which the licence does cover.
They are also gitignored, since they are build outputs.

**If a track is swapped or the subscription lapses, re-check the delivered
videos against the licence terms before publishing anything new.**

## Everything else

- Source code in this repository: no licence file is present; treat as
  all-rights-reserved unless one is added.
- Fonts: Anton and Archivo are used under the SIL Open Font License 1.1.
- Voiceover: synthesised at render time with `edge-tts`; no third-party voice
  samples are stored in the repo.
