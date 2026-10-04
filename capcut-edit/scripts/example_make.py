"""example_make.py — a per-video plan on top of render.py. Copy this next to your work folder, rename, change the tables.

Run:  python3 make.py times | check | preview | layers
Needs in work/: cut.mp4, frames/00001.jpg…, words/words.txt, segments.json (from cutplan.py), optional masks/.
Needs in work/assets/: any real images you reference (a reel cover, a thumbnail). Never invent what you can't source.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # or the skill's scripts/ folder
from render import *

WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work"); OUT = os.path.dirname(WORK)
E = Edit(WORK, OUT)
T = E.T

# ---- the words that matter (from words/words.txt; the Whisper times are the truth) ----
t_claude = T("claude"); t_if = T("if"); t_cool = T("cool"); t_switch = T("switch"); t_dark = T("dark"); t_myst = T("mysterious")
t_next = T("a", after=t_dark + 1.0)          # first word of the idea after the dark section
t_wrong = T("wrong"); t_comment = T("comment"); t_edit = T("edit", after=t_comment); t_send = T("send", after=t_comment)

# ---- looks: windows on the footage itself, on at the word that names them ----
E.windows = {"cool": (t_cool - 0.10, t_dark - 0.10), "noir": (t_dark - 0.10, t_next - 0.04)}
E.push = (E.windows["noir"][0], E.windows["noir"][1], 1.06)
E.punch = [(t_wrong - 0.02, t_wrong + 0.6, 1.12)]

# ---- captions: phrases as spoken, one keyword each. Dark-section cues are dropped (the serif words speak) ----
CUES = [("Nothing you are watching", ""), ("right now", ""), ("was edited by me", "edited by me"), ("Claude did all of it", "Claude"),
        ("Say you want the", ""), ("Cool Girl aesthetic", "Cool Girl"), ("well I'll switch", ""), ("to Cool Girl", "Cool Girl"),
        ("a lot of people", ""), ("are doing it wrong", "wrong"), ("Comment edit", "edit"), ("and I'll send you", ""), ("the skill", "skill")]
E.cues(CUES, proper=("Claude", "CapCut", "I", "I'll", "Cool", "Girl"), skip=[E.windows["noir"]])
E.blurb = [0.0, t_if - 0.06, "Claude edited this whole video"]

# ---- the asset table: name · in · out · builder · sound · note ----
E.add("00-captions", 0.0, E.dur, lambda d: captions(E.cuelist, d), None, "captions, keyword in yellow", layer="text")
E.add("01-blurb", 0.0, t_if - 0.06, lambda d: classic_box(["Claude edited this whole video"], d), None, "hook blurb", layer="text")
E.add("02-prompt", 1.0, t_claude - 0.04, lambda d: chat_card(d, [(0.0, "msg", ["Edit this video. Cool girl aesthetic,", "then dark and mysterious."]), (d - 0.9, "badge", "done")], cy=600), [(0.0, "tap"), (1.5, "tap")], "the ask, in the app")
E.add("03-pop-claude", t_claude - 0.02, t_if - 0.04, lambda d: bigword("Claude", d, WHITE, y=470, size=190), "pop", "big word")
E.add("06-flash-cool", E.windows["cool"][0], E.windows["cool"][0] + 0.3, lambda d: flash(d, 0.92), "sparkle", "flash on the switch")
E.add("07-cool-title", E.windows["cool"][0] + 0.02, E.windows["cool"][1], lambda d: serif_title("cool girl", d, t_sw=t_switch - E.windows["cool"][0], sub="A E S T H E T I C   L I K E   T H I S"), None, "gold serif title")
E.add("08-sparkles", E.windows["cool"][0] + 0.2, E.windows["cool"][1], sparkles, None, "twinkles")
E.add("11-dip", E.windows["noir"][0], E.windows["noir"][0] + 0.22, lambda d: flash(d, 0.8, (0, 0, 0)), "bass", "black dip")
E.add("12-dust", E.windows["noir"][0], E.windows["noir"][1], dust, None, "dust")
E.add("13-dark", t_dark - 0.04, t_myst - 0.02, lambda d: serif_slide("dark", d, size=210), None, "serif word")
E.add("14-mysterious", t_myst - 0.02, E.windows["noir"][1], lambda d: serif_slide("mysterious", d, size=160, caps="E D I T I N G   F E E L", caps_at=0.5), None, "serif word + caps")
E.add("16-flash-back", E.windows["noir"][1], E.windows["noir"][1] + 0.25, lambda d: flash(d, 0.85), "whoosh", "back to normal")
E.add("18-pop-wrong", t_wrong - 0.02, t_wrong + 0.6, lambda d: bigword("wrong", d, YEL, y=470, size=200), "pop", "big word")
E.add("30-comments", t_comment - 0.02, E.dur, lambda d: comment_box(d, "EDIT", t_edit - t_comment - 0.1, t_send - t_comment), [(t_edit - t_comment - 0.1 + k * 0.09, "tick") for k in range(4)] + [(t_send - t_comment, "click")], "comment box")

if __name__ == "__main__":
    E.run(sys.argv, check_ts=[0.3, 1.6, t_claude + 0.2, t_cool + 0.3, t_switch + 0.2, t_dark + 0.2, t_myst + 0.5, t_next + 0.3, t_wrong + 0.1, t_comment + 0.6, E.dur - 0.3])
