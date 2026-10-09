"""Shared edit decision list for the v1 (first approved video) post. All times are in NEW (output) timeline seconds.
Edit this file and re-run build/make_all.sh to revise."""
import os  # v1 reference build: paths via env (see README.md in this folder)
R = os.environ.get('V1_ROOT', '.'); REPO = os.environ.get('EDITOR_SKILL_ROOT', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
MODELS = os.environ.get('EDITOR_MODELS_DIR', REPO + '/pipeline/models'); FONTS = os.environ.get('EDITOR_FONTS_DIR', REPO + '/assets/fonts'); MUSICDIR = os.environ.get('EDITOR_MUSIC_DIR', REPO + '/assets/music')
import json
FPS = 60000/1001
JOIN_FRAME = 840                    # first frame of "Mọi người..." in the rough cut
INSERT_FRAMES = 7                   # natural-pause frames inserted from source at the join
SHIFT = INSERT_FRAMES/FPS           # 0.11678 s
JOIN_T = JOIN_FRAME/FPS             # 14.014 s (cut timeline)
NFRAMES = 2286
DUR = NFRAMES/FPS
PINK = (255, 79, 163)               # accent, sampled from mic (#C34C8E) and brightened -> #FF4FA3
INK = (17, 17, 17)                  # #111111
PAPER = (250, 250, 250)             # #FAFAFA

def shift(t):  # cut-timeline -> output timeline
    return t + SHIFT if t >= JOIN_T - 1e-6 else t

# shot boundaries (first frame index in output) = rough-cut hard cuts
CUT_FRAMES = [0, 220, 285, 428, 609, 840, 1114, 1274, 1445, 1704, 1918, NFRAMES]
CUTS = [f/FPS for f in CUT_FRAMES]

WORDS = json.load(open(R + '/build/words_aligned.json'))
for w in WORDS:
    w['start'] = round(shift(w['start']), 3); w['end'] = round(shift(w['end']), 3)

# ---- caption pages DSL -------------------------------------------------------
# lines separated by ' / '; tokens separated by spaces; '_' joins words of one token
# prefix '*' = accent keyword (pink italic serif, big); '^' = big white heavy sans; no prefix = small white
# a token consumes as many transcript words as it has '_'-parts (override with {n} suffix, e.g. A_→_Z{3})
# 'SKIP n' consumes n words without caption (covered by a card).
PAGES = """
đây là / cái *video
của mình làm / ^hoàn_toàn / với *AI
và tiếp cận / *hàng_triệu / người
chỉ bằng một / cách làm / *duy_nhất
đó chính là / sử dụng bộ / *skill
và *câu_lệnh / bên mình
bên mình đang / ^hỗ_trợ / rất nhiều bên
làm / *video
xây dựng / *thương_hiệu / ^cá_nhân
làm video / *bán_hàng
mà mình / không cần / *lộ_mặt
SKIP 7
mọi người / chỉ cần đưa
^mong_muốn / cho *AI
là *AI / có thể làm
SKIP 4
SKIP 7
mà *AI / còn đăng bài
cho mọi người
lên *tất_cả / nền tảng
giúp mọi người / *làm_sao?
SKIP 8
đây là / *cơ_hội
dành cho / anh em nào
nắm bắt / *sớm
để sử dụng / *AI
vào / ^công_việc / luôn
để giúp / công ty
*phát_triển / hơn
so với các / công ty / ^đối_thủ khác
chưa biết / sử dụng *AI?
hãy sử dụng / *AI / ^ngay
trước khi / *quá_muộn
*Inbox / cho bên mình
để bên mình / *tư_vấn / chi tiết
cách làm sao / sử dụng
cảm ơn / ^mọi_người / rất nhiều
"""

def parse_pages():
    pages = []; wi = 0
    for raw in PAGES.strip().splitlines():
        raw = raw.strip()
        if not raw: continue
        if raw.startswith('SKIP'):
            wi += int(raw.split()[1]); continue
        lines = []
        for ln in raw.split(' / '):
            toks = []
            for tk in ln.split():
                kind = 'small'
                if tk[0] == '*': kind, tk = 'key', tk[1:]
                elif tk[0] == '^': kind, tk = 'big', tk[1:]
                n = None
                if '{' in tk: tk, n = tk.split('{'); n = int(n.rstrip('}'))
                parts = tk.split('_'); n = n or len(parts)
                ws = WORDS[wi:wi+n]; wi += n
                toks.append(dict(text=' '.join(parts), kind=kind, start=ws[0]['start'], end=ws[-1]['end'],
                                 src=' '.join(w['word'] for w in ws)))
            lines.append(toks)
        pages.append(dict(lines=lines, start=lines[0][0]['start']))
    assert wi == len(WORDS), (wi, len(WORDS))
    for i, p in enumerate(pages):
        last = max(t['end'] for l in p['lines'] for t in l)
        nxt = pages[i+1]['start'] if i+1 < len(pages) else DUR
        p['end'] = min(nxt, last + 0.7)
    return pages

# ---- cards / graphic inserts (voice continues underneath) ------------------
# times: in, out. 'exit' = how it leaves: 'cut' or 'flash'
CARDS = [
    dict(kind='nolist', t0=12.10, t1=CUTS[5] + SHIFT * 0 + INSERT_FRAMES/FPS, enter='slide_up', exit='flash'),  # 12.10 -> 14.131
    dict(kind='pip_az', t0=16.55, t1=CUTS[6], enter='shrink', exit='cut'),                                    # 16.55 -> 18.585
    dict(kind='savings', t0=22.36, t1=CUTS[8], enter='slide_left', exit='flash'),                             # 22.36 -> 24.108
]
# overlays on the talking head (not full cards)
OVERLAYS = [
    dict(kind='hook', t0=0.0, t1=CUTS[1]),            # "100% AI" behind his head
    dict(kind='chips', t0=20.40, t1=CUTS[7]),         # platform chips
    dict(kind='cta', t0=34.62, t1=37.25),             # pink CTA pill
]
# punch-ins (instant jump, hold, reset on t1). z = zoom factor
PUNCH = [
    dict(t0=4.45, t1=CUTS[2], z=1.22),     # duy nhất
    dict(t0=9.37, t1=CUTS[4], z=1.15),     # xây dựng thương hiệu cá nhân
    dict(t0=11.33, t1=12.10, z=1.20),      # không cần lộ mặt
    dict(t0=20.42, t1=CUTS[7], z=1.16),    # tất cả nền tảng
    dict(t0=24.55, t1=25.60, z=1.14),      # cơ hội
    dict(t0=29.30, t1=29.88, z=1.18),      # phát triển
    dict(t0=33.74, t1=34.44, z=1.25),      # quá muộn
    dict(t0=34.44, t1=35.15, z=1.11),      # Inbox
]
PUSH = 0.06            # slow push-in over each calm stretch (1.00 -> 1.06)
FLASHES = []           # filled from cards with exit='flash'
for c in CARDS:
    if c['exit'] == 'flash': FLASHES.append(c['t1'])
END_FADE = (WORDS[-1]['end'] + 0.02, DUR)   # quick fade after the last word

if __name__ == '__main__':
    for p in parse_pages():
        print(f"{p['start']:6.2f}-{p['end']:6.2f} | " + ' / '.join(' '.join(('*' if t['kind']=='key' else '^' if t['kind']=='big' else '')+t['text']+f"[{t['start']:.2f}]" for t in l) for l in p['lines']))
        for l in p['lines']:
            for t in l:
                import unicodedata
                a = unicodedata.normalize('NFC', t['text'].lower().replace('?','')); b = unicodedata.normalize('NFC', t['src'].lower().replace('?','').replace(',',''))
                if a != b: print('      map:', t['text'], '<-', t['src'])
    print('DUR', DUR, 'cards', [(c['kind'], round(c['t0'],3), round(c['t1'],3)) for c in CARDS], 'end fade', END_FADE)
