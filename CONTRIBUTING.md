# Contributing to MADHOUSE

## The room

MADHOUSE is a meeting engine disguised as a game. Everything here serves one
question: **does this help people meet each other?** If it doesn't, it doesn't
go in — no matter how clever it is.

## The four filters (in order)

1. **Meeting engine** — does it help people meet each other?
2. **Grandparents' question** — does it make money / could it hit a home run?
3. **Twelve-year-old's test** — learnable in one showing?
4. **Wholesomeness test** — Peace Corps meets Boy Scouts. No dark patterns, no
   extraction, no wound-mining, no loot boxes, no pay-to-win, no randomness
   sold as gameplay.

## Ground rules

- **Additive.** Add to history; don't erase it. Where a later decision
  supersedes an earlier one, say so plainly in the same document.
- **Nothing is real until it's real.** Don't claim code, tests, or deployments
  work until they've run in the intended environment. A successful test run is
  not a deployment.
- **Synthetic data only** in development and tests. Never real user data, never
  scraped data.
- **No secrets in commits.** No tokens, keys, credentials, private locations,
  or identifying metadata — in code, screenshots, or logs. Ever.
- **Plain words.** Explain technical work so a non-programmer can follow it.
  The founder reads every word; the code is not his language.
- **Conservation is sacred.** Pool + all Pockets + in-flight balances always
  equals the fixed supply. No minting, no replenishment, no negative balances,
  no action-born issuance. Any change that breaks this is rejected outright.
- **NPCs never mint.** They move existing Dots only — seeded purses, capped
  quest budgets. The moment an NPC prints a Dot, the game's central promise
  is a lie.
- **Admin is aggregate-only.** No feature may expose an individual player's
  pocket, location, or behavior to any admin view.
- **Minors.** No bio publishing, matching, or wish-board contact under 16.
  This is non-negotiable and precedes every feature touching real users.

## How to pick something up

1. Read [HELP-WANTED.md](HELP-WANTED.md). Pick a number.
2. Open an issue saying which number and your smallest first step.
3. Build the smallest first step. Test it. Show it running.
4. Doctrine items (section A) are comment-only — the founder rules on naming
   and monetary policy. Argue well; don't ship unilaterally.

## What "done" looks like

It runs in the intended environment, the tests are green, conservation holds
to the Dot, and all four filters pass. Then it ships.
