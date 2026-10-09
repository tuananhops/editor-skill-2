"""Video render: punch-ins/push-ins, kinetic captions, hook depth text, cards, flashes.
usage: s4_render.py full            -> build/video_nosound.mp4
       s4_render.py stills t1 t2 .. -> cache/still_<t>.png"""
import os  # v1 reference build: paths via env (see README.md in this folder)
R = os.environ.get('V1_ROOT', '.'); REPO = os.environ.get('EDITOR_SKILL_ROOT', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
MODELS = os.environ.get('EDITOR_MODELS_DIR', REPO + '/pipeline/models'); FONTS = os.environ.get('EDITOR_FONTS_DIR', REPO + '/assets/fonts'); MUSICDIR = os.environ.get('EDITOR_MUSIC_DIR', REPO + '/assets/music')
import sys, subprocess, numpy as np, cv2, math, functools
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import timeline as T
W, H = 1080, 1920; FPS = T.FPS; FD = FONTS + '/'
PINK = np.array(T.PINK) / 255.; INK = np.array(T.INK) / 255.

# ---------------- fonts ----------------
@functools.lru_cache(None)
def font(name, size, wght=None):
    f = ImageFont.truetype(FD + name, size)
    if wght is not None:
        ax = f.get_variation_axes()
        f.set_variation_by_axes([wght] if len(ax) == 1 else [min(32, max(14, size / 3)), wght])
    return f
SMALL = lambda s=54: font('BeVietnamPro-SemiBold.ttf', s)
BIG = lambda s=104: font('BeVietnamPro-ExtraBold.ttf', s)
SERIF = lambda s=140, w=800: font('PlayfairDisplay-Italic-VariableFont_wght.ttf', s, w)
INTER = lambda s=100, w=800: font('Inter-VariableFont_opsz,wght.ttf', s, w)

# ---------------- sprites (premultiplied float RGBA) ----------------
class Sprite:
    def __init__(s, arr, ox, oy): s.a, s.ox, s.oy = arr, ox, oy   # ox,oy = offset of anchor point inside arr
def text_sprite(text, f, color, shadow=0.6, shadow_r=14, glow=None, glow_r=26, pad=70):
    l, t, r, b = f.getbbox(text, anchor='ls')
    w, h = r - l + 2 * pad, b - t + 2 * pad
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).text((pad - l, pad - t), text, font=f, fill=255, anchor='ls')
    A = np.asarray(m, np.float32) / 255.
    out = np.zeros((h, w, 4), np.float32)
    def add(col, alpha):  # 'over' composite of a premultiplied layer onto out
        lay = np.dstack([alpha[..., None] * np.array(col, np.float32), alpha])
        out[:] = lay + out * (1 - alpha[..., None])
    if glow is not None:
        g = cv2.GaussianBlur(A, (0, 0), glow_r) * glow[3]; add(glow[:3], np.clip(g * 1.6, 0, 1))
    if shadow:
        sh = cv2.GaussianBlur(np.roll(A, 5, 0), (0, 0), shadow_r); add((0, 0, 0), np.clip(sh * shadow * 1.4, 0, shadow))
    add(color, A)
    return Sprite(out, pad - l, pad - t), (l, t, r, b), f.getlength(text)

def blit(canvas, sp_arr, x, y, alpha=1.0):
    """composite premultiplied sprite with its top-left at (x,y)"""
    h, w = sp_arr.shape[:2]; x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1: return
    s = sp_arr[y0 - y:y1 - y, x0 - x:x1 - x] * alpha
    c = canvas[y0:y1, x0:x1]; c *= (1 - s[..., 3:4]); c += s[..., :3]
