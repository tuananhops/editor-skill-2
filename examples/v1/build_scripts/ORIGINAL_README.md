# v1 (first approved video) post-production (dviet-style) — re-renderable build

Run everything: `build/make_all.sh`  (≈5 min on the box). Output: `v1/final_v1.mp4`, `v1/preview_sheet.jpg`, `v1/stills/`.

| step | file | what |
|---|---|---|
| 1 | build/s1_base.sh | rough cut + 7 natural-pause frames from the source inserted at the 14.014 s join (+0.1168 s), color grade (`build/grade.txt`) -> build/base.mp4 |
| 2 | build/s2_analyze.py | YuNet face track per frame (cache/faces.npy), mediapipe selfie-multiclass person masks for the hook (cache/masks.npz) |
| – | build/align.py, build/words_text.py | corrected transcript + MMS forced alignment (torchaudio MMS_FA) -> build/words_aligned.json |
| – | build/timeline.py | THE EDL: caption pages DSL, cards, overlays, punch-ins, flashes. Edit here for revisions. |
| 3 | build/s3_audio.py | dialogue fix, phrase leveling, voice chain, music stem, synth SFX, master -> stems/ |
| 4 | build/s4_render.py | zooms, captions, hook depth text, cards, flashes -> build/video_nosound.mp4 (`stills t1 t2…` mode for previews) |
| 5 | build/s5_master.sh | mux AAC 320k + faststart, loudness report |
| 6 | build/s6_preview.py | contact sheet + stills from the final file |

Stems (48 kHz): stems/voice.wav, stems/music.wav (swappable), stems/sfx.wav, stems/mix_master.wav; stems/sfx_events.json.

## Licenses / sources
- Music: "Unwind" by HoliznaCC0, album "Kick It (laid back HipHop)", CC0 1.0 Universal (public domain dedication, commercial use OK, no attribution required).
  Page: https://freemusicarchive.org/music/holiznacc0/kick-it-laid-back-hiphop/unwind/ (saved: assets/music_unwind.page.html). Used 158.03 s–196.17 s of the track.
  Alternate also downloaded: "Not It (Lofi)" HoliznaCC0, CC0 — https://freemusicarchive.org/music/holiznacc0/lo-fi-and-chill/not-it-lofimp3/
- SFX: all synthesized in build/s3_audio.py (numpy), no third-party samples.
- Fonts: Be Vietnam Pro, Playfair Display, Inter — Google Fonts, SIL Open Font License 1.1 (copied to fonts/).
- Denoise model: rnnoise "std.rnnn" from github.com/richardpl/arnndn-models (processing tool only).
- Segmentation: MediaPipe selfie_multiclass_256x256 (Apache 2.0). Face detection: OpenCV YuNet.
