---
name: capcut-edit
description: >
  Turn a raw talking-head take (or a cut you already made in CapCut) into a fully EDITED, fully EDITABLE CapCut project:
  word-synced captions with one highlighted keyword placed inside the platform's safe zones, big word pops, real app
  cards in front of and BEHIND the person, two switchable restrained aesthetics ("soft & warm" and "moody") that the
  viewer watches ramp in, the breathing-camera zooms that winning talking heads use, a flicker open, the person's own
  videos orbiting their head, sound from the editor's own library, all as separate clips and real text elements so every
  piece can still be changed inside CapCut. Use whenever someone says "edit this video", "edit my video in CapCut",
  "make this look like [aesthetic]", "add captions and graphics", "turn my raw footage into a CapCut project", or hands
  you a take and a description of the edit they want. macOS, CapCut desktop, ffmpeg, Python 3, Node (for capcut-cli).
---

# capcut-edit — Claude edits your video, and you can still edit it after

The thing most "Claude video editor" setups get wrong: they hand you back a flat mp4. One typo, one wrong sound, and
you're re-prompting. This skill never renders a flat file as the deliverable. It writes a **CapCut project** where the
take is one clip per cut, every graphic is its own alpha clip, every caption is a real text element, and the zooms are
keyframes. The secret is that a CapCut project is just files on disk (`draft_content.json`, `draft_info.json`), and
[capcut-cli](https://github.com/renezander030/capcut-cli) writes them.

Read `references/capcut-cli.md` before building, `references/safe-zones.md` and `references/captions-and-cards.md`
before placing anything, `references/looks.md` for the aesthetics, `references/motion.md` for zooms and the flicker,
`references/sound.md` before touching sound, `references/lessons.md` for everything that went wrong once.

## Intake — ask these things, every time

1. **Raw or pre-cut?** Raw take (one long recording with bad takes) → this skill cuts it. Already cut in CapCut →
   read their draft and rebuild from its exact cut points (`cutplan.py from-draft`). Don't guess; ask.
2. **What should it feel like?** A reference video link beats adjectives. If they name an aesthetic, confirm which
   reading they mean with one line each (see `looks.md`), then go.
3. **A 4K export of the same cut**, if they have one: zooms cropped from 4K stay sharp at 1080 (`motion.md`).
4. **Which sounds they already use in CapCut.** Run `scripts/capcut_sounds.py`; the names that repeat across their old
   projects are their taste. Never synthesize (`sound.md`).
5. **A 10-second screen recording of their CapCut timeline**, when the script shows "the editor". It becomes a real
   card; scripted clicking into CapCut is blocked on macOS.
6. **Behind or in front?** Creators who film with headroom usually want cards behind their head. Ask once, then it's a
   rule for them: and when it's behind them, it's fully behind them (no see-through).

Everything else (what to show when, which words to highlight) you decide from the transcript. Don't ask about it.

## The pipeline

Work in a scratch folder next to the footage (`<video>-edit/work/`). Deliver to `<video>-edit/`.

1. **Cut.** Raw: `python3 scripts/cutplan.py silence raw.mp4 --out cut.mp4` (audio-envelope pause trim: handles of a
   few frames, pauses shortened to ~0.12 s; no dead air between lines). Pre-cut: `python3 scripts/cutplan.py from-draft
   "<CapCut draft dir>" raw.mp4 --out cut.mp4` rebuilds their cut frame-exactly and writes `segments.json`.
   For a raw take with repeated lines, `capcut detect-retakes --srt words.srt` finds them; keep the LAST take of each line.
   A 4K export of the same cut goes in as `work/take_4k.mp4` + `work/frames4k/` (verify it's the same cut: PSNR > 35 dB).
2. **Time the words.** `python3 scripts/transcribe.py cut.mp4 words/` → `words/words.txt` (`  6.40 three`). Every
   placement comes from these times. People's own estimates of when they say something run 1–2 s early.
3. **Frames + masks.** `ffmpeg -i cut.mp4 -q:v 2 frames/%05d.jpg`. Masks are needed for anything behind the person and
   for the flicker: `swiftc -O scripts/segbatch.swift -o segbatch && ./segbatch frames masks` (macOS Vision, ~1 min per
   1,300 frames). The flicker also needs an empty-room plate: 2 s of the empty room filmed from the same spot, or
   `python3 scripts/plate.py work` (median of mask-free pixels; the chair centre ends up inpainted, say so).
4. **Look at the footage first.** Contact sheet (`fps=1/2,scale=270:-1,tile=8x6`), then Read it. Find where the head
   top is, where hands come up, how much headroom there is. Everything below depends on that.
5. **Sounds.** `python3 scripts/capcut_sounds.py --copy work/assets` lists the editor's cached library sounds with the
   names from their drafts; pick by role (`sound.md`: pop = a picture of them appears, click = computer-screen footage,
   typing = a real typing recording sliced per keystroke, one bell per look switch). If they want a sound you don't have,
   they press **+** on it in CapCut and it appears in the cache.
6. **Plan the asset table before writing code.** One row per graphic: name · the word it lands on · in · out · builder ·
   sound · layer (text / front / back). Then write `make.py` from `scripts/example_make.py` on top of `scripts/render.py`.
   Motion too: 3–6 breathing pushes (1.08–1.15× in over ~1.5 s, hold, out), 2–3 hard punches on joke/warning words, a slow
   creep across the moody look (`motion.md`).
7. **Check before rendering.** `python3 make.py check` renders composite frames at the beats into one sheet with the
   platform's no-go zones tinted red. Read it. Fix anything touching a red zone, cards over the face, two things in the
   headroom at once, a back card showing through hair. Repeat.
8. **Render.** `python3 make.py preview` (the finished mp4, zooms cropped from 4K when present, effects mixed; caption
   ticks left out) and `python3 make.py layers` (take pieces with grades/flicker baked, premultiplied ProRes 4444 alpha
   clips for back and front, the SFX wavs, `meta.json` with the eased zoom keys).
9. **Build the project.** `python3 scripts/build_project.py <layers dir> "<Project name>"` → a new CapCut draft with
   `take · back1..n · cutout · front1..n · blurb · captions · sfx · caption ticks`. It reports how many clips landed; if
   CapCut was open and dropped some, `python3 scripts/fill_project.py <layers dir> "<Project name>"`. Quit and reopen
   CapCut; it's in the list. Never write into a draft the user made.
10. **Iterate cheaply.** A sound swap is `make.py sound` (2 s, picture untouched, wav copied into the project's own media
    folder). A blurb or opening change is `make.py head` (30 s). Only a visual change elsewhere needs a full render.
11. **README.** Placement table (time, file, what happens on which word), the zooms, the looks, what's baked vs.
    editable, which sounds are whose, what was left out, how to delete the layers folder once the project is confirmed.
12. **Post it and look.** Ask for a phone screen recording of the posted video. If their phone's UI differs from the
    measured zones in `safe-zones.md`, re-measure once (10 minutes) and make the numbers theirs.

## Rules that make the edit good (defaults; a reference video overrides them)

- **Frame zero is the person + one line of text** (or the text popping in). The blurb is centred between the platform's
  top tabs and the head, not as high as it can go. A visual that supports the hook can pop in from ~1 s and can be big.
- **Nothing but footage in the platform's zones:** the top band (y<260), the right icon column (x>880 below y 930), the
  bottom block (y>1690), and 40 px off each side. Measured, not guessed (`safe-zones.md`).
- **Captions on every line, 2–4 words per cue, one keyword per cue in the highlight colour, ≤720 px wide, centred at
  x=500.** Cues come from the transcript, phrase by phrase, and never run into a section that speaks through its own
  typography.
- **Big single-word pops above the head** on the words that carry the line, auto-fit to the safe width. Never while a
  card already owns the headroom.
- **Cards look real** (the app, a Finder window, a code editor, a player window, a comments card, THEIR screen recording
  of the editor) with a soft shadow and a slight tilt. No clip-art, no mascots, no mock UI with invented numbers, and no
  drawn timeline when a real recording is one ask away.
- **The sandwich.** Pictures of the person and app cards go behind the head; word pops, serif words, the opening proof
  card (on the chest) and the paywall (headroom) go in front. Occlusion is binary: the cutout at full opacity, never a
  dimmed or soft-edged back card.
- **A look is not an overlay.** When the script names an aesthetic, re-grade the FOOTAGE itself (take and cutout, same
  function, same noise seed), restrained, and let its strength RAMP across the phrase so the viewer watches it happen.
  On at the word that names it, off at the first word of the next idea. One soft sound on the switch, not two.
- **The camera breathes.** Winning talking heads spend ~25% of the runtime in slow push-and-release zooms; hard punches
  are rarer and land on a joke or warning word with a treatment (two black-and-white frames). Keyframes, never baked.
- **Sound lands on the verb, from the editor's library.** Pop when a picture of them appears, click when a computer
  screen appears, a real typing recording when text is typed, a bell on a warm switch, a low swell on a moody one. About
  20 dB under the voice. Caption ticks on their own muted track. The music bed is theirs to add.
- **Nothing lingers past the next spoken beat.** Pop-ins 0.3 s, fades out 0.2–0.3 s.
- **Truth.** A number or a name on screen comes from somewhere real (the user's own stats, the actual file name, the
  actual folder, their real covers and view counts). If you don't have it, don't invent it; draw the card without it.

## What you deliver

`<video>-edit/` with `FINAL.mp4`, `SOUND_AUDITION.mp4` when sounds were chosen for them, `capcut_layers/` (every clip,
named `NN_<start>s_<what>`), `README.txt`, and the CapCut project named in the README. In the project: `take` (one clip
per cut, grades and flicker baked where they apply, 4K when available) · `back1..n` · `cutout` · `front1..n` · `blurb` +
`captions` (real text elements with the keyword range coloured) · `sfx` · `caption ticks`. Tell the user: quit and reopen
CapCut, select the caption clips and pick a heavy sans, add a music bed, export from CapCut. Once they confirm the
project is good, the layers folder (a duplicate of the project's own media) and the frames can be deleted.
