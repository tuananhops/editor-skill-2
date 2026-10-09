import json,sys,numpy as np
d=json.load(open(sys.argv[1])); F=d['frames']; fps=d['fps']; sc=d[sys.argv[2] if len(sys.argv)>2 else 'content']
T=np.array([f['t'] for f in F])
rows=[]
print(f"{'#':>2} {'start':>6} {'end':>6} {'len':>5} | cutScale inl | inShotZoom | Y   Ystd p2  p98  sat  a    b    R-B")
for k,(s,e) in enumerate(sc):
    i0=int(round(s*fps)); i1=min(int(round(e*fps)),len(F))
    seg=F[i0:i1]
    cs=F[i0]['scale'] if i0<len(F) else None; inl=F[i0].get('inl',0) if i0<len(F) else 0
    sc_in=[f['scale'] for f in seg[1:] if f['scale'] and 0.8<f['scale']<1.25]
    zoom=float(np.prod(sc_in)) if sc_in else None
    m=lambda key: np.mean([f[key] for f in seg])
    r=dict(i=k,s=s,e=e,L=e-s,cutscale=cs,inl=inl,zoom=zoom,**{x:float(m(x)) for x in ('Y','Ystd','p2','p98','sat','a','b','RmB')})
    rows.append(r)
    print(f"{k:2d} {s:6.2f} {e:6.2f} {e-s:5.2f} | {cs if cs is None else round(cs,3)!s:>6} {inl:3d} | {zoom if zoom is None else round(zoom,3)!s:>6} | {r['Y']:5.1f} {r['Ystd']:4.1f} {r['p2']:4.0f} {r['p98']:4.0f} {r['sat']:5.1f} {r['a']:5.1f} {r['b']:5.1f} {r['RmB']:5.1f}")
json.dump(rows,open(sys.argv[1].replace('video.json','shots.json'),'w'))
