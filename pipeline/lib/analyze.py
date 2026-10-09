"""Step 2b: per-frame face track (YuNet) + person masks (mediapipe selfie multiclass) for the first SEG_SECONDS
(hook depth text). -> cache/faces.npy, cache/masks.npz     usage: python3 analyze.py <project_dir>"""
import subprocess, numpy as np, cv2, sys, os
sys.path.insert(0, os.path.dirname(__file__)); import proj, paths
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
P = proj.arg_project(); LIB = os.path.dirname(os.path.abspath(__file__)); W, H = 1080, 1920
SEGN = int(getattr(P, 'SEG_SECONDS', 4.0) * P.FPS)
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', os.path.join(P.BUILD, 'base.mp4'), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
det = cv2.FaceDetectorYN.create(paths.model('yunet.onnx'), '', (540, 960), 0.6, 0.3, 5)
seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
    base_options=BaseOptions(model_asset_path=paths.model('selfie_multiclass_256x256.tflite')),
    running_mode=vision.RunningMode.VIDEO, output_confidence_masks=True, output_category_mask=False))
faces, masks, i = [], [], 0
while True:
    b = p.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    sm = cv2.resize(np.frombuffer(b, np.uint8).reshape(H, W, 3), (540, 960), interpolation=cv2.INTER_AREA)
    _, r = det.detect(sm[:, :, ::-1].copy())
    faces.append(r[np.argmax(r[:, 2] * r[:, 3])][:14] * 2 if r is not None and len(r) else np.full(14, np.nan))
    if i < SEGN:
        res = seg.segment_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(sm)), int(i * 1000 / P.FPS))
        masks.append(((1 - res.confidence_masks[0].numpy_view()) * 255).clip(0, 255).astype(np.uint8))
    i += 1
F = np.array(faces); miss = np.isnan(F[:, 0])
if miss.any():   # fill gaps by nearest valid frame
    idx = np.where(~miss)[0]
    for j in np.where(miss)[0]: F[j] = F[idx[np.argmin(np.abs(idx - j))]]
np.save(os.path.join(P.CACHE, 'faces.npy'), F); np.savez_compressed(os.path.join(P.CACHE, 'masks.npz'), m=np.array(masks))
print(i, 'frames; face missing', int(miss.sum()), '; masks', len(masks))
os._exit(0)
