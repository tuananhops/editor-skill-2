import sys, json, os, cv2, numpy as np
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector, AdaptiveDetector
path=sys.argv[1]; out=sys.argv[2]; os.makedirs(out,exist_ok=True)
res={}
# scenes
def detect(det):
    v=open_video(path); sm=SceneManager(); sm.add_detector(det); sm.detect_scenes(v)
    return [(s.get_seconds(),e.get_seconds()) for s,e in sm.get_scene_list()], v.frame_rate
sc_c,fps=detect(ContentDetector(threshold=27))
sc_a,_=detect(AdaptiveDetector())
fps=float(fps); res['fps']=fps; res['content']=sc_c; res['adaptive']=sc_a
# per-frame analysis: color stats + similarity-transform scale between consecutive frames
cap=cv2.VideoCapture(path); orb=cv2.ORB_create(800); bf=cv2.BFMatcher(cv2.NORM_HAMMING,crossCheck=True)
frames=[]; prev=None; i=0
while True:
    ok,f=cap.read()
    if not ok: break
    small=cv2.resize(f,(270,480))
    hsv=cv2.cvtColor(small,cv2.COLOR_BGR2HSV); lab=cv2.cvtColor(small,cv2.COLOR_BGR2LAB).astype(np.float32)
    g=cv2.cvtColor(small,cv2.COLOR_BGR2GRAY)
    L=lab[...,0]*100/255; a=lab[...,1]-128; b=lab[...,2]-128
    rec={'t':i/fps,'Y':float(g.mean()),'Ystd':float(g.std()),'p2':float(np.percentile(g,2)),'p98':float(np.percentile(g,98)),
         'sat':float(hsv[...,1].mean()),'a':float(a.mean()),'b':float(b.mean()),
         'RmB':float(small[...,2].astype(float).mean()-small[...,0].astype(float).mean()),'scale':None,'diff':None}
    gg=cv2.resize(cv2.cvtColor(f,cv2.COLOR_BGR2GRAY),(360,640))
    if prev is not None:
        rec['diff']=float(np.abs(gg.astype(float)-prev[0].astype(float)).mean())
        kp,des=orb.detectAndCompute(gg,None)
        if des is not None and prev[2] is not None and len(kp)>20:
            m=bf.match(prev[2],des)
            if len(m)>15:
                p1=np.float32([prev[1][x.queryIdx].pt for x in m]); p2=np.float32([kp[x.trainIdx].pt for x in m])
                M,inl=cv2.estimateAffinePartial2D(p1,p2,ransacReprojThreshold=3)
                if M is not None and inl.sum()>12:
                    rec['scale']=float(np.sqrt(M[0,0]**2+M[1,0]**2)); rec['inl']=int(inl.sum())
        prev=(gg,kp,des)
    else:
        kp,des=orb.detectAndCompute(gg,None); prev=(gg,kp,des)
    frames.append(rec); i+=1
res['frames']=frames; res['nframes']=i
json.dump(res,open(os.path.join(out,'video.json'),'w'))
print('fps',fps,'frames',i,'content shots',len(sc_c),'adaptive shots',len(sc_a))
