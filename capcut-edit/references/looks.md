# Looks — aesthetics that re-grade the footage itself

A look is applied to the take pieces AND the cutout with the same numpy function and the same per-frame noise seed, so
the person and the room shift together. It's on from the word that names it (lead 0.10 s) to the first word of the next
idea, with a flash or a black dip on the switch, its own typography, cards and sound. Two are built into `render.py`.

## Base (the whole video, outside any window)
`(a−128)×1.04+128` · saturation ×0.92 · R+3, B−3 · soft vignette (edges to ~84%). A mild film look; keep it subtle.

## Cool girl (the "aesthetic reels" reading: soft, creamy, gold serif, sparkles)
- Grade: `a×0.86+26` (lifted blacks) · R×1.04+7, G×1.01+3, B×0.95+1 (cream-gold cast) · saturation ×0.88 · halation
  (blurred highlights above 168, ×0.20) · soft edge fall-off · grain σ 4.
- Switch: white flash 0.3 s (alpha 0.92→0) + sparkle. Another flash + sparkle if the script "switches" again.
- Type: Didot Italic, lowercase, gold (#ECC45C) with a warm shadow and a gold glow, white four-point sparkles around it,
  a tracked-caps subline ("A E S T H E T I C   L I K E   T H I S") in cream. Twinkling stars across the frame.
- Cards: the user's own reels as phone cards at the sides of the head.
- The other reading ("editorial cool girl": black/white, bold condensed caps, red accent) exists; ask which one.

## Dark & mysterious (the "cinematic noir" reading)
- Grade: saturation ×0.30 · `(a−30)×1.18` · cold tint (R×0.94, B×1.06) · heavy vignette (edges to ~38%) · flicker
  `1+0.03·sin(2π·9.3t)+0.015·sin(2π·23t)` · grain σ 7 · slow push-in 1.00→1.06 over the window (scale keyframes).
- Switch: black dip 0.22 s + bass hit; white flash + whoosh on the way out. No letterbox bars (the reference had none).
- Type: huge Bodoni 72 Italic words (140–210 px), white with a soft shadow, sliding in from the right with a blur-in and
  drifting slowly left; tiny tracked caps beneath. Captions are off; the words ARE the captions.
- Dust: 60 slow-drifting motes at low alpha.
- The louder reading ("moodcore": scanlines, glitch, red accent) exists; ask which one.

## Writing a new look
Copy `grade_cool` or `grade_noir` in `render.py`, change the numbers, keep the noise seed per frame index. Give it a
switch sound, one type treatment, one card idea. Add its window to `take_pieces()` so the take gets split at the switch.
