# Live server snapshot — 2026-10-19

Exact copies of the files as they ran on the PythonAnywhere server
(`ce56342458.pythonanywhere.com`, `/home/CE56342458/madhouse/`) on 2026-10-19,
downloaded read-only via the Files UI. This directory is the single source of
truth for the live deployment — see `files/pythonanywhere-deploy/SECURITY.md`
section 3 (the 2026-10-19 rule: every deploy goes through git first).

## Contents

| File | Live modified | Notes |
|---|---|---|
| madhouse_bot.py | 2026-10-19 06:29 UTC | Main-chat front page + /wish + /worlds + /map MERGED with the deployment chat's ZORBS onboarding (4 doors, Cosmic Passport). Both tracks intact — verified: FRONT PAGE, wish_cmd, GENEROSITY, door_pick, pp_name all present. |
| app.py | 2026-10-19 06:29 UTC | Deployment chat's dedicated worker-thread design (tg-worker owns one loop + one PTB Application; webhook queues updates, answers 200 instantly). Fixes the "Event loop is closed" freeze. |
| generosity.py | 2026-10-18 22:07 UTC | Identical to main-chat version (Generosity AI, Gemini `gemini-3.8-flash`). |
| passport_render.py | 2026-10-18 22:07 UTC | Identical to main-chat version (face-choice passport renderer). |
| server.py | — | 168 KB, over the push limit — stored as `server-live-2026-10-19.patch` (unified diff against `files/pythonanywhere-deploy/server.py`; 13 diff lines: the /api/join passport-answers extension). Reconstruct: `patch server.py < server-live-2026-10-19.patch`. SHA256 of the full live file in SHA256SUMS.txt. |
| extend_yourself_101.json | 2026-10-18 08:09 | data/ content snapshot |
| student_ways_101.json | 2026-10-18 08:09 | data/ content snapshot |

## Not present on the server's data/ (2026-10-19)

No `ai_worlds.json` (Generosity wish ledger — created on first /wish),
no `faces/` directory (created on first passport photo upload),
no other ledger files in `data/`. The main Dots ledger location is
determined by server.py's data path — verify before assuming.

## Integrity

SHA256SUMS.txt holds hashes of the full live files (including server.py).
