"""Join inspector: for every segment boundary print a 10 ms energy strip (dB, source audio) around the out-point
and the next in-point, so clipped tails / leaked onsets / missing room tone are visible.
usage: python3 joins.py <project_dir> [pre=0.30] [post=0.30]"""
import sys, os, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); import proj
P = proj.arg_project(); SR = 16000
pre = float(sys.argv[2]) if len(sys.argv) > 2 else 0.30; post = float(sys.argv[3]) if len(sys.argv) > 3 else 0.30
x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', P.SRC, '-map', '0:a:0', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                                 capture_output=True).stdout, np.float32)
h = SR // 100
def db(t): i = int(t * SR); s = x[max(0, i):i + h]; return 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-9) if len(s) else -99
def strip(t0, t1, mark):
    out = []
    for k in range(int(round((t1 - t0) * 100))):
        t = t0 + k / 100; d = db(t); c = ' ▁▂▃▄▅▆▇█'[int(np.clip((d + 60) / 45 * 8, 0, 8))]
        out.append(('|' if abs(t - mark) < 0.005 else '') + c)
    return ''.join(out)
floor = np.percentile([db(t) for t in np.arange(0, len(x) / SR - 0.01, 0.01)], 5)
print(f'noise floor (5th pct) {floor:.1f} dB; strip: 10 ms/char, |=cut point, scale -60..-15 dB')
S = P.SEGMENTS; cuts = getattr(P, 'CUTS', None)
for k in range(len(S)):
    s = S[k]; o = (f'@out {cuts[k + 1]:6.2f}' if cuts else '')
    nx = S[k + 1]['in'] if k + 1 < len(S) else None
    print(f"#{k + 1:02d} out {s['out']:7.2f} {o}  {strip(s['out'] - pre, s['out'] + post, s['out'])}")
    if nx is not None: print(f"#{k + 2:02d} in  {nx:7.2f}            {strip(nx - pre, nx + post, nx)}")
