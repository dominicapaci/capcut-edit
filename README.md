# capcut-edit

A [Claude Code](https://claude.com/claude-code) skill that edits your talking-head video **and hands you back a CapCut
project**, not a flat mp4. Captions synced to every word with one keyword highlighted, placed where TikTok's buttons
aren't. Big word pops. Your own app windows and your own videos floating in front of you and behind your head. Two
restrained aesthetics you can switch into mid-sentence and watch ramp in. The slow breathing zooms the top talking heads
use. A flicker open. Sound effects from your own CapCut library, not synthesized ones. Every piece is its own clip or a
real text element, so when Claude gets one word wrong you fix it in CapCut in two seconds instead of re-prompting.

The secret is that a CapCut project is just files on your computer. Claude writes them.

This is the skill behind the "Claude edited this whole video" videos. If you got here by commenting **EDIT**: welcome.

## What you need

- macOS with **CapCut desktop** installed (tested on 9.2)
- [Claude Code](https://claude.com/claude-code)
- **ffmpeg** (`brew install ffmpeg`)
- **Python 3** with `pillow`, `numpy` and, for the flicker's empty-room plate, `opencv-python-headless`
  (`pip3 install pillow numpy opencv-python-headless`)
- **Node** and [capcut-cli](https://github.com/renezander030/capcut-cli): `npm i -g capcut-cli`
- a speech-to-text engine for word timestamps, one of: `pipx install mlx-whisper` (Apple Silicon, fast),
  `pip3 install faster-whisper`, or `pip3 install openai-whisper`
- for graphics *behind* your head and the flicker: Xcode command-line tools (`xcode-select --install`) so the
  person-mask tool compiles

## Install

**Easiest:** open Claude Code and paste this:

```
Install the skill from https://github.com/dominicapaci/capcut-edit into my ~/.claude/skills folder
```

**Or in your terminal:**

```bash
git clone https://github.com/dominicapaci/capcut-edit.git
cp -r capcut-edit/capcut-edit ~/.claude/skills/
```

Restart Claude Code and it's available.

## Use

Put your raw take (one long recording, bad takes and all) in a folder, open Claude Code there, and say what you want:

```
Edit this into a CapCut project. Captions with the keyword in yellow, big word pops, my best four videos
orbiting my head, and when I say "aesthetic" warm the whole look up, then "moody" when I say it.
```

Or, if you already cut the take in CapCut yourself:

```
I cut this in CapCut (project "1004"). Here's the 4K export too. Edit it from my cut points
and give me back a CapCut project.
```

Claude will ask a few things (raw or pre-cut, what it should feel like, ideally a link to a video you like, which
sounds you already use in CapCut, and a 10-second screen recording of your timeline if the video shows the editor),
then: cut the take on the words, transcribe it, plan the graphics on a contact sheet with the platform's no-go zones
drawn in, render every layer, write the CapCut project, and leave you a `README.txt` with the placement table. Quit and
reopen CapCut; the project is in your list.

Changed your mind about a sound? That's a two-second remix, the picture never re-renders. New opening line? Thirty seconds.

## What you get back

```
<your video>-edit/
  FINAL.mp4            the finished video (post this, or export from CapCut after your tweaks)
  SOUND_AUDITION.mp4   every candidate sound played twice with its name, so you can swap by ear
  capcut_layers/       every clip: take pieces, graphics as ProRes 4444 alpha, sound
  README.txt           what happens on which word, the zooms, the looks, what's baked, what's editable
```

and a CapCut project with tracks: `take` (one clip per cut, 4K when you gave one) · `back1..n` (behind your head) ·
`cutout` (you) · `front1..n` (every graphic in front) · `blurb` and `captions` (real text elements, the keyword already
coloured) · `sfx` · `caption ticks` (muted by default). Zooms are eased keyframes. Select the caption clips and pick a
heavy sans font once; CapCut uses its default until you do. Add a music bed; every performing reel has one.

## What's inside

```
capcut-edit/
  SKILL.md                      the instructions Claude follows
  references/capcut-cli.md      the exact capcut-cli recipe that opens in CapCut, and the gotchas
  references/safe-zones.md      TikTok's UI measured in video pixels: where nothing may go, and how to measure yours
  references/captions-and-cards.md   the visual language: cues, keyword, pops, the cards, the sandwich, the orbit
  references/looks.md           the two restrained aesthetics (and the two louder ones) as grade numbers + type + sound
  references/motion.md          the breathing camera (measured on top reels), punch-ins, the flicker open
  references/sound.md           use your own CapCut library sounds; pop vs click; typing; levels; the sound-only remix
  references/lessons.md         everything that went wrong once
  scripts/transcribe.py         word timestamps (mlx-whisper / faster-whisper / whisper)
  scripts/cutplan.py            raw take → tight cut (audio-envelope pause trim), or rebuild a CapCut draft's cut
  scripts/segbatch.swift        macOS Vision person masks (for graphics behind you and the flicker)
  scripts/plate.py              an empty-room plate for the flicker, from the take itself
  scripts/capcut_sounds.py      lists the sounds CapCut has cached on your Mac, with the names from your old projects
  scripts/render.py             the rendering library: cards, captions, pops, looks, zooms, flicker, sound, ProRes alpha, the Edit class
  scripts/build_project.py      capcut_layers/ → a CapCut project (eased zoom keyframes, back/front tracks)
  scripts/fill_project.py       re-adds clips CapCut dropped while it was open
  scripts/example_make.py       a worked per-video plan to copy
```

## Honest limits

- macOS + CapCut desktop only. The project writer relies on capcut-cli's CapCut 9.x support.
- Claude's first pass is a draft. Look at the check sheet, say what's off, it re-renders. Timing is driven by the
  transcript, so a mumbled word can land a graphic a beat late; nudge it in CapCut.
- The safe zones were measured on one iPhone in the TikTok feed. Yours may differ by a few pixels; the reference
  explains how to measure them in ten minutes.
- The flicker's empty room is rebuilt from your footage; the part of your chair you never move away from is inpainted.
  Two seconds of the empty room filmed from the same spot fixes that.
- Captions in the project use CapCut's default font until you pick one. The preview shows the intended look.
- It never invents numbers, names or prices for a card. If you want a stat on screen, give it a real one.
- Sounds come from what CapCut has already cached on your Mac. Preview a sound and press + once to make it available.
- The project keeps its own copy of every clip (about 1 GB for a 45-second edit). Delete the layers folder afterwards.

## Credits

[capcut-cli](https://github.com/renezander030/capcut-cli) by renezander030 does the writing into CapCut.
Word timestamps via [mlx-whisper](https://github.com/ml-explore/mlx-examples) or faster-whisper. The flicker is Kalyl's
(instagram.com/kalylsfilms); the visual language follows Marc Cleroux's reels. MIT licensed.
