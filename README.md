# capcut-edit

A [Claude Code](https://claude.com/claude-code) skill that edits your talking-head video **and hands you back a CapCut
project**, not a flat mp4. Captions synced to every word with one keyword highlighted, big word pops, app windows and
file cards floating in front of you, two aesthetics you can switch into mid-sentence ("cool girl", "dark & mysterious"),
punch-ins, sound effects. Every piece is its own clip or a real text element, so when Claude gets one word wrong you fix
it in CapCut in two seconds instead of re-prompting.

The secret is that a CapCut project is just files on your computer. Claude writes them.

This is the skill behind the "Claude edited this whole video" videos. If you got here by commenting **EDIT**: welcome.

## What you need

- macOS with **CapCut desktop** installed (tested on 9.2)
- [Claude Code](https://claude.com/claude-code)
- **ffmpeg** (`brew install ffmpeg`)
- **Python 3** with `pillow` and `numpy` (`pip3 install pillow numpy`)
- **Node** and [capcut-cli](https://github.com/renezander030/capcut-cli): `npm i -g capcut-cli`
- a speech-to-text engine for word timestamps, one of: `pipx install mlx-whisper` (Apple Silicon, fast),
  `pip3 install faster-whisper`, or `pip3 install openai-whisper`
- optional, for graphics *behind* your head: Xcode command-line tools (`xcode-select --install`) so the person-mask tool compiles

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
Edit this into a CapCut project. Captions with the keyword in yellow, big word pops,
and when I say "cool girl" switch the whole look, then "dark and mysterious".
```

Or, if you already cut the take in CapCut yourself:

```
I cut this in CapCut (project "1003"). Edit it from my cut points and give me back a CapCut project.
```

Claude will ask two things (raw or pre-cut, and what it should feel like, ideally a link to a video you like), then:
cut the take on the words, transcribe it, plan the graphics on a contact sheet, render every layer, write the CapCut
project, and leave you a `README.txt` with the placement table. Quit and reopen CapCut; the project is in your list.

## What you get back

```
<your video>-edit/
  PREVIEW.mp4          the whole edit flattened, for a quick watch
  capcut_layers/       every clip: take pieces, graphics as ProRes 4444 alpha, sound
  README.txt           what happens on which word, what's baked, what's editable
```

and a CapCut project with tracks: `take` (one clip per cut) · `front1..n` (every graphic) · `blurb` and `captions`
(real text elements, the keyword already coloured) · `sfx`. Punch-ins are keyframes. Select the caption clips and pick a
heavy sans font once; CapCut uses its default until you do.

## What's inside

```
capcut-edit/
  SKILL.md                      the instructions Claude follows
  references/capcut-cli.md      the exact capcut-cli recipe that opens in CapCut, and the gotchas
  references/captions-and-cards.md   the visual language: cues, keyword, pops, the cards
  references/looks.md           the two aesthetics as grade numbers + type + sound
  references/lessons.md         everything that went wrong once
  scripts/transcribe.py         word timestamps (mlx-whisper / faster-whisper / whisper)
  scripts/cutplan.py            raw take → tight cut (audio-envelope pause trim), or rebuild a CapCut draft's cut
  scripts/segbatch.swift        macOS Vision person masks (for graphics behind you)
  scripts/render.py             the rendering library: cards, captions, pops, looks, sound, ProRes alpha, the Edit class
  scripts/build_project.py      capcut_layers/ → a CapCut project
  scripts/example_make.py       a worked per-video plan to copy
```

## Honest limits

- macOS + CapCut desktop only. The project writer relies on capcut-cli's CapCut 9.x support.
- Claude's first pass is a draft. Look at the check sheet, say what's off, it re-renders. Timing is driven by the
  transcript, so a mumbled word can land a graphic a beat late; nudge it in CapCut.
- Captions in the project use CapCut's default font until you pick one. The preview shows the intended look.
- It never invents numbers, names or prices for a card. If you want a stat on screen, give it a real one.

## Credits

[capcut-cli](https://github.com/renezander030/capcut-cli) by renezander030 does the writing into CapCut.
Word timestamps via [mlx-whisper](https://github.com/ml-explore/mlx-examples) or faster-whisper. MIT licensed.
