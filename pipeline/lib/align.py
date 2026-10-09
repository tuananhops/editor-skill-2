"""Step 2a: MMS forced alignment of project.TEXT (corrected transcript, one string per sentence) on stems/dialogue.wav
-> build/words_aligned.json.   usage: python3 align.py <project_dir>"""
import sys, os, json; sys.path.insert(0, os.path.dirname(__file__)); import proj, mms
P = proj.arg_project()
wav = mms.load16k(os.path.join(P.STEMS, 'dialogue.wav'))
words, seg = [], []
for si, s in enumerate(P.TEXT):
    for w in s.split():
        if mms.roman(w): words.append(w); seg.append(si)
out = mms.align(wav, words)
for o, si in zip(out, seg): o['seg'] = si
json.dump(out, open(os.path.join(P.BUILD, 'words_aligned.json'), 'w'), ensure_ascii=False, indent=0)
for o in out: print(f"{o['seg']:2d} {o['word']:12s} {o['start']:6.2f}-{o['end']:6.2f} {o['score']:.2f}" + ('   <-- low' if o['score'] < 0.1 else ''))
