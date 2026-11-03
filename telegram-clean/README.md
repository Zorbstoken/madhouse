# MADHOUSE Telegram Clean — one Dashboard, one tap

A clean rebuild of the Telegram front-end, from what already exists.
Not a report. Not a new layer on the old bot. A package ready to load
into a FRESH bot.

**This package does NOT touch the live @Zorbianbot. It does NOT claim
the new bot is live. The new bot is not live until the single step at
the bottom of this file is done, by the user, on his phone.**

## What is in here, in order

1. **Dashboard** — `index.html`. Home. Welcome, one-tap tiles, honest
   engine status. No Pocket number is shown, because no engine is
   connected to this package yet. No fake live numbers.
2. **Compass** — `compass.html`. The journey in order: Welcome → Play
   → Pictures → Story → Three Questions → Town Hall → Why Not You →
   Map → Pinboard → Prep → Ready → Meet / Make / Help / Play / Explore.
   Story, Currents, Free Ports and Why Not You are short cards here.
3. **Control Panel** — `control.html`. Skin changer (6 skins), world
   changer (10 worlds), sound on/off (WebAudio beep, not music),
   text size, safety in plain words. Every control works on the page.
4. **Site Map** — `sitemap.html`. Every page, plus what was removed
   on purpose and what replaced it, plus what is not built yet.
5. **Games** — `games.html`. Tic Tac Toe with win/draw detection,
   and Simon Says with a real sequence check. Seven further games are
   listed as queued, with no fake playable button.
6. **Map** — `map.html`. Living Nodes Map, moving globe, search,
   zoom, rotate. Nodes are SAMPLES, city-level only, not tracked,
   no GPS. The old engine sky map is not in here; it needs an engine
   host, and is listed as a future second map.
7. **Town Hall** — `townhall.html`. Three Questions and Meet / Make /
   Help / Play / Explore, each showing its answer on the page.
   Nothing is sent anywhere. No live room is faked.
8. **Help** — `help.html`. How to open the Dashboard, what is here
   and what is not, safety in plain words.
9. **bot.py** — the fresh-bot code. Three commands only: start,
   dashboard, help. One button: Open Dashboard. Menu button set to
   the WebApp. Any other text gets the same button. No registration
   conversation, no pocket flow, no command hunting, no engine call.
10. **check_links.py** — the checker. Every internal link must exist,
    no banned links (dead muse.ai map, old @Zorbianbot, other
    github.io pages), bottom nav complete on every page, bot.py must
    compile, old commands must be absent.

Shared files: `styles.css` (phone-first, 19px base, big buttons,
sticky bottom menu), `app.js` (Telegram WebApp expand, skins/worlds,
sound, haptic — all local, no tracking).

## What is ready to load

- The 8 pages + 2 shared files: ready to serve as static files.
  Intended public URL, once GitHub Pages publishes this folder:
  `https://zorbstoken.github.io/madhouse/telegram-clean/`
  That URL is NOT verified live until Pages publishes it. See VERIFY.
- `bot.py`: ready to run, once a fresh bot token exists. It needs
  only `python-telegram-bot` (see requirements.txt). Polling mode is
  the first-load test; webhook mode is optional, see below.

## What is NOT ready, honestly

- Live Dots, Pockets, trades, live players: NOT in this package.
  They need a game-engine host connected to this front-end.
- Generosity AI chat: NOT in this package. No AI button pretends
  to answer.
- Real music, recorded voice-over, Pinboard, 7 further games,
  live engine sky map, crisis news feed: NOT in this package.
  Each is listed on the Site Map page, not hidden, not faked.
- The fresh bot itself: NOT live. See the single remaining step.

## The single remaining step — user only, on his phone

1. In Telegram, open @BotFather, create a NEW bot (not @Zorbianbot),
   and copy its token. Do NOT paste the token in any chat, and do
   NOT send it to any assistant. Keep it on the phone / host only.
2. On the host that will run bot.py, set in the environment only:
   `TELEGRAM_BOT_TOKEN=<the new token>`
   `WEBAPP_URL=https://zorbstoken.github.io/madhouse/telegram-clean/`
   Leave WEBHOOK_URL empty for the first test, so bot.py polls.
3. Run: `python3 bot.py`
4. Verify with VERIFY.md, in the Telegram client itself, on the phone:
   open the new bot, tap the menu button (or Open Dashboard), and
   check Dashboard, Compass, Control, Site Map, Games and Map, in
   that order, with no typing.

## Optional webhook mode, after the polling test passes

Set `WEBHOOK_URL` to the public https base of the host, and
`WEBHOOK_SECRET` to a long random string, then run bot.py again.
Telegram will call `WEBHOOK_URL/tg-webhook` and must present that
secret. Do not use webhook mode until the polling test passes.

## Old bot — untouched

@Zorbianbot, its webhook, its engine host and its telegram-page are
NOT changed by this package. This package lives in its own folder
(`telegram-clean/`) in the madhouse repo, so the poster QR
(`https://zorbstoken.github.io/madhouse/`) and the repo root pages
are unchanged.

## Sources reused, not thrown away blindly

- UI Design Tree (next-entry-redesign-draft/ui-design-tree.html):
  bottom menu, Dashboard definition, 13-branch journey.
- Games draft (games.html): Tic Tac Toe and Simon meanings, rebuilt
  here with win/draw and sequence checks.
- Living Nodes Map draft (living-nodes-map.html): sample globe,
  city-level, not tracked, World of Streams adaptation, no tokenomics.
- Telegram page v3 words, in short form only: story, currents,
  kindness currents starter, free ports, young free ports, crisis
  framing. The 243-button page itself is NOT reused as an entry.
- Old webapp (pythonanywhere-deploy/webapp/): Play / Map / Quests /
  Shop structure, NOT its engine coupling. Its Pocket, trades and
  keepers return only with an engine host.
- Old bot (madhouse_bot.py): the lesson of what blocks one tap —
  see AUDIT.md — NOT its conversation flow or its command list.
