"""Derived timeline helpers shared by audio.py / render.py: caption pages from the DSL, word lookups."""
import unicodedata
def word_t(P, word, after=0.0, which='start'):
    word = unicodedata.normalize('NFC', word.lower())
    c = [w for w in P.WORDS if unicodedata.normalize('NFC', w['word'].strip('?,.!').lower()) == word and w['start'] >= after - 1e-6]
    if not c: raise KeyError(f'word {word!r} after {after}')
    return c[0][which]
def at(P, v):
    """time reference: number, or 'word@after' (start of first such word at/after `after` s), optional '|offset' e.g. 'phí@30|0.1'"""
    if isinstance(v, (int, float)): return float(v)
    off = 0.0
    if '|' in v: v, o = v.split('|'); off = float(o)
    w, a = v.split('@'); return word_t(P, w, float(a)) + off
def parse_pages(P):
    pages = []; wi = 0; WORDS = P.WORDS
    for raw in P.PAGES.strip().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith('#'): continue
        if raw.startswith('SKIP'):
            wi += int(raw.split()[1]); continue
        lines = []
        for ln in raw.split(' / '):
            toks = []
            for tk in ln.split():
                kind = 'small'
                if tk[0] == '*': kind, tk = 'key', tk[1:]
                elif tk[0] == '^': kind, tk = 'big', tk[1:]
                n = None
                if '{' in tk: tk, n = tk.split('{'); n = int(n.rstrip('}'))
                parts = tk.split('_'); n = n if n is not None else len(parts)
                ws = WORDS[wi:wi + n]; wi += n
                toks.append(dict(text=' '.join(parts), kind=kind, start=ws[0]['start'], end=ws[-1]['end'], src=' '.join(w['word'] for w in ws)))
            lines.append(toks)
        pages.append(dict(lines=lines, start=lines[0][0]['start']))
    assert wi == len(WORDS), f'caption DSL consumed {wi} words, transcript has {len(WORDS)}'
    for i, p in enumerate(pages):
        last = max(t['end'] for l in p['lines'] for t in l)
        nxt = pages[i + 1]['start'] if i + 1 < len(pages) else P.DUR
        p['end'] = min(nxt, last + 0.7)
    return pages
def check_pages(P):
    """print pages and any display-text vs transcript-word mismatch (intended corrections show up here)"""
    for p in parse_pages(P):
        print(f"{p['start']:6.2f}-{p['end']:6.2f} | " + ' / '.join(' '.join(('*' if t['kind'] == 'key' else '^' if t['kind'] == 'big' else '') + t['text'] + f"[{t['start']:.2f}]" for t in l) for l in p['lines']))
        for l in p['lines']:
            for t in l:
                a = unicodedata.normalize('NFC', t['text'].lower()).replace('?', '').replace(',', '').replace('.', '').replace(':', '')
                b = unicodedata.normalize('NFC', t['src'].lower()).replace('?', '').replace(',', '').replace('.', '').replace(':', '')
                if a != b: print('      display:', t['text'], '<- words:', t['src'])
if __name__ == '__main__':
    import sys, os; sys.path.insert(0, os.path.dirname(__file__)); import proj
    check_pages(proj.arg_project())
