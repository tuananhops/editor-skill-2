import os  # v1 reference build: paths via env (see README.md in this folder)
R = os.environ.get('V1_ROOT', '.'); REPO = os.environ.get('EDITOR_SKILL_ROOT', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
MODELS = os.environ.get('EDITOR_MODELS_DIR', REPO + '/pipeline/models'); FONTS = os.environ.get('EDITOR_FONTS_DIR', REPO + '/assets/fonts'); MUSICDIR = os.environ.get('EDITOR_MUSIC_DIR', REPO + '/assets/music')
import subprocess,numpy as np
w,h=90,160
p=subprocess.run(['ffmpeg','-v','error','-i',os.environ['V1_CUT'],'-vf',f'scale={w}:{h}','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True)
f=np.frombuffer(p.stdout,np.uint8).reshape(-1,h,w).astype(np.float32)
d=np.abs(np.diff(f,axis=0)).mean((1,2))
print('frames',len(f))
med=np.median(d)
for i in np.argsort(-d)[:16]: print(i+1, round((i+1)*1001/60000,3), round(float(d[i]),2))
