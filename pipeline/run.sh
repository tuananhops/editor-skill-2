#!/usr/bin/env bash
# Per-video @__dviet-style post pipeline.
#   pipeline/run.sh <project_dir> [all|base|analyze|align|joins|captions|audio|stills <t..>|montage [t..]|render|master|preview [t..]]
# <project_dir> must contain project.py (template: pipeline/project_template/project.py).
# 'all' skips base/analyze/align if their outputs exist (delete <project>/build/base.mp4 to rebuild after changing SEGMENTS/GRADE).
# Paths: see pipeline/lib/paths.py (EDITOR_FONTS_DIR, EDITOR_MUSIC_DIR, EDITOR_MODELS_DIR override the repo defaults).
set -eo pipefail
L="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib"
[ -n "$1" ] || { sed -n 2,6p "$0"; exit 1; }
D=$(cd "$1" && pwd); step=${2:-all}; shift 2 || shift $#
[ -f "$D/project.py" ] || { echo "no project.py in $D"; exit 1; }
quiet() { grep -v -E "^(W0|I0)|WARN|Warn" || true; }
case $step in
  base) python3 "$L/base.py" "$D" ;;
  analyze) python3 "$L/analyze.py" "$D" 2>&1 | quiet ;;
  align) python3 "$L/align.py" "$D" 2>&1 | quiet ;;
  joins) python3 "$L/joins.py" "$D" "$@" ;;
  captions) python3 "$L/timeline.py" "$D" ;;
  audio) python3 "$L/audio.py" "$D" ;;
  stills) python3 "$L/render.py" "$D" stills "$@" ;;
  montage) python3 "$L/montage.py" "$D" "$@" ;;
  render) python3 "$L/render.py" "$D" full ;;
  master) python3 "$L/master.py" "$D" ;;
  preview) python3 "$L/preview.py" "$D" "$@" ;;
  all)
    [ -f "$D/build/base.mp4" ] || python3 "$L/base.py" "$D"
    [ -f "$D/cache/faces.npy" ] || python3 "$L/analyze.py" "$D" 2>&1 | quiet
    [ -f "$D/build/words_aligned.json" ] || python3 "$L/align.py" "$D" 2>&1 | quiet
    python3 "$L/timeline.py" "$D" > "$D/build/captions_check.txt"
    python3 "$L/audio.py" "$D"
    python3 "$L/render.py" "$D" full
    python3 "$L/master.py" "$D"
    python3 "$L/preview.py" "$D" ;;
  *) echo "unknown step: $step"; exit 1 ;;
esac
