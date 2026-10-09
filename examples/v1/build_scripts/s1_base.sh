#!/bin/bash
# Step 1: base video = rough cut + 7 natural-pause frames from source inserted at the 14.014 s join, then color grade.
set -e
cd "${V1_ROOT:-.}"; : "${V1_SRC:?set V1_SRC=source footage}" "${V1_CUT:?set V1_CUT=rough cut}"
G=$(cat build/grade.txt)
ffmpeg -v error -y -i "$V1_CUT" -ss 31.6 -i "$V1_SRC" -filter_complex "
[0:v]trim=start_frame=0:end_frame=840,setpts=PTS-STARTPTS[a];
[1:v]trim=start_frame=17:end_frame=24,setpts=PTS-STARTPTS,scale=1080:1920:flags=lanczos,setsar=1,format=yuv420p[b];
[0:v]trim=start_frame=840,setpts=PTS-STARTPTS[c];
[a][b][c]concat=n=3:v=1:a=0,fps=60000/1001,$G,format=yuv420p[v]" -map "[v]" -c:v libx264 -preset veryfast -crf 10 -an build/base.mp4
ffprobe -v error -count_frames -show_entries stream=nb_read_frames,r_frame_rate -of csv build/base.mp4