def anim_sprite(sp, cx, cy, alpha, scale, blur):
    """place sprite so that its anchor lands at (cx,cy), scaled around anchor, blurred"""
    a = sp.a
    if blur > 0.3: a = cv2.GaussianBlur(a, (0, 0), blur)
    if abs(scale - 1) > 1e-3:
        a = cv2.resize(a, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    return a, cx - sp.ox * scale, cy - sp.oy * scale
def ease_out(p): p = min(1, max(0, p)); return 1 - (1 - p) ** 3
def entrance(t, t0, dur=0.12, s0=0.85, b0=7.0):
    p = ease_out((t - t0) / dur); return p, s0 + (1 - s0) * p, b0 * (1 - p)

# ---------------- face / zoom ----------------
faces = np.load(R + '/cache/faces.npy')
fcx = faces[:, 0] + faces[:, 2] / 2; fcy = faces[:, 1] + faces[:, 3] / 2
mouth = (faces[:, 11] + faces[:, 13]) / 2
def shot_of(t):
    for i in range(len(T.CUTS) - 1):
        if T.CUTS[i] - 1e-6 <= t < T.CUTS[i + 1] - 1e-6: return i
    return len(T.CUTS) - 2
ANCH = []
for i in range(len(T.CUT_FRAMES) - 1):
    a, b = T.CUT_FRAMES[i], T.CUT_FRAMES[i + 1]
    ANCH.append((float(np.median(fcx[a:b])), float(np.median(fcy[a:b]))))
def zoom_at(t):
    s = shot_of(t); t0, t1 = T.CUTS[s], T.CUTS[s + 1]
    z = 1 + T.PUSH * (t - t0) / (t1 - t0)
    for p in T.PUNCH:
        if p['t0'] <= t < p['t1']: z = p['z'] * (1 + 0.02 * (t - p['t0']))
    return z, ANCH[s]
def warp(img, z, anch, interp=cv2.INTER_CUBIC):
    ax, ay = anch
    M = np.float32([[z, 0, ax * (1 - z)], [0, z, ay * (1 - z)]])
    return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=interp, borderMode=cv2.BORDER_REFLECT)

# ---------------- captions ----------------
PAGES = T.parse_pages()
def in_card(t): return any(c['t0'] - 0.02 <= t < c['t1'] for c in T.CARDS)
def tok_sprite(tok):
    k = tok['kind']; txt = tok['text']
    if k == 'small': return text_sprite(txt.lower() if txt not in ('AI', 'AI?') else txt, SMALL(54), (1, 1, 1), shadow=0.75, shadow_r=12)
    if k == 'big': return text_sprite(txt.lower(), BIG(100), (1, 1, 1), shadow=0.7, shadow_r=16)
    txt = txt if any(c.isupper() for c in txt) else txt.lower()
    return text_sprite(txt, SERIF(150, 800), tuple(PINK), shadow=0.55, shadow_r=18, glow=(1.0, 0.31, 0.64, 0.35), glow_r=24)
def layout_page(p, cx=W / 2, maxw=860):
    lines = []
    for ln in p['lines']:
        items = [tok_sprite(tk) + (tk,) for tk in ln]
        sp = 20
        widths = [it[2] for it in items]; tot = sum(widths) + sp * (len(items) - 1)
        asc = max(-it[1][1] for it in items); desc = max(it[1][3] for it in items)
        lines.append(dict(items=items, tot=tot, asc=asc, desc=desc, sp=sp))
    hgt = sum(l['asc'] + l['desc'] for l in lines) + 2 * (len(lines) - 1)
    return lines, hgt
for p in PAGES: p['layout'] = layout_page(p)
def page_top(p):
    a, b = int(p['start'] * FPS), max(int(p['start'] * FPS) + 1, int(p['end'] * FPS))
    ys = []
    for fi in range(a, min(b, T.NFRAMES)):
        z, (ax, ay) = zoom_at(fi / FPS); ys.append(ay + (mouth[fi] - ay) * z)
    m = max(ys) if ys else 1000
    return float(np.clip(m + 115, 1110, 1240))
