"""Step 4: video render — zooms (punch-ins/push-ins), kinetic captions, hook depth text, cards, overlays, flashes.
usage: python3 render.py <project_dir> full            -> build/video_nosound.mp4
       python3 render.py <project_dir> stills t1 t2..   -> cache/still_<t>.png"""
import sys, os, subprocess, numpy as np, cv2, math, functools, time
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__)); import proj, paths, timeline as TL
P = proj.arg_project(); LIB = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920; FPS = P.FPS; FD = paths.FONTS + '/'
ACC = tuple(P.ACCENT); PINK = np.array(ACC) / 255.; INK = np.array((17, 17, 17)) / 255.; PAPER = (250, 250, 250)
GLOW = (PINK[0], PINK[1], PINK[2], 0.35)
AT = lambda v: TL.at(P, v)
PUSH = getattr(P, 'PUSH', 0.06)
# ---------------- fonts / sprites ----------------
@functools.lru_cache(None)
def font(name, size, wght=None):
    f = ImageFont.truetype(FD + name, size)
    if wght is not None:
        ax = f.get_variation_axes(); f.set_variation_by_axes([wght] if len(ax) == 1 else [min(32, max(14, size / 3)), wght])
    return f
SMALL = lambda s=54: font('BeVietnamPro-SemiBold.ttf', s)
BIG = lambda s=100: font('BeVietnamPro-ExtraBold.ttf', s)
BLACK = lambda s=240: font('BeVietnamPro-Black.ttf', s)
SERIF = lambda s=150, w=800: font('PlayfairDisplay-Italic-VariableFont_wght.ttf', s, w)
INTER = lambda s=100, w=800: font('Inter-VariableFont_opsz,wght.ttf', s, w)
FONTS = dict(small=lambda s: SMALL(s), big=lambda s: BIG(s), black=lambda s: BLACK(s), serif=lambda s: SERIF(s, 800),
             serif9=lambda s: SERIF(s, 900), inter=lambda s: INTER(s, 800), medium=lambda s: font('BeVietnamPro-Medium.ttf', s),
             bold=lambda s: font('BeVietnamPro-Bold.ttf', s))
COL = lambda c: tuple(PINK) if c == 'accent' else tuple(INK) if c == 'ink' else (1, 1, 1) if c == 'white' else tuple(np.array(c) / 255.)
class Sprite:
    def __init__(s, arr, ox, oy): s.a, s.ox, s.oy = arr, ox, oy
@functools.lru_cache(None)
def text_sprite(text, fkey, size, color, shadow=0.6, shadow_r=14, glow=None, glow_r=26, pad=70):
    f = FONTS[fkey](size); color = COL(color)
    l, t, r, b = f.getbbox(text, anchor='ls'); w, h = r - l + 2 * pad, b - t + 2 * pad
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).text((pad - l, pad - t), text, font=f, fill=255, anchor='ls')
    A = np.asarray(m, np.float32) / 255.; out = np.zeros((h, w, 4), np.float32)
    def add(col, alpha):
        lay = np.dstack([alpha[..., None] * np.array(col, np.float32), alpha]); out[:] = lay + out * (1 - alpha[..., None])
    if glow: g = cv2.GaussianBlur(A, (0, 0), glow_r) * glow; add(PINK, np.clip(g * 1.6, 0, 1))
    if shadow: sh = cv2.GaussianBlur(np.roll(A, 5, 0), (0, 0), shadow_r); add((0, 0, 0), np.clip(sh * shadow * 1.4, 0, shadow))
    add(color, A)
    return Sprite(out, pad - l, pad - t), (l, t, r, b), f.getlength(text)
def blit(canvas, sp, x, y, alpha=1.0):
    h, w = sp.shape[:2]; x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1 or alpha <= 0: return
    s = sp[y0 - y:y1 - y, x0 - x:x1 - x] * alpha; c = canvas[y0:y1, x0:x1]; c *= (1 - s[..., 3:4]); c += s[..., :3]
def ease_out(p): p = min(1, max(0, p)); return 1 - (1 - p) ** 3
def entrance(t, t0, dur=0.12, s0=0.85, b0=7.0):
    p = ease_out((t - t0) / dur); return p, s0 + (1 - s0) * p, b0 * (1 - p)
