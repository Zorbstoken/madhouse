# madhouse
Game - trade - commerce - fun

Public front door for the MADHOUSE game: `https://zorbstoken.github.io/madhouse/`

## What these pages are

- `index.html` — the join door: a parlor-game taste of the MADHOUSE (pick a number, a color, a name).
- `pocket.html` — a demonstration sketch of the game loop: the Pool, Pockets, the Price List, the Donation, conservation.

Both pages are **front door + demo**. The live game — real Dots, real Pockets, trades, quests, matching — runs in Telegram via **@Zorbianbot**, which is the engine's public face. Every "play" path on these pages routes to the bot: `https://t.me/Zorbianbot?start=poster`.

## The QR code

Printed posters carry a QR encoding exactly:

```
https://zorbstoken.github.io/madhouse/
```

**This URL must never change.** Posters are printed; the QR is permanent. Verified by independent decode (OpenCV) — do not alter the Pages custom domain / path without reprinting.

## Cutover: Phase A → Phase B

**Phase A (current, default) — bot-routing mode.**
`ENGINE_API_URL = ''` in both pages' scripts. The pages make no engine calls; the join door's primary call-to-action is the Telegram deep link. This is correct while the engine has no public HTTPS home.

**Phase B — direct engine mode.**
When the engine (server.py) gets a public HTTPS home:
1. Set `ENGINE_API_URL` in `index.html` and `pocket.html` to the engine's base URL, e.g. `https://engine.example.com` (no trailing slash).
2. The pages will call the engine directly (`ENGINE_API_URL + /api/...`). CORS on the engine must allow `https://zorbstoken.github.io` (server.py already defaults `MADHOUSE_CORS_ORIGIN` to it).
3. Keep the bot deep link as the primary CTA regardless — Telegram remains the richest client (Mini App, push, identity).

## House rules for this repo

- Trades resolve by the recipient's **unique 6-character trade token, never by name**. (Token alphabet: `ABCDEFGHJKMNPQRSTUVWXYZ23456789` — no 0/O/1/I/L.)
- Fixed supply: 1,000,000 Dots. Nothing is printed, ever. Pool + Pockets + in-flight = supply.
- Dots-denominated only. No fiat, no on/off-ramps in this repo.
- `.nojekyll` stays — Pages serves these files directly.
