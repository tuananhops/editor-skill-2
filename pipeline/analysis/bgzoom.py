import cv2,numpy as np,json,sys
path=sys.argv[1]; D=sys.argv[2]; key=sys.argv[3] if len(sys.argv)>3 else 'adaptive'
sc=json.load(open(D+'/video.json'))[key]
cap=cv2.VideoCapture(path)
def fr(t):
    cap.set(cv2.CAP_PROP_POS_MSEC,t*1000); ok,f=cap.read(); return cv2.cvtColor(cv2.resize(f,(540,960)),cv2.COLOR_BGR2GRAY)
sift=cv2.SIFT_create(1500)
mask=np.zeros((960,540),np.uint8); mask[:,:110]=255; mask[:,430:]=255; mask[:200,:]=255  # edges + top
def scale(a,b):
    k1,d1=sift.detectAndCompute(a,mask); k2,d2=sift.detectAndCompute(b,mask)
    if d1 is None or d2 is None or len(k1)<10 or len(k2)<10: return None,0
    m=cv2.BFMatcher().knnMatch(d1,d2,k=2); g=[x[0] for x in m if len(x)==2 and x[0].distance<0.75*x[1].distance]
    if len(g)<10: return None,len(g)
    p1=np.float32([k1[x.queryIdx].pt for x in g]); p2=np.float32([k2[x.trainIdx].pt for x in g])
    M,inl=cv2.estimateAffinePartial2D(p1,p2,ransacReprojThreshold=2)
    if M is None: return None,0
    return float(np.hypot(M[0,0],M[1,0])),int(inl.sum())
print('shot start len  inShot(scale,inl)  cutVsPrev(scale,inl)')
prev_end=None
for k,(s,e) in enumerate(sc):
    a=fr(s+0.05); b=fr(max(s+0.05,e-0.1))
    z=scale(a,b); c=scale(prev_end,a) if prev_end is not None else (None,0)
    print(f'{k:2d} {s:6.2f} {e-s:5.2f}  {z[0] and round(z[0],3)!s:>6} {z[1]:4d}   {c[0] and round(c[0],3)!s:>6} {c[1]:4d}')
    prev_end=b
