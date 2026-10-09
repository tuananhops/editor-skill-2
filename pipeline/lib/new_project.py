"""Bootstrap a project dir from the cutting bot's hand-off ("cắt ghép master": <name>_cut.mp4, notes.md,
transcript_output.json, transcript_source.json).
usage: python3 new_project.py <handoff_dir> <project_dir> [--src <source.mp4>]
 - copies pipeline/project_template/project.py -> <project_dir>/project.py (never overwrites an existing one)
 - fills SRC (from notes.md '- Source: `...`' or --src), CUT_REF, OUT_NAME, SEGMENTS (segment table in notes.md)
 - fills TEXT with the notes.md content column / transcript_output.json segments as a STARTING POINT:
   you still have to correct it word by word (see SKILL.md 'Caption accuracy')."""
import sys, os, re, json, glob, shutil
LIB = os.path.dirname(os.path.abspath(__file__))
def parse_notes(path):
    src, segs = None, []
    for line in open(path, encoding='utf-8'):
        m = re.search(r'Source:\s*`([^`]+)`', line)
        if m and not src: src = m.group(1)
        m = re.match(r'\|\s*\d+\s*\|\s*([\d.]+)\s*[–-]\s*([\d.]+)\s*\|\s*[\d.]+\s*[–-]\s*[\d.]+\s*\|\s*(.*?)\s*\|\s*$', line)
        if m: segs.append((float(m.group(1)), float(m.group(2)), m.group(3)))
    return src, segs
def main():
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    hand, pdir = os.path.abspath(a[0]), os.path.abspath(a[1]); src_arg = a[a.index('--src') + 1] if '--src' in a else None
    os.makedirs(pdir, exist_ok=True); out = os.path.join(pdir, 'project.py')
    if os.path.exists(out): sys.exit(f'{out} exists -- not overwriting')
    notes = os.path.join(hand, 'notes.md'); src, segs = parse_notes(notes) if os.path.exists(notes) else (None, [])
    src = src_arg or src or 'input/SOURCE.mp4'
    cut = (glob.glob(os.path.join(hand, '*_cut.mp4')) + glob.glob(os.path.join(hand, '*.mp4')) + [''])[0]
    name = os.path.basename(pdir.rstrip('/'))
    text = [c.replace('(?)', '') for _, _, c in segs]
    to = os.path.join(hand, 'transcript_output.json')
    if not text and os.path.exists(to): text = [s['text'].strip() for s in json.load(open(to, encoding='utf-8'))]
    T = open(os.path.join(LIB, '..', 'project_template', 'project.py'), encoding='utf-8').read()
    T = T.replace("SRC = 'input/SOURCE.mp4'", f'SRC = {src!r}').replace("CUT_REF = 'input/NAME_cut.mp4'", f'CUT_REF = {cut!r}')
    T = T.replace("OUT_NAME = 'NAME_final.mp4'", f"OUT_NAME = '{name}_final.mp4'")
    if segs:
        T = re.sub(r'SEGMENTS = \[.*?\n\]', 'SEGMENTS = [\n' + ''.join(f'    seg({x:.3f}, {y:.3f}),\n' for x, y, _ in segs) + ']', T, flags=re.S)
    if text:
        T = re.sub(r'TEXT = \[.*?\n\]', 'TEXT = [   # FROM THE CUTTING BOT -- VERIFY EVERY WORD before align\n' + ''.join(f'    {t!r},\n' for t in text) + ']', T, flags=re.S)
    open(out, 'w', encoding='utf-8').write(T)
    print(f'wrote {out}: {len(segs)} segments, {len(text)} text lines, SRC={src}')
if __name__ == '__main__': main()
