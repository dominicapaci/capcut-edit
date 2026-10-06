# Learning a style from example videos

The most common ask: "here are 5–10 of my videos, edit like this" or "here are a few from a creator I love, edit like
that". Do not design from adjectives when examples exist. Study them, write the style down, confirm it, then edit.

## What the user says
- Their own style: "Go through these frame by frame to understand my style. Pay attention to everything: the camera
  angles, the font, when I cut the video, the sounds I use, everything. Ask any clarifying questions rather than assume,
  and if you need any more files or assets from me, let me know."
- Someone else's: the same, ending "…then edit my raw footage in that style."
Five to ten examples beats one: one video is a single edit, ten show what is constant.

## How to study each example (10 minutes for ten videos)
1. **Get the files.** Local files as given. Links: `yt-dlp` (Instagram needs `--cookies-from-browser chrome`). Put
   downloads in their own folder.
2. **Contact sheet + key frames.** `ffmpeg -i X.mp4 -vf "fps=2,scale=216:-1,tile=10x10" sheet.png`, Read it, then pull
   full-resolution frames wherever text or a graphic is on screen.
3. **Words.** `scripts/transcribe.py X.mp4 out/` so every observation is tied to the word it lands on.
4. **Captions and text.** Font family (serif / heavy sans / condensed / script), case, size as a fraction of frame width,
   position as a % of height, colours, one keyword highlighted or not, box / outline / shadow, how it animates in (pop,
   slide, blur-in, word by word), words per cue, how long each holds.
5. **Cuts.** `ffmpeg -i X.mp4 -vf "select='gt(scene,0.22)',showinfo" -f null -` gives hard cuts: seconds per cut, whether
   pauses are trimmed, whether they cut on the word.
6. **Zooms.** Scene detection cannot see a slow zoom. Register the background between frames (top third of the frame,
   homography) or track face size at 10 fps: count slow pushes, hard punches, how far, on which words (`motion.md`).
7. **Framing and colour.** Head position and headroom, shot sizes, whether the grade is warm / flat / contrasty, vignette,
   grain, whether a look changes mid-video.
8. **Graphics.** What appears (app windows, screenshots, B-roll cards, stickers, their own videos), in front of or behind
   the person, how big, how often something new enters the frame, what frame zero looks like.
9. **Sound.** Is there a music bed; where effects land (run an onset detector: 50 ms RMS jumps), what kind (pop, click,
   whoosh, riser, bell), how loud against the voice. For the user's own style, their sounds are in CapCut's cache
   (`scripts/capcut_sounds.py`, `sound.md`).

## Write the style down, then confirm it
Summarise what is CONSTANT across the examples as a one-page `style.md` next to the footage: captions, text, cuts, zooms,
colour, graphics, sound, opening, ending. List what varied and ask which way they want it. Ask every question you would
otherwise guess at (which font is that, do you want the same music, should cards sit behind you), and ask for any asset
you cannot source (their logo, a font file, their sound effects, covers of their own videos). Never copy another
creator's logo, face or branded assets into the edit; reproduce the techniques.

## Then edit
Translate `style.md` into `make.py` settings: caption size/position/colour and highlight, pop and card builders, the
grade, `E.breath` / `E.punch`, the sound map. Safe zones still apply even if the example ignored them (`safe-zones.md`).
When the user is happy, offer to save `style.md` into the skill folder as their default so the next video starts there.
