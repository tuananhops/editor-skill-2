import cv2,numpy as np,json,sys,csv
path,D=sys.argv[1],sys.argv[2]
cap=cv2.VideoCapture(path); fps=cap.get(cv2.CAP_PROP_FPS); step=int(round(fps/5)); i=0; out=[]
while True:
    ok=cap.grab()
    if not ok: break
    if i%step==0:
        _,f=cap.retrieve(); s=cv2.resize(f,(270,480)); lab=cv2.cvtColor(s,cv2.COLOR_BGR2LAB).astype(np.float32)
        a=lab[...,1]-128; b=lab[...,2]-128; L=lab[...,0]
        mid=(L>60)&(L<200)
        out.append((i/fps,float(np.hypot(a,b).mean()),float(a[mid].mean()) if mid.any() else 0,float(b[mid].mean()) if mid.any() else 0,float((L<10).mean()),float((L>250).mean())))
    i+=1
v=json.load(open(D+'/video.json')); sc=v['adaptive']
o=np.array(out)
rows=[]
for k,(s,e) in enumerate(sc):
    m=(o[:,0]>=s)&(o[:,0]<e)
    if not m.any(): continue
    rows.append([k,round(s,2),round(e,2),round(e-s,2)]+[round(float(x),2) for x in o[m,1:].mean(0)])
json.dump(rows,open(D+'/chroma_shots.json','w'))
print('overall chroma %.1f  mid a* %+.1f mid b* %+.1f  crushed(L<10) %.1f%%  clipped(L>250) %.2f%%'%(o[:,1].mean(),o[:,2].mean(),o[:,3].mean(),o[:,4].mean()*100,o[:,5].mean()*100))
