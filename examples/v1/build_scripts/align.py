import os  # v1 reference build: paths via env (see README.md in this folder)
R = os.environ.get('V1_ROOT', '.'); REPO = os.environ.get('EDITOR_SKILL_ROOT', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
MODELS = os.environ.get('EDITOR_MODELS_DIR', REPO + '/pipeline/models'); FONTS = os.environ.get('EDITOR_FONTS_DIR', REPO + '/assets/fonts'); MUSICDIR = os.environ.get('EDITOR_MUSIC_DIR', REPO + '/assets/music')
import subprocess,json,re,sys,numpy as np,torch,torchaudio
from unidecode import unidecode
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from words_text import SEGS
p=subprocess.run(['ffmpeg','-v','error','-i',os.environ['V1_CUT'],'-ac','1','-ar','16000','-f','f32le','-'],capture_output=True)
wav=torch.from_numpy(np.frombuffer(p.stdout,np.float32).copy())[None]
b=torchaudio.pipelines.MMS_FA; model=b.get_model(); tok=b.get_tokenizer(); aligner=b.get_aligner()
words=[];disp=[]
for si,s in enumerate(SEGS):
    for w in s.split():
        r=re.sub(r"[^a-z']","",unidecode(w).lower().replace('đ','d'))
        if not r: continue
        words.append(r); disp.append((si,w))
with torch.inference_mode():
    em,_=model(wav)
    em=torch.log_softmax(em,-1)
    spans=aligner(em[0],tok(words))
ratio=wav.shape[1]/em.shape[1]/16000
out=[]
for (si,w),sp in zip(disp,spans):
    st=sp[0].start*ratio; en=sp[-1].end*ratio
    sc=float(np.mean([x.score for x in sp]))
    out.append(dict(seg=si,word=w,start=round(st,3),end=round(en,3),score=round(sc,3)))
json.dump(out,open(R + '/build/words_aligned.json','w'),ensure_ascii=False,indent=0)
old=[w for s in json.load(open(os.environ.get('V1_TRANSCRIPT', 'transcript_output.json'))) for w in s['words']]
for o in out: print(f"{o['seg']:2d} {o['word']:10s} {o['start']:6.2f}-{o['end']:6.2f} {o['score']:.2f}")
