"""Step 1: rebuild the edit frame-accurately from the SOURCE using project.SEGMENTS (the rough-cut segment list
with join fixes applied), scale to 1080x1920, apply project.GRADE -> build/base.mp4; dialogue audio -> stems/dialogue.wav;
segment map -> build/segmap.json.   usage: python3 base.py <project_dir>"""
import subprocess, numpy as np, soundfile as sf, json, sys, os
sys.path.insert(0, os.path.dirname(__file__)); import proj
P = proj.arg_project(); FPS = P.FPS; SR = 48000
segs = []; f_out = 0
for s in P.SEGMENTS:
    a, b = int(round(s['in'] * FPS)), int(round(s['out'] * FPS))
    segs.append(dict(s, src_f0=a, src_f1=b, out_f0=f_out, out_f1=f_out + b - a)); f_out += b - a
json.dump(segs, open(os.path.join(P.BUILD, 'segmap.json'), 'w'), indent=1, ensure_ascii=False)
print('frames', f_out, 'dur %.3f' % (f_out / FPS))
# ---- audio: sample-exact to frame grid, short fades at every join ----
p = subprocess.run(['ffmpeg', '-v', 'error', '-i', P.SRC, '-map', '0:a:0', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True)
src = np.frombuffer(p.stdout, np.float32).reshape(-1, 2).astype(np.float64)
parts = []
for s in segs:
    i0 = int(round(s['src_f0'] / FPS * SR)); n = int(round(s['out_f1'] / FPS * SR)) - int(round(s['out_f0'] / FPS * SR))
    x = src[i0:i0 + n].copy()
    fi, fo = int(s.get('fade_in', 0.010) * SR), int(s.get('fade_out', 0.010) * SR)
    if fi: x[:fi] *= np.sin(np.linspace(0, np.pi / 2, fi))[:, None] ** 2
    if fo: x[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo))[:, None] ** 2
    parts.append(x)
sf.write(os.path.join(P.STEMS, 'dialogue.wav'), np.concatenate(parts).astype(np.float32), SR, subtype='FLOAT')
# ---- video ----
sel = '+'.join(f'between(n\\,{s["src_f0"]}\\,{s["src_f1"] - 1})' for s in segs)
vf = (f"{getattr(P, 'PRE', '') + ',' if getattr(P, 'PRE', '') else ''}select='{sel}',setpts=N/({P.FPS_STR})/TB,scale=1080:1920:flags=lanczos,setsar=1,fps={P.FPS_STR},{P.GRADE},format=yuv420p")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', P.SRC, '-map', '0:v:0', '-vf', vf, '-vsync', 'passthrough',
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '10', '-an', os.path.join(P.BUILD, 'base.mp4')], check=True)
n = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0',
                    os.path.join(P.BUILD, 'base.mp4')], capture_output=True, text=True).stdout.strip()
print('base frames', n, '(expected', f_out, ')')
