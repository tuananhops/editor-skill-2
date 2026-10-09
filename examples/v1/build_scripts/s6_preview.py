import os  # v1 reference build: paths via env (see README.md in this folder)
R = os.environ.get('V1_ROOT', '.'); REPO = os.environ.get('EDITOR_SKILL_ROOT', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
MODELS = os.environ.get('EDITOR_MODELS_DIR', REPO + '/pipeline/models'); FONTS = os.environ.get('EDITOR_FONTS_DIR', REPO + '/assets/fonts'); MUSICDIR = os.environ.get('EDITOR_MUSIC_DIR', REPO + '/assets/music')
# contact sheet every 1.5 s with timestamps + representative full-res stills from the FINAL file
import subprocess, numpy as np, sys
from PIL import Image, ImageDraw, ImageFont
F=R + '/v1/final_v1.mp4'; W,H=1080,1920
def grab(t):
    p=subprocess.run(['ffmpeg','-v','error','-ss',f'{t:.3f}','-i',F,'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True)
    return Image.frombytes('RGB',(W,H),p.stdout)
dur=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',F],capture_output=True,text=True).stdout)
ts=np.arange(0,dur,1.5); cols=7; tw=270; th=480; rows=int(np.ceil(len(ts)/cols))
S=Image.new('RGB',(cols*tw,rows*th),'black'); d=ImageDraw.Draw(S)
fnt=ImageFont.truetype(FONTS + '/BeVietnamPro-Bold.ttf',22)
for i,t in enumerate(ts):
    x,y=(i%cols)*tw,(i//cols)*th; S.paste(grab(t).resize((tw,th),Image.LANCZOS),(x,y))
    d.rectangle([x,y,x+96,y+30],fill=(0,0,0)); d.text((x+6,y+3),f'{t:05.2f}s',font=fnt,fill=(255,230,0))
S.save(R + '/v1/preview_sheet.jpg',quality=90)
for t in [float(a) for a in sys.argv[1:]]:
    grab(t).save(f'{R}/v1/stills/still_{t:05.2f}s.png')
print('ok',len(ts))
