"""MMS forced alignment helpers (torchaudio MMS_FA)."""
import re, subprocess, numpy as np, torch, torchaudio, functools
from unidecode import unidecode
SR = 16000
@functools.lru_cache(None)
def _m():
    b = torchaudio.pipelines.MMS_FA
    return b.get_model(), b.get_tokenizer(), b.get_aligner()
def load16k(path, t0=None, dur=None):
    a = ['ffmpeg', '-v', 'error']
    if t0 is not None: a += ['-ss', f'{t0:.3f}']
    a += ['-i', path]
    if dur is not None: a += ['-t', f'{dur:.3f}']
    p = subprocess.run(a + ['-map', '0:a:0', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True)
    return np.frombuffer(p.stdout, np.float32).copy()
def roman(w):
    return re.sub(r"[^a-z']", "", unidecode(w.replace('đ', 'd').replace('Đ', 'D')).lower())
def align(wav, words, offset=0.0):
    """words: display words -> list of dict(word,start,end,score); also returns total log-prob"""
    model, tok, aligner = _m()
    rw = [roman(w) for w in words]; keep = [i for i, r in enumerate(rw) if r]
    with torch.inference_mode():
        em, _ = model(torch.from_numpy(wav)[None]); em = torch.log_softmax(em, -1)
        spans = aligner(em[0], tok([rw[i] for i in keep]))
    ratio = len(wav) / em.shape[1] / SR
    out = []
    for i, sp in zip(keep, spans):
        out.append(dict(word=words[i], start=round(offset + sp[0].start * ratio, 3), end=round(offset + sp[-1].end * ratio, 3),
                        score=round(float(np.mean([x.score for x in sp])), 3)))
    return out
def ctc_score(wav, text):
    """forced-alignment log-likelihood per frame for a hypothesis (for comparing alternatives)"""
    import torchaudio.functional as F
    model, tok, _ = _m()
    toks = [t for w in text.split() for t in tok([roman(w)])[0]]
    with torch.inference_mode():
        em, _ = model(torch.from_numpy(wav)[None]); em = torch.log_softmax(em, -1)
        ali, sc = F.forced_align(em, torch.tensor([toks], dtype=torch.int32), blank=0)
    return float(sc.sum()) / em.shape[1]
