"""Find 'drop' points in a music file (energy jump after a quieter stretch) to land on the CTA.
usage: python3 music_scan.py <file>  -> prints candidate drop times (s, 20 ms precision) and rise in dB"""
import sys, subprocess, numpy as np
x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', sys.argv[1], '-ac', '1', '-ar', '8000', '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
h = 160; e = np.array([20 * np.log10(np.sqrt(np.mean(x[i:i + h] ** 2)) + 1e-9) for i in range(0, len(x) - h, h)])   # 20 ms
def avg(a, b): return np.mean(e[max(0, a):b])
c = []
for i in range(100, len(e) - 100):
    before, after = avg(i - 75, i - 5), avg(i + 2, i + 75)    # 1.4 s windows
    if after - before > 5 and e[i + 1] - e[i - 1] > 6: c.append((after - before, i * 0.02))
c.sort(reverse=True); out = []
for r, t in c:
    if all(abs(t - u) > 3 for _, u in out): out.append((r, t))
print('dur %.1f s' % (len(x) / 8000)); [print(f'  drop @ {t:7.2f} s  +{r:4.1f} dB') for r, t in sorted(out[:8], key=lambda z: z[1])]
