# @__dviet style guide (research notes, cleaned up)

Source: frame-by-frame + audio analysis of 6 public TikTok videos by **@__dviet** (Aug–Oct 2026), done with
`pipeline/analysis/*.py` (PySceneDetect, YuNet face tracking, SIFT background scale, Lab colour stats, EBU R128,
Demucs stem split, librosa beat tracking). Contact sheets are in `reference/`.
Section 7 says how we **adapt** this style for our Vietnamese talking-head ads. SKILL.md has the binding rules.

| reference file | video |
|---|---|
| reference/main_7677448217667063061_contact_01..04.jpg | main study video "Việt Mỏi Lưng", 71.7 s, 30 fps |
| reference/contact_7693026626333871381.jpg | music-selection, talking head ep.2 (2026-10-05) |
| reference/contact_7688934517783989524.jpg | invideo sponsored (2026-09-24) |
| reference/contact_7683763922234641684.jpg | blend modes (2026-09-10) |
| reference/contact_7672413018575146261.jpg | CapCut outro tutorial (2026-08-10) |
| reference/contact_7670574911680777492.jpg | CapCut effects series (2026-08-05) |

---

## 1. Channel-wide traits (seen in all or nearly all 6 videos)

1. **Look.** Centered medium close-up talking head in a dark, low-key room with one saturated coloured practical light.
   Handheld wireless mic in frame, glasses. Talking-head luma ~40–85/255, crushed blacks (p2 ~1–12, 5–31 % near-black
   pixels), highlights rolled off below ~195, low overall chroma. The accent hue changes per video, and **the caption
   accent colour matches the set light and grade** (purple/pink light → purple text; green → green; warm orange → yellow/gold).
2. **Captions.** Word-by-word kinetic captions in the centre/chest area, 1–3 words per line. Small white sans words
   paired with a big italic serif / script / heavy keyword. Soft shadow or glow, **no outlines, no emoji**. One accent colour per video.
3. **Editing.** Hard cuts on speech; median shot ~2.2–3.3 s (8–23 cuts/min; screen tutorials slowest). Hook-heavy
   openings (5–7 edits in the first 10 s). Punch-ins of 1.2–1.6× on the talking head (face width ~25 % of frame
   → ~33–40 %), returning to base on the next cut.
4. **B-roll / graphics.** Screen recordings (CapCut etc.), tilted 3D screen/phone mockups, squircle PiP of himself with a
   glow, full-screen type cards with numbered steps (01/02/03, "bước một/hai/ba/bốn"), glossy 3D / gradient backgrounds.
   Small single-line white subtitles at the bottom over B-roll in tutorial parts.
5. **Audio.** Continuous music bed under the voice (98–100 % of the runtime), **no ducking / sidechain**. Bed 4–7.5 LU
   under the voice. Loud, compressed masters: −10.9 to −12.1 LUFS integrated, LRA 1.6–3.0 LU, true peak above 0 dBTP
   (+0.7 to +3.0: he does not limit — **we do**, see SKILL.md). Tempo 88–122 BPM. **Cuts are not beat-synced**
   (they follow speech). SFX (whooshes, pops, ticks) mark graphic and text changes.
6. **Series branding / CTA.** "talking head VIDEO" chrome title with "ep.N". CTA endings: "follow mình",
   "FOLLOW 4 MORE <3", comment a keyword to get resources ("Blend", "invideo", "EDIT", "tài nguyên").

## 2. Main video in numbers (7677448217667063061, "Việt Mỏi Lưng")

**Format.** HEVC 1080×1920, 30.000 fps CFR (2152 frames, 71.73 s); AAC 44.1 kHz ~96 kbps. (His other 5 videos are 60 fps.)

**Cuts.** PySceneDetect Content thr 27 + Adaptive, merged within 0.3 s: 28 cuts → 29 shots; mean 2.47 s, median 2.13 s,
min 0.43 s, max 6.30 s; **23.4 cuts/min**.
Cut times (s): 3.93, 5.77, 7.07, 7.5, 8.0, 8.5, 9.1, 10.53, 16.83, 19.77, 21.33, 25.53, 28.13, 30.07, 31.97, 34.8,
37.03, 40.67, 42.77, 46.47, 50.2, 52.33, 56.63, 59.53, 61.47, 63.23, 66.9, 67.83.

