"""render.py — the rendering library behind capcut-edit. Import it from a per-video make.py (see example_make.py).

Everything renders at 1080x1920 @ 30 fps. Graphics are drawn 2x supersampled in a Region and downscaled, so text and
shapes are antialiased. Stickers encode to ProRes 4444 with PREMULTIPLIED alpha (what CapCut expects). Grades re-colour
the footage itself for "looks". Sound is synthesized. Public surface:

  tokens ......... W H FPS SS, WHITE INK YEL GOLD CREAM PAPER CARD_DARK ACC GREEN GREY, F(size, weight), FT(path, size, index)
  easing ......... c01 seg eo3 eio eob lerp lp A
  canvas ......... Region, full, twidth, blank, card, shadowed, place, pop, fan, shrink, glyph_star, traffic
  icons .......... cursor check lock page
  builders ....... classic_box captions bigword chat_card code_card finder_card player_card phone yt_card
                   serif_title sparkles flash serif_slide dust comment_box timeline_card
  grades ......... grade_base grade_cool grade_noir GRADES
  sound .......... snd_tap snd_click snd_pop snd_sparkle snd_bass snd_whoosh snd_tick mix_track write_wav
  the edit ....... Edit (words, cues, clips, punch-ins, windows, compose, check, preview, layers)
"""
import os, sys, math, re, glob, json, random, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------- tokens ----------
W, H, FPS, SS = 1080, 1920, 30, 2
WHITE = (255, 255, 255, 255); INK = (17, 17, 19, 255); INK2 = (40, 38, 35, 255); GREY = (200, 200, 206, 255)
YEL = (242, 207, 74, 255); GOLD = (236, 196, 92, 255); CREAM = (255, 246, 226, 255); PAPER = (245, 241, 234, 255)
CARD_DARK = (26, 26, 30, 255); ACC = (217, 119, 87, 255); GREEN = (34, 197, 94, 255)
SUP = "/System/Library/Fonts/Supplemental/"
def _first(*paths):
    for p in paths:
        if os.path.exists(p): return p
    return None
SANS = _first("/System/Library/Fonts/Avenir Next.ttc", "/System/Library/Fonts/HelveticaNeue.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
SANS_IDX = {"heavy": 8, "bold": 0, "demi": 2, "med": 5} if SANS and "Avenir" in SANS else {"heavy": 1, "bold": 1, "demi": 1, "med": 0}
MONO = _first("/System/Library/Fonts/Menlo.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
SERIF_I = _first(SUP + "Didot.ttc", SUP + "Georgia Italic.ttf"); SERIF_I_IDX = 1 if SERIF_I and "Didot" in SERIF_I else 0
SERIF_B = _first(SUP + "Bodoni 72.ttc", SUP + "Georgia Italic.ttf"); SERIF_B_IDX = 1 if SERIF_B and "Bodoni" in SERIF_B else 0
@lru_cache(None)
def FT(path, size, index=0): return ImageFont.truetype(path, max(1, int(size * SS)), index=index)
def F(size, w="heavy"): return FT(SANS, size, SANS_IDX.get(w, 0))
def f_mono(size): return FT(MONO, size)
def f_serif_i(size): return FT(SERIF_I, size, SERIF_I_IDX)
def f_serif_b(size): return FT(SERIF_B, size, SERIF_B_IDX)

# ---------- easing ----------
def c01(x): return max(0.0, min(1.0, x))
def seg(t, a, b): return c01((t - a) / (b - a)) if b > a else (1.0 if t >= b else 0.0)
def eo3(x): x = c01(x); return 1 - (1 - x) ** 3
def eio(x): x = c01(x); return x * x * (3 - 2 * x)
def eob(x):
    x = c01(x); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def lerp(a, b, p): return a + (b - a) * p
def lp(a, b, p): return (lerp(a[0], b[0], p), lerp(a[1], b[1], p))
def A(col, a): return (col[0], col[1], col[2], int(col[3] * c01(a)))

# ---------- canvas ----------
class Region:
    """A rectangle of the 1080x1920 canvas drawn at SS× and downscaled. All coordinates are canvas coordinates."""
    def __init__(s, x0, y0, w, h):
        s.x0, s.y0, s.w, s.h = x0, y0, w, h
        s.im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); s.d = ImageDraw.Draw(s.im)
    def P(s, x, y): return ((x - s.x0) * SS, (y - s.y0) * SS)
    def box(s, b): return (*s.P(b[0], b[1]), *s.P(b[2], b[3]))
    def rr(s, b, r, fill=None, outline=None, width=0):
        if fill is not None and len(fill) == 4 and fill[3] <= 1 and outline is None: return   # alpha-0 fills punch holes; skip them
        s.d.rounded_rectangle(s.box(b), max(0, r * SS), fill=fill, outline=outline, width=int(width * SS))
    def ell(s, b, fill=None, outline=None, width=0): s.d.ellipse(s.box(b), fill=fill, outline=outline, width=int(width * SS))
    def line(s, pts, fill, width): s.d.line([s.P(*p) for p in pts], fill=fill, width=max(1, int(width * SS)), joint="curve")
    def poly(s, pts, fill=None, outline=None, width=0): s.d.polygon([s.P(*p) for p in pts], fill=fill, outline=outline, width=int(width * SS))
    def arc(s, b, a0, a1, fill, width): s.d.arc(s.box(b), a0, a1, fill=fill, width=int(width * SS))
    def text(s, xy, txt, font, fill, anchor="mm", stroke=0, sfill=INK):
        if len(fill) == 4 and fill[3] <= 1: return
        s.d.text(s.P(*xy), txt, font=font, fill=fill, anchor=anchor, stroke_width=int(stroke * SS), stroke_fill=sfill)
    def ttext(s, xy, txt, font, fill, track=0):
        x, y = xy
        for ch in txt: s.d.text(s.P(x, y), ch, font=font, fill=fill, anchor="lm"); x += font.getlength(ch) / SS + track
    def shadow(s, b, r, blur=12, alpha=110, dy=10):
        l = Image.new("RGBA", s.im.size, (0, 0, 0, 0))
        ImageDraw.Draw(l).rounded_rectangle(s.box((b[0], b[1] + dy, b[2], b[3] + dy)), max(0, r * SS), fill=(0, 0, 0, int(alpha)))
        s.im.alpha_composite(l.filter(ImageFilter.GaussianBlur(blur * SS)))
    def glow(s, b, r, col, blur=18, alpha=160):
        l = Image.new("RGBA", s.im.size, (0, 0, 0, 0)); ImageDraw.Draw(l).rounded_rectangle(s.box(b), max(0, r * SS), fill=A(col, alpha / 255))
        s.im.alpha_composite(l.filter(ImageFilter.GaussianBlur(blur * SS)))
    def paste(s, img, center, size, alpha=1.0):
        iw, ih = img.size; k = min(size * SS / iw, size * SS / ih); im2 = img.resize((max(1, int(iw * k)), max(1, int(ih * k))), Image.LANCZOS)
        if alpha < 1: im2.putalpha(im2.getchannel("A").point(lambda v: int(v * alpha)))
        cx, cy = s.P(*center); s.im.alpha_composite(im2, (int(cx - im2.width / 2), int(cy - im2.height / 2)))
    def paste_rgb(s, img, topleft): s.im.paste(img.resize((img.width * SS, img.height * SS)), (int(topleft[0] * SS), int(topleft[1] * SS)))
    def fade(s, a):
        a = c01(a)
        if a < 1: s.im.putalpha(s.im.getchannel("A").point(lambda v: int(v * a)))
    def out(s): return s.im.resize((s.w, s.h), Image.LANCZOS)
def full(*regs):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for r in regs: im.alpha_composite(r.out(), (r.x0, r.y0))
    return im
def twidth(txt, font, track=0): return sum(font.getlength(ch) / SS + track for ch in txt) - track
def blank(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))

