"""montage of cache/still_*.png (or given times) -> cache/rev_<k>.jpg, 7 per row block.  usage: montage.py <proj> [t ...]"""
import sys, glob, os
from PIL import Image, ImageDraw
d = sys.argv[1] + '/cache'; ts = sys.argv[2:]
fs = [f'{d}/still_{float(t):06.2f}.png' for t in ts] if ts else sorted(glob.glob(d + '/still_*.png'))
for k in range(0, len(fs), 7):
    g = fs[k:k + 7]; im = Image.new('RGB', (7 * 360, 640))
    for i, f in enumerate(g):
        t = Image.open(f).convert('RGB').resize((360, 640)); ImageDraw.Draw(t).text((5, 5), os.path.basename(f)[6:-4], fill='yellow'); im.paste(t, (i * 360, 0))
    import time; fn = f'{d}/rev_{int(time.time()) % 100000}_{k // 7}.jpg'; im.save(fn, quality=88); print(fn)
