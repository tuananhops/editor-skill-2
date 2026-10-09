"""Step 5: mux video + master (AAC 320k, faststart) -> final/<OUT_NAME>; print stats.  usage: python3 master.py <project_dir>"""
import sys, os, subprocess; sys.path.insert(0, os.path.dirname(__file__)); import proj
P = proj.arg_project(); out = os.path.join(P.FINAL, P.OUT_NAME)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', P.BUILD + '/video_nosound.mp4', '-i', P.STEMS + '/mix_master.wav', '-map', '0:v', '-map', '1:a',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-movflags', '+faststart', out], check=True)
print(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,profile,width,height,r_frame_rate,pix_fmt,bit_rate,nb_frames',
                      '-show_entries', 'format=duration', '-of', 'compact', out], capture_output=True, text=True).stdout)
r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', out, '-map', '0:a', '-af', 'ebur128=peak=true:framelog=quiet', '-f', 'null', '-'], capture_output=True, text=True).stderr
print('\n'.join(l for l in r.splitlines() if l.strip().startswith(('I:', 'LRA:', 'Peak:'))))
