import os  # v1 reference build: paths via env (see README.md in this folder)
R = os.environ.get('V1_ROOT', '.'); REPO = os.environ.get('EDITOR_SKILL_ROOT', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
MODELS = os.environ.get('EDITOR_MODELS_DIR', REPO + '/pipeline/models'); FONTS = os.environ.get('EDITOR_FONTS_DIR', REPO + '/assets/fonts'); MUSICDIR = os.environ.get('EDITOR_MUSIC_DIR', REPO + '/assets/music')
# Step 2: per-frame face detection (YuNet) + person segmentation for the hook frames (mediapipe selfie multiclass)
import subprocess,numpy as np,cv2,sys
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
W,H=1080,1920; SEGN=int(sys.argv[1]) if len(sys.argv)>1 else 240
p=subprocess.Popen(['ffmpeg','-v','error','-i','build/base.mp4','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
det=cv2.FaceDetectorYN.create(MODELS + '/yunet.onnx','',(540,960),0.6,0.3,5)
seg=vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
    base_options=BaseOptions(model_asset_path=MODELS + '/selfie_multiclass_256x256.tflite'),
    running_mode=vision.RunningMode.VIDEO,output_confidence_masks=True,output_category_mask=False))
faces=[];masks=[];i=0
while True:
    b=p.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    f=np.frombuffer(b,np.uint8).reshape(H,W,3)
    sm=cv2.resize(f,(540,960),interpolation=cv2.INTER_AREA)
    _,r=det.detect(sm[:,:,::-1].copy())
    if r is not None and len(r):
        r=r[np.argmax(r[:,2]*r[:,3])]; faces.append(r[:14]*2)
    else: faces.append(np.full(14,np.nan))
    if i<SEGN:
        res=seg.segment_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,data=np.ascontiguousarray(sm)),int(i*1001/60))
        bg=res.confidence_masks[0].numpy_view()
        masks.append(((1-bg)*255).clip(0,255).astype(np.uint8))
    i+=1
np.save('cache/faces.npy',np.array(faces)); np.savez_compressed('cache/masks.npz',m=np.array(masks))
print(i,'frames; face missing',int(np.isnan(np.array(faces)[:,0]).sum()))
