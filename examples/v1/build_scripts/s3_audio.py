"""Audio: insert natural pause at the 14.0 s join, level-match the quiet sentence, voice cleanup, music bed (CC0),
synth SFX, master to -11 LUFS / <= -1 dBTP. Writes stems to $V1_ROOT/stems."""
import os  # v1 reference build: paths via env (see README.md in this folder)
R = os.environ.get('V1_ROOT', '.'); REPO = os.environ.get('EDITOR_SKILL_ROOT', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
MODELS = os.environ.get('EDITOR_MODELS_DIR', REPO + '/pipeline/models'); FONTS = os.environ.get('EDITOR_FONTS_DIR', REPO + '/assets/fonts'); MUSICDIR = os.environ.get('EDITOR_MUSIC_DIR', REPO + '/assets/music')
import subprocess, numpy as np, soundfile as sf, pyloudnorm as pyln, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import timeline as T
from scipy.signal import butter, sosfilt, resample_poly
SR = 48000; ST = R + '/stems/'
SRC = os.environ['V1_SRC']
def load(args):
    p = subprocess.run(['ffmpeg', '-v', 'error'] + args + ['-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True)
    return np.frombuffer(p.stdout, np.float32).reshape(-1, 2).astype(np.float64)
def ff(x, flt):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'f64le', '-ar', str(SR), '-ac', str(x.shape[1]), '-i', '-', '-af', flt,
                        '-f', 'f64le', '-ar', str(SR), '-ac', str(x.shape[1]), '-'], input=x.astype(np.float64).tobytes(), capture_output=True)
    return np.frombuffer(p.stdout, np.float64).reshape(-1, x.shape[1]).copy()
meter = pyln.Meter(SR)
def lufs(x): return meter.integrated_loudness(x)

# ---------- 1. dialogue edit ----------
cut = load(['-i', os.environ['V1_CUT']])
src = load(['-ss', '31.70', '-i', SRC, '-t', '0.6'])       # source audio around the removed tail (src t = 31.70 + i/SR)
L = int(0.008 * SR)                                        # 8 ms crossfades
a = int(13.990 * SR); c = int(14.030 * SR)
shift = int(round(T.SHIFT * SR))
plen = shift + c - a + 2 * L
s0 = int((31.880 - (14.020 - (a - L) / SR) - 31.70) * SR)  # source sample aligned with cut sample a-L
piece = src[s0:s0 + plen].copy()
# gain-match source to the (loudnormed) cut on the overlapping pre-join room tone
ov_cut = cut[a - L - int(0.03 * SR): a - L]; ov_src = src[s0 - int(0.03 * SR): s0]
g = np.sqrt((ov_cut ** 2).mean() / ((ov_src ** 2).mean() + 1e-12)); piece *= g
print('join gain src->cut %.2f dB' % (20 * np.log10(g)))
ramp = np.linspace(0, 1, L)[:, None]
out = np.concatenate([cut[:a - L], cut[a - L:a] * (1 - ramp) + piece[:L] * ramp, piece[L:-L],
                      piece[-L:] * (1 - ramp) + cut[c:c + L] * ramp, cut[c + L:]])
assert abs(len(out) - (len(cut) + shift)) < 2
# ---------- 2. phrase level-matching (incl. "Giúp mọi người ... thời gian") ----------
# measure gated loudness per transcript sentence and pull each toward the median (+-4 dB), gain ramps sit in the gaps
segs = {}
for w in T.WORDS: segs.setdefault(w['seg'], []).append(w)
spans = [(ws[0]['start'] - 0.05, ws[-1]['end'] + 0.05) for k, ws in sorted(segs.items())]
lv = [lufs(out[int(x0 * SR):int(x1 * SR)]) if x1 - x0 > 0.45 else np.nan for x0, x1 in spans]
med = np.nanmedian(lv); env = np.ones(len(out)); r = int(0.03 * SR)
LEVEL_LOG = []
for (x0, x1), l in zip(spans, lv):
    gdb = 0.0 if np.isnan(l) else float(np.clip(med - l, -4, 4))
    LEVEL_LOG.append((round(x0, 2), round(x1, 2), round(l, 1), round(gdb, 1)))
    i0, i1 = int(x0 * SR), int(x1 * SR); gl = 10 ** (gdb / 20)
    env[i0:i1] = gl; env[max(0, i0 - r):i0] = np.linspace(env[max(0, i0 - r)], gl, i0 - max(0, i0 - r))
for i, ((x0, x1), l) in enumerate(zip(spans, lv)):
    print(f'  sentence {x0:6.2f}-{x1:6.2f} {l:6.1f} LUFS gain {LEVEL_LOG[i][3]:+.1f} dB')
out *= env[:, None]
N = int(round(T.DUR * SR)); out = np.pad(out, ((0, max(0, N - len(out))), (0, 0)))[:N]
sf.write(ST + 'voice_edit.wav', out.astype(np.float32), SR)
# ---------- 3. voice cleanup ----------
mono = out.mean(1, keepdims=True)
VCHAIN = ('highpass=f=80:p=2,arnndn=m=' + MODELS + '/rnn_std.rnnn:mix=0.7,afftdn=nr=6:nf=-32:tn=1,'
          'equalizer=f=250:t=q:w=1.0:g=-2,equalizer=f=3500:t=q:w=1.2:g=2,'
          'acompressor=threshold=-24dB:ratio=2.5:attack=20:release=150:knee=6,'
          'deesser=i=0.4:m=0.5:f=0.5,'
          'acompressor=threshold=-14dB:ratio=2:attack=15:release=200:knee=6')
voice = ff(mono, VCHAIN)[:N]
voice *= 10 ** ((-12.0 - lufs(voice)) / 20)
# per-shot consistency check
print('voice per shot LUFS:', [round(lufs(voice[int(a_ * SR):int(b_ * SR)]), 1) for a_, b_ in zip(T.CUTS[:-1], T.CUTS[1:])])
sf.write(ST + 'voice.wav', np.repeat(voice, 2, 1).astype(np.float32), SR)
# ---------- 4. music (CC0: HoliznaCC0 - "Unwind") ----------
MUSIC = MUSICDIR + '/music_unwind.mp3'; MOFF = 192.50 - 34.47   # kick returns after the breakdown exactly on "Inbox"
mus = load(['-ss', f'{MOFF:.3f}', '-i', MUSIC, '-t', f'{T.DUR + 0.5:.3f}'])[:N]
mus = ff(mus, 'equalizer=f=2500:t=q:w=1.5:g=-3,highpass=f=35')[:N]
MUSIC_UNDER = 6.0                                            # LU under the voice (dviet: 3.8-7.5)
mus *= 10 ** ((lufs(np.repeat(voice, 2, 1)) - MUSIC_UNDER - lufs(mus)) / 20)
fo = int(0.10 * SR); mus[-fo:] *= np.linspace(1, 0, fo)[:, None]
fi = int(0.03 * SR); mus[:fi] *= np.linspace(0, 1, fi)[:, None]
sf.write(ST + 'music.wav', mus.astype(np.float32), SR)
# ---------- 5. SFX (synthesized) ----------
rng = np.random.default_rng(7)
def bp(x, lo, hi, order=2): return sosfilt(butter(order, [lo, hi], 'bandpass', fs=SR, output='sos'), x)
def pop(level=-24):
    n = int(0.09 * SR); t = np.arange(n) / SR
    f = 900 * np.exp(-t * 30) + 520
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 55)
    s += bp(rng.standard_normal(n), 2500, 7000) * np.exp(-t * 160) * 0.25
    s /= np.abs(s).max(); return s * 10 ** (level / 20)