**Pacing** (cuts per 10 s): 7 | 3 | 3 | 4 | 3 | 4 | 4 | 0. Front-loaded hook (7 cuts in 0–10 s, incl. a 7.07–9.10 s
montage of other creators' clips swapping every ~0.1–0.2 s inside one frame), then ~1 edit / 2.5–3 s; the final 4 s CTA
has no cut. Detectors undercount: much of the "edit rhythm" is on-screen graphics changes (word-by-word captions, card
changes) with no camera cut.

**Punch-ins** (YuNet face width + SIFT background scale). Base face width ~137 px / 540 (~25 % of frame width).
Punch-ins 1.27–1.39× at 4.07 s (hidden under a light-leak flash), 5.77, 19.77, 66.90; each returns to base on the next cut.
Occasional slow push-in inside a shot (16.8–19.8 s: ~+7 %/s, ~1.14× total).

**Colour, talking-head shots** (14 shots). Mean luma 37.7/255, luma std 44.3, p2 0.8, p98 183, ~31 % of pixels near-black
(L<10), Lab chroma 6.9 (low saturation), midtone a* +16 (magenta/pink), b* +6.5 (slightly warm).
Grade = low-key, crushed (not lifted) blacks, soft highlight roll-off (p98 ~183, almost nothing clipped), desaturated
except a hot-pink practical LED behind the speaker.
Graphic cards: white #FAFAFA / lavender gradient (Y 205–245), one purple card (#8C6CFF-ish, a* +41, b* −45), dark grey gradient card.

**Audio.** Integrated −10.9 LUFS, true peak +0.7 dBTP, LRA 2.1 LU (heavily compressed).
Demucs split: vocals −13.0 LUFS, music bed −16.8 LUFS (bed only 3.8 LU under the voice), music present 100 % of the time,
no ducking (vocal vs music level correlation −0.07; music −19.6 dB under speech vs −18.2 dB in pauses).
Tempo 120.0 BPM; drums enter ~9–10 s (opening impact at 0 s, quiet breakdown 2–9 s with near-silence ~6–8 s, full groove
from the "xin chào" cut at 9.1 s, swell 36–40 s). Cuts vs beats: mean offset 125 ms vs 124 ms random → **not beat-synced** (p = 0.51).
Likely SFX (bright off-beat transients): 4.0–4.3 (light-leak whoosh), 7.08, 7.34, 8.13, 8.66 (montage swaps,
centroid 4.4–6.5 kHz), 12.4–14.6 (icon pops on white card), 18.90, 24.06, 25.59 (fonts card), 43.61, 44.81, 48.48,
50.55, 51.08 (font-card changes), 64.9, 65.6.

## 3. Captions and type

- Kinetic, word-by-word, synced to speech. Each word fades/blurs in, often scaling or sliding in with motion blur.
  Usually 1–3 words per line, stacked 2–3 lines.
- Two-level hierarchy: tiny white clean sans (SF Pro / Inter look) for filler words; the keyword large in a condensed
  italic serif (Playfair / Instrument Serif Italic look) or a heavy sans. Keywords white or the accent (#8C6CFF in the main
  video; the palette is literally shown at 64–66 s: #FAFAFA / #111111 / #8C6CFF). Some words in script.
- No hard stroke/outline. Soft drop shadow or outer glow; slight bloom on the accent. All-lowercase Vietnamese except
  title words ("VIDEO": huge bold white, chrome gradient, accent shadow, "ep.1" tag, italic accent "talking head" over it).
- Position: chest/centre (~45–60 % of frame height); big keywords sometimes at the top (~15–25 %) above the head.
  No emoji or stickers; small flat line-icons (camera, timeline, pen) pop in on white cards.

## 4. Overlays, B-roll, transitions

- Rounded squircle PiP with accent outer glow on white/lavender backgrounds; montage of other creators' talking heads;
  screen recordings in the top half with the talking head below (split screen); tilted laptop B-roll; full-screen type
  cards (white, lavender gradient, purple, dark chrome) with numbered "01/02/03" lists; glitch / pixel-sort background
  (21–25 s); colour swatches over the talking head.
- Transitions: mostly **hard cuts**. Also a white light-leak / film-burn flash (~4.0–4.3 s), blur/fade-in from white
  (37 s), fast font-cycling card (new typeface every ~0.1 s), motion-blur text slides. Punch-in jump cuts for emphasis.
- Set: dark room, black tee, glasses, handheld wireless mic always visible, hot-pink LED behind the left shoulder,
  monitors/shelves in the background, centred medium close-up.

## 5. The other five videos

| id | date | dur | fps | shots | mean/med shot s | cuts/min | LUFS / TP | music vs voice | BPM | cuts on beat? | talking-head grade |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 7693026626333871381 (music selection, ep.2) | 2026-10-05 | 49 s | 60 | 19 | 2.59/2.20 | 21.9 | −11.9 / +2.1 | −4.3 LU | ~92 (or 136) | no (p=0.73) | cool magenta/purple, a*+9 b*−8 |
| 7688934517783989524 (invideo sponsored) | 2026-09-24 | 65 s | 60 | 17 | 3.81/3.30 | 14.8 | −12.1 / +1.4 | −7.5 LU | 122 | weak (p=0.09) | neutral-warm, low chroma 5 |
| 7683763922234641684 (blend modes) | 2026-09-10 | 59 s | 60 | 20 | 2.97/2.73 | 19.2 | −10.9 / +1.1 | −5.7 LU | 105 | no (p=0.69) | green-yellow, a*−7 b*+14 |
| 7672413018575146261 (CapCut outro tutorial) | 2026-08-10 | 65 s | 60 | 10 | 6.51/5.45 | 8.3 | −12.1 / +0.7 | −6.6 LU | 88 | no (p=0.34) | neutral dark, chroma 5 |
| 7670574911680777492 (CapCut effects series) | 2026-08-05 | 63 s | 60 | 20 | 3.16/2.66 | 18.0 | −11.5 / +3.0 | −7.1 LU | 101 | no (p=0.52) | warm orange, a*+13 b*+21 |
| **main** 7677448217667063061 | 2026-08-24 | 72 s | 30 | 29 | 2.47/2.13 | 23.4 | −10.9 / +0.7 | −3.8 LU | 120 | no (p=0.51) | dark, magenta accent, a*+16 b*+6.5 |

Specific to the main video: white/lavender design cards and the #8C6CFF palette (shared only with ep.2), the montage of
other creators' clips, the font-showcase cards, the fastest pacing (23.4 cuts/min) and the loudest bed (−3.8 LU), 30 fps.

## 6. Reproducing the measurements

```bash
pip install -r pipeline/requirements-analysis.txt
yt-dlp -o 'study/%(id)s.%(ext)s' --write-info-json https://www.tiktok.com/@__dviet/video/<id>
python3 pipeline/analysis/video_an.py study/<id>.mp4 study/<id>      # cuts (Content + Adaptive), per-frame stats
python3 pipeline/analysis/face.py     study/<id>.mp4 study/<id>      # face track -> face.json
python3 pipeline/analysis/zoom.py     study/<id> content             # punch-in factors per shot
python3 pipeline/analysis/audio_an.py study/<id>.mp4 study/<id>      # loudness, LRA, TP
# music: demucs --two-stems vocals -o sep/out study/<id>.mp4 ; then music.py / align.py (beats vs cuts), chroma.py (colour)
```
See `pipeline/analysis/README.md` for each script's arguments.

## 7. How we adapt it (our house style, approved by Tracy)

Our footage is different (Vietnamese business talking heads, often **daylight / street**, lavalier/DJI mic with a coloured
transmitter), so we keep the *grammar* and adapt the *look*:
- accent colour = strongest coloured element in our shot (e.g. pink DJI mic → **#FF4FA3**; raspberry under hard sun → #FF3D6E);
- grade adapted to the footage: daylight → clean cinematic (slight contrast, soft roll-off, greens/cyans pulled down,
  light vignette), **not** crushed;
- captions: small white **Be Vietnam Pro** + big accent **Playfair Display Italic** keywords (+ big white heavy sans);
- behind-the-head hook text in the first ~4 s (person segmentation);
- punch-ins 1.10–1.25× on key beats (reset on the next phrase) + slow 1.00→1.06 push-ins; 2–4 clean cards / glowing PiP;
- hard cuts + 1–2 white flashes; synthesized pop / whoosh / riser SFX;
- CC0 lo-fi bed ~6 LU under the voice, no ducking; master −11 LUFS but **true peak ≤ −1 dBTP** (TikTok re-encode safe).
