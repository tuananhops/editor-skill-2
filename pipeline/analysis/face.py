import cv2,sys,json,numpy as np,os
path=sys.argv[1]; out=sys.argv[2]
det=cv2.FaceDetectorYN.create(os.path.join(os.environ.get('EDITOR_MODELS_DIR',os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','models')),'yunet.onnx'),'',(540,960),0.7)
cap=cv2.VideoCapture(path); fps=cap.get(cv2.CAP_PROP_FPS); step=max(1,int(round(fps/15)))
res=[]; i=0
while True:
    ok=cap.grab()
    if not ok: break
    if i%step==0:
        ok,f=cap.retrieve(); g=cv2.resize(f,(540,960)); _,fs=det.detect(g); fs=[] if fs is None else [r[:4].astype(int) for r in fs]
        if len(fs):
            x,y,w,h=max(fs,key=lambda r:r[2]*r[3]); res.append((i/fps,int(x),int(y),int(w)))
        else: res.append((i/fps,None,None,None))
    i+=1
json.dump({'fps':fps,'face':res},open(os.path.join(out,'face.json'),'w'))
print('done',sum(r[3] is not None for r in res),'/',len(res))
