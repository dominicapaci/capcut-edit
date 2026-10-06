# Looks — aesthetics that re-grade the footage itself

A look is applied to the take pieces AND the cutout with the same numpy function and the same per-frame noise seed, so
the person and the room shift together. It's on from the word that names it (lead 0.10 s) to the first word of the next
idea, with a flash or a dip on the switch, its own typography, cards and sound. Four are built into `render.py`: the two
**restrained** ones below are the defaults (`grade_soft`, `grade_moody`); the two louder ones at the bottom are kept for
reference (`grade_cool`, `grade_noir`).

## Base (the whole video, outside any window)
`(a−128)×1.04+128` · saturation ×0.92 · R+3, B−3 · soft vignette (edges to ~84%). A mild film look; keep it subtle.

## Soft & warm (default; from the reference reel's "cool girl")
- Grade: `a×(1−0.05k)+12k` · R+9k, G+3k, B−7k · saturation ×(1−0.05k), where k is the look's strength 0–1.
- **Let the viewer watch it happen.** Switch on at k=0.35 on the word that names it and RAMP k to 1 across the next
  phrase ("watch the whole thing warm up"): the grade visibly warms while they say it. `E.windows["soft"] = (a, b)` plus
  `E.ramps["soft"] = (ramp_start, ramp_end)`.
- Switch sound: one short bell. Nothing on the title that follows.
- Type: one gold Didot-italic word, lowercase (`serif_title`), with a DARK glow behind it (40,26,10 @150, blur 40) or it
  washes out on a bright ceiling; two or three small white four-point sparkles, no more; a tracked-caps subline.
- Cards: the user's own reels as phone cards; a magazine masthead on "like a magazine cover" (Didot caps, two gold rules,
  a gold italic cover line, tiny tracked caps), kept inside y 280–600.
- Captions stay on.

## Moody (default; from the reference reel's "cool dude")
- Grade: exposure `×(1−0.16k)` · contrast `(a−90)×(1+0.10k)+90` · saturation ×(1−0.32k) · a touch cold (R×0.97, B×1.03)
  · vignette a little deeper. Still colour, still the room.
- Switch: a soft dip (black, 0.55 peak, 0.3 s) + a low swell. k=0.5 on the word, ramps to 1 on "drop" (the colour visibly
  drops on the word).
- Type: huge white Bodoni-italic words sliding in from the right with a blur-in, drifting slowly (`serif_slide`), tiny
  tracked caps beneath. They sit on the chest (y≈1470) in a close-up and alternate with cards there; one-liners can go
  in the headroom (y≈420). Captions are OFF: the words are the captions. Auto-fit to 790 px so they clear the icon column.
- A warning word ("wrong") gets two black-and-white frames (`E.bw = (a, b)`) + a hard punch. A slow 1.00→1.07 creep across
  the whole look (`E.push`).
- No flicker, no grain, no heavy vignette, no letterbox bars, no dust in this version.

## Writing a new look
Copy a grade function in `render.py`, change the numbers, keep the noise seed per frame index, give it a strength `k`
so it can ramp. Give it one switch sound, one type treatment, one card idea. Add its window to `E.windows` so the take
gets split at the switch. Halve every departure from the base grade before you show it.

## Keep looks restrained (lesson, 2026-10-04)
The first pass of the two looks below read as "way too over the top, no one actually uses those in real life." What real
creators use is subtler: a light warm lift with one serif-italic word and a couple of sparkles; a moody pass that only
pulls exposure and saturation down a little and lets big white serif words carry the mood. Never put a scrapbook of
doodles or a black-and-white crush on a talking head unless the reference video does.

## Reference only — the louder readings

**Cool girl, scrapbook reading** (`grade_cool`): `a×0.86+26` (lifted blacks) · R×1.04+7, G×1.01+3, B×0.95+1 ·
saturation ×0.88 · halation (blurred highlights above 168, ×0.20) · grain σ 4; white flash + sparkle on the switch; Didot
Italic gold title with a glow and twinkles across the frame; Polaroids and doodles.

**Dark & mysterious, cinematic-noir reading** (`grade_noir`): saturation ×0.30 · `(a−30)×1.18` · cold tint · heavy
vignette (edges to ~38%) · flicker `1+0.03·sin(2π·9.3t)+0.015·sin(2π·23t)` · grain σ 7 · 60 drifting dust motes; black
dip + bass on the way in, white flash + whoosh on the way out.