def place_token(canvas, tok, x, y, a, sc=1.0, bl=0.0):
    """tok = text_sprite(...) result; (x,y) = pen pos (left, baseline); scale/blur about the visual centre"""
    sp, bbox, adv = tok; arr = sp.a
    if bl > 0.3: arr = cv2.GaussianBlur(arr, (0, 0), bl)
    scx, scy = sp.ox + adv / 2, sp.oy + (bbox[1] + bbox[3]) / 2; ccx, ccy = x + adv / 2, y + (bbox[1] + bbox[3]) / 2
    if abs(sc - 1) > 1e-3: arr = cv2.resize(arr, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
    blit(canvas, arr, ccx - scx * sc, ccy - scy * sc, a)
def pill_sprite(text, fkey, size, fill, txtcol, h, padx, dot=None, glow=0.0, shadow=0.0, arrow=False, strike=False):
    f = FONTS[fkey](size); tw = f.getlength(text); fa = INTER(int(size * 1.1), 800); aw = fa.getlength('→') + 18 if arrow else 0
    dx = 34 if dot else 0; pw = int(tw + aw + dx + 2 * padx); pad = 60
    im = Image.new('RGBA', (pw + 2 * pad, h + 2 * pad), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    dr.rounded_rectangle([pad, pad, pad + pw, pad + h], h // 2, fill=tuple(fill) + (255,) if len(fill) == 3 else tuple(fill))
    if dot: dr.ellipse([pad + padx - 4, pad + h / 2 - 8, pad + padx + 12, pad + h / 2 + 8], fill=tuple(dot) + (255,))
    base = pad + h / 2 + size * 0.36
    dr.text((pad + padx + dx, base), text, font=f, fill=tuple(txtcol) + (255,), anchor='ls')
    if arrow: dr.text((pad + padx + dx + tw + 18, base), '→', font=fa, fill=tuple(txtcol) + (255,), anchor='ls')
    a = np.asarray(im, np.float32) / 255.; out = np.dstack([a[..., :3] * a[..., 3:4], a[..., 3:4]])
    if glow:
        g = cv2.GaussianBlur(a[..., 3], (0, 0), 22) * glow; out = out + np.dstack([g[..., None] * PINK, g[..., None]]) * (1 - out[..., 3:4])
    if shadow:
        g = cv2.GaussianBlur(np.roll(a[..., 3], 6, 0), (0, 0), 12) * shadow; out = out + np.dstack([np.zeros_like(a[..., :3]), g[..., None]]) * (1 - out[..., 3:4])
    return Sprite(out, (pw + 2 * pad) / 2, (h + 2 * pad) / 2), pw
def put_sprite(canvas, sp, cx, cy, a, sc=1.0, bl=0.0):
    arr = sp.a if bl < 0.3 else cv2.GaussianBlur(sp.a, (0, 0), bl)
    if abs(sc - 1) > 1e-3: arr = cv2.resize(arr, None, fx=sc, fy=sc)
    blit(canvas, arr, cx - sp.ox * sc, cy - sp.oy * sc, a)
# ---------------- face / zoom ----------------
faces = np.load(P.CACHE + '/faces.npy'); fcx = faces[:, 0] + faces[:, 2] / 2; fcy = faces[:, 1] + faces[:, 3] / 2
mouth = (faces[:, 11] + faces[:, 13]) / 2
def shot_of(t):
    for i in range(len(P.CUTS) - 1):
        if P.CUTS[i] - 1e-6 <= t < P.CUTS[i + 1] - 1e-6: return i
    return len(P.CUTS) - 2
ANCH = [(float(np.median(fcx[a:b])), float(np.median(fcy[a:b]))) for a, b in zip(P.CUT_FRAMES[:-1], P.CUT_FRAMES[1:])]
PUNCH = [dict(p, t0=AT(p['t0']), t1=AT(p['t1'])) for p in P.PUNCH]
def zoom_at(t):
    s = shot_of(t); t0, t1 = P.CUTS[s], P.CUTS[s + 1]; z = 1 + PUSH * (t - t0) / (t1 - t0)
    for p in PUNCH:
        if p['t0'] <= t < p['t1']: z = p['z'] * (1 + 0.02 * (t - p['t0']))
    return z, ANCH[s]
def warp(img, z, anch, interp=cv2.INTER_CUBIC):
    ax, ay = anch; M = np.float32([[z, 0, ax * (1 - z)], [0, z, ay * (1 - z)]])
    return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=interp, borderMode=cv2.BORDER_REFLECT)
# ---------------- cards / overlays: resolve times ----------------
CARDS = [dict(c, t0=AT(c['t0']), t1=AT(c['t1'])) for c in P.CARDS]
OVER = [dict(o, t0=AT(o['t0']), t1=AT(o['t1'])) for o in P.OVERLAYS]
FLASHES = [c['t1'] for c in CARDS if c.get('exit') == 'flash'] + [AT(x) for x in getattr(P, 'EXTRA_FLASHES', [])]
END_FADE = (P.WORDS[-1]['end'] + 0.02, P.DUR)
def in_card(t): return any(c['t0'] - 0.02 <= t < c['t1'] for c in CARDS)
# ---------------- captions ----------------
PAGES = TL.parse_pages(P)
def tok_sprite(tok):
    k, txt = tok['kind'], tok['text']
    low = txt if any(c.isupper() for c in txt) else txt.lower()
    if k == 'small': return text_sprite(low, 'small', 54, 'white', 0.75, 12)
    if k == 'big': return text_sprite(low, 'big', 100, 'white', 0.7, 16)
    return text_sprite(low, 'serif', 150, 'accent', 0.55, 18, 0.35, 24)
def layout_page(p):
    lines = []
    for ln in p['lines']:
        items = [tok_sprite(tk) + (tk,) for tk in ln]; sp = 20
        tot = sum(it[2] for it in items) + sp * (len(items) - 1)
        scale = min(1.0, 880 / tot)   # keep clear of TikTok's right rail
        lines.append(dict(items=items, tot=tot, asc=max(-it[1][1] for it in items), desc=max(it[1][3] for it in items), sp=sp, scale=scale))
    return lines, sum((l['asc'] + l['desc']) * l['scale'] for l in lines) + 2 * (len(lines) - 1)
def page_top(p):
    a = int(p['start'] * FPS); b = max(a + 1, int(p['end'] * FPS)); ys = []
    for fi in range(a, min(b, P.NFRAMES)):
        z, (ax, ay) = zoom_at(fi / FPS); ys.append(ay + (mouth[fi] - ay) * z)
    return float(np.clip((max(ys) if ys else 1000) + 115, 1110, 1240))
for p in PAGES: p['layout'] = layout_page(p); p['top'] = page_top(p)
def draw_captions(canvas, t):
    if in_card(t): return
    for p in PAGES:
        if not (p['start'] - 0.04 <= t < p['end']): continue
        if in_card(p['start']): continue   # page began under a card: don't flash it after the card exits
        lines, hgt = p['layout']; top = min(p['top'], 1530 - hgt)
        for o in OVER:
            if o['kind'] in ('cta', 'chips') and o['t0'] - 0.3 <= p['start'] < o['t1']: top = min(top, o.get('y', 1452) - 62 - hgt)
        fade = min(1, (p['end'] - t) / 0.035); y = top
        for l in lines:
            s = l['scale']; y += l['asc'] * s; x = W / 2 - l['tot'] * s / 2
            for sp, bbox, adv, tk in l['items']:
                t0 = tk['start'] - 0.04
                if t >= t0:
                    big = tk['kind'] != 'small'
                    a, sc, bl = entrance(t, t0, 0.16 if big else 0.11, 0.8 if big else 0.88, 8 if big else 5)
                    cy = (bbox[1] + bbox[3]) / 2   # scale about token centre, keep baseline position scaled
                    place_token(canvas, (sp, bbox, adv), x + adv * (s - 1) / 2, y + cy * (s - 1), a * fade, sc * s, bl)
                x += (adv + l['sp']) * s
            y += l['desc'] * s + 2
# ---------------- hook: big text behind the head ----------------
_masks = np.load(P.CACHE + '/masks.npz')['m']
def person_mask(fi, z, anch):
    m = cv2.resize(_masks[min(fi, len(_masks) - 1)], (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.
    m = cv2.GaussianBlur(np.clip((m - 0.5) * 2.2 + 0.5, 0, 1), (0, 0), 1.6); return warp(m, z, anch, cv2.INTER_LINEAR)
_HOOK = {}
def draw_hook(canvas, t, fi, z, anch, o):
    if 'toks' not in _HOOK:
        specs = o['tokens']; sizes = [s['size'] for s in specs]
        for _ in range(3):
            tot = sum(FONTS[s['font']](sz).getlength(s['text']) for s, sz in zip(specs, sizes)) + o.get('gap', 30) * (len(specs) - 1)
            if tot <= 990: break
            sizes = [int(sz * 990 / tot) for sz in sizes]
        _HOOK['toks'] = [text_sprite(s['text'], s['font'], sz, s['color'], 0.55 if s['color'] == 'white' else 0.45, 22,
                                     0.5 if s['color'] == 'accent' else None, 30) for s, sz in zip(specs, sizes)]
    toks = _HOOK['toks']; gap = o.get('gap', 30); tot = sum(tk[2] for tk in toks) + gap * (len(toks) - 1); x = W / 2 - tot / 2; base = o.get('base_y', 420)
    p_in, sc, bl = entrance(t, o['t0'] - 0.16, 0.30, 1.18, 10); fade = min(1, (o['t1'] - t) / 0.05)
    layer = np.zeros((H, W, 4), np.float32)
    for k, (tk, spec) in enumerate(zip(toks, o['tokens'])):
        s = sc
        if spec.get('pulse_at'): s *= 1 + 0.07 * math.exp(-((t - AT(spec['pulse_at']) - 0.02) / 0.09) ** 2)
        sp, bbox, adv = tk; arr = sp.a if bl < 0.3 else cv2.GaussianBlur(sp.a, (0, 0), bl)
        scx, scy = sp.ox + adv / 2, sp.oy + (bbox[1] + bbox[3]) / 2; ccx, ccy = x + adv / 2, base + (bbox[1] + bbox[3]) / 2
        if abs(s - 1) > 1e-3: arr = cv2.resize(arr, None, fx=s, fy=s)
        X, Y = int(round(ccx - scx * s)), int(round(ccy - scy * s)); h, w = arr.shape[:2]
        x0, y0, x1, y1 = max(0, X), max(0, Y), min(W, X + w), min(H, Y + h)
        src = arr[y0 - Y:y1 - Y, x0 - X:x1 - X]; dst = layer[y0:y1, x0:x1]; dst[:] = src + dst * (1 - src[..., 3:4])
        x += adv + gap
    k = (1 - person_mask(fi, z, anch)[..., None]) * p_in * fade
    canvas *= (1 - layer[..., 3:4] * k); canvas += layer[..., :3] * k
# ---------------- card backgrounds / icons ----------------
@functools.lru_cache(None)
def card_bg(style):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); bg = np.ones((H, W, 3), np.float32) * np.array(PAPER, np.float32) / 255.
    tint = np.clip(np.array(ACC) / 255. * 0.22 + 0.78, 0, 1); lav = np.array((226, 220, 255)) / 255.
    blobs = {0: [(980, 220, 520, tint, 0.85), (80, 1750, 620, lav, 0.75)], 1: [(540, 650, 700, tint, 0.75), (900, 1800, 600, lav, 0.6)],
             2: [(120, 260, 560, lav, 0.75), (980, 1650, 640, tint, 0.85)], 3: [(900, 300, 600, lav, 0.7), (150, 1500, 650, tint, 0.8)]}[style % 4]
    for cx, cy, r, col, s in blobs:
        d = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)))[..., None] * s; bg = bg + d * (col - bg)
    return np.clip(bg, 0, 1)
