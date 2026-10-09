"""Step 3: dialogue -> phrase leveling -> voice chain; music bed; synth SFX; mix + true-peak-safe master.
Reads stems/dialogue.wav, project MUSIC / SFX settings. Writes stems/{voice,music,sfx,mix_master}.wav.
usage: python3 audio.py <project_dir>"""
import subprocess, numpy as np, soundfile as sf, pyloudnorm as pyln, sys, os, json
sys.path.insert(0, os.path.dirname(__file__)); import proj, paths, timeline as TL
from scipy.signal import butter, sosfilt, resample_poly
from scipy.ndimage import minimum_filter1d
P = proj.arg_project(); SR = 48000; ST = P.STEMS + '/'
LIB = os.path.dirname(os.path.abspath(__file__))
def load(args):
    p = subprocess.run(['ffmpeg', '-v', 'error'] + args + ['-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).astype(np.float64)
def ff(x, flt):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'f64le', '-ar', str(SR), '-ac', str(x.shape[1]), '-i', '-', '-af', flt,
                        '-f', 'f64le', '-ar', str(SR), '-ac', str(x.shape[1]), '-'], input=x.astype(np.float64).tobytes(), capture_output=True)
    return np.frombuffer(p.stdout, np.float64).reshape(-1, x.shape[1]).copy()
meter = pyln.Meter(SR); lufs = meter.integrated_loudness
N = int(round(P.DUR * SR))
out, _ = sf.read(ST + 'dialogue.wav'); out = np.pad(out, ((0, max(0, N - len(out))), (0, 0)))[:N]
# ---------- phrase level matching ----------
segs = {}
for w in P.WORDS: segs.setdefault(w['seg'], []).append(w)
spans = [(ws[0]['start'] - 0.05, ws[-1]['end'] + 0.05) for k, ws in sorted(segs.items())]
spans = [(max(0.0, a), min(b, N / SR)) for a, b in spans]
lv = [lufs(out[int(a * SR):int(b * SR)]) if b - a > 0.45 else np.nan for a, b in spans]
med = np.nanmedian(lv); env = np.ones(N); r = int(0.03 * SR)
for (a, b), l in zip(spans, lv):
    gdb = 0.0 if np.isnan(l) else float(np.clip(med - l, -4, 4)); g = 10 ** (gdb / 20)
    i0, i1 = int(a * SR), int(b * SR); prev = env[max(0, i0 - r)]
    env[i0:i1] = g; env[max(0, i0 - r):i0] = np.linspace(prev, g, i0 - max(0, i0 - r))
    print(f'  sentence {a:6.2f}-{b:6.2f} {l:6.1f} LUFS  gain {gdb:+.1f} dB')
out *= env[:, None]
# ---------- voice chain ----------
VCHAIN = getattr(P, 'VCHAIN', None) or (
    f'highpass=f=80:p=2,arnndn=m={paths.model('rnn_std.rnnn')}:mix=0.7,afftdn=nr=6:nf=-32:tn=1,'
    'equalizer=f=250:t=q:w=1.0:g=-2,equalizer=f=3500:t=q:w=1.2:g=2,'
    'acompressor=threshold=-24dB:ratio=2.5:attack=20:release=150:knee=6,deesser=i=0.4:m=0.5:f=0.5,'
    'acompressor=threshold=-14dB:ratio=2:attack=15:release=200:knee=6')
voice = ff(out.mean(1, keepdims=True), VCHAIN)[:N]
voice = np.pad(voice, ((0, N - len(voice)), (0, 0)))
voice *= 10 ** ((-12.0 - lufs(voice)) / 20)
print('voice per shot LUFS:', [round(float(lufs(voice[int(a * SR):int(b * SR)])), 1) for a, b in zip(P.CUTS[:-1], P.CUTS[1:]) if b - a > 0.45])
vo = np.repeat(voice, 2, 1); sf.write(ST + 'voice.wav', vo.astype(np.float32), SR)
# ---------- music ----------
M = P.MUSIC
mus = load(['-ss', f"{M['offset']:.3f}", '-i', M['path'], '-t', f'{P.DUR + 0.5:.3f}'])[:N]
mus = np.pad(mus, ((0, N - len(mus)), (0, 0)))
mus = ff(mus, M.get('eq', 'equalizer=f=2500:t=q:w=1.5:g=-3,highpass=f=35'))[:N]
mus *= 10 ** ((lufs(vo) - M.get('under_lu', 6.0) - lufs(mus)) / 20)
fo = int(0.10 * SR); mus[-fo:] *= np.linspace(1, 0, fo)[:, None]; fi = int(0.03 * SR); mus[:fi] *= np.linspace(0, 1, fi)[:, None]
sf.write(ST + 'music.wav', mus.astype(np.float32), SR)
# ---------- SFX (synthesized) ----------
rng = np.random.default_rng(7)
def bp(x, lo, hi, order=2): return sosfilt(butter(order, [lo, hi], 'bandpass', fs=SR, output='sos'), x)
def pop(level=-24):
    n = int(0.09 * SR); t = np.arange(n) / SR; f = 900 * np.exp(-t * 30) + 520
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 55) + bp(rng.standard_normal(n), 2500, 7000) * np.exp(-t * 160) * 0.25
    return s / np.abs(s).max() * 10 ** (level / 20)
def tick(level=-30):
    n = int(0.03 * SR); t = np.arange(n) / SR; s = bp(rng.standard_normal(n), 3000, 9000) * np.exp(-t * 300)
    return s / np.abs(s).max() * 10 ** (level / 20)
