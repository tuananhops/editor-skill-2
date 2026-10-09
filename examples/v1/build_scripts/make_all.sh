#!/bin/bash
# Full re-render. Edit build/timeline.py (captions/cards/punch-ins), build/grade.txt (color), s3_audio.py (mix), then run.
set -e; cd "${V1_ROOT:-.}"
[ -f build/base.mp4 ] || build/s1_base.sh             # base: cut + 7 pause frames + grade (re-run if grade.txt changes)
[ -f cache/faces.npy ] || python3 build/s2_analyze.py 240   # face track + hook segmentation masks
python3 build/s3_audio.py                               # stems + master
python3 build/s4_render.py full                        # graphics/captions/zooms -> build/video_nosound.mp4
build/s5_master.sh                                      # mux -> v1/final_v1.mp4 + loudness report
python3 build/s6_preview.py 0.0 12.9 17.3 20.95 23.2 35.0
