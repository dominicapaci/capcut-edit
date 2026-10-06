# Sound — use the editor's own library, and follow three rules

Two rounds of synthesized sound effects (noise bursts for static, filtered noise for whooshes, sine pops) were rejected
by a real creator as "absolutely horrible and hard on the ears", then "still so bad". Synthesized SFX read as cheap on a
phone speaker. Real library sounds are what every performing reel uses. So:

## Rule 1 — use CapCut's own library sounds, never synthesize

CapCut caches every library sound the user has previewed-and-added or used, as
`~/Movies/CapCut/User Data/Cache/music/<md5>.mp3` (macOS). Short files there (< 4 s) are sound effects; long ones are
music. Their names are recoverable from the user's old drafts: each `draft_content.json` lists
`materials.audios[].name` with a `path` containing the md5. `scripts/capcut_sounds.py` does both (lists the cache with
names, durations and a rough character: attack, brightness, noisiness).

- Ask the user which sounds they already use (the names repeat across their projects: those are their taste).
- Previewing a sound in CapCut only streams it. It lands on disk only when added to a timeline. If the user wants a
  specific sound you don't have, ask them to press **+** on it in any project; the file appears in the cache within a
  second (newest `.mp3`); then they can delete the clip.
- Load them with `snd_file(path)` in `render.py` (any sample rate, mono-summed, peak-normalised, optional trim/fade) and
  map roles with `SND = {...}`. Keep the synthesized functions only as a last resort when there is no library at all.
- The cached copy can be a short preview of a longer sound (a 4 s "typing" came down as 1.8 s with 0.26 s of actual
  keystrokes). Slice what's there (`slice_transients`) and sequence the slices; it's still the real sound.

## Rule 2 — what sounds on what

- **A picture of the person appears** (their own reels as phone cards, a frame of their take in a before/after): a **pop**.
- **A recording of a computer screen appears** (an editor timeline, an app window, a player window, a web card, a comments
  box): a **click**. Not a pop.
- **Typed text** (a slash command, a comment being typed): a keyboard sound, one keystroke per character, from a real
  typing recording (slice and sequence it; never a tick per letter from a click sound).
- **A look switch**: one soft sound (a short bell for a warm look, a low swell for a moody one). One, not two. Nothing
  on the title that follows it.
- **Word pops** keep a pop. **A warning word** ("wrong") gets one low hit.
- **Caption changes**: a tick is what the research shows winners doing, but creators hear it as noise on their own voice.
  Render the ticks to their own wav (`06_*_caption-ticks.wav`), put it on its own track in the project, and leave it OUT
  of the flattened mp4. The user can turn it on.

## Rule 3 — levels

Peak-normalise every sample, then gain 0.16–0.55 per role before the 0.4 master scale: that puts effects about 20 dB
under the voice. The mix's own peak should land around −13 dBFS; the finished file with voice around −4 dBFS peak.

## What the research says (21 top editing-style reels, 2026-10)

Every performing talking-head reel has a continuous music bed and something audible every 0.6–1.3 s: a soft tick on
caption swaps, a pop per sticker, a whoosh on a card or section change. Big hits are saved for frame 0, section switches
and the CTA. Sticker sounds sit under the voice; only transitions sit at voice level. The music bed is the user's call
(they add it in the app from a licensed library); the skill never ships music.

## Audition reel and sound-only remix

- `make.py audition` writes `SOUND_AUDITION.mp4`: every candidate plays twice with its name on screen, under a minute.
  The user picks by ear and names a number.
- `make.py sound` re-mixes the effects track onto the EXISTING picture (`-c:v copy`) in a couple of seconds and copies
  the new wav into the CapCut project's own media folder (projects keep their own copies; see `lessons.md`). A sound swap
  never re-renders a frame.
