#!/usr/bin/env python3
"""plate.py <work dir> [--frames a:b:step] — build an empty-room plate (1080x1920) for the flicker open from the take itself:
the median of every pixel over the frames where the person mask says "not a person", then row-by-row interpolation for
the wall band above the chair and inpainting below. The part of the chair the person never leaves cannot be recovered;
say so in the README (or ask the user to film 2 s of the empty room and use that instead).
Needs work/frames/*.jpg, work/masks/*.png (segbatch.swift), numpy, Pillow, opencv-python-headless."""
import os, sys, numpy as np, multiprocessing as mp
from PIL import Image, ImageFilter
W = os.path.abspath(sys.argv[1]); a, b, step = (14, 560, 3)
if "--frames" in sys.argv: a, b, step = map(int, sys.argv[sys.argv.index("--frames") + 1].split(":"))
idx = list(range(a, b, step))
def load(i):
    f = np.asarray(Image.open(f"{W}/frames/{i + 1:05d}.jpg").convert("RGB"))
    m = np.asarray(Image.open(f"{W}/masks/{i + 1:05d}.png").convert("L").filter(ImageFilter.MaxFilter(41))) < 20
    return f, m
def strip(args):
    y0, y1 = args; S = np.stack([F[y0:y1] for F in FR]).astype(np.float32); V = np.stack([M[y0:y1] for M in MS]); S[~V] = np.nan
    with np.errstate(all="ignore"): med = np.nanmedian(S, axis=0)
    return y0, med, V.sum(0)
if __name__ == "__main__":
    with mp.Pool(8) as p: r = p.map(load, idx)
    FR = [x for x, _ in r]; MS = [y for _, y in r]; H = FR[0].shape[0]
    with mp.get_context("fork").Pool(8) as p: res = p.map(strip, [(y, min(H, y + 60)) for y in range(0, H, 60)])
    med = np.zeros(FR[0].shape, np.float32); cnt = np.zeros(FR[0].shape[:2], int)
    for y0, m, c in res: med[y0:y0 + len(m)] = m; cnt[y0:y0 + len(c)] = c
    hole = cnt < 12; out = np.nan_to_num(med).clip(0, 255)
    print(f"{len(idx)} frames; never-revealed area {hole.mean():.1%}")
    import cv2
    rows_wall = int(H * 0.5)                                   # above the chair: interpolate each row across the hole
    for y in range(rows_wall):
        row = hole[y]
        if not row.any(): continue
        x = 0; Wd = row.size
        while x < Wd:
            if row[x]:
                x0 = x
                while x < Wd and row[x]: x += 1
                L = out[y, max(0, x0 - 6):x0].mean(0) if x0 > 0 else None; R = out[y, x:min(Wd, x + 6)].mean(0) if x < Wd else None
                L = R if L is None else L; R = L if R is None else R; t = np.linspace(0, 1, x - x0)[:, None]; out[y, x0:x] = L * (1 - t) + R * t
            else: x += 1
    hm = (hole * 255).astype(np.uint8); hm[:rows_wall] = 0
    out = cv2.cvtColor(cv2.inpaint(cv2.cvtColor(out.astype(np.uint8), cv2.COLOR_RGB2BGR), cv2.dilate(hm, np.ones((7, 7), np.uint8)), 25, cv2.INPAINT_TELEA), cv2.COLOR_BGR2RGB)
    os.makedirs(f"{W}/plate", exist_ok=True); Image.fromarray(out).save(f"{W}/plate/plate_1080.png"); np.save(f"{W}/plate/hole.npy", hole)
    print("wrote", f"{W}/plate/plate_1080.png", "— check it; the chair centre is inpainted, not real")
