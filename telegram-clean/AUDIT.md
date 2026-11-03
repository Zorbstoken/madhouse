# Audit — Telegram front-end, 3 November 2026

Checked by hand and by live page fetch on 3 Nov 2026, about 11:08–11:10 UTC
(14:08–14:10 Kaş time). A claim below says LIVE only if it was fetched
in that window. Anything else is labelled REPORTED or NOT VERIFIED.

## LIVE — verified in this window

- `https://ce56342458.pythonanywhere.com/health` → `{"ok": true}`.
- `https://ce56342458.pythonanywhere.com/webapp/` → MADHOUSE Play.
  Tiles: Play, Living Map, Quests, Pippa's Mercantile, Extend Yourself,
  Talk to the AI. Pocket / keepers / Pool load by JavaScript after the
  page opens, and need Telegram initData for a real Pocket. Without it
  the page shows its door note. Bottom tabs are Play / Map / Quests /
  Shop — Extend Yourself has a tile but no bottom tab.
- `https://ce56342458.pythonanywhere.com/telegram-page` → Next Entry v3,
  Alpha Two, LIVE. 507 lines in text fetch. Sections: colour board,
  skins, Auto Mode, voice-over (browser text-to-speech placeholder),
  Play → Pictures → Story → Three Questions → Town Hall → Why Not You,
  boxes, conscription, Off the Rails, Consul / wealthy, 36 projects /
  77 things / 100 additional, worlds, AI, Atlantis 12, BOYGODS, creature
  buttons, 18 bot commands, Original Alpha beside New Work, Crisis News
  Feed (holding page, no checked items yet), Free Ports, Young Free
  Ports, Living Nodes Map, participants-not-tracked, Consul Form,
  Currents, Kindness Currents (starter list only), World of Streams,
  Alpha Two, Moving Symphony, Crisis News Stream (first verified run
  pending), Living Nodes Map, Management Outline, Crisis Management
  Report. Counted in the workspace copy of v3: 243 buttons, 35 h2
  sections, 2 links. It is a long scrolling everything-page, not a
  dashboard. It has NO dedicated Dashboard page, NO Compass page,
  NO Control Panel page and NO Site Map page.
- `https://ce56342458.pythonanywhere.com/living-nodes-map.html` → Living
  Nodes Map, Moving Globe. LIVE in this window, even though the file
  is missing from the workspace copy of the deploy bundle. The live
  server and the workspace copy diverge — see below.
- `https://ce56342458.pythonanywhere.com/games` → Games, Tic Tac Toe.
  Text fetch shows the trading-floor framing and a Back link only;
  the game itself is JavaScript.
- `https://ce56342458.pythonanywhere.com/ui-design-tree` → UI Design
  Tree, 13 branches, phone-first, tap not type, sticky menu
  Home | Play | Map | Town Hall | Help.
- `https://zorbstoken.github.io/madhouse/` → front-door join door.
  LIVE. It routes to `https://t.me/Zorbianbot?start=poster`, which lands
  in the OLD bot's registration conversation, not in a dashboard.

## DEAD — verified in this window

- `https://muse.ai/s/the-living-map-fd6tyxlsxlxhx0xd` → "Shared link
  unavailable. This page is no longer shared." This URL is hard-coded
  in the old bot as `LIVING_MAP_URL` (madhouse_bot.py, line 1748) and
  is the target of the old bot's 🌐 Living Map button. Tapping Living
  Map in the old bot is a dead end. This link is removed in the clean
  package and replaced by the built-in Map page.

## NOT VERIFIED — do not treat as live or dead

- `mysterium-consul.jpg` on the live telegram-page. The workspace copy
  of the deploy bundle does not contain it, and a text fetch cannot
  prove whether the live server serves the image. In the clean package
  there are no image files at all, so there is no broken-image risk.
