import sys,numpy as np,librosa,subprocess,re,json
d=sys.argv[1]; base=f'sep/out/htdemucs/{d}/'
def lufs(p):
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',p,'-af','ebur128','-f','null','-'],capture_output=True,text=True).stderr
    s=r[r.rfind('Summary'):]; m=re.search(r'I:\s+(-?[\d.]+)',s); return float(m.group(1))
Lv=lufs(base+'vocals.wav'); Lm=lufs(base+'no_vocals.wav')
y,sr=librosa.load(base+'no_vocals.wav',sr=22050)
yv,_=librosa.load(base+'vocals.wav',sr=22050)
rm=librosa.feature.rms(y=y)[0]; rv=librosa.feature.rms(y=yv)[0]; t=librosa.frames_to_time(np.arange(len(rm)),sr=sr)
dbm=20*np.log10(rm+1e-9); dbv=20*np.log10(rv+1e-9)
# presence: fraction of 1s windows where music stem > -45 dBFS rms
win=[(a,np.mean(dbm[(t>=a)&(t<a+1)])) for a in range(int(t[-1]))]
pres=np.mean([x>-45 for a,x in win])
oenv=librosa.onset.onset_strength(y=y,sr=sr)
tempo,beats=librosa.beat.beat_track(onset_envelope=oenv,sr=sr)
bt=librosa.frames_to_time(beats,sr=sr)
tg=librosa.feature.tempogram(onset_envelope=oenv,sr=sr); ac=tg.mean(1); bpms=librosa.tempo_frequencies(tg.shape[0],sr=sr)
ok=(bpms>70)&(bpms<180); top=[(round(float(bpms[ok][i]),1),round(float(ac[ok][i]),2)) for i in np.argsort(ac[ok])[::-1][:4]]
# beat regularity
ibi=np.diff(bt); reg=float(np.std(ibi)/np.mean(ibi)) if len(ibi)>2 else None
# sidechain/ducking: correlation between vocal level and music level
m=(dbv>-50)
corr=float(np.corrcoef(dbv[m],dbm[m])[0,1])
# music level when voice active vs voice pauses
act=dbv>np.percentile(dbv,40); pau=dbv<np.percentile(dbv,15)
# SFX transients in music stem: high-flux peaks
S=np.abs(librosa.stft(y,n_fft=2048,hop_length=512)); f=librosa.fft_frequencies(sr=sr,n_fft=2048)
flux=np.r_[0,np.maximum(0,np.diff(np.log1p(S),axis=1)).sum(0)]
z=(flux-np.median(flux))/(1.4826*np.median(np.abs(flux-np.median(flux)))+1e-9)
pk=librosa.util.peak_pick(z,pre_max=8,post_max=8,pre_avg=20,post_avg=20,delta=5,wait=6)
ts=librosa.frames_to_time(np.arange(len(z)),sr=sr,hop_length=512)
cent=librosa.feature.spectral_centroid(S=S,sr=sr)[0]
tr=[(round(float(ts[i]),2),round(float(z[i]),1),int(cent[i])) for i in pk if z[i]>7]
# whoosh: windows of 0.15-0.6s with rising broadband energy (>3k) and high centroid
res=dict(vocal_LUFS=Lv,music_LUFS=Lm,music_minus_voice=round(Lm-Lv,1),music_presence_frac=round(float(pres),2),
  music_median_dB=round(float(np.median(dbm)),1),tempo=round(float(np.atleast_1d(tempo)[0]),1),tempogram_top=top,beat_ibi_cv=reg,
  vox_music_level_corr=round(corr,2),music_dB_voice_active=round(float(np.median(dbm[act])),1),music_dB_voice_pause=round(float(np.median(dbm[pau])),1),
  transients=tr)
json.dump(dict(res,beats=bt.tolist()),open(f'sep/{d}_music.json','w'))
print(json.dumps(res))
