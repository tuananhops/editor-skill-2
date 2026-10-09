"""Load a per-video project config (project.py in the project dir) + derived timing helpers.
FPS: project.FPS ('60000/1001', '30000/1001', 30, ...) if set, else the source's r_frame_rate (keep source fps)."""
import importlib.util, json, os, sys, subprocess
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import paths
def _src_fps(src):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate',
                        '-of', 'csv=p=0', src], capture_output=True, text=True).stdout.strip()
    return r or '60000/1001'
def load(pdir):
    pdir = os.path.abspath(pdir)
    spec = importlib.util.spec_from_file_location('project', os.path.join(pdir, 'project.py'))
    P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
    P.DIR = pdir
    if hasattr(P, 'SRC'): P.SRC = paths.resolve(P.SRC, pdir)
    if getattr(P, 'MUSIC', None) and P.MUSIC.get('path'): P.MUSIC = dict(P.MUSIC, path=paths.music(P.MUSIC['path'], pdir))
    fr = Fraction(str(getattr(P, 'FPS', None) or _src_fps(P.SRC))).limit_denominator(1001)
    P.FPS_STR = f'{fr.numerator}/{fr.denominator}'; P.FPS = float(fr)
    for k, v in dict(BUILD='build', CACHE='cache', STEMS='stems', FINAL='final').items():
        setattr(P, k, os.path.join(pdir, v)); os.makedirs(getattr(P, k), exist_ok=True)
    sm = os.path.join(P.BUILD, 'segmap.json')
    if os.path.exists(sm):
        S = json.load(open(sm)); P.SEGMAP = S
        P.CUT_FRAMES = [s['out_f0'] for s in S] + [S[-1]['out_f1']]
        P.CUTS = [f / P.FPS for f in P.CUT_FRAMES]; P.NFRAMES = P.CUT_FRAMES[-1]; P.DUR = P.NFRAMES / P.FPS
    wa = os.path.join(P.BUILD, 'words_aligned.json')
    if os.path.exists(wa): P.WORDS = json.load(open(wa))
    return P
def arg_project():
    if len(sys.argv) < 2: sys.exit('usage: <script> <project_dir> ...')
    return load(sys.argv[1])
