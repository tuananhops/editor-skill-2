# Caption accuracy tools

All read audio straight from a media file with ffmpeg (16 kHz mono). Models download on first use (install.sh pre-warms them).

| tool | command | use |
|---|---|---|
| MMS forced alignment | `pipeline/run.sh <project> align` | word start/end + score for project TEXT; score < 0.1 = check that word |
| PhoWhisper (VinAI) | `python3 pipeline/lib/pho.py medium <src.mp4> 32.0-36.85 74.6-77.5` | independent Vietnamese ASR on short windows (2–5 s). CPU: ~15–140 s per window; run in background. `large` may be OOM-killed on 16 GB boxes |
| CTC A/B | `python3 pipeline/lib/ctc_ab.py <src.mp4> 32.0 36.85 "cand A" "cand B"` | which wording fits the audio best (higher score = better) |

Procedure and the list of common errors: SKILL.md §4. Logs from these runs are scratch — don't commit them (they contain client speech).
