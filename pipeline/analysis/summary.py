import json,numpy as np,sys,glob,os
def union(a,b,gap=0.3):
    cuts=sorted([s for s,e in a[1:]]+[s for s,e in b[1:]]); out=[]
    for c in cuts:
        if not out or c-out[-1]>gap: out.append(c)
    return out
for D in ['analysis/main']+sorted(glob.glob('analysis/76*')):
    if not os.path.isdir(D): continue
    v=json.load(open(D+'/video.json')); fc=json.load(open(D+'/face.json'))['face']
    dur=v['nframes']/v['fps']
    cuts=union(v['content'],v['adaptive'])
    b=[0]+cuts+[dur]; L=np.diff(b)
    print(f"== {os.path.basename(D)} fps={v['fps']} dur={dur:.1f}s")
    for k in ('content','adaptive'):
        LL=np.array([e-s for s,e in v[k]]); print(f"  {k}: shots={len(LL)} mean={LL.mean():.2f} med={np.median(LL):.2f}")
    print(f"  union: shots={len(L)} mean={L.mean():.2f} med={np.median(L):.2f} min={L.min():.2f} max={L.max():.2f} cuts/min={len(cuts)/dur*60:.1f}")
    print('  cuts:',[round(c,2) for c in cuts])
    w=10; print('  cuts per 10s:',[sum(1 for c in cuts if a<=c<a+w) for a in range(0,int(dur)+1,w)])
    # color: frames with face (talking head) vs without
    F=v['frames']; fps=v['fps']; ft=np.array([r[0] for r in fc]); has=np.array([r[3] is not None for r in fc])
    def hasface(t): i=np.searchsorted(ft,t); i=min(i,len(ft)-1); return has[i]
    th=[f for f in F if hasface(f['t'])]; ot=[f for f in F if not hasface(f['t'])]
    for name,S in (('talking-head',th),('other',ot),('all',F)):
        if not S: continue
        m=lambda k: np.mean([f[k] for f in S])
        print(f"  {name:12s} n={len(S)/len(F)*100:4.0f}%  Y={m('Y'):5.1f} contrast(std)={m('Ystd'):4.1f} p2={m('p2'):4.1f} p98={m('p98'):5.1f} satHSV={m('sat'):5.1f} a*={m('a'):+.1f} b*={m('b'):+.1f} R-B={m('RmB'):+.1f}")