def tick(level=-30):
    n = int(0.03 * SR); t = np.arange(n) / SR
    s = bp(rng.standard_normal(n), 3000, 9000) * np.exp(-t * 300); s /= np.abs(s).max(); return s * 10 ** (level / 20)
def whoosh(d=0.32, level=-24, peak=0.6):
    n = int(d * SR); t = np.linspace(0, 1, n)
    env = np.where(t < peak, (t / peak) ** 2, ((1 - t) / (1 - peak)) ** 1.5)
    x = rng.standard_normal(n); out = np.zeros(n); blk = 512
    for k in range(0, n, blk):   # sweeping band-pass
        fc = 500 + 4500 * np.sin(np.pi * min(1, k / n)) ** 2
        out[k:k + blk] = bp(x[max(0, k - 2048):k + blk], fc * 0.6, min(fc * 1.6, 20000))[-len(x[k:k + blk]):]
    out *= env; out /= np.abs(out).max(); return out * 10 ** (level / 20)
def riser(d=1.4, level=-26):
    n = int(d * SR); t = np.linspace(0, 1, n); x = rng.standard_normal(n); out = np.zeros(n); blk = 512
    for k in range(0, n, blk):
        fc = 300 * (40 ** (k / n))
        out[k:k + blk] = bp(x[max(0, k - 2048):k + blk], fc * 0.7, min(fc * 1.4, 20000))[-len(x[k:k + blk]):]
    out *= t ** 2.5; out /= np.abs(out).max(); return out * 10 ** (level / 20)
def hit(level=-18):
    n = int(0.7 * SR); t = np.arange(n) / SR
    f = 120 * np.exp(-t * 18) + 45
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)
    s += bp(rng.standard_normal(n), 200, 3000) * np.exp(-t * 25) * 0.35
    s /= np.abs(s).max(); return s * 10 ** (level / 20)