for p in PAGES: p['top'] = page_top(p)
def place_token(canvas, sp, bbox, adv, x, y, a, sc, bl):
    """x,y = pen position (left, baseline) on canvas; scale/blur around the token's visual centre"""
    arr = sp.a
    if bl > 0.3: arr = cv2.GaussianBlur(arr, (0, 0), bl)
    scx, scy = sp.ox + adv / 2, sp.oy + (bbox[1] + bbox[3]) / 2
    ccx, ccy = x + adv / 2, y + (bbox[1] + bbox[3]) / 2
    if abs(sc - 1) > 1e-3: arr = cv2.resize(arr, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
    blit(canvas, arr, ccx - scx * sc, ccy - scy * sc, a)
def draw_captions(canvas, t):
    if in_card(t): return
    for p in PAGES:
        if not (p['start'] - 0.04 <= t < p['end']): continue
        lines, hgt = p['layout']
        top = min(p['top'], 1530 - hgt)
        if any(o['kind'] == 'cta' and o['t0'] - 0.3 <= p['start'] < o['t1'] for o in T.OVERLAYS): top = min(top, 1400 - hgt)
        if any(o['kind'] == 'chips' and o['t0'] - 0.3 <= p['start'] < o['t1'] for o in T.OVERLAYS): top = min(top, 1422 - hgt)
        fade = min(1, (p['end'] - t) / 0.035)
        y = top
        for l in lines:
            y += l['asc']; x = W / 2 - l['tot'] / 2
            for sp, bbox, adv, tk in l['items']:
                t0 = tk['start'] - 0.04
                if t >= t0:
                    big = tk['kind'] != 'small'
                    a, sc, bl = entrance(t, t0, 0.16 if big else 0.11, 0.8 if big else 0.88, 8 if big else 5)
                    place_token(canvas, sp, bbox, adv, x, y, a * fade, sc, bl)
                x += adv + l['sp']
            y += l['desc'] + 2

# ---------------- hook: "100% AI" behind his head ----------------
_masks = np.load(R + '/cache/masks.npz')['m']
def person_mask(fi, z, anch):
    m = cv2.resize(_masks[fi], (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.
    m = np.clip((m - 0.5) * 2.2 + 0.5, 0, 1)
    m = cv2.GaussianBlur(m, (0, 0), 1.6)
    return warp(m, z, anch, cv2.INTER_LINEAR)
HOOK = None
def hook_layer():
    global HOOK
    if HOOK is None:
        sa, sb = 236, 300
        for _ in range(2):
            fa, fb = font('BeVietnamPro-Black.ttf', sa), SERIF(sb, 900)
            tot = fa.getlength('100%') + 30 + fb.getlength('AI')
            if tot <= 990: break
            sa, sb = int(sa * 990 / tot), int(sb * 990 / tot)
        a, ba, adv_a = text_sprite('100%', fa, (1, 1, 1), shadow=0.55, shadow_r=22)
        b, bb, adv_b = text_sprite('AI', fb, tuple(PINK), shadow=0.45, shadow_r=22, glow=(1.0, 0.31, 0.64, 0.5), glow_r=30)
        HOOK = (a, ba, adv_a, b, bb, adv_b)
    return HOOK
def draw_hook(canvas, t, fi, z, anch, o):
    a, ba, adv_a, b, bb, adv_b = hook_layer()
    gap = 30; tot = adv_a + gap + adv_b; x = W / 2 - tot / 2; base = 420
    lay = np.zeros((H, W, 3), np.float32); al = np.zeros((H, W, 1), np.float32)
    tmp = np.zeros((H, W, 4), np.float32)
    p_in, sc, bl = entrance(t, o['t0'] - 0.16, 0.30, 1.18, 10)   # already ~70% in on frame 0 (thumbnail)
    fade = min(1, (o['t1'] - t) / 0.05)
    pulse = 1 + 0.07 * math.exp(-((t - 2.22) / 0.09) ** 2)     # "AI" spoken at 2.20
    tc = np.zeros((H, W, 3), np.float32); ta = np.zeros((H, W, 1), np.float32)
    cv = np.zeros((H, W, 3), np.float32)
    # render the two words onto a transparent premultiplied layer
    layer = np.zeros((H, W, 4), np.float32)
    def put(sp, bbox, adv, px, s):
        arr = sp.a
        if bl > 0.3: arr = cv2.GaussianBlur(arr, (0, 0), bl)
        scx, scy = sp.ox + adv / 2, sp.oy + (bbox[1] + bbox[3]) / 2
        ccx, ccy = px + adv / 2, base + (bbox[1] + bbox[3]) / 2
        if abs(s - 1) > 1e-3: arr = cv2.resize(arr, None, fx=s, fy=s, interpolation=cv2.INTER_LINEAR)
        X, Y = int(round(ccx - scx * s)), int(round(ccy - scy * s)); h, w = arr.shape[:2]
        x0, y0, x1, y1 = max(0, X), max(0, Y), min(W, X + w), min(H, Y + h)
        src = arr[y0 - Y:y1 - Y, x0 - X:x1 - X]; dst = layer[y0:y1, x0:x1]
        dst[:] = src + dst * (1 - src[..., 3:4])
    put(a, ba, adv_a, x, sc)
    put(b, bb, adv_b, x + adv_a + gap, sc * pulse)
    m = person_mask(fi, z, anch)[..., None]
    k = (1 - m) * p_in * fade
    canvas *= (1 - layer[..., 3:4] * k); canvas += layer[..., :3] * k

# ---------------- generic helpers for cards ----------------
def rrect_mask(w, h, r, ss=2):
    im = Image.new('L', (w * ss, h * ss), 0); ImageDraw.Draw(im).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], r * ss, fill=255)
    return np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255.
@functools.lru_cache(None)
def card_bg(kind):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    bg = np.ones((H, W, 3), np.float32) * np.array(T.PAPER, np.float32) / 255.
    def blob(cx, cy, r, col, s):
        d = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)))[..., None] * s
        return d * (np.array(col, np.float32) / 255. - bg)
    if kind == 'nolist':
        bg = bg + blob(980, 220, 520, (255, 210, 232), 0.85); bg = bg + blob(80, 1750, 620, (226, 220, 255), 0.75)
    elif kind == 'pip_az':
        bg = bg + blob(540, 650, 700, (255, 214, 236), 0.75); bg = bg + blob(900, 1800, 600, (232, 226, 255), 0.6)
    else:
        bg = bg + blob(120, 260, 560, (232, 224, 255), 0.75); bg = bg + blob(980, 1650, 640, (255, 210, 232), 0.85)
    return np.clip(bg, 0, 1)
