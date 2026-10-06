# Captions, pops and cards — the visual language

Learned from the reels that work in the "Claude edited this" niche: word-synced captions with one highlighted word, a
big single word popping above the head, and real-looking app windows floating around the person. It reads as "a lot of
editing went into this" while every piece stays a separate, editable clip. Placement obeys `safe-zones.md`.

## Captions
- Resolve cues against the Whisper transcript **by phrase, in order** (`CUES = [("the part you dread", "dread"), …]`).
  A cue starts on its first word's time and ends 0.02 s before the next cue, capped at 1.5–1.6 s.
- 2–4 words per cue. One keyword per cue in the highlight colour (default yellow `#F2CF4A`), the rest white. Heavy sans
  (Avenir Next Heavy on macOS), ~58–60 px, dark soft shadow + 2 px dark stroke.
- **Centred at x=500, max 720 px wide, two lines max** (`captions(cuelist, dur, cx=500, maxw=720)`): the save and
  comment buttons sit at x>880 from y 930 down, and 940-px captions ran straight into them.
- Lowercase, except proper nouns (Claude, CapCut) and "I". Numbers stay numbers.
- Captions switch OFF inside a section that speaks through its own typography (the moody section's serif words).
- In the project each cue is a real text element (`add-text` + `text-style --shadow` + `text-ranges` for the keyword).
  The preview renders them with the real font; CapCut uses its default until the user picks a font for the track.

## The opening blurb
One line in the classic white box, on from frame zero (or popping in: `classic_pop`), centred between the platform's top
tabs and the top of the head (y≈415 on a chest-up framing). Its job is to say what the video gives them, in plain words.

## Big word pops
- 150–200 px heavy sans, white or highlight colour, in the headroom (y≈430 when the head top is ≈600).
- In: scale 1.45→1.0 over 0.24 s with a Gaussian blur 16→0 px, alpha in 0.1 s. Out: fade 0.15 s. Hold ≈ the cue.
- **Auto-fit** (`bigword(..., maxw=860)`): the font shrinks so the word never runs off the cropped sides.
- Only on the words that carry the line ("Claude", "wrong", "20 minutes", "one sentence"), and never while a card owns
  the headroom. Four to six per minute is the reference's density.

## Behind or in front: the sandwich
`take → back cards → the person's cutout → front cards`. Creators who film with headroom film it so things can sit behind
their head. Defaults, confirmed on a real post:
- **Behind the head (layer="back"):** the person's own reels (the back pair of the orbit), a Claude/app card with a
  checklist, a before/after of their own frames. **Occlusion is binary.** The cutout goes on at full opacity everywhere
  (mask cut at 60, grown 1 px, blur 0.7); never dim or fade a back card "for depth": it reads as see-through, and the
  user will say "if it's behind me, it's behind me."
- **In front (layer="front"):** word pops, serif words, the front pair of reels over the chest, a timeline/player card low
  on the chest (x≈470), a paywall or comments card in the headroom at 0.8 scale, flashes, sparkles.
- The opening proof card (the editor timeline) goes in FRONT on the chest, just above the captions, not behind the head.

## Cards (soft shadow, ±1–8° tilt, pop-in 0.32 s with a little overshoot, a slow wobble)
- **The app** (`chat_card`): light paper (#F5F1EA), a sidebar, the app's title line, then a scripted sequence by local
  time: a typed message · a "done" badge · a drop zone that receives the REAL file name · a slash command typed in ·
  a checklist with green checks · a spinner. Use it for "I asked", "drop your clips", "it's working", "send it back".
- **Code card** (`code_card`): dark editor with traffic lights, mono type, a highlighted header.
- **Finder window** (`finder_card`): the actual project folder's file names; highlight the row that matters on its word.
- **Player window** (`player_card`): the flat mp4 that came back, a frame of the video, "one flat file", a lock on
  "that's it". Width 760 so it clears the icon column.
- **The editor timeline** (`screen_card`): **real footage**, never a drawing. The user screen-records their CapCut
  project (10 s is plenty); crop the timeline band (on a 1264×976 window recording that's y 340–870) to
  `capture/<name>/%05d.jpg` at 30 fps and the card plays it. Scripted clicking into CapCut is blocked by macOS accessibility
  permissions and CapCut may not even have a window on the current desktop: ask for the recording instead.
- **Phone cards / the orbit** (`phone`, `reel_orbit`): four of the user's own videos (real covers, real view counts,
  `make_reel_card`) on a slow merry-go-round round the head: the two with z<0 render into the back layer, the two with
  z≥0 into the front layer, 24°/s, front pair over the chest (orbit centre y≈1040, rx 250, ry 250), back pair peeking
  out behind the head. One pop per card as they float in.
- **Before/after** (`before_after`): the raw frame and the edited frame as two tiles (270×480) behind the head, labels
  and an arrow ABOVE them so they stay visible; keep it up until the next section starts.
- **Thumbnail cards** (`yt_card`): other creators' videos on "everyone's doing this", real thumbnails, 340 wide, inside
  x 100–860.
- **Comments card** (`comment_box`): a comment typed letter by letter, the send ripple on the verb.
- **Paywall card** (`paywall_card`): the lock row at the TOP of the card so it stays visible; unlocks on "not".

## Where things go (1080×1920, chest-up talking head)
Measure the head top on the contact sheet first. In a 4K-cropped chest-up take the head top was at y≈600 and the face
centre at (540, 850) wide, (513, 840) close. Headroom is y 260–600. Captions at 1500. Big back cards (900 px wide, 600
tall) centre at y≈600 so their top third shows above the hair. Low front cards centre at (470, 1400). Nothing above y 260,
nothing right of x 880 below y 930, nothing below y 1690, nothing within 40 px of the sides.

## Text systems that win (from 21 top editing-style reels)
Two systems: (1) big keyword + small phrase (keyword 40–80% of frame width in heavy caps or an editorial serif, the rest
small), or (2) one word at a time at 10–18% width. Text stays off the face: chest (y 45–60%) or top third. Pop-ins scale
over 3–5 frames; cards hold 1–2 s. Something new enters the frame every 1–2 s even with a locked camera.
