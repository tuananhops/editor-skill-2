"""<NAME> — per-video config for pipeline/lib (run: pipeline/run.sh <this dir> <step>).
Copy this file into a new project dir (or run pipeline/lib/new_project.py on the cutting bot's hand-off folder).
All relative paths are relative to THIS project dir. Times in CARDS/OVERLAYS/PUNCH are OUTPUT-timeline seconds
or word refs 'word@after|offset' = start of the first transcript word `word` at/after `after` s, plus offset."""

# ---------------- input / output ----------------
SRC = 'input/SOURCE.mp4'          # ORIGINAL source footage (we rebuild the edit from it, frame-accurately)
CUT_REF = 'input/NAME_cut.mp4'    # cutting bot's rough cut (reference only, never re-encoded)
OUT_NAME = 'NAME_final.mp4'       # -> <project>/final/<OUT_NAME>
# FPS = '60000/1001'              # optional; default = source r_frame_rate (house rule: keep source fps)
# PRE = 'hqdn3d=1.2:1.0:3:3'      # optional ffmpeg filters applied to the source BEFORE select/scale (denoise, deinterlace...)
# CRF = 17                        # x264 CRF of the final (default 17)

# ---------------- edit: segment list (SOURCE seconds) ----------------
# From the cutting bot's notes.md table. Apply join fixes here (see SKILL.md 'Audio repair'):
#   move an in/out by a few frames to keep a clipped tail / drop a leaked onset of the next take,
#   extend a head/tail by 0.05-0.2 s of room tone when a join feels rushed; fade_in/fade_out in seconds (default 0.010).
def seg(a, b, **kw): return {'in': a, 'out': b, **kw}
SEGMENTS = [
    seg(0.00, 4.00),
    seg(5.20, 9.80, fade_out=0.020, note='why this join was changed'),
]

# ---------------- look ----------------
ACCENT = (255, 79, 163)   # #FF4FA3 — sample the strongest coloured element in the shot (mic, LED, shirt) and brighten it
# ffmpeg filter chain for the grade (applied in base.mp4). Daylight street footage: clean cinematic, NOT crushed.
GRADE = ("eq=contrast=1.07:gamma=0.98,curves=master='0/0 0.10/0.085 0.5/0.5 0.80/0.78 0.92/0.87 1/0.93',"
         "huesaturation=saturation=-0.40:colors=g+c:strength=2,huesaturation=saturation=-0.15:colors=b+y:strength=1.5,"
         "colorbalance=rh=0.015:bh=-0.01,vignette=angle=0.30:mode=forward")
PUSH = 0.06               # slow push-in per shot: 1.00 -> 1.06 across each shot
SEG_SECONDS = 4.0         # seconds of person masks computed for the behind-the-head hook

# ---------------- transcript (spoken form, one string per sentence) ----------------
# Used for MMS forced alignment + per-sentence leveling. Must match what is SAID (numbers as words: "bốn mười nghìn").
# Display text can differ: the caption DSL below maps tokens to transcript words.
TEXT = [
    "Câu thứ nhất đúng như người nói.",
    "Câu thứ hai.",
]

# ---------------- captions DSL (lib/timeline.py) ----------------
# one line = one caption page; ' / ' = line break inside the page; tokens separated by spaces
#   plain = small white Be Vietnam Pro   *word = big accent Playfair Display Italic   ^word = big white heavy sans
#   a_b = one token spanning 2 transcript words   tok{n} = token consumes n transcript words (e.g. *4–10_nghìn{3})
#   SKIP n = n words without captions (covered by a card / chips)   # comment lines are ignored
# 1-3 words per line, 1 accent keyword per page max 2. `run.sh <p> captions` prints every display≠spoken mapping.
PAGES = """
Câu / *thứ_nhất
đúng như / ^người_nói.
Câu / *thứ_hai.
"""

# ---------------- cards (full-screen graphics; voice continues) ----------------
# kinds: list (title + rows w/ icons x/check/down, numbered), compare (label + big value, optional strike_at),
#        tools (pill chips crossed out + big result), pip (talking head shrinks into glowing rounded PiP + big tokens)
# enter: cut | slide_up | slide_left | flash ; exit: cut | flash (white flash, max 1-2 per video)
CARDS = [
    # dict(kind='list', t0='cắt@10|-0.12', t1=13.0, enter='slide_up', exit='flash', title='AI tự làm hết:', icon='check',
    #      rows=[dict(text='cắt ghép', at='cắt@10'), dict(text='hiệu ứng', at='hiệu@11')]),
    # dict(kind='pip', t0='một@33|-0.08', t1=35.6, exit='cut', labels=[('1 con AI làm được', 'con@33')],
    #      big=[dict(text='10–20', at='mười@34', size=230), dict(text='video', font='inter', color='ink', size=110, at='video@35', dy=70)]),
]
# ---------------- overlays on the talking head ----------------
# hook: big text BEHIND the head (person segmentation) for the first seconds; cta: accent pill with arrow; chips: small pills
OVERLAYS = [
    # dict(kind='hook', t0=0.0, t1=3.9, base_y=430, tokens=[dict(text='hàng', font='black', size=150, color='white'),
    #                                                      dict(text='triệu?', font='serif9', size=200, color='accent', pulse_at='triệu@3')]),
    # dict(kind='chips', t0=20.4, t1=22.0, texts=['TikTok', 'Facebook', 'YouTube'], y=1466),
    # dict(kind='cta', t0='inbox@40|-0.06', t1=44.2, text='Inbox để được tặng skill', y=1590),
]
# ---------------- punch-ins on key beats (jump, hold, reset at t1 / next phrase). z 1.10-1.25 ----------------
PUNCH = [
    # dict(t0='sao@7|-0.06', t1=7.40, z=1.20),
]
EXTRA_FLASHES = []        # extra white flashes (times); card exit='flash' already adds one
# ---------------- audio ----------------
# CC0 music bed, ~6 LU under the voice, no ducking. 'path' = file name in assets/music or a path.
# offset = track time that lands on output 0 s; tip: lib/music_scan.py finds drops -> land a drop on the CTA word.
MUSIC = dict(path='music_not-it-lofimp3.mp3', offset=0.0, under_lu=6.0)
SFX_EXTRA = []            # [(time_or_wordref, 'pop'|'tick'|'whoosh'), ...]; pops on keywords / whooshes on punches are automatic
CTA_HIT = None            # word ref of the CTA (riser + hit land here), e.g. 'inbox@40'
TARGET_LUFS = -11.0
# VCHAIN = '...'          # override the voice-cleanup ffmpeg chain (default in lib/audio.py)
STILLS = [0.5, 2.0, 5.0]  # stills exported by `preview` for QA