@functools.lru_cache(None)
def icon(kind, d=118):
    S = d * 2; im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im); wh = (255, 255, 255, 255); w = int(S * 0.1)
    dr.ellipse([0, 0, S - 1, S - 1], fill=ACC + (255,))
    if kind == 'x':
        m = S * 0.31; dr.line([m, m, S - m, S - m], fill=wh, width=w); dr.line([S - m, m, m, S - m], fill=wh, width=w)
    elif kind == 'check':
        dr.line([S * 0.27, S * 0.53, S * 0.43, S * 0.69, S * 0.74, S * 0.34], fill=wh, width=w, joint='curve')
    elif kind == 'down':
        dr.line([S / 2, S * 0.25, S / 2, S * 0.72], fill=wh, width=w); dr.line([S * 0.3, S * 0.52, S / 2, S * 0.74, S * 0.7, S * 0.52], fill=wh, width=w, joint='curve')
    a = np.asarray(im.resize((d, d), Image.LANCZOS), np.float32) / 255.; pad = 40
    o = np.pad(np.dstack([a[..., :3] * a[..., 3:4], a[..., 3:4]]), ((pad, pad), (pad, pad), (0, 0)))
    g = np.pad(cv2.GaussianBlur(a[..., 3], (0, 0), 14) * 0.45, pad)
    big = np.dstack([g[..., None] * PINK, g[..., None]]); return Sprite(o + big * (1 - o[..., 3:4]), pad, pad)