def sweep(n, fc_fn):
    x = rng.standard_normal(n); o = np.zeros(n); blk = 512
    for k in range(0, n, blk):
        fc = fc_fn(k / n); o[k:k + blk] = bp(x[max(0, k - 2048):k + blk], fc * 0.6, min(fc * 1.6, 20000))[-len(x[k:k + blk]):]
    return o
def whoosh(d=0.32, level=-24, peak=0.6):
    n = int(d * SR); t = np.linspace(0, 1, n); env = np.where(t < peak, (t / peak) ** 2, ((1 - t) / (1 - peak)) ** 1.5)
    o = sweep(n, lambda u: 500 + 4500 * np.sin(np.pi * u) ** 2) * env; return o / np.abs(o).max() * 10 ** (level / 20)
def riser(d=1.4, level=-26):
    n = int(d * SR); t = np.linspace(0, 1, n); o = sweep(n, lambda u: 300 * 40 ** u) * t ** 2.5
    return o / np.abs(o).max() * 10 ** (level / 20)
def hit(level=-18):
    n = int(0.7 * SR); t = np.arange(n) / SR; f = 120 * np.exp(-t * 18) + 45
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6) + bp(rng.standard_normal(n), 200, 3000) * np.exp(-t * 25) * 0.35
    return s / np.abs(s).max() * 10 ** (level / 20)
sfx = np.zeros((N, 2)); events = []
def ev(t, name, s, pan=0.0):
    i = int(t * SR); s = s[:max(0, N - i)]
    sfx[i:i + len(s), 0] += s * (1 - pan); sfx[i:i + len(s), 1] += s * (1 + pan); events.append((round(t, 3), name))
CARDS = [dict(c, t0=TL.at(P, c['t0']), t1=TL.at(P, c['t1'])) for c in P.CARDS]
PUNCH = [dict(p_, t0=TL.at(P, p_['t0']), t1=TL.at(P, p_['t1'])) for p_ in P.PUNCH]
in_card = lambda t: any(c['t0'] <= t < c['t1'] for c in CARDS)
for p in TL.parse_pages(P):
    for l in p['lines']:
        for tk in l:
            if tk['kind'] == 'key' and not in_card(tk['start']): ev(tk['start'] - 0.03, 'pop', pop(-25))
for c in CARDS:
    for r in c.get('rows', []) + c.get('chips', []) + c.get('big', []):
        if r.get('at') is not None: ev(TL.at(P, r['at']) - 0.05, 'tick(row)', tick(-31))
    if c.get('enter', 'cut') != 'cut': ev(c['t0'] - 0.12, 'whoosh(card)', whoosh(0.34, -22))
for p_ in PUNCH:
    if not p_.get('silent'): ev(p_['t0'] - 0.10, 'whoosh(punch)', whoosh(0.18, -31, 0.7))
for c in CARDS:
    if c.get('exit') == 'flash': ev(c['t1'] - 0.02, 'tick(flash)', tick(-28))
for t, kind in getattr(P, 'SFX_EXTRA', []):
    t = TL.at(P, t)
    ev(t - 0.03, kind, dict(pop=lambda: pop(-26), tick=lambda: tick(-30), whoosh=lambda: whoosh(0.3, -24))[kind]())
if getattr(P, 'CTA_HIT', None) is not None:
    th = TL.at(P, P.CTA_HIT); ev(th - 1.45, 'riser', riser(1.45, -27)); ev(th - 0.01, 'hit(CTA)', hit(-17))
sf.write(ST + 'sfx.wav', sfx.astype(np.float32), SR); json.dump(sorted(events), open(ST + 'sfx_events.json', 'w'))
# ---------- mix + master ----------
TARGET = getattr(P, 'TARGET_LUFS', -11.0)
mix = vo + mus + sfx; mix *= 10 ** ((TARGET - lufs(mix)) / 20)
def tp_limit(x, ceil_db=-1.6, att=0.0015, rel=0.08):
    up = resample_poly(x, 4, 1, axis=0); sr4 = SR * 4; ceil = 10 ** (ceil_db / 20)
    need = np.minimum(1, ceil / np.maximum(np.abs(up).max(1), 1e-9)); la = int(att * sr4)
    g = minimum_filter1d(need, size=2 * la + 1, mode='nearest'); a_r = np.exp(-1 / (rel * sr4)); gs = np.empty_like(g); cur = 1.0
    for i in range(0, len(g), 64):
        m = g[i:i + 64].min(); cur = m if m < cur else cur * a_r ** 64 + m * (1 - a_r ** 64); gs[i:i + 64] = cur
    gs = np.minimum(np.convolve(gs, np.ones(la) / la, 'same'), 1); gs = np.minimum(gs, minimum_filter1d(gs, size=la, mode='nearest'))
    return resample_poly(up * gs[:, None], 1, 4, axis=0)[:len(x)]
for it in range(6):
    m = tp_limit(mix); l = lufs(m)
    if abs(l - TARGET) < 0.05: break
    mix *= 10 ** ((TARGET - l) / 20)
sf.write(ST + 'mix_master.wav', m.astype(np.float32), SR, subtype='FLOAT')
print('master LUFS %.2f | voice %.1f | music %.1f (under %.1f LU) | sfx events %d' % (lufs(m), lufs(vo), lufs(mus), lufs(vo) - lufs(mus), len(events)))