- The old Xiorbs bot /start flow (old welcome and pocket flow). This
  was reported on 3 Nov, it was NOT re-tested in this audit window,
  and it is not in the clean package either way.

## DUPLICATES — the layering that blocks one tap

- Five doors, none of them a dashboard: (1) old /start conversation,
  (2) /play command → WebApp button → /webapp/, (3) telegram-page
  PLAY NOW → scroll, (4) GitHub Pages front-door join door →
  @Zorbianbot?start=poster, (5) old pocket simulation in
  madhouse-frontdoor/pages/pocket.html (local simulation, not the
  live engine).
- Three maps: /webapp/map.html (engine sky, needs engine + initData),
  living-nodes-map.html (sample globe), and the dead muse.ai map.
- Four telegram-page versions in the workspace: telegram-page.html,
  telegram-page-v2.html, telegram-page-v3.html (backups/2026-11-03)
  and telegram-page-v5.html plus next-entry-redesign-draft/index.html.
  The file title in the workspace copy says "DRAFT, NOT LIVE" while
  the live page says "LIVE". Same content, diverging labels.
- Command sprawl in the old bot: about 50 handlers, including pocket,
  play, token, whoami, prices, rules, safety, gift, npcs, quest,
  giftcard, teleport, passport, claim, wish/worlds, map, redeem, talk,
  buy, sell, shop, donate, pool, lore, match, bio, session, need,
  offer, simon, done, tag, vote, board, chains, notforme, plus the
  Zorbs journey and matching journey handlers. The telegram-page
  lists 18 of them as "live commands". A newcomer must hunt commands.
- Workspace vs live server diverge: living-nodes-map.html, games and
  ui-design-tree exist on the live server but are not in the workspace
  deploy copy. The workspace copy is therefore NOT a faithful snapshot
  of live. The clean package is built from the workspace copies that
  could be read, plus the live pages fetched above, and it does not
  pretend to be a copy of the live server.

## BLOCKERS — why one tap did not work before

1. No menu button is set in the old bot code. No `set_chat_menu_button`
   and no `set_my_commands` were found in madhouse_bot.py. Opening the
   bot does not offer a Dashboard.
2. /start is a registration conversation: pick a number, a colour, a
   name, a time. Returning players get only HOME_TEXT plus a
   4-button keyboard: Wish a world, My worlds, Living Map (dead link),
   Passport. No Dashboard button.
3. /play is a command the user must know and type, then tap a WebApp
   button. That is two steps plus command hunting, not one tap.
4. The telegram-page bottom menu (Home, Play, Town hall, Help,
   Support) mostly plays a sound on tap. Only Home shows a section.
   Play, Town hall, Help and Support in that menu do not navigate.
5. The old webapp Pocket needs the engine and Telegram initData. If
   the engine is down, the bot fails closed to an "engine down"
   message. The front-end cannot open cleanly without the engine.
6. The old bot is layered by design: "integrated, NOT overridden",
   "nothing lost, nothing removed". Every layer stayed, so the entry
   got longer instead of cleaner.
7. A fresh bot token does not exist yet in this task. It can only be
   created by the user on his phone in @BotFather. Until then no menu
   button and no webhook can be set for a fresh bot. This is the
   single remaining step, and it is user-only.

## What the clean package does about each blocker

1. bot.py sets the menu button to the WebApp in post_init, and sets
   only three commands: start, dashboard, help.
2. /start sends one message with one button: Open Dashboard. No
   registration conversation.
3. No /play command to hunt. The menu button and the /start button
   are the same one tap.
4. Every bottom-menu link in the clean package navigates to a real
   page, checked by check_links.py. No sound-only menu buttons.
5. The clean Dashboard works without an engine and says so. Live
   Dots are not simulated and not shown until a host is connected.
6. Old layers are removed, with the removal and its replacement
   listed on the Site Map page, not hidden.
7. The fresh-bot step is stated in README.md and VERIFY.md, with no
   token asked for in chat and no reset triggered.
