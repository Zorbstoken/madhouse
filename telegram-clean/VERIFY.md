# Verify — before anyone calls this live

## 1. Static check (done before push, repeat after any edit)

Run, from inside the telegram-clean folder:

```
python3 check_links.py
```

Pass means: all pages parse, every internal link exists, no banned
link (dead muse.ai map, old @Zorbianbot, other github.io pages),
bottom nav complete on every page, bot.py compiles, old commands
absent. If it fails, the package is not ready. Fix it, do not claim
around it.

Also run, by hand, three times, as ordered:

- Open index.html, compass.html, control.html, sitemap.html,
  games.html, map.html, townhall.html, help.html in a phone-width
  browser. Tap every tile and every bottom-menu link.
- Play Tic Tac Toe to a win and to a draw. Play Simon to a correct
  sequence and to a wrong tap. Change a skin, change a world, turn
  sound off and on, change text size.
- On the Map, search a city, zoom in and out, pause and resume rotate.
  Confirm the sample-node warning is visible.

## 2. GitHub Pages check (after push, before bot testing)

Open, in a browser:

```
https://zorbstoken.github.io/madhouse/telegram-clean/
```

Pass means: the Dashboard loads, with the bottom menu Dashboard |
Compass | Control | Site Map | Games | Map, and every page in the
Site Map loads from that same Pages path. If Pages has not published
yet, or any page 404s, the bot step below must wait. The Pages URL
is not "live" until this check passes.

Also confirm the poster QR is unchanged:

```
https://zorbstoken.github.io/madhouse/
```

It must still load the old front-door join page. If it does not,
stop: the push touched the repo root, and that must be undone.

## 3. Fresh-bot one-tap check (in Telegram, on the phone, user only)

Prerequisite: a NEW bot created in @BotFather by the user, token set
in the host environment only, bot.py running in polling mode.

- Open the NEW bot in Telegram. Do not type a command first.
- Tap the menu button. The Dashboard must open inside Telegram.
- If there is no menu button, tap /start, then tap Open Dashboard.
  The Dashboard must open inside Telegram.
- Tap, in order, with no typing: Dashboard → Compass → Control →
  Site Map → Games → Map. Then Town Hall and Help from the Dashboard.
- Play one Tic Tac Toe game. Play one Simon round. Change a skin.
- Confirm: no registration questions, no number / colour / name
  flow, no pocket flow, no command list, no dead link, no button
  that only plays a sound.

Pass is all of the above, in the Telegram client, on the phone.
A browser test alone is not a pass. A claim from the server side
alone is not a pass.

## 4. What is NOT verified by this package

- The new bot is not verified until step 3 passes. Until then it is
  "ready to load", not "live".
- Live Dots, Pockets, trades and live players are not verified by
  this package at all. They need an engine host, which is a separate
  step, with its own verification.
- The old @Zorbianbot is not verified here, and is not changed here.
  Its live status on 3 Nov is in AUDIT.md, for the window checked.
