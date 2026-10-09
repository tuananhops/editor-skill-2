"""Central path config. Everything is relative to the repo unless overridden by env vars:
  EDITOR_SKILL_ROOT  repo root (default: two levels above this file)
  EDITOR_FONTS_DIR   fonts            (default: <root>/assets/fonts)
  EDITOR_MUSIC_DIR   music library    (default: <root>/assets/music)
  EDITOR_MODELS_DIR  downloaded models: yunet.onnx, selfie_multiclass_256x256.tflite, rnn_std.rnnn
                     (default: <root>/pipeline/models, filled by pipeline/install.sh)"""
import os
LIB = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.environ.get('EDITOR_SKILL_ROOT', os.path.join(LIB, '..', '..')))
FONTS = os.path.abspath(os.environ.get('EDITOR_FONTS_DIR', os.path.join(ROOT, 'assets', 'fonts')))
MUSIC = os.path.abspath(os.environ.get('EDITOR_MUSIC_DIR', os.path.join(ROOT, 'assets', 'music')))
MODELS = os.path.abspath(os.environ.get('EDITOR_MODELS_DIR', os.path.join(ROOT, 'pipeline', 'models')))
def font(name): return os.path.join(FONTS, name)
def model(name):
    p = os.path.join(MODELS, name)
    if not os.path.exists(p): raise SystemExit(f'missing model {p} -- run pipeline/install.sh (or set EDITOR_MODELS_DIR)')
    return p
def resolve(path, base):
    """absolute path as-is; '~' / $VARS expanded; relative -> relative to `base` (the project dir)"""
    path = os.path.expandvars(os.path.expanduser(path))
    return path if os.path.isabs(path) else os.path.abspath(os.path.join(base, path))
def music(path, base):
    """MUSIC['path']: bare file name -> looked up in the music library; otherwise like resolve()"""
    if os.sep not in path and not os.path.exists(os.path.join(base, path)): return os.path.join(MUSIC, path)
    return resolve(path, base)
