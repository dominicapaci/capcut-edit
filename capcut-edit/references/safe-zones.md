# Safe zones — where the platform UI sits on top of your video (measured, not guessed)

TikTok, Reels and Shorts draw their UI over the video. Anything you put there is covered or cropped. The first
version of a real edit was posted to TikTok and screen-recorded on the phone; the overlay was then measured by matching
a rendered frame into that recording. Numbers below are for a 1080×1920 video on an iPhone in the TikTok feed. Instagram
and YouTube are close but not identical; measure once per platform the same way (see the bottom of this file).

TikTok fills the feed height with the 9:16 video and **crops about 40 px off each side**.

| Zone | Video px (1080×1920) | What lives there |
|---|---|---|
| Top band | y < 260 | status bar, LIVE, Following / For You (underline at y≈237), search |
| Right column | x > 880, from y 930 to 1900 | avatar (970–1087), like (1149), comment (1310), save (1472), share (1641), sound disc (1802–1881) |
| Bottom block | y > 1690, full width | username (1720), caption (1802), sound line (1857–1888); the tab bar starts at 1919 |
| Side crop | x < 40 and x > 1040 | simply off screen on the phone |

## The rules that follow (defaults in `render.py`)

- **Nothing but the footage in those zones.** No caption, card, word pop, title or sticker touches them.
- **Captions:** centred at x=500, max 720 px wide (so x 140–860), two lines max, at y≈1500. A 940-px caption hits the
  save button. `captions(..., cx=500, maxw=720)`.
- **Word pops and serif words** auto-shrink to fit: pops inside x 60–1020 (they live above y 930), serif words max 790 px
  wide centred at x=470 (they live on the chest, next to the right column).
- **Cards** that sit low (a timeline, a player window) centre at x≈470 so their right edge stays under 880.
- **The opening blurb** is centred between the For You underline (y 237) and the top of the person's head on the opening
  framing. With the head top at y≈600 that's y≈415. "As high as possible" puts it under the Following / For You tabs.
- **The check sheet draws the zones** (`make.py check` tints them red). Look at every tile against them before rendering.

## Measure it yourself (10 minutes)

1. Post the first render (or a private/friends-only post), open it in the app, screen-record the phone for 10 s.
2. Pull one frame of the recording and one rendered frame of the video at the same moment (`ffmpeg -ss T -frames:v 1`).
3. Find where the video sits inside the recording: template-match a UI-free band of the rendered frame (the middle 40%)
   against the recording at a range of scales (`cv2.matchTemplate`, TM_CCOEFF_NORMED). The best match gives the drawn
   width and offset; a score above 0.9 means it's right. Don't match on a flat wall: colour matching "finds" a flat wall at
   any scale. Match on edges or on a band with real content.
4. Read the UI element positions off a 4× enlarged recording frame with a grid, convert with the scale/offset, write them
   into this table. Apply as defaults.
