# Style-study scripts (weekly @__dviet research)

Quick-and-dirty research scripts used to produce STYLE_GUIDE.md. Optional deps: `pip install -r ../requirements-analysis.txt`
(scenedetect, librosa, demucs, yt-dlp) + `../install.sh` for the YuNet model. Work in a scratch dir, e.g. `study/`.
`<D>` = an output dir per video.

| script | usage | output |
|---|---|---|
| video_an.py | `python3 video_an.py <video.mp4> <D>` | `<D>/video.json`: cut lists (`content`, `adaptive`), fps, per-frame luma/colour stats |
| shots.py | `python3 shots.py <D>/video.json [content|adaptive]` | per-shot table (len, zoom, Y, p2/p98, sat, Lab) → `<D>/shots.json` |
| face.py | `python3 face.py <video.mp4> <D>` | `<D>/face.json` YuNet face boxes at ~15 fps |
| zoom.py | `python3 zoom.py <D> [content|adaptive]` | punch-in factors from face width per shot |
| bgzoom.py | `python3 bgzoom.py <video.mp4> <D> [adaptive]` | SIFT background scale across cuts (punch-in check without a face) |
| chroma.py | `python3 chroma.py <video.mp4> <D>` | `<D>/chroma_shots.json` Lab colour per shot |
| audio_an.py | `python3 audio_an.py <video.mp4> <D>` | `<D>/audio.json` LUFS / LRA / true peak / spectral stats |
| music.py | `demucs --two-stems vocals -o sep/out <video.mp4>` then `python3 music.py <id>` (run in the dir containing `sep/`) | `sep/<id>_music.json`: voice vs bed LUFS, ducking correlation, BPM |
| align.py | `python3 align.py <id> <D>` | beats vs cuts (are cuts beat-synced? p-value vs random) |
| summary.py | `python3 summary.py` (from the parent of `analysis/`; scans `analysis/main` + `analysis/76*`) | merged cut list (content ∪ adaptive within 0.3 s) + summary numbers |

Download: `yt-dlp -o 'study/%(id)s.%(ext)s' --write-info-json https://www.tiktok.com/@__dviet` (or single video URLs).
Contact sheet: `ffmpeg -i v.mp4 -vf "fps=1/1.5,scale=270:-1,tile=8x6" -frames:v 1 contact.jpg`.
Append new findings to STYLE_GUIDE.md (dated section) — see WORKFLOW.md "Weekly Monday routine".
