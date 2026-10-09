"""ad_01 — approved example (batch 2). Per-video config for pipeline/lib (run: pipeline/run.sh <this dir>)."""
SRC = 'input/ad_01.mp4'   # source footage (NOT in repo), relative to this project dir
CUT_REF = 'input/ad_01_cut.mp4'     # rough cut (reference only)
FPS = '60000/1001'   # source was 59.94p (default when omitted: source fps)
OUT_NAME = 'ad_01_final.mp4'

# Rough-cut segment list (source seconds, from notes.md) with join fixes. fade_* in seconds.
def seg(a, b, **kw): return {'in': a, 'out': b, **kw}
SEGMENTS = [
    seg(3.50, 7.63),
    seg(9.64, 12.42),
    seg(14.96, 15.482, fade_out=0.020, note='+1 fr: let "sao" decay into the b-prevoicing instead of a hard clip'),
    seg(26.27, 31.88, note='head -0.18 s: room tone so "Bởi vì sao?" gets a beat before "Thì bây giờ"'),
    seg(32.10, 32.80, fade_out=0.012, note='-1 fr: drop the onset of the "v" of the abandoned take'),
    seg(37.46, 42.40, note='tail +0.10 s room tone: "After Effects, | Premiere" was rushed'),
    seg(44.79, 53.00),
    seg(56.01, 61.11),
    seg(62.64, 63.56, fade_out=0.025, note='-0.24 s: cut contained "phí một | Một con AI" (doubled một); end after phí'),
    seg(75.62, 78.34, note='head -0.14 s room tone: sentence pause after "chi phí"'),
    seg(78.55, 80.53, note='tail +0.05 s: full decay of "là"'),
    seg(83.80, 86.45),
    seg(86.72, 90.75),
]

ACCENT = (255, 79, 163)        # #FF4FA3 — pink mic is again the strongest colored element in the shot
GRADE = ("eq=contrast=1.07:gamma=0.98,curves=master='0/0 0.10/0.085 0.5/0.5 0.80/0.78 0.92/0.87 1/0.93',"
         "huesaturation=saturation=-0.40:colors=g+c:strength=2,huesaturation=saturation=-0.15:colors=b+y:strength=1.5,"
         "colorbalance=rh=0.015:bh=-0.01,vignette=angle=0.30:mode=forward")

# Corrected transcript of the edit, one string per sentence (used for MMS alignment + phrase leveling).
TEXT = [
    "Ngày xưa edit một video map dạng như này, vẽ biểu đồ như này, mất hàng triệu đồng.",
    "Thì bây giờ mọi người chỉ mất bốn mười nghìn một video như này.",
    "Bởi vì sao?",
    "Thì bây giờ AI đã edit một video như này rồi, từ việc cắt ghép những cảnh quay, thêm hiệu ứng, thêm âm thanh, thêm sub, hoặc ngay cả vẽ những bản đồ map khối này.",
    "Ngày xưa thì mình phải dùng DaVinci Resolve, After Effects, Premiere, tức là rất nhiều phần mềm để có thể làm được một video hoàn thiện.",
    "Thì bây giờ mọi người sẽ không cần phần mềm này nữa, không cần đầu tư hàng chục triệu để đầu tư phần mềm này nữa.",
    "Mà bây giờ mọi người chỉ cần đầu tư cho mình một trăm hai thôi, một con AI là mọi người có thể làm được video này rồi.",
    "Rất là tiết kiệm chi phí.",
    "Một con AI này có thể làm cho mọi người mười đến hai mươi video,",
    "nên là câu chuyện mọi người không cần lo lắng về việc là làm video chuyên nghiệp như nào, làm video map như nào thì AI làm hết.",
    "Inbox cho bên mình, bên mình sẽ tặng cho mọi người skill này.",
    "Inbox ngay nhá.",
    "Cảm ơn mọi người rất nhiều.",
]