# ---------- icons ----------
def cursor(r, tip, s=1.0, alpha=1.0):
    pts = [(0, 0), (0, 58), (14, 45), (23, 66), (32, 62), (23, 42), (40, 42)]
    r.poly([(tip[0] + x * 1.15 * s, tip[1] + y * 1.15 * s) for x, y in pts], fill=A(WHITE, alpha), outline=A(INK, alpha), width=3)
def check(r, c, size, col, width=8):
    x, y = c
    if size > 0.5: r.line([(x - size * .45, y), (x - size * .1, y + size * .38), (x + size * .5, y - size * .4)], col, width)
def lock(r, c, s, col):
    x, y = c; r.arc((x - 16 * s, y - 34 * s, x + 16 * s, y + 4 * s), 180, 360, col, 6 * s); r.rr((x - 24 * s, y - 12 * s, x + 24 * s, y + 24 * s), 6 * s, fill=col)
def page(r, c, w, h, s, fill=WHITE, ink=INK, lines=4, label=None, alpha=1.0):
    x, y = c; w *= s; h *= s; fold = 0.28 * w; x0, y0, x1, y1 = x - w / 2, y - h / 2, x + w / 2, y + h / 2
    r.poly([(x0, y0), (x1 - fold, y0), (x1, y0 + fold), (x1, y1), (x0, y1)], fill=A(fill, alpha), outline=A(ink, alpha), width=4 * s)
    r.poly([(x1 - fold, y0), (x1 - fold, y0 + fold), (x1, y0 + fold)], fill=A(ink, alpha))
    for i in range(lines):
        ly = y0 + h * 0.42 + i * h * 0.12; lw = w * (0.62 if i % 2 else 0.5); r.line([(x0 + w * .18, ly), (x0 + w * .18 + lw, ly)], A(ink, alpha), 4 * s)
    if label: r.text((x, y1 - h * 0.13), label, f_mono(22 * s), A(ink, alpha))

# ---------- cards / placement ----------
PADC = 60; _cache = {}
def card(content, rad=30):
    """RGB content → RGBA layer with rounded corners and a soft drop shadow, padded by PADC on every side."""
    w, h = content.size; key = (w, h, rad)
    if key not in _cache:
        sh = Image.new("L", (w + 2 * PADC, h + 2 * PADC), 0)
        ImageDraw.Draw(sh).rounded_rectangle((PADC, PADC + 14, PADC + w, PADC + h + 14), rad, fill=130); sh = sh.filter(ImageFilter.GaussianBlur(22))
        m = Image.new("L", (w * 2, h * 2), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), rad * 2, fill=255); _cache[key] = (sh, m.resize((w, h), Image.LANCZOS))
    sh, m = _cache[key]; lay = Image.new("RGBA", sh.size, (0, 0, 0, 0)); lay.putalpha(sh); lay.paste(content.convert("RGB"), (PADC, PADC), m); return lay
def shadowed(rgba, dy=14, a=0.5):
    sh = rgba.getchannel("A").filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * a))
    lay = Image.new("RGBA", (rgba.width + 2 * PADC, rgba.height + 2 * PADC), (0, 0, 0, 0))
    s = Image.new("RGBA", rgba.size, (0, 0, 0, 255)); s.putalpha(sh); lay.alpha_composite(s, (PADC, PADC + dy)); lay.alpha_composite(rgba, (PADC, PADC)); return lay
def place(canvas, im, center, scale=1.0, angle=0.0, alpha=1.0):
    if alpha <= 0.004 or scale <= 0.02: return
    if abs(scale - 1) > 1e-3: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if abs(angle) > 1e-3: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    x = int(round(center[0] - im.width / 2)); y = int(round(center[1] - im.height / 2))
    sx0, sy0 = max(0, -x), max(0, -y); sx1, sy1 = min(im.width, canvas.width - x), min(im.height, canvas.height - y)
    if sx1 > sx0 and sy1 > sy0: canvas.alpha_composite(im.crop((sx0, sy0, sx1, sy1)), (x + sx0, y + sy0))
def pop(t, st, dur, out=True, hold_out=0.22):
    """scale/alpha of a card that pops in at st (overshoot) and leaves before dur."""
    s = 0.80 + 0.20 * eob(seg(t, st, st + 0.32)); a = eo3(seg(t, st, st + 0.14))
    if out: k = eio(seg(t, dur - hold_out, dur)); s *= 1 - 0.06 * k; a *= 1 - k
    return s, a
def fan(layers, centers, tilts, starts, dur, out=True, wob=1.0):
    def frame(t):
        c = blank()
        for i, (lay, ce, ti, st) in enumerate(zip(layers, centers, tilts, starts)):
            s, a = pop(t, st, dur, out)
            if a <= 0.01: continue
            place(c, lay, (ce[0], ce[1] + 4 * wob * math.sin(2 * math.pi * t / 3.1 + i)), s, ti + 0.4 * wob * math.sin(2 * math.pi * t / 3.7 + i), a)
        return c
    return frame
def shrink(fn, s=0.82, pivot=(540, 380)):
    def frame(t):
        im = fn(t); im2 = im.resize((int(W * s), int(H * s)), Image.LANCZOS); c = blank()
        c.alpha_composite(im2, (int(pivot[0] - pivot[0] * s), int(pivot[1] - pivot[1] * s))); return c
    return frame
def glyph_star(r, c, s, col, w=4):
    if s <= 0.01: return
    x, y = c; r.line([(x - 34 * s, y), (x + 34 * s, y)], col, w); r.line([(x, y - 34 * s), (x, y + 34 * s)], col, w)
    r.line([(x - 14 * s, y - 14 * s), (x + 14 * s, y + 14 * s)], col, w * 0.6); r.line([(x - 14 * s, y + 14 * s), (x + 14 * s, y - 14 * s)], col, w * 0.6)
