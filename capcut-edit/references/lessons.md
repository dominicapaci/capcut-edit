# Lessons — everything that went wrong once

## Rendering
- **Straight alpha = halo.** CapCut reads ProRes 4444 as premultiplied. Multiply RGB by alpha before encoding every
  sticker and the cutout (`render.premul`). ffmpeg's `overlay` composites straight alpha, so the preview never shows it.
- **`-shortest` drops a frame.** Trimmed AAC is a hair shorter than n/30 s; 14 of 23 take pieces came back one frame
  short and the whole timeline ended 0.47 s early. Use `-af apad -t <n/fps>`.
- **Tile the take by frame counts**, not by the 10 ms-rounded start in a file name. CapCut's magnetic main track closes
  gaps on open and shifts everything after them.
- **Drawing with alpha 0 on a filled card punches a hole.** PIL draws, it doesn't blend; `eob(0)` is 2e-16 not 0, so
  `if p <= 0:` guards fail. Guard pops with `<= 0.01`. Symptom: a dark word showing through a white card.
- **`alpha_composite` refuses negative destinations.** Clamp with `max(0, …)` when a rotated prop can poke above a card.
- **A glow colour needs an alpha channel.** `Region.glow(..., col=(40, 26, 10))` crashes inside `A()`; pass 4-tuples.
- **Placing a full-frame image "at a point" moves it off screen.** `classic_box` returns a full 1080×1920 layer; crop to
  `getbbox()` before `place()`-ing it with a scale (the popping blurb was invisible for one render because of this).
- **A sound-only or opening-only change must not re-render the video.** `make.py sound` remuxes with `-c:v copy` (2 s);
  `make.py head` re-renders only the frames up to the blurb's end and concatenates (30 s). A full render is 3 min for 44 s.
- **Zoom from the 4K export.** A 1.2× punch cropped from 1080 goes soft; the same cut exported at 4K is identical (check
  with a PSNR compare, >35 dB) and keeps the zooms sharp.

## Measuring instead of guessing
- **Scene-change detection cannot see a slow zoom.** The first research pass concluded winners "barely punch in". Register
  the background between frames (top third, homography) to measure zooms; face size alone is fooled by leaning in.
- **Colour matching finds a flat wall at any zoom.** Fit a plate or a frame on edges (Sobel + normalised correlation).
- **Measure the platform UI from a phone screen recording**, by template-matching a rendered frame into it. "Top 10% is a
  red zone" was a guess; the real zones are in `safe-zones.md` and the save button sat exactly where the captions were.
- **The user's time estimates run early** ("around 5 seconds" was 6.4). Place on `words.txt`, never on the script.

## Taste calls that are now rules
- **Reference beats adjectives.** Ask for a link before designing. The first "cool girl / dark" edit built from the words
  was a scrapbook of hand-drawn hearts; the reference wanted captions + yellow keyword, word pops, real app cards.
- **Restrained looks.** Halve every departure from the base grade (see `looks.md`).
- **If it's behind them, it's behind them.** No dimmed or soft-edged back cards; full-opacity cutout.
- **Cards go behind by default** when the person films with headroom; the opening proof card and the paywall go in front.
- **Real screen footage** for an editor-timeline card, never a drawing; ask for a screen recording.
- **Sounds from the editor's library, never synthesized** (`sound.md`); pop for pictures of the person, click only for
  computer-screen footage, one bell per look switch, typing = a real typing recording.
- **Captions ≤ 720 px wide, centred at x=500**; pops and serif words auto-fit. Blurb centred under the top tabs.

## capcut-cli and the app
- **A keyframe at a segment's end time belongs to the next segment.** Otherwise the push-in's start keyframe lands on the
  previous clip and the section holds at the peak the whole way.
- **Projects keep their own copies of every media file** in `<project>/assets/` (~1 GB for a 44 s edit) and reference
  those, not your layers folder. Overwriting a layer file on disk does NOT reach the project: copy the new file into
  `assets/<type>/` with the same name (`make.py sound` does). Once built, the layers folder is a duplicate you can delete.
- **Segments can vanish mid-build while CapCut is open** with a sibling project loaded (5 of 29 clips survived one build).
  Verify with `capcut segments` after every build and run `scripts/fill_project.py "<name>"`, which adds every missing
  02_/04_ clip idempotently and re-checks each one right after adding it.
- **Never write into a draft the user made.** If you must retry, delete your own folder AND its entry in
  `root_meta_info.json` (`all_draft_store` + `draft_ids`), back that file up first.
- **Previewing a library sound only streams it.** It's on disk only once added to a timeline (press **+**), then it's the
  newest file in `Cache/music`. The cached copy can be a shortened preview of the full sound.
- **Scripted clicking into CapCut needs accessibility permission** for the terminal, and the app may have no window on the
  current desktop. Don't fight it: ask for a screen recording.
- **The screen-recording file name has a narrow no-break space** before AM/PM. Find it with `find … -name "Screen Recording 2026*"`
  and `-exec cp`, never by typing the path.

## Working with the person
- **Cards in front vs. behind the head** is their call; ask once, then make it a rule for that creator.
- **Two sessions, one folder.** Before touching an edit folder, `stat` the make files; if something changed in the last
  hour that you didn't do, stop and ask.
- **Instagram/TikTok cover URLs expire** within hours. Download real covers the moment you find them; a thumbnail can be a
  bad frame (a ceiling), so grab a frame from the video itself if it is.
- **Disk space.** Frames + masks + a 4K copy + layers + the project's own copy is ~4 GB per edit. After the project is
  confirmed good, delete the layers folder and the superseded projects (via `root_meta_info.json`), keep frames only
  while visual tweaks are still coming.
