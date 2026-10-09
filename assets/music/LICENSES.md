# Music licenses

All tracks are by **HoliznaCC0**, published on the Free Music Archive under **CC0 1.0 Universal** (public-domain dedication:
commercial use OK, no attribution required). Verified on each track page at download time (2026-10-09).

| file in this folder | title | used in | track page | direct file |
|---|---|---|---|---|
| music_unwind.mp3 | Unwind (album "Kick It (laid back HipHop)") | examples/v1 (offset 158.03 s, kick returns on "Inbox") | https://freemusicarchive.org/music/holiznacc0/kick-it-laid-back-hiphop/unwind/ | https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/LAgVpVHq5zNtFfoGRuekcRZSz9kkCpgxRjRsOqqt.mp3 |
| music_not-it-lofimp3.mp3 | Not It (Lofi) (album "Lo-fi and Chill") | examples/ad_01, template default | https://freemusicarchive.org/music/holiznacc0/lo-fi-and-chill/not-it-lofimp3/ | https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/w1MYaC19HagFOSBpkPXj7LmuEABahWvzzC3qgfoi.mp3 |
| music_creature-comforts.mp3 | Creature Comforts (album "Lo-fi and Chill") | examples/ad_02 | https://freemusicarchive.org/music/holiznacc0/lo-fi-and-chill/creature-comforts/ | https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/1186U6k2bOt7pNuiQ1F8bstYFgzO9wS0Wv8F9xIU.mp3 |

Also vetted (CC0, same artist) but not stored here, download if you want more variety:

| file name to use | title | track page | direct file |
|---|---|---|---|
| music_morning-coffee.mp3 | Morning Coffee | https://freemusicarchive.org/music/holiznacc0/lo-fi-and-chill/morning-coffee/ | https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/3oECfGbiMKRefansiQFDoumFo0fXknIhsLtlE3x4.mp3 |
| music_new-shoes.mp3 | New Shoes | https://freemusicarchive.org/music/holiznacc0/lo-fi-and-chill/new-shoes/ | https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/lFCAIOaX9YXuVwVGHlIZhZ5iRFSFDBDXiz1kOBGA.mp3 |
| music_ramenmp3.mp3 | Ramen | https://freemusicarchive.org/music/holiznacc0/lo-fi-and-chill/ramenmp3/ | https://files.freemusicarchive.org/storage-freemusicarchive-org/tracks/fVn5fseD1bzDmbU0fxkhzufvByvMeSeNy2JAHWmR.mp3 |

```bash
cd assets/music && curl -fL -o music_morning-coffee.mp3 "<direct file URL>"
```

Rules for adding music: only CC0 / public-domain (or a license that explicitly allows commercial ads with no attribution),
save the track page URL + license in this table, lo-fi / chill hip-hop ~85-120 BPM, no vocals.
`python3 pipeline/lib/music_scan.py <file>` lists "drop" points so a drop can land on the CTA word.

## SFX
No samples: pop / tick / whoosh / riser / hit are synthesized with numpy in `pipeline/lib/audio.py`.

## Other third-party items (downloaded by install.sh, not in git)
- rnnoise model `std.rnnn` — https://github.com/richardpl/arnndn-models (used by ffmpeg `arnndn`)
- MediaPipe `selfie_multiclass_256x256.tflite` — Apache 2.0, Google
- OpenCV Zoo YuNet `face_detection_yunet_2023mar.onnx` — MIT
- torchaudio `MMS_FA` (Meta MMS forced aligner, CC-BY-NC 4.0 weights: processing tool only), `vinai/PhoWhisper-medium` (BSD-3)