def traffic(r, w, title, bar=(38, 38, 44, 255), fg=GREY):
    """macOS window title bar with the three lights."""
    r.rr((0, 0, w, 54), 24, fill=bar); r.rr((0, 30, w, 54), 0, fill=bar)
    for k, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]): r.ell((22 + k * 28, 17, 42 + k * 28, 37), fill=(*col, 255))
    r.text((w / 2, 27), title, F(21, "demi"), fg)
def floating(content_region, center, dur, rad=24, tilt=0.0, wobble=0.4):
    """turn a finished Region into a popping, wobbling card frame function (static content)."""
    lay = shadowed(card(content_region.out().convert("RGB"), rad))
    def frame(t):
        c = blank(); s, a = pop(t, 0, dur)
        if a > 0.01: place(c, lay, center, s, tilt + wobble * math.sin(t * 1.5), a)
        return c
    return frame

# ---------- builders ----------
def classic_box(lines, dur, cy=330, size=50, fin=0.12, fout=0.12, pad=(44, 22), rad=16):
    """CapCut's classic white box with dark text (the preview version; the project uses a real text element)."""
    f = F(size, "demi")
    def frame(t):
        r = Region(0, cy - 180, W, 360); a = eo3(seg(t, 0, fin)) * (1 - eio(seg(t, dur - fout, dur)))
        if a <= 0.01: return full(r)
        lh = size * 1.22; tw = max(twidth(l, f) for l in lines); bw = tw + 2 * pad[0]; bh = len(lines) * lh + 2 * pad[1]
        b = (540 - bw / 2, cy - bh / 2, 540 + bw / 2, cy + bh / 2); r.shadow(b, rad, blur=6, alpha=70, dy=4); r.rr(b, rad, fill=WHITE)
        for i, l in enumerate(lines): r.text((540, cy - bh / 2 + pad[1] + lh * (i + 0.5) + 1), l, f, INK)
        r.fade(a); return full(r)
    return frame
