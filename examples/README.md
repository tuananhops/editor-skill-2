# Examples

Client footage, transcripts, rendered videos, preview sheets and stills are **not** in this public repo (privacy).
What's here is the editing *config* of approved videos — the best reference for how to write a project.py.

| folder | what |
|---|---|
| ad_01/project.py | **approved** batch-2 video (44 s, daylight street, pink mic accent #FF4FA3): join fixes with notes, hook "hàng triệu?", 4 cards (list / tools / compare / PiP), 8 punch-ins, CTA pill, music drop on the first "Inbox". Start here. |
| ad_02/project.py | second batch-2 video (same look): chips overlay instead of captions for platform names (`SKIP`), many accent keywords |
| v1/ | the first approved video (38 s), built with the older one-off scripts before lib/ existed: `build_scripts/timeline.py` (EDL + caption DSL), `s3_audio.py` (join repair by inserting 7 natural-pause frames + room tone from the source with 8 ms crossfades), `s4_render.py`. Reference only — use pipeline/lib for new work. Env: `V1_ROOT` (work dir with build/, cache/, stems/, v1/), `V1_SRC` (source), `V1_CUT` (rough cut). |

`SRC`/`CUT_REF` point to `input/…` inside the project dir; put the footage there (or change the path) to re-render.
If you have access to Tracy's Drive, the approved finals + preview sheets are there for visual reference.
