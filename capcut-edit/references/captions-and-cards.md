# Captions, pops and cards — the visual language

Learned from the reels that work in the "Claude edited this" niche: word-synced captions with one highlighted word, a
big single word popping above the head, and real-looking app windows floating in front of the person. It reads as "a
lot of editing went into this" while every piece stays a separate, editable clip.

## Captions
- Resolve cues against the Whisper transcript **by phrase, in order** (`CUES = [("the part you dread", "dread"), …]`).
  A cue starts on its first word's time and ends 0.02 s before the next cue, capped at 1.5 s.
- 2–4 words per cue. One keyword per cue in the highlight colour (default yellow `#F2CF4A`), the rest white. Heavy sans
  (Avenir Next Heavy on macOS), ~60 px, dark soft shadow + 2 px dark stroke, centred over the chest (y≈1500 on 1080×1920).
- Lowercase, except proper nouns (Claude, CapCut) and "I". Numbers stay numbers.
- Captions switch OFF inside a section that speaks through its own typography (the dark section's serif words).
- In the project each cue is a real text element (`add-text` + `text-style --shadow` + `text-ranges` for the keyword).
  The preview renders them with the real font; CapCut uses its default until the user picks a font for the track.

## Big word pops
- 150–200 px heavy sans, white or highlight colour, centred in the headroom (y≈470 when the head top is ≈600).
- In: scale 1.45→1.0 over 0.24 s with a Gaussian blur 16→0 px, alpha in 0.1 s. Out: fade 0.15 s. Hold ≈ the cue.
- Only on the words that carry the line ("Claude", "wrong", "can't edit it", "20 minutes", "not me"), and never while a
  card owns the headroom. Four to six per minute is the reference's density.

## Cards (all in front of the person, soft shadow, ±1–8° tilt, pop-in 0.32 s with a little overshoot, a slow wobble)
- **The app** (`chat_card`): light paper (#F5F1EA), a sidebar, the app's title line, then a scripted sequence by local
  time: a typed message · a "done" badge · a drop zone that receives the REAL file name · a slash command typed in ·
  a checklist with green checks · a spinner. Use it for "I asked", "drop your clips", "it's working", "send it back".
- **Code card** (`code_card`): dark editor with traffic lights, mono type, a highlighted header — the SKILL.md moment.
- **Finder window** (`finder_card`): the actual project folder's file names (Resources, Timelines, draft_info.json…);
  highlight the row that matters on its word.
- **Player window** (`player_card`): the flat mp4 that came back — a frame of the video, a burned-in caption with a
  typo circled, "one flat layer", a lock on "can't edit it", a cursor that clicks and gets a shake.
- **Phone cards** (`phone`): the user's own reels (real covers / counts) fanned at the sides of the head.
- **Thumbnail cards** (`yt_card`): other creators' videos on "everyone's doing this" — real thumbnails, titles under.
- **Comments card** (`comment_box`): a comment typed letter by letter, the send ripple on the verb.
- **Timeline card**: a long cluttered timeline that flies off screen on "hand it off".

## Where things go (1080×1920, chest-up talking head)
Measure first. In a 4K-cropped chest-up take the head top was at y≈600 and the face centre at (540, 1050): headroom is
y 200–600, captions at 1500, the bottom 200 px is the platform's caption zone, x>930 between y 1000–1600 is the icon
column. Big cards (900 px wide, 500–600 tall) centre at y≈520–600, so their bottom edge tucks behind/over the hair.
Side cards at x≈150 and x≈930, y≈700. The top 10% is a red zone; nothing starts above y 192.

## Sound
tap (pop-ins, one per item), click (cursor), pop (big words: noise transient + 240/120 Hz), sparkle (rising arpeggio),
bass (120→38 Hz sweep), whoosh (band-passed noise, sin² envelope), tick (typewriter letters). All synthesized.
