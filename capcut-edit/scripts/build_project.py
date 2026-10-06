#!/usr/bin/env python3
"""build_project.py <layers dir> "<Project name>" — write a CapCut project from a capcut_layers/ folder with capcut-cli.

Expects the files make.py/Edit.layers() writes:
  01_<start>s_TAKE[_look].mp4   the take, one clip per cut point (grades baked where a look applies)
  02_*_BACK_alpha.mov           optional stickers that sit behind the person (needs the cutout)
  03_00.00s_CUTOUT_alpha.mov    optional, the person cut out (premultiplied alpha)
  04_*_FRONT_alpha.mov          every graphic in front
  05_00.00s_SFX.wav             the sound effects
  meta.json                     punch-ins, push window, blurb, caption cues
Proven on CapCut 9.2 (Mac) with capcut-cli 0.27. Never touches an existing project: pick a new name.
"""
import os, re, sys, json, subprocess
S = os.environ.get("CAPCUT_DRAFT_DIR", os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft"))
L = os.path.abspath(sys.argv[1]); NAME = sys.argv[2] if len(sys.argv) > 2 else "capcut-edit project"; P = f"{S}/{NAME}"
META = json.load(open(f"{L}/meta.json")); FPS = META.get("fps", 30); F1 = 1 / FPS; HI = os.environ.get("CAPCUT_HIGHLIGHT", "#F2CF4A")
def run(*a):
    r = subprocess.run(["capcut", *a, "--force-write"], capture_output=True, text=True)
    if r.returncode != 0: raise SystemExit(f"FAIL {a[:3]} {r.stdout[-400:]} {r.stderr[-400:]}")
    return r.stdout
def quiet(*a): return subprocess.run(["capcut", *a, "--force-write"], capture_output=True, text=True)
def dur(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
def nframes(p): return int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip() or 0)
def lanes(its):
    ends = []; res = []
    for t, d, f in its:
        k = next((i for i, e in enumerate(ends) if e <= t + 0.001), None)
        if k is None: ends.append(0); k = len(ends) - 1
        ends[k] = t + d; res.append((k, t, d, f))
    return res
files = sorted(os.listdir(L))
def items(pre): return sorted((float(re.match(r"\d\d_(\d+\.\d+)s_", f).group(1)), dur(f"{L}/{f}"), f) for f in files if f.startswith(pre))
if os.path.exists(P): raise SystemExit(f"{P} exists — pick another name (never overwrite a project)")
run("init", NAME, "--template", "auto", "--ratio", "9:16")
acc = 0
for t, d, f in items("01_"):                                                   # tile the take from real frame counts
    n = nframes(f"{L}/{f}"); run("add-video", P, f"{L}/{f}", f"{acc / FPS:.6f}s", f"{n / FPS:.6f}s", "--track-name", "take"); acc += n
for k, t, d, f in lanes(items("02_")): run("add-video", P, f"{L}/{f}", f"{t}s", f"{d}s", "--track-name", f"back{k + 1}")
cut = next((f for f in files if f.startswith("03_")), None)
if cut: run("add-video", P, f"{L}/{cut}", "0s", f"{dur(f'{L}/{cut}')}s", "--track-name", "cutout")
for k, t, d, f in lanes(items("04_")): run("add-video", P, f"{L}/{f}", f"{t}s", f"{d}s", "--track-name", f"front{k + 1}")
sfx = next((f for f in files if f.startswith("05_")), None)
if sfx: run("add-audio", P, f"{L}/{sfx}", "0s", f"{dur(f'{L}/{sfx}')}s", "--track-name", "sfx", "--volume", "1.0")
def seg_id(r): return r.get("id") or r.get("segment_id") or (r.get("segment") or {}).get("id")
if META.get("blurb"):
    b0, b1, btxt = META["blurb"]
    bid = seg_id(json.loads(run("add-text", P, f"{b0}s", f"{b1 - b0}s", btxt, "--font-size", "10", "--color", "#111113", "--align", "1", "--x", "0", "--y", "0.66", "--track-name", "blurb")))
    if bid: quiet("text-style", P, bid, "--bg-color", "#FFFFFF", "--bg-alpha", "1", "--bg-round-radius", "0.25", "--bg-width", "1", "--bg-height", "0.8", "--no-shadow")
for st, en, txt, kw in META.get("cues", []):                                   # captions: real text elements, keyword range in the highlight colour
    sid = seg_id(json.loads(run("add-text", P, f"{st}s", f"{en - st}s", txt, "--font-size", "9", "--color", "#FFFFFF", "--align", "1", "--x", "0", "--y", "-0.56", "--track-name", "captions")))
    if not sid: continue
    quiet("text-style", P, sid, "--shadow", "--shadow-alpha", "0.6", "--shadow-distance", "4")
    if kw:
        i = txt.lower().find(kw)
        if i >= 0: quiet("text-ranges", P, sid, "--styles", json.dumps([{"start": i, "end": i + len(kw), "font_color": HI, "bold": True}]))
sfx2 = next((f for f in files if f.startswith("06_")), None)                   # caption ticks: their own track, off by default in the mp4
if sfx2: run("add-audio", P, f"{L}/{sfx2}", "0s", f"{dur(f'{L}/{sfx2}')}s", "--track-name", "caption ticks", "--volume", "1.0")
# scale keyframes: the breathing zooms / punches / push as EASED keyframes (zoom_keys), on every take piece they fall in and on the cutout
segs = json.loads(run("segments", P, "--track", "video"))
def seg_at(pre, t):
    for s in segs:
        if s.get("label", "").startswith(pre):
            a = s["start_us"] / 1e6; b = a + s["duration_us"] / 1e6
            if a - 1e-4 <= t < b - 1e-4: return s["id"], a               # a boundary time belongs to the NEXT piece
    return None, None
keys = META.get("zoom_keys")
if not keys:                                                                   # older meta.json: rebuild from punch/push
    keys = []
    for a, b, s in META.get("punch", []): keys += [(a - F1, 1.0), (a, s), (b, s), (b + F1, 1.0)]
    if META.get("push"): a, b, s = META["push"]; keys += [(a, 1.0), (b, s), (b + F1, 1.0)]
    keys = sorted(keys)
def zval(t):
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t <= t1: return v0 + (v1 - v0) * ((t - t0) / (t1 - t0) if t1 > t0 else 0)
    return keys[-1][1] if keys else 1.0
def pieces(pre): return sorted([(s["id"], s["start_us"] / 1e6, (s["start_us"] + s["duration_us"]) / 1e6) for s in segs if s.get("label", "").startswith(pre)], key=lambda x: x[1])
for pre in ("01_", "03_"):
    for sid, a, b in pieces(pre):
        local = [(a, zval(a))] + [(t, v) for t, v in keys if a + 1e-4 < t < b - F1] + [(b - F1, zval(b - F1))]
        if all(abs(v - 1.0) < 1e-4 for _, v in local): continue
        for t, v in local: quiet("keyframe", P, sid, "scale", f"{max(0.0, t - a):.4f}s", f"{v}", "--easing", "ease-in-out")
run("register", P, "--apply", "--materials"); run("sync-timelines", P, "--nested", "--apply")
print(subprocess.run(["capcut", "lint", P, "--fix", "--force-write", "-H"], capture_output=True, text=True).stdout.strip()[-300:])
segs2 = json.loads(run("segments", P, "--track", "video")); want = sum(1 for f in files if f[:3] in ("01_", "02_", "03_", "04_")); have = len(segs2)
print(f"built {P}  ({have}/{want} video clips landed)")
if have < want: print(f"  {want - have} clips went missing (CapCut was open): run  python3 scripts/fill_project.py <layers dir> \"{NAME}\"")
print("Quit and reopen CapCut to see it. Select the caption clips and pick a heavy sans font.")