# ---------------- captions (DSL, see lib/timeline.py) ----------------
# '*' accent serif key, '^' big white, '_' joins words, '{n}' = n transcript words for one display token
PAGES = """
Ngày xưa / *edit một video *map
dạng như này, / vẽ *biểu_đồ như này,
mất / ^hàng *triệu_đồng.
Thì bây giờ / mọi người chỉ mất
*4–10_nghìn{3} / một video như này.
Bởi vì / ^sao?
# "AI đã/có thể edit": verb said too fast to be sure -> caption omits it (edit{2} eats it)
Thì bây giờ *AI / edit{2} một video như này rồi,
từ việc / *cắt_ghép những cảnh_quay,
thêm *hiệu_ứng, / thêm *âm_thanh, thêm *sub,
hoặc ngay cả / vẽ những *bản_đồ
*map_khối này.
Ngày xưa thì / mình phải dùng
*DaVinci_Resolve,
*After_Effects,
*Premiere,
tức là / rất ^nhiều *phần_mềm
để có thể làm được / một video *hoàn_thiện.
Thì bây giờ / mọi người sẽ
^không_cần / *phần_mềm này nữa,
không cần đầu tư / *hàng_chục_triệu
để đầu tư / phần mềm này nữa.
Mà bây giờ / mọi người chỉ cần
đầu tư cho mình / *120k{3} thôi,
một con *AI / là mọi người
có thể làm được / video này rồi.
Rất là / ^tiết_kiệm *chi_phí.
Một con *AI này / có thể làm cho mọi người
*10_đến_20{4} *video,
nên là câu chuyện / mọi người ^không_cần *lo_lắng
về việc là / làm video *chuyên_nghiệp như nào,
làm video *map / như nào
thì *AI / ^làm_hết.
*Inbox cho bên mình, / bên mình sẽ tặng
cho mọi người / *skill này.
*Inbox / ^ngay nhá.
Cảm ơn mọi người / rất nhiều.
"""

# ---------------- cards (output-time refs: seconds or 'word@after|offset') ----------------
CARDS = [
    dict(kind='list', t0='cắt@10|-0.12', t1=13.013, enter='slide_up', exit='flash', title='AI tự làm hết:', icon='check',
         rows=[dict(text='cắt ghép', at='cắt@10'), dict(text='hiệu ứng', at='hiệu@11'),
               dict(text='âm thanh', at='âm@12'), dict(text='sub', at='sub@12')]),
    dict(kind='tools', t0='davinci@16|-0.12', t1='để@20.5|-0.03', enter='slide_left', exit='cut', title='Ngày xưa phải dùng', title_size=64, title_gap=190, chip_size=80, chip_dy=230, y0=620,
         chips=[dict(text='DaVinci Resolve', at='davinci@16'), dict(text='After Effects', at='after@17'), dict(text='Premiere', at='premiere@18')],
         result=dict(text='rất nhiều', at='rất@19.5', sub='phần mềm', size=210, y=1430)),
    dict(kind='compare', t0=26.86, t1='một@29.5|-0.04', enter='flash', exit='cut', y0=820, x=150,
         rows=[dict(label='trước', value='hàng chục triệu', at='mà@26.9', size=118, strike_at='trăm@28'),
               dict(label='giờ', value='120k', at='trăm@28|-0.12', color='accent', size=240)]),
    dict(kind='pip', t0='một@33|-0.08', t1=35.602, exit='cut',
         labels=[('1 con AI làm được', 'con@33')],
         big=[dict(text='10–20', at='mười@34', size=230), dict(text='video', font='inter', color='ink', size=110, at='video@35', dy=70)],
         pulse=['hai@35']),
]
OVERLAYS = [
    dict(kind='hook', t0=0.0, t1=3.95, base_y=430, tokens=[
        dict(text='hàng', font='black', size=150, color='white'),
        dict(text='triệu?', font='serif9', size=200, color='accent', pulse_at='triệu@3')]),
    dict(kind='cta', t0='inbox@40|-0.06', t1=44.278, text='Inbox để được tặng skill', y=1590),
]
PUNCH = [
    dict(t0='bốn@5|-0.05', t1=6.86, z=1.16),
    dict(t0='sao@7|-0.06', t1=7.40, z=1.28),
    dict(t0=13.013, t1=13.70, z=1.18),
    dict(t0='nhiều@19.9|-0.05', t1=21.95, z=1.14),
    dict(t0='không@23|-0.05', t1=24.45, z=1.18),
    dict(t0='rất@31.9|-0.05', t1=32.86, z=1.24),
    dict(t0='thì@39.5|-0.05', t1=40.22, z=1.22),
    dict(t0='inbox@42.5|-0.05', t1=43.45, z=1.14),
]
# music: HoliznaCC0 "Not It (Lofi)" (CC0, FMA). Drums-only break 144-146 s; full band re-enters at 146.08 = first "Inbox".
MUSIC = dict(path='music_not-it-lofimp3.mp3', offset=146.08 - 40.36, under_lu=6.0)
SFX_EXTRA = []
CTA_HIT = 'inbox@40'
STILLS = [0.5, 2.0, 3.5, 5.9, 7.3, 9.0, 11.0, 12.9, 13.4, 15.0, 17.0, 18.9, 20.2, 21.0, 23.8, 26.0, 27.6, 29.3, 30.5, 32.4, 33.6, 35.3, 37.0, 39.9, 41.0, 43.0]
