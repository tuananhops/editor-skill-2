import json,sys,numpy as np,librosa
d=sys.argv[1]; vdir=sys.argv[2]
M=json.load(open(f'sep/{d}_music.json'))
y,sr=librosa.load(f'sep/out/htdemucs/{d}/no_vocals.wav',sr=22050)
hop=256; oenv=librosa.onset.onset_strength(y=y,sr=sr,hop_length=hop)
# fine BPM via autocorrelation
ac=librosa.autocorrelate(oenv-oenv.mean()); lags=np.arange(len(ac))*hop/sr
m=(lags>60/180)&(lags<60/70); L=lags[m][np.argmax(ac[m])]
# parabolic refine
i=np.where(m)[0][np.argmax(ac[m])]; a,b,c=ac[i-1],ac[i],ac[i+1]; off=0.5*(a-c)/(a-2*b+c); Lr=(i+off)*hop/sr
bpm=60/Lr
# beats: use librosa with start_bpm
tempo,beats=librosa.beat.beat_track(onset_envelope=oenv,sr=sr,hop_length=hop,start_bpm=bpm,tightness=400)
bt=librosa.frames_to_time(beats,sr=sr,hop_length=hop)
ibi=np.median(np.diff(bt))
v=json.load(open(f'{vdir}/video.json'))
def union(a,b,gap=0.3):
    cuts=sorted([s for s,e in a[1:]]+[s for s,e in b[1:]]); out=[]
    for c in cuts:
        if not out or c-out[-1]>gap: out.append(c)
    return out
cuts=np.array(union(v['content'],v['adaptive']))
allc=cuts.copy(); cuts=cuts[(cuts>bt[0]-0.1)&(cuts<bt[-1]+0.1)]
def offs(ts,grid):
    return np.array([np.min(np.abs(grid-t)) for t in ts])
o=offs(cuts,bt)
half=np.sort(np.r_[bt,(bt[:-1]+bt[1:])/2]); oh=offs(cuts,half)
rng=np.random.default_rng(0); R=rng.uniform(bt[0],bt[-1],(2000,len(cuts)))
ro=np.array([offs(r,bt).mean() for r in R[:300]])
p=float(np.mean(ro<=o.mean()))
print(json.dumps(dict(video=d,bpm_autocorr=round(bpm,2),beat_ibi_med=round(float(ibi),3),bpm_from_beats=round(60/ibi,1),first_beat=round(float(bt[0]),2),
  n_cuts=len(cuts),cut_beat_offset_mean_ms=round(float(o.mean()*1000)),cut_within_80ms_of_beat=f"{int((o<0.08).sum())}/{len(cuts)}",
  within_80ms_of_halfbeat=f"{int((oh<0.08).sum())}/{len(cuts)}",random_expect_ms=round(float(ro.mean()*1000)),p_value=round(p,3))))
# off-grid transients (SFX candidates)
tr=M['transients']; sfx=[(t,z,c) for t,z,c in tr if np.min(np.abs(bt-t))>0.07 and (c>2800 or z>15)]
print('SFX candidates (off-beat, bright/strong) t,z,centroid,nearest_cut_dt:')
print([ (t,z,c, round(float(allc[np.argmin(np.abs(allc-t))]-t),2) if len(allc) else None) for t,z,c in sfx])
json.dump(dict(bpm=bpm,beats=bt.tolist(),cuts=cuts.tolist()),open(f'sep/{d}_align.json','w'))