def x_icon(d=112):
    im = Image.new('RGBA', (d * 2, d * 2), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    dr.ellipse([0, 0, d * 2 - 1, d * 2 - 1], fill=T.PINK + (255,))
    m = d * 0.62; w = int(d * 0.2)
    dr.line([m, m, 2 * d - m, 2 * d - m], fill=(255, 255, 255, 255), width=w); dr.line([2 * d - m, m, m, 2 * d - m], fill=(255, 255, 255, 255), width=w)
    im = im.resize((d, d), Image.LANCZOS); a = np.asarray(im, np.float32) / 255.
    out = np.dstack([a[..., :3] * a[..., 3:4], a[..., 3:4]])
    glow = cv2.GaussianBlur(a[..., 3], (0, 0), 14) * 0.45; pad = 40
    big = np.zeros((d + 2 * pad, d + 2 * pad, 4), np.float32)
    big[..., :3] = glow_pad = 0
    g = np.pad(glow, pad); big[..., 3] = g; big[..., :3] = g[..., None] * PINK
    o = np.pad(out, ((pad, pad), (pad, pad), (0, 0))); big = o + big * (1 - o[..., 3:4])
    return Sprite(big, pad, pad)
def layer_over(canvas, layer_rgb, alpha):
    canvas *= (1 - alpha); canvas += layer_rgb * alpha
def directional_blur(img, dx, dy):
    L = int(max(abs(dx), abs(dy)))
    if L < 2: return img
    k = np.zeros((2 * L + 1, 2 * L + 1), np.float32)
    for i in range(L + 1):
        k[int(round(L + dy * i / L * 0.5)), int(round(L + dx * i / L * 0.5))] = 1
    k /= k.sum(); return cv2.filter2D(img, -1, k)

def word_t(word, after):
    return min(w['start'] for w in T.WORDS if w['word'].strip('?,').lower() == word.lower() and w['start'] >= after)

# ---------------- cards ----------------
_CS = {}
def card_nolist(t, c):
    """full-screen off-white card: không cần  ✕ lộ mặt  ✕ quay  ✕ edit"""
    cv = card_bg('nolist').copy()
    if 'nl' not in _CS:
        lab = text_sprite('không cần', font('BeVietnamPro-SemiBold.ttf', 60), tuple(INK * 1.0), shadow=0)
        rows = [text_sprite(s, SERIF(168, 800), tuple(INK), shadow=0.12, shadow_r=16) for s in ('lộ mặt', 'quay', 'edit')]
        nums = [text_sprite(s, font('BeVietnamPro-Medium.ttf', 38), tuple(PINK), shadow=0) for s in ('01', '02', '03')]
        _CS['nl'] = (lab, rows, nums, x_icon(118))
    lab, rows, nums, ic = _CS['nl']
    a, sc, bl = entrance(t, c['t0'] + 0.10, 0.18, 0.9, 6); place_token(cv, *lab, 190, 560, a * 0.75, sc, bl)
    times = [c['t0'] + 0.14, word_t('quay', c['t0']) - 0.04, word_t('edit', c['t0']) - 0.04]
    for k, (row, tt) in enumerate(zip(rows, times)):
        if t < tt: continue
        p = ease_out((t - tt) / 0.18); y = 790 + k * 250; dx = 70 * (1 - p)
        bl = 7 * (1 - p)
        arr = ic.a if bl < 0.3 else cv2.GaussianBlur(ic.a, (0, 0), bl)
        blit(cv, arr, 190 - ic.ox + dx, y - 92 - ic.oy, p)
        place_token(cv, *row, 350 + dx, y, p, 1.0, bl)
        place_token(cv, *nums[k], 880 + dx * 0.5, y - 40, p * 0.9, 1.0, 0)
    return cv
def card_savings(t, c):
    cv = card_bg('savings').copy()
    if 'sv' not in _CS:
        lab = text_sprite('tiết kiệm', font('BeVietnamPro-Bold.ttf', 72), tuple(INK), shadow=0)
        arrow = text_sprite('↓', INTER(170, 800), tuple(PINK), shadow=0, glow=(1.0, 0.31, 0.64, 0.45), glow_r=20)
        rows = [text_sprite(s, SERIF(170, 800), tuple(INK), shadow=0.12, shadow_r=16) for s in ('chi phí', 'thời gian')]
        nums = [text_sprite(s, font('BeVietnamPro-Medium.ttf', 38), tuple(PINK), shadow=0) for s in ('01', '02')]
        _CS['sv'] = (lab, arrow, rows, nums)
    lab, arrow, rows, nums = _CS['sv']
    a, sc, bl = entrance(t, c['t0'] + 0.08, 0.18, 0.9, 6); place_token(cv, *lab, 170, 640, a, sc, bl)
    times = [word_t('chi', c['t0']) - 0.04, word_t('thời', c['t0']) - 0.04]
    for k, (row, tt) in enumerate(zip(rows, times)):
        if t < tt: continue
        p, sc, bl = entrance(t, tt, 0.18, 0.86, 8); y = 900 + k * 260
        place_token(cv, *arrow, 150, y + 10 - 40 * (1 - p), p, 1.0, bl)
        place_token(cv, *rows[k], 300, y, p, sc, bl)
        place_token(cv, *nums[k], 880, y - 40, p * 0.9, 1.0, 0)
    return cv
PIP = dict(x=172, y=150, w=736, h=980, r=84)
def card_pip(t, c, frame):
    """talking head shrinks into a rounded PiP with a pink glow; 'A → Z' below"""
    p = ease_out((t - c['t0']) / 0.32)
    tx, ty, tw, th, tr = PIP['x'], PIP['y'], PIP['w'], PIP['h'], PIP['r']
    x = tx * p; y = ty * p; w = W + (tw - W) * p; h = H + (th - H) * p; r = tr * p
    bg = card_bg('pip_az').copy()
    # content: crop around face with PiP aspect, scaled into (w,h)
    asp = tw / th; ch = H * (1 - 0.25 * p); cw = ch * asp if p > 0 else W
    cw = min(W, max(cw, W * (1 - p) + cw * p)); ch = cw / (w / h)
    fx, fy = 540, 760
    x0 = np.clip(fx - cw / 2, 0, W - cw); y0 = np.clip(fy - ch * 0.42, 0, H - ch)
    sub = cv2.resize(frame[int(y0):int(y0 + ch), int(x0):int(x0 + cw)], (int(round(w)), int(round(h))), interpolation=cv2.INTER_AREA)
    m = rrect_mask(sub.shape[1], sub.shape[0], max(1, int(r)))[..., None]
    # glow
    gm = np.zeros((H, W), np.float32); X, Y = int(round(x)), int(round(y))
    hh, ww = sub.shape[:2]; gm[max(0, Y):Y + hh, max(0, X):X + ww] = m[:H - max(0, Y), :W - max(0, X), 0][:min(hh, H - Y), :min(ww, W - X)]
    g = cv2.GaussianBlur(gm, (0, 0), 38)[..., None] * 0.85 * p
    out = bg * (1 - g) + PINK * g
    reg = out[Y:Y + hh, X:X + ww]; reg[:] = reg * (1 - m) + sub * m
    # text
    if 'az' not in _CS:
        _CS['az'] = (text_sprite('làm từ', font('BeVietnamPro-SemiBold.ttf', 58), tuple(INK), shadow=0),
                     text_sprite('không những làm từ', font('BeVietnamPro-SemiBold.ttf', 58), tuple(INK), shadow=0),
                     text_sprite('A', SERIF(240, 900), tuple(PINK), shadow=0.15, shadow_r=18, glow=(1.0, 0.31, 0.64, 0.35), glow_r=26),
                     text_sprite('→', INTER(170, 700), tuple(INK), shadow=0),
                     text_sprite('Z', SERIF(240, 900), tuple(PINK), shadow=0.15, shadow_r=18, glow=(1.0, 0.31, 0.64, 0.35), glow_r=26))
    l1, l2, aa, ar, zz = _CS['az']
    lab = l1 if t < word_t('không', c['t0']) - 0.04 else l2
    tl = c['t0'] + 0.2 if lab is l1 else word_t('không', c['t0']) - 0.04
    a, sc, bl = entrance(t, tl, 0.14, 0.9, 5)
    place_token(out, *lab, W / 2 - lab[2] / 2, 1215, a * 0.85, sc, bl)
    ta = word_t('a', c['t0']) - 0.04
    if t >= ta:
        a, sc, bl = entrance(t, ta, 0.18, 0.78, 9)
        sc *= 1 + 0.08 * math.exp(-((t - (word_t('a', 18.0) + 0.04)) / 0.08) ** 2)
        g = 40; tot = aa[2] + ar[2] + zz[2] + 2 * g; x = W / 2 - tot / 2
        place_token(out, *aa, x, 1440, a, sc, bl)
        ta2 = word_t('đến', c['t0']) - 0.04; tz = word_t('z', c['t0']) - 0.04
        if t >= ta2:
            a2, sc2, bl2 = entrance(t, ta2, 0.16, 0.8, 6); place_token(out, *ar, x + aa[2] + g + 40 * (1 - a2) * -1, 1405, a2, 1.0, bl2)
        if t >= tz:
            a3, sc3, bl3 = entrance(t, tz, 0.18, 0.78, 9); place_token(out, *zz, x + aa[2] + ar[2] + 2 * g, 1440, a3, sc3 * (sc / max(1e-3, entrance(t, ta, 0.18, 0.78, 9)[1])), bl3)
    return out, p
def white(canvas, a): canvas *= (1 - a); canvas += a

# ---------------- overlays: chips, CTA ----------------
def chip_sprite(text):
    f = font('BeVietnamPro-Bold.ttf', 31); l, tp, r, b = f.getbbox(text, anchor='ls'); tw = f.getlength(text)
    pw, ph = int(tw + 50 + 20), 64; pad = 30
    im = Image.new('RGBA', (pw + 2 * pad, ph + 2 * pad), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    sh = Image.new('L', im.size, 0); ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 6, pad + pw, pad + ph + 6], ph // 2, fill=120)
    sh = np.asarray(sh.filter(ImageFilter.GaussianBlur(12)), np.float32) / 255.
    dr.rounded_rectangle([pad, pad, pad + pw, pad + ph], ph // 2, fill=(255, 255, 255, 240))
    dr.ellipse([pad + 20, pad + ph / 2 - 7, pad + 34, pad + ph / 2 + 7], fill=T.PINK + (255,))
    dr.text((pad + 44, pad + ph / 2 + 11), text, font=f, fill=T.INK + (255,), anchor='ls')
    a = np.asarray(im, np.float32) / 255.
    out = np.dstack([a[..., :3] * a[..., 3:4], a[..., 3:4]])
    shl = np.dstack([np.zeros_like(sh)[..., None].repeat(3, 2), sh[..., None]])
    out = out + shl * (1 - out[..., 3:4])
    return Sprite(out, (pw + 2 * pad) / 2, (ph + 2 * pad) / 2), pw
CHIPS = None
def draw_chips(canvas, t, o):
    global CHIPS
    if CHIPS is None: CHIPS = [chip_sprite(s) for s in ('TikTok', 'Facebook', 'YouTube', 'Instagram')]
    gap = 12; tot = sum(c[1] for c in CHIPS) + gap * 3; x = W / 2 - tot / 2; y = 1466
    fade = min(1, (o['t1'] - t) / 0.04)
    for k, (sp, pw) in enumerate(CHIPS):
        tt = 20.47 + 0.11 * k
        if t >= tt:
            a, sc, bl = entrance(t, tt, 0.14, 0.7, 4)
            arr = sp.a if bl < 0.3 else cv2.GaussianBlur(sp.a, (0, 0), bl)
            if abs(sc - 1) > 1e-3: arr = cv2.resize(arr, None, fx=sc, fy=sc)
            blit(canvas, arr, x + pw / 2 - sp.ox * sc, y - sp.oy * sc, a * fade)
        x += pw + gap
CTA = None
def draw_cta(canvas, t, o):
    global CTA
    if CTA is None:
        f = font('BeVietnamPro-ExtraBold.ttf', 44); txt = 'Inbox để được tư vấn chi tiết'
        tw = f.getlength(txt); fa = INTER(48, 800); aw = fa.getlength('→')
        pw, ph = int(tw + aw + 110), 104; pad = 60
        im = Image.new('RGBA', (pw + 2 * pad, ph + 2 * pad), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        dr.rounded_rectangle([pad, pad, pad + pw, pad + ph], ph // 2, fill=T.PINK + (255,))
        dr.text((pad + 44, pad + ph / 2 + 16), txt, font=f, fill=(255, 255, 255, 255), anchor='ls')
        dr.text((pad + 44 + tw + 22, pad + ph / 2 + 16), '→', font=fa, fill=(255, 255, 255, 255), anchor='ls')
        a = np.asarray(im, np.float32) / 255.
        g = cv2.GaussianBlur(a[..., 3], (0, 0), 22) * 0.55
        glow = np.dstack([g[..., None] * PINK, g[..., None]])
        out = np.dstack([a[..., :3] * a[..., 3:4], a[..., 3:4]]); out = out + glow * (1 - out[..., 3:4])
        CTA = Sprite(out, (pw + 2 * pad) / 2, (ph + 2 * pad) / 2)
    a, sc, bl = entrance(t, o['t0'], 0.2, 0.75, 6)
    sc *= 1 + 0.025 * math.sin(max(0, t - o['t0'] - 0.3) * 2 * math.pi * 1.6) * (t > o['t0'] + 0.3)
    fade = min(1, (o['t1'] - t) / 0.08)
    arr = CTA.a if bl < 0.3 else cv2.GaussianBlur(CTA.a, (0, 0), bl)
    if abs(sc - 1) > 1e-3: arr = cv2.resize(arr, None, fx=sc, fy=sc)
    blit(canvas, arr, W / 2 - CTA.ox * sc, 1452 - CTA.oy * sc, a * fade)

# ---------------- frame compositor ----------------
def render(fi, frame_u8):
    t = fi / FPS
    z, anch = zoom_at(t)
    fr = warp(frame_u8, z, anch).astype(np.float32) / 255.
    canvas = fr.copy()
    for o in T.OVERLAYS:
        if o['kind'] == 'hook' and o['t0'] <= t < o['t1']: draw_hook(canvas, t, fi, z, anch, o)
    card = next((c for c in T.CARDS if c['t0'] <= t < c['t1']), None)
    if card is None:
        draw_captions(canvas, t)
        for o in T.OVERLAYS:
            if o['t0'] <= t < o['t1']:
                if o['kind'] == 'chips': draw_chips(canvas, t, o)
                if o['kind'] == 'cta': draw_cta(canvas, t, o)
    else:
        if card['kind'] == 'pip_az':
            canvas, p = card_pip(t, card, fr)
        else:
            cv = card_nolist(t, card) if card['kind'] == 'nolist' else card_savings(t, card)
            p = ease_out((t - card['t0']) / 0.24)
            if p < 1:
                v = (ease_out((t + 1 / FPS - card['t0']) / 0.24) - p)
                if card['enter'] == 'slide_up':
                    off = H * (1 - p); cv = directional_blur(cv, 0, v * H * 0.9)
                    canvas[int(off):] = cv[:H - int(off)]
                else:
                    off = W * (1 - p); cv = directional_blur(cv, v * W * 0.9, 0)
                    canvas[:, int(off):] = cv[:, :W - int(off)]
            else: canvas = cv
    # white flashes around card exits
    for ft in T.FLASHES:
        d = (t - ft) * FPS
        if -2.5 <= d < 0: white(canvas, 0.45 if d < -1.5 else 0.85)
        elif 0 <= d < 6: white(canvas, 0.92 * math.exp(-d / 1.6))
    if T.END_FADE[0] <= t: canvas *= max(0, 1 - (t - T.END_FADE[0]) / (T.END_FADE[1] - T.END_FADE[0] - 1 / FPS))
    return (np.clip(canvas, 0, 1) * 255 + 0.5).astype(np.uint8)

def read_frames(start=0, n=None):
    args = ['ffmpeg', '-v', 'error']
    if start: args += ['-ss', f'{start / FPS:.5f}']
    args += ['-i', R + '/build/base.mp4']
    if n: args += ['-frames:v', str(n)]
    p = subprocess.Popen(args + ['-vf', 'scale=in_color_matrix=bt709:in_range=tv:out_range=pc', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, bufsize=10 ** 8)
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)

if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        for ts in sys.argv[2:]:
            fi = int(round(float(ts) * FPS)); fr = next(read_frames(fi, 1))
            Image.fromarray(render(fi, fr)).save(f'{R}/cache/still_{float(ts):06.2f}.png')
            print('still', ts, flush=True)
    else:
        out = sys.argv[2] if len(sys.argv) > 2 else R + '/build/video_nosound.mp4'
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '60000/1001', '-i', '-',
                                '-vf', 'scale=out_color_matrix=bt709:out_range=tv', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-profile:v', 'high', '-pix_fmt', 'yuv420p',
                                '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', '-x264-params', 'keyint=120', out], stdin=subprocess.PIPE)
        import time; t0 = time.time()
        for fi, fr in enumerate(read_frames()):
            enc.stdin.write(render(fi, fr).tobytes())
            if fi % 200 == 0: print(fi, f'{time.time() - t0:.0f}s', flush=True)
        enc.stdin.close(); enc.wait(); print('done', fi + 1, 'frames')
