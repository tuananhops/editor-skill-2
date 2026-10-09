#!/bin/bash
# mux video + mastered audio (AAC 320k), faststart; then measure.
set -e; cd "${V1_ROOT:-.}"; mkdir -p v1/stills
ffmpeg -v error -y -i build/video_nosound.mp4 -i stems/mix_master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -ar 48000 \
  -movflags +faststart -shortest v1/final_v1.mp4
ffprobe -v error -show_entries stream=codec_name,profile,width,height,r_frame_rate,pix_fmt,bit_rate,sample_rate,nb_frames -show_entries format=duration -of compact v1/final_v1.mp4
ffmpeg -hide_banner -nostats -i v1/final_v1.mp4 -map 0:a -af ebur128=peak=true:framelog=quiet -f null - 2>&1 | grep -E "^ +(I|LRA|Peak):"