def directional_blur(img, dx, dy):
    L = int(max(abs(dx), abs(dy)))
    if L < 2: return img
    k = np.zeros((2 * L + 1, 2 * L + 1), np.float32)
    for i in range(L + 1): k[int(round(L + dy * i / L * 0.5)), int(round(L + dx * i / L * 0.5))] = 1
    return cv2.filter2D(img, -1, k / k.sum())
def white(canvas, a): canvas *= (1 - a); canvas += a
def strike(canvas, x0, x1, y, p, col=PINK, th=10):
    if p <= 0: return
    xe = int(x0 + (x1 - x0) * min(1, p)); cv2.line(canvas, (int(x0), int(y)), (xe, int(y)), tuple(float(c) for c in col), th, cv2.LINE_AA)
# ---------------- card types ----------------
_FIT = {}
def _fit_rows(c, rs, tx):
    """one common row size for the whole card so every row fits (numbers column reserved if numbered)"""
    key = (id(c), rs)
    if key not in _FIT:
        maxw = W - 70 - tx - (130 if c.get('numbered', True) else 0); sz = rs
        while sz > 40 and max(FONTS[r.get('font', 'serif')](sz).getlength(r['text']) for r in c['rows']) > maxw: sz = int(sz * 0.96)
        _FIT[key] = sz
    return _FIT[key]
