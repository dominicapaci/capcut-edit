---
name: capcut-edit
description: >
  Turn a raw talking-head take (or a cut you already made in CapCut) into a fully EDITED, fully EDITABLE CapCut project:
  word-synced captions with one highlighted keyword, big word pops, floating app/UI cards, two switchable aesthetics
  ("cool girl" and "dark & mysterious"), punch-ins, sound effects, all as separate clips and real text elements so every
  piece can still be changed inside CapCut. Use whenever someone says "edit this video", "edit my video in CapCut",
  "make this look like [aesthetic]", "add captions and graphics", "turn my raw footage into a CapCut project", or hands
  you a take and a description of the edit they want. macOS, CapCut desktop, ffmpeg, Python 3, Node (for capcut-cli).
---

# capcut-edit — Claude edits your video, and you can still edit it after

The thing most "Claude video editor" setups get wrong: they hand you back a flat mp4. One typo, one wrong sound, and
you're re-prompting. This skill never renders a flat file as the deliverable. It writes a **CapCut project** where the
take is one clip per cut, every graphic is its own alpha clip, every caption is a real text element, and the punch-ins
are keyframes. The secret is that a CapCut project is just files on disk (`draft_content.json`, `draft_info.json`), and
[capcut-cli](https://github.com/renezander030/capcut-cli) writes them.

Read `references/capcut-cli.md` before building, `references/captions-and-cards.md` before designing graphics,
`references/looks.md` for the aesthetics, `references/lessons.md` for everything that went wrong once.

## Intake — ask these two things, every time

1. **Raw or pre-cut?** Raw take (one long recording with bad takes) → this skill cuts it. Already cut in CapCut →
   read their draft and rebuild from its exact cut points (`cutplan.py from-draft`). Don't guess; ask.
2. **What should it feel like?** A reference video link beats adjectives. If they name an aesthetic ("cool girl",
   "dark and mysterious", "cinematic"), confirm which reading they mean with one line each (see `looks.md`), then go.

Everything else (what to show when, which words to highlight) you decide from the transcript. Don't ask about it.

## The pipeline

Work in a scratch folder next to the footage (`<video>-edit/work/`). Deliver to `<video>-edit/`.

1. **Cut.** Raw: `python3 scripts/cutplan.py silence raw.mp4 --out cut.mp4` (audio-envelope pause trim: handles of a
   few frames, pauses shortened to ~0.12 s; no dead air between lines). Pre-cut: `python3 scripts/cutplan.py from-draft
   "<CapCut draft dir>" raw.mp4 --out cut.mp4` rebuilds their cut frame-exactly and writes `segments.json`.
   For a raw take with repeated lines, `capcut detect-retakes --srt words.srt` finds them; keep the LAST take of each line.
2. **Time the words.** `python3 scripts/transcribe.py cut.mp4 words/` → `words/words.txt` (`  6.40 three`). Every
   placement comes from these times. People's own estimates of when they say something run 1–2 s early.
3. **Frames + (optional) masks.** `ffmpeg -i cut.mp4 -q:v 2 frames/%05d.jpg`. If anything should sit BEHIND the
   person, `swiftc -O scripts/segbatch.swift -o segbatch && ./segbatch frames masks` (macOS Vision person masks).
4. **Look at the footage first.** Contact sheet (`fps=1/2,scale=270:-1,tile=8x6`), then Read it. Find where the head
   top is, where hands come up, how much headroom there is. Everything below depends on that.
5. **Plan the asset table before writing code.** One row per graphic: name · the word it lands on · in · out · builder.
   Then write `make.py` from `scripts/example_make.py` (cues, pops, cards, looks) on top of `scripts/render.py`.
6. **Check before rendering.** `python3 make.py check` renders 30-ish composite frames at the beats into one sheet.
   Read it. Fix collisions (cards over the face, text in the top 10%, two things in the headroom at once). Repeat.
7. **Render.** `python3 make.py preview` (flattened mp4 + synthesized SFX, for watching) and `python3 make.py layers`
   (take pieces with grades baked, premultiplied ProRes 4444 alpha clips, SFX wav, `meta.json`).
8. **Build the project.** `python3 scripts/build_project.py <layers dir> "<Project name>"` → a new CapCut draft. Quit and
   reopen CapCut; it's in the list. Never write into a draft the user made.
9. **README.** Placement table (time, file, what happens on which word), what's baked vs. editable, what was left out.

## Rules that make the edit good (defaults; a reference video overrides them)

- **Frame zero is the person + one line of text.** No card, no logo at 0:00. A visual that supports the hook can pop
  in from ~1 s and can be big.
- **Top 5% of the frame is off limits, top 10% is a red zone** (platform UI lives there). Captions sit over the chest.
- **Captions on every line, 2–4 words per cue, one keyword per cue in the highlight colour.** Cues come from the
  transcript, phrase by phrase, and never run into a section that speaks through its own typography.
- **Big single-word pops above the head** on the words that carry the line. Never while a card already owns the headroom.
- **Cards look real** (the app, a Finder window, a code editor, a player window, a comments card) and float in front
  of the person with a soft shadow and a slight tilt. No clip-art, no mascots, no mock UI with invented numbers.
- **A look is not an overlay.** When the script names an aesthetic, re-grade the FOOTAGE itself (take and cutout, same
  function, same noise seed) and bring the look's own type, cards and sound. On at the word that names it, off at the
  first word of the next idea. A white flash or a black dip sells the switch.
- **One re-hook punch-in** (scale keyframe, 1.08–1.14, instant) on the line that turns the video. A slow push-in over a
  dark section. Keyframes, never baked.
- **Sound lands on the verb.** Tap per pop (one per item in a group), click on cursor clicks, a sparkle / bass hit /
  whoosh on look switches, ticks on typewriter letters. Synthesized in `render.py`; no sample packs.
- **Nothing lingers past the next spoken beat.** Pop-ins 0.3 s, fades out 0.2–0.3 s.
- **Truth.** A number or a name on screen comes from somewhere real (the user's own stats, the actual file name, the
  actual folder). If you don't have it, don't invent it; draw the card without it.

## What you deliver

`<video>-edit/` with the CapCut project name in the README, `PREVIEW_<name>.mp4`, `capcut_layers/` (every clip, named
`NN_<start>s_<what>`), `README.txt`. In the project: `take` (one clip per cut, grades baked where a look applies) ·
`cutout` (optional) · `front1..n` (every graphic) · `blurb` + `captions` (real text elements with the keyword range
coloured) · `sfx`. Tell the user: quit and reopen CapCut, select the caption clips and pick a heavy sans, export from CapCut.
