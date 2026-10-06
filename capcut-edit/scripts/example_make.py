"""example_make.py — a per-video plan on top of render.py. Copy this next to your work folder, rename, change the tables.

Run:  python3 make.py times | check | preview | layers | sound | head [seconds] | audition
Needs in work/: cut.mp4, frames/00001.jpg…, words/words.txt, segments.json (from cutplan.py), masks/ (segbatch) for
anything behind the person, optional take_4k.mp4 + frames4k/ (the same cut exported at 4K: zooms stay sharp).
Needs in work/assets/: real images you reference (reel covers, thumbnails) and the user's own CapCut library sounds as
wav (see references/sound.md; scripts/capcut_sounds.py --copy work/assets). Never invent what you can't source.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # or the skill's scripts/ folder
from render import *

WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work"); OUT = os.path.dirname(WORK); AS = f"{WORK}/assets"
E = Edit(WORK, OUT); T = E.T; E.project_name = "My edit (Claude)"

# ---- the words that matter (from words/words.txt; the Whisper times are the truth) ----
t_claude = T("claude"); t_pick = T("pick"); t_aes = T("aesthetic"); t_watch = T("watch"); t_up = T("up"); t_float = T("float")
t_dropped = T("dropped"); t_later = T("later"); t_moody = T("moody"); t_drop = T("drop"); t_wrong = T("wrong"); t_they = T("they")
t_one = T("one"); t_different = T("different"); t_paywalls = T("paywalls"); t_not = T("not", after=t_paywalls); t_comment = T("comment")
t_edit = T("edit", after=t_comment); t_send = T("send", after=t_comment)

# ---- looks: windows on the footage itself, on at the word that names them; the strength ramps so the viewer watches it happen ----
E.windows = {"soft": (t_aes - 0.10, t_moody - 0.4), "moody": (t_moody - 0.10, t_one - 0.10)}
E.ramps = {"soft": (t_watch + 0.2, t_up + 0.1), "moody": (t_drop - 0.12, t_drop + 0.45)}
E.bw = (t_wrong - 0.02, t_wrong + 0.05)                      # two black-and-white frames on the warning word
E.push = (E.windows["moody"][0], E.windows["moody"][1], 1.07)  # a slow creep across the moody look
# ---- motion: the breathing camera (motion.md) + hard punches ----
E.breath = [(0.9, t_claude - 0.3, t_claude - 0.2, t_claude, 1.12), (t_watch, t_up + 0.05, t_float - 0.3, t_float, 1.15), (t_paywalls - 1.3, t_paywalls, t_paywalls + 0.2, t_paywalls + 0.6, 1.12)]
E.punch = [(t_wrong - 0.02, t_they - 0.04, 1.15), (t_not - 0.02, t_not + 0.6, 1.20)]
# ---- the flicker open (motion.md): needs work/plate/plate_1080.png (scripts/plate.py) and masks ----
if os.path.exists(f"{WORK}/plate/plate_1080.png"):
    E.plate = Image.open(f"{WORK}/plate/plate_1080.png").convert("RGB")
    E.flicker = {0: "P", 1: "P", 2: "P", 3: "P", 4: "I", 5: "N", 6: "N", 7: "I", 8: "P", 9: "P", 10: "P", 11: "P"}
    E.flicker = {k: v for k, v in E.flicker.items() if v != "N"}

# ---- sounds: the user's OWN CapCut library sounds (sound.md). Roles: pop = a picture of them, click = computer-screen footage ----
if os.path.exists(f"{AS}/sfx_pop.wav"):
    SND.update({"pop": (snd_file(f"{AS}/sfx_pop.wav"), 0.40), "click": (snd_file(f"{AS}/sfx_click.wav"), 0.35), "whoosh": (snd_file(f"{AS}/sfx_whoosh.wav"), 0.40),
                "bell": (snd_file(f"{AS}/sfx_bell.wav", trim=1.2, fade=0.4), 0.30), "low": (snd_file(f"{AS}/sfx_low.wav", trim=1.6, fade=0.5), 0.5),
                "unlock": (snd_file(f"{AS}/sfx_ding.wav", trim=1.2, fade=0.4), 0.40), "static": (snd_file(f"{AS}/sfx_static.wav"), 0.45)})
    keys = slice_transients(f"{AS}/sfx_typing.wav")            # one real keystroke per typed character
    SND.update({"typing12": (lambda: typing_run(keys, 12, 0.06), 0.45), "typing4": (lambda: typing_run(keys, 4, 0.09), 0.45)})
E.audition_list = [(os.path.basename(p), p) for p in sorted(glob.glob(f"{AS}/sfx_*.wav"))]

# ---- captions: phrases as spoken, one keyword each. Moody-section cues are dropped (the serif words speak) ----
CUES = [("Nothing you are watching", ""), ("right now", ""), ("was edited by me", "me"), ("Claude did all of it", "Claude"),
        ("and you can pick", "pick"), ("whatever vibe you want", "vibe"), ("more aesthetic", "aesthetic"), ("warm up", "warm up"),
        ("one sentence", "one sentence"), ("different video", "different"), ("behind paywalls", "paywalls"), ("and comment edit", "edit"), ("the whole skill", "skill")]
E.cues(CUES, proper=("Claude", "CapCut", "I", "I'm", "EDIT"), cap=1.6, skip=[E.windows["moody"]])
E.blurb = [0.0, t_claude - 0.04, "Edit your videos with Claude"]

# ---- the asset table: name · in · out · builder · sound · note · layer ("text" | "front" | "back") ----
REELS = sorted(glob.glob(f"{AS}/reel*.png"))                                  # make_reel_card(cover, "476.1K", f"{AS}/reel1.png") from REAL covers + counts
E.add("00-captions", 0.0, E.dur, lambda d: captions(E.cuelist, d), None, "captions, keyword in yellow, ≤720 wide", layer="text")
E.add("01-blurb", 0.0, t_claude - 0.04, lambda d: classic_pop(["Edit your videos with Claude"], d, cy=415), None, "hook blurb, pops in, centred under the top tabs", layer="text")
if E.flicker: E.add("02-static", 0.0, 12 / FPS, lambda d: static_flash(d), "static", "film static over the flicker")
if os.path.isdir(f"{WORK}/capture/proof"): E.add("03-proof", 1.0, t_claude - 0.04, lambda d: screen_card(f"{WORK}/capture/proof", d, cx=470, cy=1235), "click", "the editor timeline (their screen recording), in front on the chest")
E.add("04-pop-claude", t_claude - 0.02, t_pick - 0.3, lambda d: bigword("Claude", d, WHITE, y=430, size=190), "pop", "big word")
E.add("06-bell", E.windows["soft"][0], E.windows["soft"][0] + 0.32, lambda d: flash(d, 0.35, (255, 236, 205)), "bell", "one soft bloom + one bell on the switch")
E.add("07-title", E.windows["soft"][0] + 0.02, t_float - 0.1, lambda d: serif_title("aesthetic", d, cy=430, sub="S O F T   &   W A R M"), None, "gold serif word")
if len(REELS) == 4:
    E.add("10-reels-back", t_float - 0.08, t_dropped - 0.1, lambda d: reel_orbit(REELS, d, "back"), [(0.14, "pop"), (0.42, "pop")], "their own reels: the pair behind the head", layer="back")
    E.add("10-reels-front", t_float - 0.08, t_dropped - 0.1, lambda d: reel_orbit(REELS, d, "front"), [(0.0, "pop"), (0.28, "pop")], "…and the pair over the chest")
E.add("12-app", t_dropped - 0.06, t_later - 0.2, lambda d: chat_card(d, [(0.0, "drop", "raw footage  ·  bad takes and all"), (0.5, "skill", "/capcut-edit"), (1.2, "check", "Cutting the bad takes"), (1.65, "spin", "Captions, cards, sound")], cy=600, width=900),
      [(0.0, "click"), (0.5, "typing12"), (1.2, "click")], "the app card, behind the head", layer="back")
E.add("14-dip", E.windows["moody"][0], E.windows["moody"][0] + 0.30, lambda d: flash(d, 0.55, (0, 0, 0)), "low", "a soft dip + a low swell on 'moody'")
E.add("15-serif-moody", t_moody - 0.04, t_drop - 0.3, lambda d: serif_slide("moody", d, y=1470, size=230, caps="D R A M A T I C   V I B E", caps_at=0.4), None, "huge serif word on the chest")
E.add("19-serif-wrong", t_wrong - 0.04, t_they - 0.04, lambda d: serif_slide("wrong.", d, y=1470, size=240), "bass", "warning word: serif + 2 b&w frames + punch")
E.add("25-flash-back", E.windows["moody"][1], E.windows["moody"][1] + 0.25, lambda d: flash(d, 0.85), "whoosh", "white flash back to normal")
E.add("26-pop-one", t_one - 0.02, t_different - 0.5, lambda d: bigword("one sentence", d, YEL, y=430, size=150, tracking=-3), "pop", "big words, auto-fit")
E.add("28-paywall", t_paywalls - 1.3, t_not + 0.6, lambda d: paywall_card(d, (t_not) - (t_paywalls - 1.3), title="The Editing Course"), [(0.0, "click"), (t_not - (t_paywalls - 1.3), "unlock")], "paywall card in the headroom; unlocks on 'not'")
E.add("30-comments", t_comment - 0.1, E.dur, lambda d: comment_box(d, "EDIT", t_edit - t_comment, t_send - t_comment + 0.1, cy=470), [(t_edit - t_comment, "typing4"), (t_send - t_comment + 0.1, "click")], "comment box")

if __name__ == "__main__":
    E.run(sys.argv, check_ts=[0.0, 0.1, 0.2, 1.6, t_claude + 0.2, t_aes + 0.3, t_up + 0.2, t_float + 0.6, t_dropped + 0.8, t_moody + 0.2, t_drop + 0.3, t_wrong + 0.03, t_one + 0.2, t_paywalls + 0.4, t_not + 0.3, E.dur - 0.5])