def norm(w): return re.sub(r"[^a-z0-9']", "", w.lower())
def captions(cuelist, dur, cy=1500, size=60, hi=YEL):
    """word-synced captions: cuelist = [(start, end, text, keyword)], one keyword per cue in the highlight colour."""
    f = F(size, "heavy")
    def frame(t):
        c = blank()
        for st, en, txt, kw in cuelist:
            if not (st <= t < en): continue
            a = eo3(seg(t, st, st + 0.08)); r = Region(0, cy - 160, W, 320); kws = {norm(k) for k in kw.split()} if kw else set()
            words = txt.split(); lines = [words] if twidth(txt, f) <= 940 else [words[:len(words) // 2], words[len(words) // 2:]]
            for li, ws in enumerate(lines):
                line = " ".join(ws); x = 540 - twidth(line, f) / 2; y = cy + (li - (len(lines) - 1) / 2) * (size * 1.27)
                for w in ws:
                    col = hi if norm(w) in kws else WHITE
                    r.text((x + 3, y + 6), w, f, (0, 0, 0, 150), anchor="lm"); r.text((x, y), w, f, col, anchor="lm", stroke=2, sfill=(0, 0, 0, 160))
                    x += twidth(w + " ", f)
            r.fade(a); c.alpha_composite(full(r))
        return c
    return frame
def bigword(text, dur, col=WHITE, y=470, size=170, tracking=-4):
    """a big single word above the head: scales in from a blur, holds, fades."""
    def frame(t):
        c = blank(); r = Region(0, y - 200, W, 400); a = eo3(seg(t, 0, 0.10)) * (1 - eio(seg(t, dur - 0.15, dur)))
        if a <= 0.01: return c
        s = 1.45 - 0.45 * eo3(seg(t, 0, 0.24)); fs = FT(SANS, size * s, SANS_IDX["heavy"])
        tw = sum(fs.getlength(ch) / SS + tracking * s for ch in text) - tracking * s; x = 540 - tw / 2
        for ch in text:
            r.d.text(r.P(x + 4, y + 8), ch, font=fs, fill=(0, 0, 0, 120), anchor="lm"); r.d.text(r.P(x, y), ch, font=fs, fill=col, anchor="lm")
            x += fs.getlength(ch) / SS + tracking * s
        im = r.out(); br = 16 * (1 - eo3(seg(t, 0, 0.24)))
        if br > 0.5: im = im.filter(ImageFilter.GaussianBlur(br))
        if a < 1: im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        c.alpha_composite(im, (0, y - 200)); return c
    return frame
def chat_card(dur, script, cy=560, width=920, title="What are we making today?", sidebar=("New chat", "Chats", "Projects"), placeholder="Reply..."):
    """a light desktop-app window. script = [(local_t, action, payload)]:
       msg [lines] · badge text · drop file_name · skill "/command" · check line · spin line"""
    fh = F(31, "demi"); fm = F(25, "med"); fs = F(22, "demi"); fmono = f_mono(22)
    def frame(t):
        c = blank(); s, a = pop(t, 0, dur)
        if a <= 0.01: return c
        hgt = 600; r = Region(0, 0, width, hgt)
        r.rr((0, 0, width, hgt), 28, fill=PAPER); r.rr((0, 0, 170, hgt), 28, fill=(236, 232, 224, 255)); r.rr((120, 0, 170, hgt), 0, fill=(236, 232, 224, 255))
        for i, lab in enumerate(sidebar): r.text((22, 44 + i * 42), lab, F(19, "demi"), (90, 86, 80, 255), anchor="lm")
        cx = 170 + (width - 170) / 2; r.text((cx - 150, 60), "*", F(44, "heavy"), ACC); r.text((cx + 20, 62), title, fh, INK2)
        y = 118
        for st, act, pl in [(st, act, pl) for st, act, pl in script if st <= t]:
            lt = t - st
            if act == "msg":
                bx = (200, y, width - 30, y + 36 + 34 * len(pl)); r.rr(bx, 18, fill=WHITE, outline=(222, 216, 206, 255), width=2)
                for i, l in enumerate(pl):
                    n = int(eo3(seg(lt, 0.05 + i * 0.09, 0.4 + i * 0.09)) * len(l)); r.text((222, y + 26 + i * 34), l[:n], fm, INK2, anchor="lm")
                y = bx[3] + 16
            elif act == "badge":
                bp = eob(seg(lt, 0, 0.3))
                if bp > 0.01:
                    r.rr((width - 300, y, width - 30, y + 48), 24, fill=A(ACC, bp)); r.text((width - 268, y + 24), "*", F(30, "heavy"), A(WHITE, bp))
                    r.text((width - 150, y + 24), pl, fs, A(WHITE, bp)); check(r, (width - 56, y + 25), 14 * bp, WHITE, 4)
                y += 64
            elif act == "drop":
                zp = eo3(seg(lt, 0, 0.25))
                if zp > 0.01: r.rr((200, y, width - 30, y + 118), 18, fill=A(WHITE, zp), outline=A((190, 184, 176, 255), zp), width=2)
                fp = eob(seg(lt, 0.35, 0.75))
                if fp <= 0.01:
                    if zp > 0.01: r.text((cx, y + 59), "Drop files here", fm, A((150, 146, 140, 255), zp))
                else:
                    chip = (cx - 300 * fp, y + 59 - 30 * fp, cx + 300 * fp, y + 59 + 30 * fp); r.rr(chip, 14, fill=A((245, 236, 220, 255), fp), outline=A(ACC, fp), width=2)
                    r.rr((chip[0] + 14, y + 44, chip[0] + 40, y + 74), 4, fill=A(INK2, fp)); r.text((chip[0] + 56, y + 59), pl, F(21, "demi"), A(INK2, fp), anchor="lm")
                y += 134
            elif act == "skill":
                r.rr((200, y, width - 30, y + 54), 16, fill=WHITE, outline=(222, 216, 206, 255), width=2)
                n = min(len(pl), int(lt / 0.06)); r.text((222, y + 27), pl[:n] + ("|" if int(t * 3) % 2 else ""), fmono, INK2, anchor="lm"); y += 70
            elif act == "check":
                p = eo3(seg(lt, 0, 0.25))
                if p > 0.01: r.ell((214, y + 2, 240, y + 28), fill=A(GREEN, p)); check(r, (227, y + 15), 10 * p, WHITE, 3); r.text((256, y + 15), pl, fm, A(INK2, p), anchor="lm")
                y += 40
            elif act == "spin":
                ang = lt * 300; cxs, cys = 227, y + 15
                for k in range(8):
                    aa = math.radians(ang + k * 45); al = 0.2 + 0.8 * (k / 7)
                    r.ell((cxs + math.cos(aa) * 11 - 3, cys + math.sin(aa) * 11 - 3, cxs + math.cos(aa) * 11 + 3, cys + math.sin(aa) * 11 + 3), fill=A(ACC, al))
                r.text((256, y + 15), pl + "." * (1 + int(lt * 3) % 3), fm, (120, 116, 110, 255), anchor="lm"); y += 40
        r.rr((200, hgt - 70, width - 30, hgt - 22), 16, fill=WHITE, outline=(222, 216, 206, 255), width=2); r.text((222, hgt - 46), placeholder, F(20, "med"), (160, 156, 150, 255), anchor="lm")
        r.ell((width - 68, hgt - 62, width - 36, hgt - 30), fill=ACC)
        place(c, shadowed(card(r.out().convert("RGB"), 28)), (540, cy), s, -0.6 + 0.4 * math.sin(t * 1.5), a); return c
    return frame
def code_card(dur, lines, title="SKILL.md", cy=540, width=880):
    """dark editor window; lines = [(text, colour)] typed in one after another."""
    fm = f_mono(23); hgt = 100 + 36 * len(lines)
    def frame(t):
        c = blank(); s, a = pop(t, 0, dur)
        if a <= 0.01: return c
        r = Region(0, 0, width, hgt); r.rr((0, 0, width, hgt), 24, fill=CARD_DARK); traffic(r, width, title)
        for i, (l, col) in enumerate(lines):
            n = int(eo3(seg(t, 0.08 + i * 0.05, 0.36 + i * 0.05)) * len(l)); r.text((36, 92 + i * 36), l[:n], fm, col, anchor="lm")
        place(c, shadowed(card(r.out().convert("RGB"), 24)), (540, cy), s, 1.2, a); return c
    return frame
def finder_card(dur, rows, title, t_hi=None, hi_row=None, cy=520, width=860):
    """a Finder window listing (name, is_dir) rows; one row lights up at t_hi."""
    fm = F(26, "demi"); hgt = 90 + 58 * len(rows)
    def frame(t):
        c = blank(); s, a = pop(t, 0, dur)
        if a <= 0.01: return c
        r = Region(0, 0, width, hgt); r.rr((0, 0, width, hgt), 22, fill=(246, 246, 248, 255)); traffic(r, width, title, (226, 226, 230, 255), (70, 70, 76, 255))
        for i, (name, isdir) in enumerate(rows):
            rp = eo3(seg(t, 0.15 + i * 0.07, 0.4 + i * 0.07)); y = 104 + i * 58
            if rp <= 0.01: continue
            if name == hi_row and t_hi is not None:
                hp = eob(seg(t, t_hi, t_hi + 0.3))
                if hp > 0.01: r.rr((16, y - 26, width - 16, y + 26), 12, fill=A(YEL, 0.35 * hp), outline=A(YEL, hp), width=3)
            if isdir: r.rr((36, y - 16, 76, y + 14), 5, fill=(96, 165, 250, 255)); r.rr((36, y - 22, 54, y - 10), 3, fill=(96, 165, 250, 255))
            else: page(r, (56, y), 30, 38, 1.0, fill=WHITE, ink=(120, 120, 126, 255), lines=2)
            r.text((100, y), name, fm, A((40, 40, 46, 255), rp), anchor="lm")
        place(c, shadowed(card(r.out().convert("RGB"), 22)), (540, cy), s, -1.0, a); return c
    return frame
def player_card(dur, thumb_path, caption, t_typo=None, typo_len=5, t_click=None, t_lock=None, title="final.mp4", cy=560):
    """a dark player window: a frame of the video, a burned-in caption (typo circled), a cursor click that gets a shake, a lock."""
    thumb = Image.open(thumb_path).convert("RGB"); thumb = thumb.resize((236, int(thumb.height * 236 / thumb.width)), Image.LANCZOS)
    thumb = thumb.crop((0, 0, 236, min(420, thumb.height))); thumb_g = thumb.convert("L").convert("RGB").point(lambda v: int(v * 0.7))
    def frame(t):
        c = blank(); s, a = pop(t, 0, dur)
        if a <= 0.01: return c
        shake = 12 * math.sin(t * 46) if (t_click is not None and t_click + 0.1 <= t < t_click + 0.5) else 0
        r = Region(0, 0, 880, 540); r.rr((0, 0, 880, 540), 22, fill=CARD_DARK); traffic(r, 880, title)
        r.paste_rgb(thumb_g if (t_lock is not None and t >= t_lock + 0.15) else thumb, (60, 80)); x0 = 330
        r.text((x0, 120), caption, F(34, "heavy"), (235, 235, 240, 255), anchor="lm")
        if t_typo is not None:
            typ = seg(t, t_typo, t_typo + 0.3); tw = twidth(caption[:typo_len], F(34, "heavy"))
            if typ > 0.01: r.ell((x0 - 10 - 8 * typ, 92, x0 + tw + 10 + 8 * typ, 150), outline=A(YEL, typ), width=6)
        r.text((x0, 182), "one flat layer", F(24, "demi"), (150, 150, 156, 255), anchor="lm"); r.text((x0, 218), "nothing to click", F(24, "demi"), (150, 150, 156, 255), anchor="lm")
        r.rr((x0, 270, 840, 290), 10, fill=(60, 60, 66, 255)); r.rr((x0, 270, x0 + 300, 290), 10, fill=(120, 120, 126, 255))
        if t_lock is not None:
            lk = eob(seg(t, t_lock, t_lock + 0.3))
            if lk > 0.01: lock(r, (780, 150), 1.5 * lk, A(YEL, lk)); r.text((780, 215), "locked", F(20, "demi"), A(YEL, lk))
        if t_click is not None and seg(t, t_click, t_click + 0.6) > 0.01:
            tip = lp((760, 480), (x0 + 60, 135), eio(seg(t, t_click, t_click + 0.3))); cursor(r, tip, 1.0, 1 - eio(seg(t, t_click + 0.5, t_click + 0.6)))
            k = seg(t, t_click + 0.3, t_click + 0.55)
            if 0 < k < 1: r.ell((tip[0] - 60 * k, tip[1] - 60 * k, tip[0] + 60 * k, tip[1] + 60 * k), outline=A(YEL, 1 - k), width=5)
        place(c, shadowed(card(r.out().convert("RGB"), 22)), (540 + shake, cy), s, 0.8, a); return c
    return frame
def phone(path, w=270):
    im = Image.open(path).convert("RGB"); im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS); return shadowed(card(im, 26))
def yt_card(path, title, w=390):
    im = Image.open(path).convert("RGB"); im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    r = Region(0, 0, w, im.height + 54); r.rr((0, 0, w, im.height + 54), 18, fill=CARD_DARK); r.paste_rgb(im, (0, 0))
    f = F(19, "demi"); tt = title
    while twidth(tt, f) > w - 24 and len(tt) > 4: tt = tt[:-4] + "…"
    r.text((12, im.height + 27), tt, f, (225, 225, 230, 255), anchor="lm"); return shadowed(card(r.out().convert("RGB"), 18), 10, 0.45)
def serif_title(text, dur, t_sw=None, cy=330, size=150, sub=None, col=GOLD):
    """gold serif italic title with white sparkles and a tracked-caps subline; grows + bursts at t_sw."""
    fs = F(30, "demi")
    def frame(t):
        c = blank(); r = Region(0, cy - 180, W, 360); a = eo3(seg(t, 0, 0.18)) * (1 - eio(seg(t, dur - 0.2, dur)))
        if a <= 0.01: return c
        k = 1.0 + (0.10 * eob(seg(t, t_sw, t_sw + 0.4)) if t_sw is not None else 0); fi = f_serif_i(size * k); tw = twidth(text, fi)
        r.glow((540 - tw / 2 - 40, cy - 80, 540 + tw / 2 + 40, cy + 80), 60, col, blur=28, alpha=90)
        r.text((540 + 4, cy + 6), text, fi, (120, 80, 20, 128)); r.text((540, cy), text, fi, col); r.text((540 - 2, cy - 2), text, fi, (255, 246, 226, 140))
        sp = eo3(seg(t, 0.25, 0.6))
        for (x, y, s) in [(540 - tw / 2 - 70, cy - 60, 0.9), (540 + tw / 2 + 60, cy - 30, 1.1), (540 + tw / 2 + 20, cy + 80, 0.7), (540 - tw / 2 - 20, cy + 70, 0.6)]:
            glyph_star(r, (x, y), s * sp * (0.8 + 0.2 * math.sin(t * 7 + x)), WHITE)
        if sub:
            su = eo3(seg(t, 0.5, 0.9))
            if su > 0.01: r.text((540, cy + 112), sub, fs, A(CREAM, su))
        if t_sw is not None:
            b = seg(t, t_sw, t_sw + 0.6)
            if 0 < b < 1:
                for k2 in range(14):
                    ang = k2 * 26 + 7; rad = 100 + 480 * eo3(b); glyph_star(r, (540 + math.cos(math.radians(ang)) * rad, cy + 100 + math.sin(math.radians(ang)) * rad * 1.2), 0.6 * (1 - b), CREAM, 3)
        r.fade(a); return full(r)
    return frame
def sparkles(dur, n=16, seed=5):
    rnd = random.Random(seed); P = [(rnd.uniform(60, 1020), rnd.uniform(220, 1700), rnd.uniform(0.3, 0.8), rnd.uniform(0, 6.3), rnd.uniform(0.6, 1.6)) for _ in range(n)]
    def frame(t):
        c = blank(); r = Region(0, 0, W, H); a = eo3(seg(t, 0, 0.3)) * (1 - eio(seg(t, dur - 0.2, dur)))
        for x, y, s, ph, sp in P:
            tw = max(0.0, math.sin(t * sp * 2 + ph))
            if tw > 0.02: glyph_star(r, (x, y), s * tw, (255, 246, 226, 230), 3)
        r.fade(a); return full(r)
    return frame
def flash(dur, peak=0.9, col=(255, 250, 244)):
    def frame(t):
        a = peak * (1 - eo3(seg(t, 0, dur))); return Image.new("RGBA", (W, H), (*col, int(255 * a)))
    return frame
def serif_slide(text, dur, y=1400, size=170, caps=None, caps_at=0.0):
    """huge serif italic word sliding in from the right with a blur-in, drifting slowly; tiny tracked caps beneath."""
    fi = f_serif_b(size); fc = F(26, "demi")
    def frame(t):
        c = blank(); r = Region(0, y - 220, W, 440); a = eo3(seg(t, 0, 0.14)) * (1 - eio(seg(t, dur - 0.18, dur)))
        if a <= 0.01: return c
        x = 540 + 110 * (1 - eo3(seg(t, 0, 0.55))) - 28 * c01(t / max(dur, 0.1))
        r.text((x + 5, y + 7), text, fi, (0, 0, 0, 140)); r.text((x, y), text, fi, (244, 244, 246, 255))
        if caps and t >= caps_at:
            ca = eo3(seg(t, caps_at, caps_at + 0.3))
            if ca > 0.01: r.text((540, y + 118), caps, fc, A((225, 225, 230, 255), ca))
        im = r.out(); br = 12 * (1 - eo3(seg(t, 0, 0.3)))
        if br > 0.5: im = im.filter(ImageFilter.GaussianBlur(br))
        if a < 1: im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        c.alpha_composite(im, (0, y - 220)); return c
    return frame
def dust(dur, n=60, seed=11):
    rnd = random.Random(seed); P = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(1.5, 4), rnd.uniform(0, 6.3), rnd.uniform(8, 26)) for _ in range(n)]
    def frame(t):
        c = blank(); d = ImageDraw.Draw(c); a = eo3(seg(t, 0, 0.4)) * (1 - eio(seg(t, dur - 0.2, dur)))
        for x, y, s, ph, v in P:
            yy = (y - v * t * 2) % H; xx = x + 14 * math.sin(t * 0.8 + ph); al = int(120 * a * (0.5 + 0.5 * math.sin(t * 2 + ph)))
            if al > 0: d.ellipse((xx - s, yy - s, xx + s, yy + s), fill=(235, 235, 240, al))
        return c
    return frame