sfx = np.zeros((N, 2)); events = []
def place(t, s, pan=0.0):
    i = int(t * SR); s = s[:max(0, N - i)]
    sfx[i:i + len(s), 0] += s * (1 - pan) ; sfx[i:i + len(s), 1] += s * (1 + pan)
def ev(t, name, s, pan=0.0): place(t, s, pan); events.append((round(t, 3), name))
in_card = lambda t: any(c['t0'] <= t < c['t1'] for c in T.CARDS)
for p in T.parse_pages():
    for l in p['lines']:
        for tk in l:
            if tk['kind'] == 'key' and not in_card(tk['start']):
                ev(tk['start'] - 0.03, 'pop', pop(-25 if tk['kind'] == 'key' else -29))
for c in T.CARDS:
    ev(c['t0'] - 0.12, 'whoosh(card)', whoosh(0.34, -22))
cs = {c['kind']: c for c in T.CARDS}
W = {(w['word'].strip('?,').lower(), round(w['start'], 2)): w for w in T.WORDS}
def wt(word, after): return min(w['start'] for w in T.WORDS if w['word'].strip('?,').lower() == word and w['start'] >= after)
for tt in [wt('quay', 12.0), wt('edit', 12.0)]: ev(tt - 0.03, 'pop(card item)', pop(-26))
ev(wt('a', 16.5) - 0.03, 'pop(A→Z)', pop(-25)); ev(wt('z', 16.5) - 0.03, 'pop(Z)', pop(-27)); ev(wt('a', 18.0) - 0.03, 'tick(A→Z pulse)', tick(-30))
for tt in [wt('phí', 22.3), wt('thời', 22.3)]: ev(tt - 0.03, 'pop(card item)', pop(-26))
for k in range(4): ev(20.47 + 0.11 * k, 'tick(chip)', tick(-31), pan=(-0.3 + 0.2 * k))
for p_ in T.PUNCH:
    if p_['t0'] not in (34.44,): ev(p_['t0'] - 0.10, 'whoosh(punch)', whoosh(0.18, -31, 0.7))
for f in T.FLASHES: ev(f - 0.02, 'tick(flash)', tick(-28))
ev(34.47 - 1.45, 'riser', riser(1.45, -27)); ev(34.47 - 0.01, 'hit(CTA)', hit(-17))
ev(34.62, 'pop(CTA pill)', pop(-27))
sf.write(ST + 'sfx.wav', sfx.astype(np.float32), SR)
json.dump(events, open(ST + 'sfx_events.json', 'w'))
# ---------- 6. mix + master ----------
vo = np.repeat(voice, 2, 1)
mix = vo + mus + sfx
mix *= 10 ** ((-11.0 - lufs(mix)) / 20)
# true-peak safe limiter: 4x oversampled look-ahead limiter at -1.5 dBFS
def tp_limit(x, ceil_db=-1.5, att=0.0015, rel=0.08):
    up = resample_poly(x, 4, 1, axis=0); sr4 = SR * 4; ceil = 10 ** (ceil_db / 20)
    pk = np.abs(up).max(1); need = np.minimum(1, ceil / np.maximum(pk, 1e-9))
    la = int(att * sr4)
    from scipy.ndimage import minimum_filter1d
    g = minimum_filter1d(need, size=2 * la + 1, mode='nearest')
    # release smoothing (one-pole, only upward); then attack smoothing by moving average
    a_r = np.exp(-1 / (rel * sr4)); gs = np.empty_like(g); cur = 1.0
    for i in range(0, len(g), 64):
        blkmin = g[i:i + 64].min()
        cur = blkmin if blkmin < cur else cur * a_r ** 64 + blkmin * (1 - a_r ** 64)
        gs[i:i + 64] = cur
    k = np.ones(la) / la; gs = np.minimum(np.convolve(gs, k, 'same'), g * 0 + 1)
    gs = np.minimum(gs, minimum_filter1d(gs, size=la, mode='nearest'))
    return resample_poly(up * gs[:, None], 1, 4, axis=0)[:len(x)]
for it in range(5):
    m = tp_limit(mix, -1.6); l = lufs(m)
    if abs(l - (-11.0)) < 0.05: break
    mix *= 10 ** ((-11.0 - l) / 20)
mix = m
sf.write(ST + 'mix_master.wav', mix.astype(np.float32), SR, subtype='FLOAT')
print('master LUFS %.2f' % lufs(mix), 'music LUFS %.1f' % lufs(mus), 'voice LUFS %.1f' % lufs(vo))
print('sfx events', len(events))
