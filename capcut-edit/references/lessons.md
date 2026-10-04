# Lessons — everything that went wrong once

- **Straight alpha = halo.** CapCut reads ProRes 4444 as premultiplied. Multiply RGB by alpha before encoding every
  sticker and the cutout (`render.premul`). ffmpeg's `overlay` composites straight alpha, so the preview never shows it.
- **`-shortest` drops a frame.** Trimmed AAC is a hair shorter than n/30 s; 14 of 23 take pieces came back one frame
  short and the whole timeline ended 0.47 s early. Use `-af apad -t <n/fps>`.
- **Tile the take by frame counts**, not by the 10 ms-rounded start in a file name. CapCut's magnetic main track closes
  gaps on open and shifts everything after them.
- **A keyframe at a segment's end time belongs to the next segment.** Otherwise the noir push-in's start keyframe lands
  on the previous clip and the dark section holds at 1.07 the whole way.
- **Drawing with alpha 0 on a filled card punches a hole.** PIL draws, it doesn't blend; `eob(0)` is 2e-16 not 0, so
  `if p <= 0:` guards fail. Guard pops with `<= 0.01`. Symptom: a dark word showing through a white card.
- **`alpha_composite` refuses negative destinations.** Clamp with `max(0, …)` when a rotated prop can poke above a card.
- **Characters drawn for an older framing collide with the head.** Measure the head top on the contact sheet every time;
  shrink scenes about a pivot (`shrink(fn, 0.82, (540, 380))`) instead of redrawing them.
- **Reference beats adjectives.** The first edit of "cool girl / dark & mysterious" was a scrapbook of hand-drawn hearts
  and a condensed-caps noir, built from the words. The user's reference reel wanted captions + yellow keyword, big word
  pops and real app cards. Ask for a link before designing.
- **Cards in front vs. behind the head** is a taste call. The "edited by Claude" reels put them in front; a build
  walkthrough looks better sandwiched behind the person (needs the Vision mask). Ship the cutout either way.
- **The user's time estimates run early** ("around 5 seconds" was 6.4). Place on `words.txt`, never on the script.
- **Two sessions, one folder.** Before touching an edit folder, `stat` the make files; if something changed in the last
  hour that you didn't do, stop and ask.
- **Instagram/TikTok cover URLs expire** within hours. Download real covers the moment you find them.
- **`screencapture -x` works from the terminal** once Screen Recording is granted; use it to capture the real CapCut
  timeline for the "inside CapCut" card instead of drawing a mock.
