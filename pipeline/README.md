# pipeline — per-video @__dviet-style post pipeline

```
pipeline/
  install.sh               apt (ffmpeg…) + pip (requirements.txt) + models -> pipeline/models/ + weight pre-download + self-test
  requirements.txt         pinned runtime deps (CPU torch)      requirements-analysis.txt  optional style-study deps
  run.sh                   step runner: run.sh <project_dir> <step>
  project_template/project.py   commented per-video config (copy or use lib/new_project.py)
  lib/                     the engine (see table)
  asr/README.md            caption-accuracy tools (MMS alignment, PhoWhisper, CTC A/B)
  analysis/                @__dviet style-study scripts (weekly routine)
  models/                  (gitignored) yunet.onnx, selfie_multiclass_256x256.tflite, rnn_std.rnnn
```

## Setup
```bash
pipeline/install.sh          # Debian/Ubuntu; uses sudo for apt if not root. SKIP_APT=1 / SKIP_PIP=1 / SKIP_WARM=1 to skip parts
```
Needs ~6 GB disk (torch + MMS_FA 1.2 GB + PhoWhisper-medium ~3 GB in ~/.cache), 8+ GB RAM recommended, no GPU needed.
Paths are relative to the repo; override with `EDITOR_FONTS_DIR`, `EDITOR_MUSIC_DIR`, `EDITOR_MODELS_DIR` (lib/paths.py).
Hugging Face downloads work without a token (set `HF_TOKEN` only if you hit rate limits — never commit it).

## One video end to end
```bash
python3 pipeline/lib/new_project.py <handoff_dir> work/<name> --src <source.mp4>   # SRC, SEGMENTS, draft TEXT from notes.md
$EDITOR work/<name>/project.py                 # SEGMENTS join fixes, ACCENT, GRADE, verified TEXT
pipeline/run.sh work/<name> base               # -> build/base.mp4 (graded, 1080x1920, source fps), stems/dialogue.wav, build/segmap.json
pipeline/run.sh work/<name> joins              # energy strips around every join -> fix SEGMENTS, rm build/base.mp4, base again
pipeline/run.sh work/<name> analyze            # -> cache/faces.npy (YuNet per frame), cache/masks.npz (person masks, first SEG_SECONDS)
pipeline/run.sh work/<name> align              # -> build/words_aligned.json (MMS forced alignment of TEXT)
$EDITOR work/<name>/project.py                 # PAGES, CARDS, OVERLAYS, PUNCH, MUSIC, CTA_HIT, STILLS
pipeline/run.sh work/<name> captions           # page list + display≠spoken mappings
pipeline/run.sh work/<name> audio              # -> stems/{voice,music,sfx,mix_master}.wav + sfx_events.json
pipeline/run.sh work/<name> stills 0.5 3.5 9   # -> cache/still_XXX.XX.png  (iterate on the look without rendering)
pipeline/run.sh work/<name> render             # -> build/video_nosound.mp4 (10 s chunks in build/chunks, resumable)
pipeline/run.sh work/<name> master             # -> final/<OUT_NAME> + ffprobe + loudness report
pipeline/run.sh work/<name> preview            # -> final/preview_sheet.jpg + final/stills/
# or: pipeline/run.sh work/<name> all   (skips base/analyze/align if their outputs exist)
```
Project dir layout after a run: `build/` (base, chunks, words), `cache/` (faces, masks, stills), `stems/`, `final/`.
These are big (base.mp4 ≈ 7 MB/s) — keep them out of git; delete `build/` + `cache/` when a video is signed off.

## lib/
| file | what |
|---|---|
| paths.py | repo-relative paths + env overrides; `model()` errors clearly if install.sh wasn't run |
| proj.py | loads project.py; resolves SRC / MUSIC paths; FPS = project FPS or source fps; derives CUTS, DUR, WORDS |
| new_project.py | bootstrap project.py from the cutting bot's hand-off (notes.md segment table, transcript) |
| base.py | frame-accurate rebuild from source via SEGMENTS (+PRE, scale, GRADE), sample-exact dialogue with join fades |
| joins.py | join inspector (10 ms energy strips) |
| analyze.py | YuNet face track (all frames) + MediaPipe selfie-multiclass person masks for the hook |
| mms.py / align.py | torchaudio MMS_FA forced alignment (Vietnamese romanised via unidecode) |
| pho.py / ctc_ab.py | PhoWhisper second opinion / CTC A/B of candidate transcripts |
| timeline.py | caption DSL parser + `word@after|offset` time refs; `__main__` = captions check |
| audio.py | sentence leveling, voice chain, music bed (LU under voice), synth SFX, true-peak-safe master |
| render.py | zoom (push/punch), captions, hook-behind-head, cards (list/compare/tools/pip), chips, CTA, flashes, end fade; chunked x264 |
| master.py | mux AAC 320k + faststart, ffprobe, EBU R128 report |
| preview.py / montage.py | QA contact sheet + stills / montage of cache stills |
| music_scan.py | find drops in a music file to land on the CTA |

## Caption DSL (PAGES)
One line per page; ` / ` = line break; `*word` accent serif keyword, `^word` big white, plain = small white;
`a_b` joins words into one token; `tok{n}` consumes n transcript words; `SKIP n` = n words without captions; `#` comments.
The DSL must consume exactly all aligned words (assertion tells you the count). See `examples/ad_01/project.py`.

## Time references
Anywhere a time is expected (CARDS, OVERLAYS, PUNCH, CTA_HIT, SFX_EXTRA): seconds on the output timeline, or
`'word@after'` = start of the first transcript word `word` at/after `after` seconds, optionally `'|offset'`
(e.g. `'inbox@40|-0.06'`). Word refs survive small timing changes when you fix joins.