def card_list(t, c):
    """title + rows (icon x/check/down/None + big serif text), each row appears at its time"""
    cv = card_bg(c.get('bg', 0)).copy(); y0, dy, rs = c.get('y0', 760), c.get('dy', 240), c.get('row_size', 160)
    if c.get('title'):
        a, sc, bl = entrance(t, c['t0'] + 0.10, 0.18, 0.9, 6)
        place_token(cv, text_sprite(c['title'], 'bold', c.get('title_size', 64), 'ink', 0), c.get('x', 190), y0 - 210, a * 0.85, sc, bl)
    for k, r in enumerate(c['rows']):
        tt = AT(r['at']) - 0.04 if r.get('at') is not None else c['t0'] + 0.14 + 0.08 * k
        if t < tt: continue
        p = ease_out((t - tt) / 0.18); y = y0 + k * dy; dx = 70 * (1 - p); bl = 7 * (1 - p); x = c.get('x', 190)
        tx = x
        if r.get('icon', c.get('icon')):
            ic = icon(r.get('icon', c.get('icon')), int(rs * 0.7)); arr = ic.a if bl < 0.3 else cv2.GaussianBlur(ic.a, (0, 0), bl)
            blit(cv, arr, x - ic.ox + dx, y - rs * 0.55 - ic.oy, p); tx = x + rs * 0.95
        fk = r.get('font', 'serif'); sz = r.get('size', _fit_rows(c, rs, tx))
        tok = text_sprite(r['text'], fk, sz, r.get('color', 'ink'), 0.12, 16)
        place_token(cv, tok, tx + dx, y, p, 1.0, bl)
        if c.get('numbered', True): place_token(cv, text_sprite(f'{k + 1:02d}', 'medium', 38, 'accent', 0), 900 + dx * 0.5, y - rs * 0.25, p * 0.9)
    return cv