def comment_box(dur, word, t_type, t_send, others=(("@someone", "need this"),), cy=520):
    fm = F(34, "demi")
    def frame(t):
        c = blank(); s, a = pop(t, 0, dur)
        if a <= 0.01: return c
        r = Region(0, 0, 820, 300); r.rr((0, 0, 820, 300), 26, fill=CARD_DARK)
        r.text((36, 40), "Comments", F(24, "heavy"), (220, 220, 226, 255), anchor="lm"); r.line([(0, 70), (820, 70)], (60, 60, 66, 255), 2)
        for k, (nm, tx) in enumerate(list(others)[:2]):
            yy = 110 + k * 54; r.ell((36, yy - 16, 68, yy + 16), fill=(90, 90, 100, 255)); r.text((84, yy), nm, F(22, "demi"), (160, 160, 170, 255), anchor="lm")
            r.text((84 + twidth(nm, F(22, "demi")) + 14, yy), tx, F(22, "demi"), (225, 225, 230, 255), anchor="lm")
        r.rr((36, 222, 784, 276), 27, fill=(40, 40, 48, 255), outline=(80, 80, 90, 255), width=2)
        n = max(0, min(len(word), int((t - t_type) / 0.09))); txt = word[:n]
        if n == 0: r.text((66, 249), "Add comment...", fm, (130, 130, 140, 255), anchor="lm")
        else: r.text((66, 249), txt, F(38, "heavy"), YEL, anchor="lm")
        sp = eob(seg(t, t_send, t_send + 0.25)); r.ell((720, 229, 760, 269), fill=A(ACC, 0.5 + 0.5 * sp)); r.poly([(731, 249), (750, 240), (750, 258)], fill=WHITE)
        if 0 < sp < 1: r.ell((740 - 60 * sp, 249 - 60 * sp, 740 + 60 * sp, 249 + 60 * sp), outline=A(ACC, 1 - sp), width=5)
        place(c, shadowed(card(r.out().convert("RGB"), 26)), (540, cy), s, 0, a); return c
    return frame
