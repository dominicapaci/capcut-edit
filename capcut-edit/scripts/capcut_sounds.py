#!/usr/bin/env python3
"""capcut_sounds.py [--copy <dir>] — list the sound effects CapCut has cached on this Mac, with the names they had in the
user's own drafts and a rough character (duration, attack, brightness, noisiness). Use these instead of synthesizing
(see references/sound.md). --copy converts the short ones to wav into <dir>.
A sound the user merely previewed is NOT cached; it lands here once they press + on it in any project (newest .mp3)."""
import os, sys, glob, json, re, subprocess, collections, wave, numpy as np
C = os.path.expanduser("~/Movies/CapCut/User Data/Cache/music"); D = os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft")
names = collections.defaultdict(set); used = collections.Counter()
for f in glob.glob(f"{D}/*/draft_content.json") + glob.glob(f"{D}/*/draft_info.json"):
    try: d = json.load(open(f))
    except Exception: continue
    for a in d.get("materials", {}).get("audios", []):
        m = re.search(r"music/([0-9a-f]{32})", a.get("path") or "")
        if m: names[m.group(1)].add(a.get("name") or "?"); used[m.group(1)] += 1
def probe(p):
    try: return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
    except Exception: return None
rows = []
for p in sorted(glob.glob(f"{C}/*.mp3"), key=os.path.getmtime, reverse=True):
    d = probe(p)
    if not d or d > 4.0: continue
    h = os.path.basename(p)[:-4]; tmp = "/tmp/_cc_snd.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-ac", "1", "-ar", "48000", tmp])
    with wave.open(tmp) as w: a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if len(a) < 2400: continue
    env = np.abs(a); i90 = np.argmax(env > 0.9 * env.max()) / 48000
    spec = np.abs(np.fft.rfft(a * np.hanning(len(a)))); fr = np.fft.rfftfreq(len(a), 1 / 48000); cent = (spec * fr).sum() / spec.sum(); flat = np.exp(np.log(spec + 1e-9).mean()) / (spec.mean() + 1e-9)
    rows.append((h, d, i90, cent, flat, " / ".join(sorted(names.get(h, []))) or "(previewed, unnamed)", used[h]))
    if "--copy" in sys.argv:
        out = sys.argv[sys.argv.index("--copy") + 1]; os.makedirs(out, exist_ok=True); subprocess.run(["cp", tmp, f"{out}/{h[:8]}_{d:.1f}s.wav"])
print(f"{len(rows)} cached sound effects (<4 s), newest first\n")
for h, d, i90, cent, flat, nm, u in rows:
    kind = "click/tap" if d < 0.3 else ("whoosh/riser" if flat > 0.09 and i90 > 0.08 else ("low hit" if cent < 1200 else "pop/hit"))
    print(f"{h[:8]}  {d:4.2f}s  attack {i90*1000:4.0f}ms  {cent:5.0f}Hz  noisy {flat:.2f}  ~{kind:12s}  used x{u:<2d} {nm}")
