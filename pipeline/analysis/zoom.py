import json,sys,numpy as np
D=sys.argv[1]; d=json.load(open(D+'/face.json')); fc=d['face']
v=json.load(open(D+'/video.json')); sc=v[sys.argv[2] if len(sys.argv)>2 else 'content']
t=np.array([r[0] for r in fc]); w=np.array([np.nan if r[3] is None else r[3] for r in fc],float)
cx=np.array([np.nan if r[1] is None else r[1]+r[3]/2 for r in fc],float)
# smooth with rolling median over 3 samples
def med(a,k=2): return np.array([np.nanmedian(a[max(0,i-k):i+k+1]) if np.any(~np.isnan(a[max(0,i-k):i+k+1])) else np.nan for i in range(len(a))])
ws=med(w)
# 1) step changes in face width (>12%) between samples 2 apart -> punch-in/out (cut or keyframed jump)
ev=[]
for i in range(2,len(ws)-2):
    a=np.nanmedian(w[max(0,i-4):i]); b=np.nanmedian(w[i:i+4])
    if np.isnan(a) or np.isnan(b): continue
    r=b/a
    if r>1.12 or r<1/1.12: ev.append((round(float(t[i]),2),round(float(r),2),int(a),int(b)))
# collapse nearby events
out=[]
for e in ev:
    if out and e[0]-out[-1][0]<0.4:
        if abs(np.log(e[1]))>abs(np.log(out[-1][1])): out[-1]=e
    else: out.append(e)
print('face-width steps (t, ratio, w_before, w_after):'); 
for e in out: print('  ',e)
# 2) per-shot: median face width, and slow zoom (linear fit of log w over shot)
print('per shot: idx start len faceFrac medW slope%/s')
for k,(s,e) in enumerate(sc):
    m=(t>=s+0.05)&(t<e-0.05)&~np.isnan(w)
    frac=m.sum()/max(1,((t>=s)&(t<e)).sum())
    if m.sum()>=5:
        p=np.polyfit(t[m],np.log(w[m]),1)[0]*100
        print(f'  {k:2d} {s:6.2f} {e-s:5.2f} {frac:4.2f} {np.median(w[m]):5.0f} {p:+6.1f}')
    else: print(f'  {k:2d} {s:6.2f} {e-s:5.2f} {frac:4.2f}   -')
print('overall face width range',np.nanpercentile(w,[5,50,95]))
