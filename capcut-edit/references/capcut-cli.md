# capcut-cli — the backdoor, and the exact recipe that opens in CapCut

A CapCut project is a folder in `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/<name>/` (macOS). Its timeline is
JSON: `draft_content.json` (canonical), mirrored in `draft_info.json` and `template-2.tmp`. The desktop app lists drafts
from `root_meta_info.json` next to those folders. [capcut-cli](https://github.com/renezander030/capcut-cli) (npm, MIT,
unofficial) reads and writes all of that. Install: `npm i -g capcut-cli` (proven with 0.27 on CapCut 9.2 Mac).

## The recipe (proven 2026-10-03)

```bash
capcut init "My edit" --template auto --ratio 9:16 --force-write           # auto = seed from your newest app-made draft
capcut add-video "$P" take_01.mp4 0s 3.000000s --track-name take --force-write
capcut add-video "$P" card.mov 1.00s 2.90s --track-name front1 --force-write # ProRes 4444 alpha, premultiplied
capcut add-audio "$P" sfx.wav 0s 57.63s --track-name sfx --volume 1.0 --force-write
capcut add-text  "$P" 0s 3.90s "Claude edited this whole video" --font-size 10 --color "#111113" --x 0 --y 0.66 --track-name blurb --force-write
capcut text-style "$P" <id> --bg-color "#FFFFFF" --bg-alpha 1 --bg-round-radius 0.25 --no-shadow --force-write   # the classic white box
capcut text-ranges "$P" <id> --styles '[{"start":4,"end":16,"font_color":"#F2CF4A","bold":true}]' --force-write  # the yellow keyword
capcut keyframe "$P" <segment id> scale 0.5s 1.12 --force-write           # time is RELATIVE to the segment start
capcut register "$P" --apply --materials --force-write                     # or CapCut 9.1+ shows "file inaccessible"
capcut sync-timelines "$P" --nested --apply --force-write
capcut lint "$P" --fix --force-write -H
```

Then **quit and reopen CapCut.** `--force-write` is required while CapCut is running. `$P` is the draft folder path.

## Facts you need

- `capcut segments "$P" --track video` → JSON with `id`, `start_us`, `duration_us`, `label` (the file name). Match
  segments by label. `capcut segment "$P" <id>` shows `_track_name`, `clip.transform`, `common_keyframes`.
- Text position: `--x/--y` run −1..1, **y positive = up**. A caption over the chest of a 1080×1920 frame at y=1500 is
  `--y -0.56`. A box above the head at y=330 is `--y 0.66`. Font size 15 at scale 0.93 ≈ 50 px text; 9–10 for captions.
- `text-ranges` start/end are character indices into the text; gaps keep the base style.
- Keyframe times are stored verbatim as the segment-relative `time_offset`. For a hold, write the value at t−1 frame,
  the new value at t, and back at the end (+1 frame); CapCut interpolates linearly over that one frame.
- A keyframe at exactly a segment's end time belongs to the NEXT segment. Compare with `t < end − 1e-4`.
- `add-video` probes width/height with ffprobe; 1080×1920 clips land 1:1 on a 9:16 canvas. Alpha clips must be
  **premultiplied** (RGB × alpha before encoding) or CapCut draws a halo on every soft edge.
- The main (`take`) track is magnetic. Tile it from each clip's REAL frame count (`ffprobe -count_frames`), never from
  rounded file names, or CapCut closes the ms gaps on open and drifts every later clip. Lint's `main-track-gap` warning
  about −0.001 ms is µs rounding and harmless; 3–7 ms gaps are not.
- Never write into a draft the user made. `init` a new one; if you must retry, delete your own folder AND its entry in
  `root_meta_info.json` (`all_draft_store` + `draft_ids`), back that file up first.
- `capcut render` makes a proxy of the main track only — fine for a sanity check, not for a preview with graphics.
- Useful extras: `detect-silence`, `detect-retakes --srt` (keep the later take), `transition <id> <slug>`,
  `text-anim <id> --intro pop-up`, `trim <id> <src-start> <duration>`, `restore` (undo a write).