def card_compare(t, c):
    """rows of  small label  +  big value  (optional animated strike-through on a value)"""
    cv = card_bg(c.get('bg', 2)).copy(); y0, dy = c.get('y0', 760), c.get('dy', 420); x = c.get('x', 150)
    if c.get('title'):
        a, sc, bl = entrance(t, c['t0'] + 0.08, 0.18, 0.9, 6)
        place_token(cv, text_sprite(c['title'], 'bold', 64, 'ink', 0), x, y0 - 230, a * 0.85, sc, bl)
    for k, r in enumerate(c['rows']):
        tl = AT(r.get('label_at', r['at'])) - 0.04
        y = y0 + k * dy
        if t >= tl:
            a, sc, bl = entrance(t, tl, 0.14, 0.9, 5)
            place_token(cv, text_sprite(r['label'], 'medium', 56, 'ink', 0), x, y - r.get('size', 190) * 0.95, a * 0.7, sc, bl)
        tv = AT(r['at']) - 0.04
        if t >= tv:
            a, sc, bl = entrance(t, tv, 0.18, 0.8, 9)
            tok = text_sprite(r['value'], r.get('font', 'serif9'), r.get('size', 190), r.get('color', 'ink'), 0.12, 16, 0.3 if r.get('color') == 'accent' else None)
            place_token(cv, tok, x, y, a, sc, bl)
            if r.get('strike_at') is not None:
                ts = AT(r['strike_at']); strike(cv, x - 10, x + tok[2] + 10, y - r.get('size', 190) * 0.32, (t - ts) / 0.18, PINK, 12)
    return cv
def card_tools(t, c):
    """chips (software names) that get crossed out, then a big result token"""
    cv = card_bg(c.get('bg', 3)).copy()
    if c.get('title'):
        a, sc, bl = entrance(t, c['t0'] + 0.08, 0.18, 0.9, 6)
        tok = text_sprite(c['title'], 'bold', c.get('title_size', 60), 'ink', 0); place_token(cv, tok, W / 2 - tok[2] / 2, c.get('y0', 560) - c.get('title_gap', 120), a * 0.8, sc, bl)
    for k, ch in enumerate(c['chips']):
        ta = AT(ch['at']) - 0.04
        if t < ta: continue
        a, sc, bl = entrance(t, ta, 0.16, 0.75, 6); y = c.get('y0', 560) + k * c.get('chip_dy', 150); cs = c.get('chip_size', 52)
        sp, pw = pill_sprite(ch['text'], 'bold', cs, (255, 255, 255), (17, 17, 17), int(cs * 2.15), int(cs * 0.85), dot=ACC, shadow=0.35)
        put_sprite(cv, sp, W / 2, y, a, sc, bl)
        if ch.get('strike_at') is not None:
            ts = AT(ch['strike_at']); p = (t - ts) / 0.16
            if p > 0:
                strike(cv, W / 2 - pw / 2 - 20, W / 2 + pw / 2 + 20, y, p, PINK, 12)
                cv[int(y - 60):int(y + 60), int(W / 2 - pw / 2 - 30):int(W / 2 + pw / 2 + 30)] *= 1  # keep
    if c.get('result'):
        r = c['result']; tr = AT(r['at']) - 0.04
        if t >= tr:
            a, sc, bl = entrance(t, tr, 0.2, 0.7, 10)
            tok = text_sprite(r['text'], r.get('font', 'serif9'), r.get('size', 260), 'accent', 0.15, 18, 0.4, 28)
            place_token(cv, tok, W / 2 - tok[2] / 2, r.get('y', 1420), a, sc, bl)
            if r.get('sub'):
                s2 = text_sprite(r['sub'], 'bold', 56, 'ink', 0); place_token(cv, s2, W / 2 - s2[2] / 2, r.get('y', 1420) + 110, a * 0.85, sc, bl)
    return cv
PIPR = dict(x=172, y=150, w=736, h=980, r=84)
def rrect_mask(w, h, r, ss=2):
    im = Image.new('L', (w * ss, h * ss), 0); ImageDraw.Draw(im).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], r * ss, fill=255)
    return np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255.
