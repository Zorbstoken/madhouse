# MADHOUSE — Architecture

*What exists, plainly. Status: October 2026. Local/demo unless noted.*

## The money

- **Dots** — the counting unit. Fixed supply: **1,000,000**. Never minted,
  never replenished, never borrowed into existence.
- **Zorbs (Spots)** — Dots in painting/universe form. Same supply, different
  face. "Dots you count; Zorbs you receive."
- **Orbs** — separate student reward points, not Dots. Unlimited flow, reverse
  pyramid: share them and you're replenished. Convertibility to Dots: open.
- **The Pool** — the finite, visible source of all grants. Empties → grants
  refuse (fail-closed). Never prints.
- **Pocket** — the player's wallet. "How many Dots in your pocket?"

**Conservation law:** `Pool + all Pockets + in-flight balances = 1,000,000`,
always, exactly. Tested to the Dot across 614 green tests with byte-identical
ledger backup/restore.

## The ledger

One JSON ledger, single source of truth. Every grant, gift, trade, shop
purchase, and quest reward is an entry moving existing Dots — never creating
them. Overdrafts refused everywhere.

## The verbs (API)

| Verb | Endpoint | Moves Dots |
|---|---|---|
| join | `POST /api/join` | Pool → Pocket (100 welcome) |
| gift | `POST /api/gift` | Pocket → gift queue → next newcomer (5-Dot ritual) |
| trade | `POST /api/trade` | Pocket → Pocket by six-character token (never by name) |
| buy | `POST /api/shop/buy` | Pocket → Pippa's purse (game goods, 5–500 Dots) |
| quest | `POST /api/npc/quest` | Marlo's purse → Pocket (3 Dots classic; 5–50 catalog) |
| offer/need | `POST /api/offer`, `POST /api/need` | no Dots — publishes to the Exchange (16+) |
| wish | `POST /api/wish` (+ contribute/offer/fulfill) | Pocket → wish chains (16+) |
| matches | `GET /api/exchange/matches` | no Dots — Juno's offer↔need matching with named reasons |

## The NPCs (all on seeded purses — existing Dots only, never minted)

- **Marlo** — quest-giver. 202 Extend-Yourself quests; rewards from her purse.
- **Pippa Pricelist** — shopkeeper. Pippa's Mercantile: 10 game goods.
- **Poolkeeper** — the Pool's face. Visible scarcity.
- **Sage Zell** — lore.
- **Juno** — matchmaker. Offers↔needs, interests, tempos; every match names
  *why*, with the discernment warning.

## The bot

`@Zorbianbot` — verified with Telegram; commands configured October 15
(`/join /pocket /prices /rules /safety /whoami /cancel /notforme`).
`/extend /shop /wish` are built and tested as engine verbs (see table above)
but are NOT yet configured as Telegram commands — they ship with the hosted
runtime. Runtime not yet hosted.

## The front end

- Join page → Pocket page (standalone demo) + Telegram Mini Apps
  (`mercantile.html`, `extend.html`). `ENGINE_API_URL` reserved for the HTTPS
  cutover.

## What runs where

Today: everything local. Next: one always-on host (MacBook), Cloudflare
tunnel, `configure_bot.py` rerun, first-light verification — join, Pocket,
six-character trade token, shop, quests, conservation.

## Test counts (all green, 2026-10-16)

engine 303 · shop 64 · matching 90 · tg_join 23 · matching_bot 134 ·
bot_client all-pass · zorbs_journey all-pass.
