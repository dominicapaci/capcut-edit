# Motion — the breathing camera, punch-ins, and the flicker

## What winning talking heads actually do (measured, 2026-10)

A first research pass said "produced talking heads barely punch in". It was wrong: it used scene-change detection, which
only sees hard cuts. A slow 1.0→1.2 push over two seconds never trips it. Re-measured by registering the background
(the top third of the frame, Vision/OpenCV homography at 10 fps, so leaning toward the lens doesn't count):

| Reel | Hard punches | Slow push-ins | Slow pull-outs | Runtime in motion |
|---|---:|---:|---:|---:|
| the most produced one (22k likes) | 3 | 32 | 25 | 60% |
| the reference reel for this skill | 1 | 3 | 4 | 22% |
| a lo-fi phone-filmed one | 0 | 1 | 1 | 4% |
| a raw export, no edit | 0 | 0 | 0 | 2% |

**The pattern is a breathing camera**: a slow push to 1.10–1.30× over 0.8–1.9 s into the point, a short hold, then a pull
back out, often a little faster (0.5–1.0 s), once the point lands. Hard punches are a separate, rarer tool: 1.15–1.4× on
a joke or warning word, usually with a treatment (two black-and-white frames, a tint flash). Aim for ~25% of the runtime
in motion.

## In `render.py`

- `E.breath = [(start, peak_at, hold_until, back_by, scale), …]` — eased in (smoothstep), hold, eased out.
- `E.punch = [(a, b, scale)]` — instant hold, released after.
- `E.push = (a, b, scale)` — a slow creep across a whole section (a moody look).
- All three multiply into `E.scale(t)`; the take and the cutout get the same zoom; cards don't.
- **Crop from a 4K export** when you can (`E.video4k`, `frames4k/`): a 1.2× zoom then stays sharp at 1080. Ask the user to
  export 4K from CapCut; it's the same cut (verify with a PSNR compare, >35 dB means identical).
- In the CapCut project the zooms are **ease-in-out scale keyframes** on every take piece and the cutout (`zoom_keys` in
  `meta.json`; `build_project.py` writes them with `--easing ease-in-out`). A keyframe at a piece's end time belongs to
  the next piece.

## The flicker open (from a 19k-like cinematic reel)

It is not a brightness strobe. The room stays still while the PERSON toggles:

| frames at 30 fps | what shows |
|---|---|
| 0–3 | the empty room (a clean plate) |
| 4 | the person as an inverted negative over the room |
| 5–6 | normal |
| 7 | inverted |
| 8–11 | empty room |
| 12+ | normal, and the title pops |

A short static hiss with a click sits under it; the voice starts after. A callback later in the video (two frames of each
look, one inverted, then normal) ties the ending to the open.

- Inverted = `invert(rgb) * 0.45 + 140` inside the person mask (a washed white negative, not a hard invert).
- **The clean plate**: best is 2 s of the empty room filmed from the same spot (ask for it). Otherwise
  `scripts/plate.py` builds one: the median of mask-free pixels over the take (where the person moved reveals the wall),
  row-by-row interpolation for the wall and picture frames, inpainting for the rest. The part of a chair the person never
  leaves cannot be recovered; at flicker speed a drawn chair back reads fine, but say so in the README.
- Fit the plate to each opening frame on **edges** (Sobel + normalised correlation), never on raw colour: a flat wall
  matches at any zoom. If the opening has a zoom-out baked in, the plate has to follow it frame by frame.
- Implement as per-frame overrides in the take (`E.flicker = {frame: "P" | "I"}`), so the first take piece carries it
  baked and the project has a `_flicker` piece the user can drop.
