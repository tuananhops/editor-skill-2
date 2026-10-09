# editor-skill-2 — "Editor 02" (bot hậu kỳ video dọc, style @__dviet)

## Tiếng Việt

**Đây là gì:** bộ kỹ năng đầy đủ của bot hậu kỳ **Editor 02** trong team của Tracy. Bot nhận bản cắt thô từ bot
"cắt ghép master" và làm ra video quảng cáo talking-head dọc 1080x1920 tiếng Việt theo style TikTok **@__dviet**:
sub chạy từng chữ (Be Vietnam Pro trắng nhỏ + Playfair Display Italic màu accent), chữ hook sau đầu, punch-in, card/PiP,
chỉnh màu theo footage, sửa chỗ nối âm thanh, lọc giọng, nhạc CC0 lo-fi, SFX tự tổng hợp, master −11 LUFS.
Repo chứa luật style, quy trình làm việc, toàn bộ script pipeline, font, nhạc CC0 và cấu hình mẫu của các video đã duyệt,
nên bot mới cài vào là làm ra kết quả giống y vậy, không cần "dạy" lại.

**Cài lên bot mới:**
1. Máy Linux có shell (Debian/Ubuntu), ~6 GB trống, 8 GB RAM trở lên. Không cần GPU.
2. `git clone https://github.com/tuananhops/editor-skill-2.git && cd editor-skill-2 && pipeline/install.sh`
   (cài ffmpeg + thư viện Python + tải model; chạy xong có tự kiểm tra).
3. Đưa cho bot **SKILL.md** (cách làm, style, QA) + **WORKFLOW.md** (quy trình team) — dán làm skill/knowledge, và dán
   đoạn persona tiếng Việt ở cuối WORKFLOW.md làm system prompt.
4. Điền placeholder trong WORKFLOW.md: `<DRIVE_FOLDER_URL>` (folder Drive của Tracy) — repo public nên không ghi link thật.
5. Kết nối **Google Drive** cho bot (để upload video xong) và cho bot quyền đọc folder footage / hand-off của bot cắt ghép.
6. Chạy thử: `python3 pipeline/lib/new_project.py <folder hand-off> work/test --src <footage gốc>` rồi làm theo SKILL.md §6.

## English (short)

Complete, self-contained skill for a post-production bot that turns rough cuts of Vietnamese vertical talking-head ads into
finished videos in the @__dviet TikTok style. Install: clone → `pipeline/install.sh` → give the bot `SKILL.md` +
`WORKFLOW.md` (+ the persona prompt at the end of WORKFLOW.md) → connect Google Drive and fill `<DRIVE_FOLDER_URL>`.
Run one video: `SKILL.md` §6 / `pipeline/README.md`.

## Folder map

| path | what |
|---|---|
| `SKILL.md` | **the skill**: role, deliverable spec, style rules, audio repair, caption accuracy, QA checklist, how to run |
| `WORKFLOW.md` | team workflow: hand-off from the cutting bot, Drive upload, reporting to Tracy in Vietnamese, usage-limit rule, weekly study, persona prompt |
| `STYLE_GUIDE.md` | the @__dviet research (numbers, captions, graphics, audio) + how we adapt it |
| `reference/` | contact sheets of the 6 analysed @__dviet videos |
| `pipeline/` | `install.sh`, `requirements*.txt`, `run.sh`, `lib/` (engine), `project_template/`, `asr/`, `analysis/`, `README.md` |
| `assets/fonts/` | Be Vietnam Pro, Playfair Display, Inter (SIL OFL 1.1, licenses included) |
| `assets/music/` | CC0 lo-fi tracks (HoliznaCC0) + `LICENSES.md` with source URLs |
| `examples/` | project.py of approved videos (ad_01, ad_02) + the v1 build scripts |

Not included (by design): videos, stems, client footage/transcripts, preview images of clients, model weights (downloaded
by install.sh), any tokens or private links.

Licenses: code — internal use by Tracy's team; fonts — SIL OFL 1.1; music — CC0 1.0; @__dviet reference frames are
small research thumbnails of public videos (© their creator), not for reuse in videos.
