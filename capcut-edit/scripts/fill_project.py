#!/usr/bin/env python3
"""fill_project.py <layers dir> "<Project name>" — add every 02_/04_ layer clip the project is missing (idempotent), then
register/sync/lint. CapCut drops add-video calls mid-build when it is open with a sibling project loaded; this repairs that.
Each add is verified right after it lands."""
import os, re, sys, json, subprocess
S = os.environ.get("CAPCUT_DRAFT_DIR", os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft"))
L = os.path.abspath(sys.argv[1]); P = f"{S}/{sys.argv[2]}"
def run(*a):
    r = subprocess.run(["capcut", *a, "--force-write"], capture_output=True, text=True)
    if r.returncode != 0: raise SystemExit(f"FAIL {a[:3]} {r.stdout[-300:]} {r.stderr[-300:]}")
    return r.stdout
def dur(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
def labels(): return {s["label"] for s in json.loads(run("segments", P, "--track", "video"))}
have = labels(); files = sorted(os.listdir(L)); added = 0
for pre, track in (("02_", "back"), ("04_", "front")):
    its = sorted((float(re.match(r"\d\d_(\d+\.\d+)s_", f).group(1)), dur(f"{L}/{f}"), f) for f in files if f.startswith(pre))
    ends = []
    for t, d, f in its:
        k = next((i for i, e in enumerate(ends) if e <= t + 0.001), None)
        if k is None: ends.append(0); k = len(ends) - 1
        ends[k] = t + d
        if f in have: continue
        run("add-video", P, f"{L}/{f}", f"{t}s", f"{d}s", "--track-name", f"{track}{k + 1}"); added += 1
        if f not in labels(): raise SystemExit(f"segment vanished right after adding: {f} — close the project in CapCut and retry")
print("added", added)
run("register", P, "--apply", "--materials"); run("sync-timelines", P, "--nested", "--apply")
subprocess.run(["capcut", "lint", P, "--fix", "--force-write", "-H"], capture_output=True, text=True)
segs = json.loads(run("segments", P, "--track", "video"))
print("now: take", sum(1 for s in segs if s["label"].startswith("01_")), "back", sum(1 for s in segs if s["label"].startswith("02_")), "front", sum(1 for s in segs if s["label"].startswith("04_")), "cutout", sum(1 for s in segs if s["label"].startswith("03_")))