def timeline_card(dur, t_fly, label="4 hours of cutting", cy=520):
    rnd = random.Random(3); segs = [(rnd.uniform(0, 0.95), rnd.uniform(0.02, 0.09)) for _ in range(27)]
    def frame(t):
        c = blank(); s, a = pop(t, 0, dur, out=False)
        if a <= 0.01: return c
        fl = eio(seg(t, t_fly, t_fly + 0.45)); r = Region(0, 0, 860, 300); r.rr((0, 0, 860, 300), 22, fill=CARD_DARK); r.text((430, 40), label, F(24, "heavy"), GREY)
        for i in range(3):
            y = 90 + i * 60; r.rr((30, y, 830, y + 44), 6, fill=(34, 34, 40, 255))
            for a0, w in segs[i * 9:(i + 1) * 9]: x0 = 30 + a0 * 800; r.rr((x0, y + 4, min(830, x0 + w * 800), y + 40), 5, fill=[(96, 128, 170, 255), (70, 150, 110, 255), (217, 119, 87, 255)][i])
        place(c, shadowed(card(r.out().convert("RGB"), 22)), (540 + 900 * fl, cy - 40 * fl), s, 0.5 - 10 * fl, a * (1 - fl)); return c
    return frame

# ---------- grades (apply to the take AND the cutout, same function, same seed) ----------
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_rad = np.sqrt(((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2)
VIG_BASE = np.clip(1.0 - 0.16 * np.clip(_rad - 0.6, 0, 1.2), 0, 1)[..., None]
VIG_SOFT = np.clip(1.0 - 0.30 * np.clip(_rad - 0.55, 0, 1.2), 0, 1)[..., None]
VIG_HARD = np.clip(1.0 - np.clip((_rad - 0.45) / 0.8, 0, 1) ** 1.3 * 0.62, 0, 1)[..., None]
def _bloom(a):
    small = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    s = np.asarray(small).astype(np.float32); s = np.clip(s - 168, 0, None) * 1.6
    return np.asarray(Image.fromarray(np.clip(s, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BILINEAR)).astype(np.float32)
def grade_base(arr, i, t):
    a = arr.astype(np.float32); a = (a - 128) * 1.04 + 128
    g = (a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11)[..., None]; a = g + (a - g) * 0.92
    a[..., 0] += 3; a[..., 2] -= 3; a *= VIG_BASE; return np.clip(a, 0, 255).astype(np.uint8)
def grade_cool(arr, i, t):
    a = arr.astype(np.float32) * 0.86 + 26.0
    a[..., 0] = a[..., 0] * 1.04 + 7; a[..., 1] = a[..., 1] * 1.01 + 3; a[..., 2] = a[..., 2] * 0.95 + 1
    g = a.mean(-1, keepdims=True); a = g + (a - g) * 0.88; a += _bloom(a) * 0.20; a *= VIG_SOFT
    a += np.random.RandomState(i).randn(H, W, 1).astype(np.float32) * 4.0; return np.clip(a, 0, 255).astype(np.uint8)
def grade_noir(arr, i, t):
    a = arr.astype(np.float32); g = (a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11)[..., None]; a = g + (a - g) * 0.30
    a = (a - 30.0) * 1.18; a[..., 0] *= 0.94; a[..., 1] *= 0.98; a[..., 2] *= 1.06; a *= VIG_HARD
    a *= 1.0 + 0.03 * math.sin(2 * math.pi * 9.3 * t) + 0.015 * math.sin(2 * math.pi * 23.0 * t + 1.0)
    a += np.random.RandomState(i + 7).randn(H, W, 1).astype(np.float32) * 7.0; return np.clip(a, 0, 255).astype(np.uint8)
GRADES = {"base": grade_base, "cool": grade_cool, "noir": grade_noir, None: None}

# ---------- sound ----------
SR_HZ = 48000
def tone_n(f, n, tau, amp=1.0):
    t = np.arange(n) / SR_HZ; return amp * np.sin(2 * np.pi * f * t) * np.exp(-t / tau)
def snd_tap():
    n = int(SR_HZ * 0.05); t = np.arange(n) / SR_HZ; rnd = np.random.RandomState(5); return (rnd.randn(n) * np.exp(-t / 0.0018) * 0.5 + tone_n(1500, n, 0.005, 0.3)) * 0.5
def snd_click():
    n = int(SR_HZ * 0.09); t = np.arange(n) / SR_HZ; rnd = np.random.RandomState(3)
    a = rnd.randn(n) * np.exp(-t / 0.0025) * 0.8 + tone_n(1900, n, 0.006, 0.5) + tone_n(700, n, 0.012, 0.35)
    up = np.zeros(n); k = int(SR_HZ * 0.055); m = n - k; up[k:] = rnd.randn(m) * np.exp(-np.arange(m) / SR_HZ / 0.002) * 0.45 + tone_n(2400, m, 0.004, 0.25); return (a + up) * 0.6
def snd_pop():
    n = int(SR_HZ * 0.18); t = np.arange(n) / SR_HZ; rnd = np.random.RandomState(6); return (rnd.randn(n) * np.exp(-t / 0.004) * 0.7 + tone_n(240, n, 0.05, 0.7) + tone_n(120, n, 0.08, 0.4)) * 0.7
def snd_sparkle():
    n = int(SR_HZ * 0.9); out = np.zeros(n)
    for k, (f, amp) in enumerate([(1760, .5), (2217, .45), (2637, .4), (3520, .35), (4186, .25)]): i = int(SR_HZ * 0.045 * k); out[i:] += tone_n(f, n - i, 0.22, amp)
    rnd = np.random.RandomState(1); t = np.arange(n) / SR_HZ; out += rnd.randn(n) * np.exp(-t / 0.05) * 0.12 * np.sin(2 * np.pi * 6000 * t); return out * 0.6
def snd_bass():
    n = int(SR_HZ * 1.2); t = np.arange(n) / SR_HZ; f = 120 * np.exp(-t / 0.18) + 38
    out = np.sin(2 * np.pi * np.cumsum(f) / SR_HZ) * np.exp(-t / 0.42); rnd = np.random.RandomState(2); out += rnd.randn(n) * np.exp(-t / 0.03) * 0.5; return out * 0.9
def snd_whoosh():
    n = int(SR_HZ * 0.55); t = np.arange(n) / SR_HZ; rnd = np.random.RandomState(8); x = rnd.randn(n); k = 24
    x = np.convolve(x, np.ones(k) / k, "same") - np.convolve(x, np.ones(k * 6) / (k * 6), "same"); return x * np.sin(np.pi * np.clip(t / 0.55, 0, 1)) ** 2 * 2.2
def snd_tick():
    n = int(SR_HZ * 0.03); t = np.arange(n) / SR_HZ; rnd = np.random.RandomState(4); return (rnd.randn(n) * np.exp(-t / 0.0012) * 0.6 + tone_n(2600, n, 0.003, 0.3)) * 0.45
SND = {"tap": (snd_tap, 0.5), "click": (snd_click, 0.7), "pop": (snd_pop, 0.6), "sparkle": (snd_sparkle, 0.55), "bass": (snd_bass, 0.8), "whoosh": (snd_whoosh, 0.5), "tick": (snd_tick, 0.5)}
def mix_track(dur, events):
    out = np.zeros(int(SR_HZ * dur) + 1)
    for t0, sig, g in events:
        i = int(t0 * SR_HZ); j = min(len(out), i + len(sig)); out[i:j] += sig[:j - i] * g
    return out
def write_wav(path, sig):
    import wave
    pcm = (np.clip(sig * 0.5, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR_HZ); w.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())

# ---------- output ----------
def premul(im):
    a = np.asarray(im).astype(np.float32); al = a[..., 3:4] / 255.0; a[..., :3] *= al; return Image.fromarray(a.astype(np.uint8))
_FN = None
def _call(i): return _FN(i)
def pipe(cmd, fn, n, workers=8):
    """feed frames fn(i) (bytes) into an ffmpeg stdin, in parallel (fork)."""
    global _FN; _FN = fn
    import multiprocessing as mp
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with mp.get_context("fork").Pool(workers) as pool:
        for buf in pool.imap(_call, range(n), chunksize=2): p.stdin.write(buf)
    p.stdin.close(); p.wait()

# ---------- the edit ----------
class Edit:
    """Holds one video's plan: the cut, the words, the cues, the clips, punch-ins and look windows; renders check/preview/layers."""
    def __init__(self, work, out, windows=None, push=None):
        self.work, self.out = work, out; self.video = f"{work}/cut.mp4"; self.frames = f"{work}/frames"
        self.masks = f"{work}/masks_fixed" if os.path.isdir(f"{work}/masks_fixed") else f"{work}/masks"
        self.nfr = len(glob.glob(f"{self.frames}/*.jpg")); self.dur = self.nfr / FPS
        self.segs = json.load(open(f"{work}/segments.json")) if os.path.exists(f"{work}/segments.json") else None
        self.windows = windows or {}          # {"cool": (a, b), "noir": (a, b)} → GRADES
        self.push = push                      # (a, b, scale) slow push-in window
        self.punch = []; self.clips = []; self.cuelist = []; self.blurb = None
        self.words = []
        for ln in open(f"{work}/words/words.txt"):
            p = ln.split()
            if len(p) >= 2: self.words.append((float(p[0]), norm(p[1]), p[1]))
    def T(self, word, n=1, after=None):
        k = 0
        for t, w, _ in self.words:
            if after is not None and t <= after: continue
            if w == word:
                k += 1
                if k == n: return t
        raise KeyError((word, n, after))
    def cues(self, CUES, proper=("Claude", "CapCut", "I", "I'll"), cap=1.5, skip=()):
        """CUES = [(phrase as spoken, keyword)] in order → self.cuelist. skip = windows whose cues are dropped."""
        P = {norm(p): p for p in proper}; out = []; i = 0
        for phrase, kw in CUES:
            toks = [norm(w) for w in phrase.split()]; j = i
            while j + len(toks) <= len(self.words) and [w[1] for w in self.words[j:j + len(toks)]] != toks: j += 1   # whole phrase, in order
            if j + len(toks) > len(self.words): raise KeyError(("cue not found after", phrase, [w[1] for w in self.words[i:i + 6]]))
            out.append([self.words[j][0], None, " ".join(P.get(self.words[k][1], self.words[k][1]) for k in range(j, j + len(toks))), kw.lower()]); i = j + len(toks)
        for k in range(len(out)):
            en = (out[k + 1][0] - 0.02) if k + 1 < len(out) else self.dur
            for a, b in skip:
                if out[k][0] < a <= en: en = a - 0.02
            out[k][1] = min(en, out[k][0] + cap)
        self.cuelist = [c for c in out if not any(a <= c[0] < b for a, b in skip)]; return self.cuelist
    def add(self, name, t0, t1, make, sfx=None, note="", layer="front"):
        t1 = min(t1, self.dur); self.clips.append(dict(name=name, layer=layer, t0=t0, dur=t1 - t0, fn=make(t1 - t0), sfx=sfx, note=note))
    def scale(self, t):
        for a, b, s in self.punch:
            if a <= t < b: return s
        if self.push and self.push[0] <= t < self.push[1]: return 1.0 + (self.push[2] - 1.0) * (t - self.push[0]) / (self.push[1] - self.push[0])
        return 1.0
    def graded(self, fr, i):
        t = i / FPS; arr = np.asarray(fr)
        for name, (a, b) in self.windows.items():
            if a <= t < b and GRADES.get(name): return Image.fromarray(GRADES[name](arr, i, t))
        return Image.fromarray(grade_base(arr, i, t)) if GRADES["base"] else fr
    def load(self, i): return self.graded(Image.open(f"{self.frames}/{i + 1:05d}.jpg").convert("RGB"), i)
    def load_mask(self, i):
        LUT = [0 if v < 100 else min(255, int((v - 100) * 1.9)) for v in range(256)]
        return Image.open(f"{self.masks}/{i + 1:05d}.png").convert("L").point(LUT).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.1))
    @staticmethod
    def zoom(im, s, rs):
        if s <= 1.0001: return im
        w, h = W / s, H / s; return im.resize((W, H), rs, box=(int((W - w) / 2), int((H - h) / 2), int((W + w) / 2), int((H + h) / 2)))
    def compose(self, i):
        t = i / FPS; s = self.scale(t); fr = self.zoom(self.load(i), s, Image.LANCZOS); out = fr.convert("RGBA")
        back = [c for c in self.clips if c["layer"] == "back"]
        for c in back:
            if c["t0"] <= t < c["t0"] + c["dur"]: out.alpha_composite(c["fn"](t - c["t0"]))
        if back and os.path.isdir(self.masks):
            p = fr.convert("RGBA"); p.putalpha(self.zoom(self.load_mask(i), s, Image.BILINEAR)); out.alpha_composite(p)
        for c in self.clips:
            if c["layer"] != "back" and c["t0"] <= t < c["t0"] + c["dur"]: out.alpha_composite(c["fn"](t - c["t0"]))
        return out.convert("RGB")
    def times(self):
        print(f"cut {self.dur:.2f}s  windows {self.windows}")
        for c in self.clips: print(f"{c['t0']:6.2f} {c['dur']:5.2f} {c['layer']:5s} {c['name']:22s} {c['note']}")
        for st, en, txt, kw in self.cuelist: print(f"  cue {st:6.2f}-{en:6.2f}  {txt:30s} [{kw}]")
    def check(self, ts, path=None, cols=9):
        rows = (len(ts) + cols - 1) // cols; sheet = Image.new("RGB", (cols * 330, rows * 580), (40, 40, 40))
        for k, t in enumerate(ts):
            im = self.compose(min(self.nfr - 1, max(0, int(t * FPS)))).resize((324, 576), Image.LANCZOS); sheet.paste(im, ((k % cols) * 330 + 3, (k // cols) * 580 + 2))
            ImageDraw.Draw(sheet).text(((k % cols) * 330 + 8, (k // cols) * 580 + 6), f"{t:.2f}", fill=(255, 255, 0))
        path = path or f"{self.work}/check.jpg"; sheet.save(path, quality=86); print("wrote", path)
    def sfx_events(self):
        ev = []
        for c in self.clips:
            if not c["sfx"]: continue
            for off, kind in ([(0.0, c["sfx"])] if isinstance(c["sfx"], str) else c["sfx"]):
                fn, g = SND[kind]; ev.append((c["t0"] + off, fn(), g))
        return ev
    def preview(self, path=None):
        sfx = f"{self.work}/sfx.wav"; write_wav(sfx, mix_track(self.dur, self.sfx_events())); out = path or f"{self.out}/PREVIEW.mp4"
        pipe(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", self.video, "-i", sfx,
              "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=first:normalize=0[a]", "-map", "0:v", "-map", "[a]",
              "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
             lambda i: self.compose(i).tobytes(), self.nfr)
        print("wrote", out)
    def take_pieces(self):
        """the take track: one piece per cut point, split again where a look window starts or ends."""
        if self.segs: tl = []; acc = 0.0
        else: return [(0.0, self.dur, "")]
        for a, b in self.segs: tl.append((acc, acc + (b - a))); acc += b - a
        cuts = sorted({x for ab in self.windows.values() for x in ab}); pieces = []
        for a, b in tl:
            pts = [a] + [c for c in cuts if a + 0.05 < c < b - 0.05] + [b]
            for p0, p1 in zip(pts, pts[1:]):
                mid = (p0 + p1) / 2; tag = next((n for n, (wa, wb) in self.windows.items() if wa <= mid < wb), "")
                pieces.append((p0, p1, tag))
        return pieces
    def layers(self, LD=None, cutout=True):
        LD = LD or f"{self.out}/capcut_layers"; os.makedirs(LD, exist_ok=True)
        for p0, p1, tag in self.take_pieces():
            fn = f"{LD}/01_{p0:05.2f}s_TAKE{('_' + tag) if tag else ''}.mp4"
            if os.path.exists(fn): continue
            i0, i1 = int(round(p0 * FPS)), int(round(p1 * FPS)); n = i1 - i0
            pipe(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-ss", f"{i0 / FPS:.4f}", "-t", f"{n / FPS:.4f}", "-i", self.video,
                  "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-af", "apad", "-t", f"{n / FPS:.6f}", fn],
                 lambda k, i0=i0: self.load(i0 + k).tobytes(), n)
            print("  wrote", os.path.basename(fn))
        cut = f"{LD}/03_00.00s_CUTOUT_alpha.mov"
        if cutout and os.path.isdir(self.masks) and not os.path.exists(cut):
            def co(i):
                p = self.load(i).convert("RGBA"); p.putalpha(self.load_mask(i)); return premul(p).tobytes()
            pipe(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-q:v", "11", "-vendor", "apl0", cut], co, self.nfr)
            print("  wrote cutout")
        write_wav(f"{LD}/05_00.00s_SFX.wav", mix_track(self.dur, self.sfx_events()))
        for c in self.clips:
            if c["layer"] == "text": continue
            tag = "02" if c["layer"] == "back" else "04"; fn = f"{LD}/{tag}_{c['t0']:05.2f}s_{c['name']}_{'BACK' if c['layer'] == 'back' else 'FRONT'}_alpha.mov"
            if os.path.exists(fn): continue
            n = int(round(c["dur"] * FPS)); f = c["fn"]
            pipe(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-vendor", "apl0", fn],
                 lambda i, f=f: premul(f(i / FPS)).tobytes(), n)
            print(f"  wrote {os.path.basename(fn)}  {c['dur']:.2f}s")
        json.dump({"punch": self.punch, "push": self.push, "blurb": self.blurb, "cues": self.cuelist, "fps": FPS}, open(f"{LD}/meta.json", "w"))
        print("layers done", LD)
    def run(self, argv, check_ts):
        mode = argv[1] if len(argv) > 1 else "times"
        if mode == "times": self.times()
        elif mode == "check": self.check(check_ts)
        elif mode == "preview": self.preview()
        elif mode == "layers": self.layers()