def card_pip(t, c, frame):
    """talking head shrinks into a rounded PiP with accent glow; label + big tokens below"""
    p = ease_out((t - c['t0']) / 0.32); tx, ty, tw, th, tr = PIPR['x'], PIPR['y'], PIPR['w'], PIPR['h'], PIPR['r']
    x = tx * p; y = ty * p; w = W + (tw - W) * p; h = H + (th - H) * p; r = tr * p
    out = card_bg(c.get('bg', 1)).copy()
    cw = W * (1 - p) + W * 0.92 * p; ch = cw / (w / h)
    if ch > H: ch = H; cw = ch * (w / h)
    x0 = np.clip(540 - cw / 2, 0, W - cw); y0 = np.clip(760 - ch * 0.42, 0, H - ch)
    sub = cv2.resize(frame[int(y0):int(y0 + ch), int(x0):int(x0 + cw)], (int(round(w)), int(round(h))), interpolation=cv2.INTER_AREA)
    m = rrect_mask(sub.shape[1], sub.shape[0], max(1, int(r)))[..., None]; X, Y = int(round(x)), int(round(y)); hh, ww = sub.shape[:2]
    gm = np.zeros((H, W), np.float32); gm[Y:Y + hh, X:X + ww] = m[:H - Y, :W - X, 0]
    g = cv2.GaussianBlur(gm, (0, 0), 38)[..., None] * 0.85 * p; out = out * (1 - g) + PINK * g
    reg = out[Y:Y + hh, X:X + ww]; reg[:] = reg * (1 - m[:reg.shape[0], :reg.shape[1]]) + sub[:reg.shape[0], :reg.shape[1]] * m[:reg.shape[0], :reg.shape[1]]
    lab = None
    for text, ta in c.get('labels', []):
        if t >= AT(ta) - 0.04: lab = (text, AT(ta) - 0.04)
    if lab:
        a, sc, bl = entrance(t, lab[1], 0.14, 0.9, 5); tok = text_sprite(lab[0], 'small', 58, 'ink', 0)
        place_token(out, tok, W / 2 - tok[2] / 2, c.get('label_y', 1215), a * 0.85, sc, bl)
    toks = [(text_sprite(b['text'], b.get('font', 'serif9'), b.get('size', 230), b.get('color', 'accent'), 0.15 if b.get('font', 'serif9') != 'inter' else 0, 18,
                         0.35 if b.get('color', 'accent') == 'accent' else None, 26), b) for b in c['big']]
    gap = 34; tot = sum(tk[2] for tk, _ in toks) + gap * (len(toks) - 1); xx = W / 2 - tot / 2
    pulse = 1 + sum(0.08 * math.exp(-((t - AT(pa) - 0.04) / 0.08) ** 2) for pa in c.get('pulse', []))
    for tk, b in toks:
        ta = AT(b['at']) - 0.04
        if t >= ta:
            a, sc, bl = entrance(t, ta, 0.18, 0.78, 9)
            place_token(out, tk, xx, c.get('big_y', 1440) + b.get('dy', 0), a, sc * pulse, bl)
        xx += tk[2] + gap
    return out
# ---------------- overlays on the talking head ----------------
def draw_chips(canvas, t, o):
    cs = o.get('size', 31); sps = [pill_sprite(s, 'bold', cs, (255, 255, 255), (17, 17, 17), int(cs * 2.06), int(cs * 0.65), dot=ACC, shadow=0.45) for s in o['texts']]
    gap = 12; tot = sum(pw for _, pw in sps) + gap * (len(sps) - 1); x = W / 2 - tot / 2; fade = min(1, (o['t1'] - t) / 0.04)
    for k, (sp, pw) in enumerate(sps):
        tt = AT(o['at'][k]) if 'at' in o else o['t0'] + 0.07 + 0.11 * k
        if t >= tt:
            a, sc, bl = entrance(t, tt, 0.14, 0.7, 4); put_sprite(canvas, sp, x + pw / 2, o.get('y', 1466), a * fade, sc, bl)
        x += pw + gap
_CTA = {}
def draw_cta(canvas, t, o):
    if 'sp' not in _CTA: _CTA['sp'] = pill_sprite(o['text'], 'big', 44, ACC, (255, 255, 255), 104, 44, glow=0.55, arrow=True)[0]
    a, sc, bl = entrance(t, o['t0'], 0.2, 0.75, 6)
    sc *= 1 + 0.025 * math.sin(max(0, t - o['t0'] - 0.3) * 2 * math.pi * 1.6) * (t > o['t0'] + 0.3)
    put_sprite(canvas, _CTA['sp'], W / 2, o.get('y', 1452), a * min(1, (o['t1'] - t) / 0.08), sc, bl)
