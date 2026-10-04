#!/usr/bin/env python3
"""cutplan.py — get from footage to a tight cut.mp4 + segments.json (source ranges in the raw file).

  cutplan.py silence    raw.mp4 --out cut.mp4 [--thr -46] [--maxp 0.20] [--handle 0.06]
      Audio-envelope pause trim: every silence longer than --maxp is shortened to 2×--handle. No dead air between
      lines; the person finishes a word and the next clip is already talking. (A take with repeated lines: run
      transcribe.py first, then `capcut detect-retakes --srt words.srt`, and pass the keep spans with --keep keep.json.)
  cutplan.py from-draft "<CapCut draft dir>" raw.mp4 --out cut.mp4
      The user already cut the take in CapCut: read draft_info.json, rebuild that cut frame-exactly (scaled to
      1080x1920), write segments.json with their exact cut points.
"""
import os, sys, json, argparse, subprocess
import numpy as np
FPS = 30
def concat(src, regions, out, scale=True):
    fc = []; vs = []; as_ = []
    for i, (a, b) in enumerate(regions):
        sc = ",scale=1080:1920:flags=lanczos" if scale else ""
        fc.append(f"[0:v]trim={a:.4f}:{b:.4f},setpts=PTS-STARTPTS{sc}[v{i}]")
        fc.append(f"[0:a]atrim={a:.4f}:{b:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b - a - 0.012:.4f}:d=0.012[a{i}]")
        vs.append(f"[v{i}]"); as_.append(f"[a{i}]")
    fc.append("".join(v + a for v, a in zip(vs, as_)) + f"concat=n={len(regions)}:v=1:a=1[v][a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-r", str(FPS),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "13", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", out], check=True)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout)
    print(f"wrote {out}  {d:.2f}s  ({len(regions)} pieces)")
def silence_keep(src, thr=-46.0, maxp=0.20, handle=0.06, head=0.06, tail=0.55):
    SR, HOP, WIN = 16000, 0.010, 0.030
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(pcm, "<i2").astype(np.float32) / 32768.0; dur = len(x) / SR
    hop, win = int(SR * HOP), int(SR * WIN); n = (len(x) - win) // hop
    db = np.array([20 * np.log10(np.sqrt(np.mean(x[i * hop:i * hop + win] ** 2)) + 1e-9) for i in range(n)])
    floor = np.percentile(db, 10); t_ = max(thr, floor + 14); quiet = db < t_; runs = []; i = 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]: j += 1
            runs.append((i * HOP + WIN / 2, j * HOP + WIN / 2)); i = j
        else: i += 1
    cuts = []
    if runs and runs[0][0] < 0.02 and runs[0][1] > head: cuts.append((0.0, runs[0][1] - head))
    for a, b in runs:
        if a < 0.02 or b > dur - 0.05: continue
        if b - a > maxp: cuts.append((a + handle, b - handle))
    if runs and runs[-1][1] > dur - 0.05 and runs[-1][0] + tail < dur: cuts.append((runs[-1][0] + tail, dur))
    keep = []; cur = 0.0
    for a, b in cuts:
        if a > cur + 0.03: keep.append((cur, a))
        cur = max(cur, b)
    if cur < dur - 0.03: keep.append((cur, dur))
    keep = [(round(a * FPS) / FPS, round(b * FPS) / FPS) for a, b in keep]
    print(f"floor {floor:.0f} dB, threshold {t_:.0f} dB, removed {dur - sum(b - a for a, b in keep):.2f}s of pauses")
    return keep
def from_draft(draft):
    j = json.load(open(os.path.join(draft, "draft_info.json")))
    segs = [(s["source_timerange"]["start"] / 1e6, (s["source_timerange"]["start"] + s["source_timerange"]["duration"]) / 1e6)
            for t in j["tracks"] if t["type"] == "video" for s in t["segments"]]
    print(f"{len(segs)} segments in the draft, {sum(b - a for a, b in segs):.2f}s"); return segs
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["silence", "from-draft"]); ap.add_argument("a"); ap.add_argument("b", nargs="?")
    ap.add_argument("--out", default="cut.mp4"); ap.add_argument("--keep"); ap.add_argument("--thr", type=float, default=-46.0)
    ap.add_argument("--maxp", type=float, default=0.20); ap.add_argument("--handle", type=float, default=0.06); ap.add_argument("--no-scale", action="store_true")
    o = ap.parse_args()
    if o.mode == "silence":
        src = o.a
        if o.keep:                                             # pre-chosen spans (e.g. the later take of each line), then trim pauses inside them
            spans = json.load(open(o.keep)); tmp = o.out + ".rough.mp4"; concat(src, spans, tmp, not o.no_scale); src = tmp; o.no_scale = True
        keep = silence_keep(src, o.thr, o.maxp, o.handle); concat(src, keep, o.out, not o.no_scale)
        json.dump(keep, open(os.path.join(os.path.dirname(os.path.abspath(o.out)), "segments.json"), "w"))
    else:
        segs = from_draft(o.a); concat(o.b, segs, o.out, not o.no_scale)
        json.dump(segs, open(os.path.join(os.path.dirname(os.path.abspath(o.out)), "segments.json"), "w"))
