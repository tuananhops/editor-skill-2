#!/usr/bin/env bash
# One-shot setup for the editor-skill-2 pipeline on Debian/Ubuntu (CPU is fine).
#   pipeline/install.sh            # apt deps + pip deps + models
#   pipeline/install.sh --analysis # also the optional style-study deps (scenedetect, librosa, demucs, yt-dlp)
#   SKIP_APT=1 / SKIP_PIP=1 / SKIP_WARM=1 to skip parts.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS="${EDITOR_MODELS_DIR:-$HERE/models}"; mkdir -p "$MODELS"
SUDO=""; [ "$(id -u)" = 0 ] || SUDO="sudo"
if [ -z "${SKIP_APT:-}" ]; then
  $SUDO apt-get update -y
  $SUDO apt-get install -y --no-install-recommends ffmpeg python3 python3-pip python3-venv libsndfile1 fonts-dejavu-core curl git
fi
# ffmpeg needs: libx264, aac, arnndn, afftdn, deesser, ebur128, huesaturation, cas, vignette (all in Debian's ffmpeg >= 6)
for f in arnndn afftdn deesser ebur128 huesaturation cas vignette; do
  ffmpeg -hide_banner -filters 2>/dev/null | grep -qw "$f" || echo "WARNING: ffmpeg filter '$f' missing"
done
ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libx264 || echo "WARNING: ffmpeg without libx264"
if [ -z "${SKIP_PIP:-}" ]; then
  PIP="python3 -m pip install"
  python3 -m pip install --help 2>/dev/null | grep -q break-system-packages && PIP="$PIP --break-system-packages"
  $PIP -r "$HERE/requirements.txt" --extra-index-url https://download.pytorch.org/whl/cpu
  [ "${1:-}" = "--analysis" ] && $PIP -r "$HERE/requirements-analysis.txt"
fi
# ---- models (not stored in git) ----
get() {  # url file sha256
  if [ -f "$MODELS/$2" ] && echo "$3  $MODELS/$2" | sha256sum -c --quiet 2>/dev/null; then echo "ok  $2"; return; fi
  curl -fsSL -o "$MODELS/$2.part" "$1" && mv "$MODELS/$2.part" "$MODELS/$2"
  echo "$3  $MODELS/$2" | sha256sum -c --quiet && echo "got $2"
}
get https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx \
    yunet.onnx 8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4
get https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite \
    selfie_multiclass_256x256.tflite c6748b1253a99067ef71f7e26ca71096cd449baefa8f101900ea23016507e0e0
get https://raw.githubusercontent.com/richardpl/arnndn-models/master/std.rnnn \
    rnn_std.rnnn 6b8943dc4a9b6b24425873992a44f29c0577503276456af46a8854774faeb294
# ---- pre-download the alignment / ASR weights into the default caches (~1.2 GB MMS_FA, ~3 GB PhoWhisper-medium) ----
if [ -z "${SKIP_WARM:-}" ]; then
  python3 -c "import torchaudio; torchaudio.pipelines.MMS_FA.get_model(); print('MMS_FA ok')"
  python3 -c "from huggingface_hub import snapshot_download as s; s('vinai/PhoWhisper-medium'); print('PhoWhisper-medium ok')"
fi
# ---- self-test ----
cd "$HERE"
for f in lib/*.py project_template/project.py; do python3 -m py_compile "$f"; done
bash -n run.sh
python3 -c "import cv2, mediapipe, torch, torchaudio, soundfile, pyloudnorm, unidecode, PIL; print('imports ok')"
echo "install done. Models in $MODELS"
