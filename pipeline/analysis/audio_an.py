import sys, json, os, subprocess, re, numpy as np, librosa
path=sys.argv[1]; out=sys.argv[2]; os.makedirs(out,exist_ok=True)
r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',path,'-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True).stderr
summ=r[r.rfind('Summary:'):]
def g(p): m=re.search(p,summ,re.S); return float(m.group(1)) if m else None
res={'I':g(r'I:\s+(-?[\d.]+) LUFS'),'LRA':g(r'LRA:\s+(-?[\d.]+) LU'),'TP':g(r'Peak:\s+(-?[\d.]+) dBFS')}
# short-term loudness series
st=[(float(a),float(b)) for a,b in re.findall(r't:\s*([\d.]+).*?S:\s*(-?[\d.]+)',r)]
res['S_series']=st[::5]
wav=os.path.join(out,'audio.wav'); subprocess.run(['ffmpeg','-y','-loglevel','error','-i',path,'-ac','1','-ar','22050',wav]); y,sr=librosa.load(wav,sr=22050,mono=True)
H,P=librosa.effects.hpss(y)
# tempo on full mix and harmonic part
oenv=librosa.onset.onset_strength(y=y,sr=sr)
tempo,beats=librosa.beat.beat_track(onset_envelope=oenv,sr=sr)
res['tempo_full']=float(np.atleast_1d(tempo)[0]); res['beats']=librosa.frames_to_time(beats,sr=sr).tolist()
tg=librosa.feature.tempogram(onset_envelope=oenv,sr=sr)
ac=tg.mean(axis=1); bpms=librosa.tempo_frequencies(tg.shape[0],sr=sr)
ok=(bpms>60)&(bpms<200); idx=np.argsort(ac[ok])[::-1][:5]; res['tempogram_top']=[(float(bpms[ok][i]),float(ac[ok][i])) for i in idx]
# low-frequency / gap energy for music presence: rms in frames where speech absent
S=np.abs(librosa.stft(y,n_fft=2048,hop_length=512)); f=librosa.fft_frequencies(sr=sr,n_fft=2048)
rms=librosa.feature.rms(S=S)[0]; t=librosa.frames_to_time(np.arange(len(rms)),sr=sr,hop_length=512)
db=20*np.log10(rms+1e-9)
res['rms_db_pcts']=[float(np.percentile(db,p)) for p in (5,10,25,50,75,95)]
# speech-free "floor": bottom 10% frames; energy distribution there
low=db<np.percentile(db,10)
band=lambda lo,hi: float(20*np.log10(S[(f>=lo)&(f<hi)][:,low].mean()+1e-9))
res['floor_bands_db']={'sub<80':band(20,80),'80-250':band(80,250),'250-2k':band(250,2000),'2k-6k':band(2000,6000),'6k+':band(6000,11000)}
# chroma stability (music has stable chroma/periodicity) — harmonic ratio
res['harm_ratio']=float(np.sum(H**2)/np.sum(y**2)); 
# fraction of frames above -50 dBFS (i.e. no digital silence)
res['frac_silent_-60']=float(np.mean(db<-60))
# transients: onset strength peaks with high spectral flux, especially broadband / high-freq
on=librosa.onset.onset_detect(onset_envelope=oenv,sr=sr,units='time',delta=0.0)
# high-frequency flux peaks (whoosh/pop) 
hf=S[f>4000]; flux=np.maximum(0,np.diff(np.log1p(hf),axis=1)).sum(0); flux=np.r_[0,flux]
z=(flux-np.median(flux))/(np.median(np.abs(flux-np.median(flux)))*1.4826+1e-9)
pk=librosa.util.peak_pick(z,pre_max=10,post_max=10,pre_avg=20,post_avg=20,delta=6,wait=8)
res['hf_transients']=[(float(t[i]),float(z[i])) for i in pk if z[i]>8]
# whoosh-like: sustained rising broadband energy ~0.2-0.6s ending in peak: use spectral centroid + rms in 2-8k
cent=librosa.feature.spectral_centroid(S=S,sr=sr)[0]
res['centroid_med']=float(np.median(cent))
np.save(os.path.join(out,'hf_z.npy'),np.c_[t,z,db,cent])
json.dump(res,open(os.path.join(out,'audio.json'),'w'))
print(json.dumps({k:v for k,v in res.items() if k not in('S_series','beats')},indent=0))
