# MADHOUSE — help us build it

> "Not their wars — fight for our future."

MADHOUSE is a game about **meeting each other**. A student scans a poster, plays silly personality games in a Telegram bot, gets matched with like-minded peers, trades in a fixed-supply Dot economy, buys game goods at Pippa's Mercantile, publishes wishes, and extends themselves to their community through 202 quests. The Dots aren't the point — they're the excuse. The point is young people finding each other as free, sovereign, independent humans.

On **November 20, 2026** — the International Youth Walkout — the packs walk out together.

→ **[MANIFESTO.md](MANIFESTO.md)** — why we're building this, in one page. **[PROJECT-BRIEF.md](PROJECT-BRIEF.md)** — what it is, in thirteen answers. **[CREED.md](CREED.md)** — who we are. **[VALUES.md](VALUES.md)** — what we hold. **[ZORBS.md](ZORBS.md)** — what they are. **[ZORBS-CODEX.md](ZORBS-CODEX.md)** — the full lore. **[THE-1000.md](THE-1000.md)** — the living catalog. **[ZORBS-CODEX.md](ZORBS-CODEX.md)** — the full lore.

**This is a civil-rights, independent-sovereignty game.** No surveillance, no middlemen, no rent-seekers. Admin sees aggregates only — never individual pockets. Fixed supply, never printed. The game fails closed; it never prints.

## We need your help — help help help

The engine is built and tested (614 tests green, conservation exact to the Dot). What's missing is everything that turns it into *a game people play*: walkout mechanics, the pack system, the trust ladder, the living map, the season after November 20. Our October design review said it plainly: *"a beautiful door into an empty room."* We built the door. Help us furnish the room.

→ **[HELP-WANTED.md](HELP-WANTED.md)** — 27 open items, grouped, each with the smallest first step.

→ **[CONTRIBUTOR-REWARDS.md](CONTRIBUTOR-REWARDS.md)** — the deal: contribute, earn Dots. Three tiers, base plus peer-vouched kindling — better work earns more.

## What's real and what isn't

Our standard: *nothing is real until it's real.* We don't claim deployments we haven't run.

**Real:** single-ledger engine · fixed-supply Dot ledger (demo supply: 1,000,000 Dots — the launch supply is set by the founder from the backing artwork, monetary policy, and community contributions) · gift/trade by unique six-character token · five NPCs on seeded purses (Marlo, Pippa, Poolkeeper, Sage Zell, Juno) · Pippa's Mercantile (10 game goods, Dots only) · Extend Yourself (202 quests) with offer/need Exchange · Juno matching with named reasons · wish board · Telegram bot live as @Zorbianbot on an interim test host.

**Not yet real:** no players yet · the permanent production host (an interim test host is live; the move to the production box is planned) · no students or unions contacted · no legal review yet · no native iOS/Android apps (the Telegram path covers phones meanwhile).

## The four filters

Everything built here must pass, in order:

1. **Does this help people meet each other?** If not, it doesn't go in.
2. **The grandparents' question:** does it make money — could it hit a home run?
3. **The twelve-year-old's test:** learnable in one showing?
4. **The wholesomeness test:** Peace Corps meets Boy Scouts. No dark patterns, no extraction, no wound-mining.

## The creed

> Seek sanctuary — be sanctuary. Follow the QR codes, follow the signs, follow the merchants, follow your friends, follow the peer groups, follow yourself.

And the game's deeper frame, now emerging: **be seen and be heard and be free.**

## Start here

- [ARCHITECTURE.md](ARCHITECTURE.md) — how the engine works
- [HELP-WANTED.md](HELP-WANTED.md) — pick something
- [CONTRIBUTOR-REWARDS.md](CONTRIBUTOR-REWARDS.md) — what you earn for it
- [CONTRIBUTING.md](CONTRIBUTING.md) — the rules of the room

---

*Site operations notes below are carried over unchanged from this repo's previous README (October 19) — the front-door pages still run on them.*

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