# ---------------- compositor ----------------
def render(fi, frame_u8):
    t = fi / FPS; z, anch = zoom_at(t)
    fr = warp(frame_u8, z, anch).astype(np.float32) / 255.; canvas = fr.copy()
    for o in OVER:
        if o['kind'] == 'hook' and o['t0'] <= t < o['t1']: draw_hook(canvas, t, fi, z, anch, o)
    card = next((c for c in CARDS if c['t0'] <= t < c['t1']), None)
    if card is None:
        draw_captions(canvas, t)
        for o in OVER:
            if o['t0'] <= t < o['t1']:
                if o['kind'] == 'chips': draw_chips(canvas, t, o)
                if o['kind'] == 'cta': draw_cta(canvas, t, o)
    elif card['kind'] == 'pip':
        canvas = card_pip(t, card, fr)
    else:
        cv = dict(list=card_list, compare=card_compare, tools=card_tools)[card['kind']](t, card)
        p = ease_out((t - card['t0']) / 0.24); enter = card.get('enter', 'cut')
        if p < 1 and enter in ('slide_up', 'slide_left'):
            v = ease_out((t + 1 / FPS - card['t0']) / 0.24) - p
            if enter == 'slide_up':
                off = int(H * (1 - p)); cv = directional_blur(cv, 0, v * H * 0.9); canvas[off:] = cv[:H - off]
            else:
                off = int(W * (1 - p)); cv = directional_blur(cv, v * W * 0.9, 0); canvas[:, off:] = cv[:, :W - off]
        else: canvas = cv
    for ft in FLASHES:
        d = (t - ft) * FPS
        if -2.5 <= d < 0: white(canvas, 0.45 if d < -1.5 else 0.85)
        elif 0 <= d < 6: white(canvas, 0.92 * math.exp(-d / 1.6))
    for c in CARDS:   # optional flash INTO a card
        if c.get('enter') == 'flash':
            d = (t - c['t0']) * FPS
            if 0 <= d < 5: white(canvas, 0.9 * math.exp(-d / 1.4))
    if END_FADE[0] <= t: canvas *= max(0, 1 - (t - END_FADE[0]) / max(1e-3, END_FADE[1] - END_FADE[0] - 1 / FPS))
    return (np.clip(canvas, 0, 1) * 255 + 0.5).astype(np.uint8)
def read_frames(start=0, n=None):
    a = ['ffmpeg', '-v', 'error'] + (['-ss', f'{(start - 0.5) / FPS:.6f}'] if start else []) + ['-i', P.BUILD + '/base.mp4'] + (['-frames:v', str(n)] if n else [])
    p = subprocess.Popen(a + ['-vf', 'scale=in_color_matrix=bt709:in_range=tv:out_range=pc', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, bufsize=10 ** 8)
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
if __name__ == '__main__':
    if sys.argv[2] == 'stills':
        for ts in sys.argv[3:]:
            fi = int(round(float(ts) * FPS)); Image.fromarray(render(fi, next(read_frames(fi, 1)))).save(f'{P.CACHE}/still_{float(ts):06.2f}.png')
        print('stills ok')
    else:
        # chunked + resumable: each CHUNK frames -> build/chunks/c_XXXXX.mp4 (written to .tmp then renamed); rerun skips finished chunks
        out = P.BUILD + '/video_nosound.mp4'; cd = P.BUILD + '/chunks'; os.makedirs(cd, exist_ok=True); CH = int(round(10 * FPS)); parts = []
        stamp = f"{os.path.getmtime(P.DIR + '/project.py'):.0f}"
        for c0 in range(0, P.NFRAMES, CH):
            n = min(CH, P.NFRAMES - c0); fn = f'{cd}/c_{c0:05d}_{stamp}.mp4'; parts.append(fn)
            if os.path.exists(fn): print('skip', fn, flush=True); continue
            tmp = fn + '.tmp.mp4'
            enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', P.FPS_STR, '-i', '-',
                                    '-vf', 'scale=out_color_matrix=bt709:out_range=tv', '-c:v', 'libx264', '-preset', 'slow', '-crf', str(getattr(P, 'CRF', 17)),
                                    '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                                    '-color_range', 'tv', '-x264-params', f'keyint={int(round(2 * FPS))}', tmp], stdin=subprocess.PIPE)
            t0 = time.time(); k = 0
            for k, fr in enumerate(read_frames(c0, n)):
                enc.stdin.write(render(c0 + k, fr).tobytes())
            enc.stdin.close(); enc.wait(); assert k + 1 == n, (c0, k + 1, n)
            os.rename(tmp, fn); print('chunk', c0, n, f'{time.time() - t0:.0f}s', flush=True)
        lst = cd + '/list.txt'; open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', out], check=True)
        nf = subprocess.run(['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v', '-show_entries', 'stream=nb_read_packets', '-of', 'csv=p=0', out], capture_output=True, text=True).stdout.strip()
        print('done', nf, 'frames (expected', P.NFRAMES, ')')
