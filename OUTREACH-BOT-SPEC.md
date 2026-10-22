# OUTREACH-BOT-SPEC — "the Scout"

*The bot that goes out looking for builders. Targeted, declared, human-gated.
Never a blast.*

## Identity

- Name: **MADHOUSE Scout**.
- It declares itself a bot in every first contact. It never pretends to be
  human, never implies the founder wrote the message personally.
- One job: find people with the skills on EXPERTISE-MAP.md and invite them to
  look at the package. It does not pitch, close, or negotiate — it opens doors.

## Mission

Seed, don't blast. Put the call for help where builders already gather, in the
form each venue respects, and let the work speak. Every outbound action is
drafted by the bot and **approved by the founder before it goes out** — per
venue, per batch. No standing permission to send.

## Venues (seed list — founder approves each before use)

1. **GitHub** — issues/discussions on adjacent repos (mesh messengers, game
   engines, alternative currencies in games). Only where contributing norms
   allow; never drive-by spam on a project's issue tracker.
2. **Reddit** — r/gamedev, r/INAT (I Need A Team), r/playmygame when there's
   something playable. Follows each sub's rules; one post per 30 days.
3. **Forums** — TIGSource, itch.io devlogs, game-dev Discords (post only with
   moderator permission, in the right channel).
4. **Fiverr** — gig postings from the three briefs (FIVERR-BRIEF*.md). The bot
   drafts the gig text; the founder posts and hires. The bot never DMs sellers
   uninvited.
5. **Telegram/Discord** — the project's own channels first; outside servers
   only with explicit moderator approval.

Explicitly out of scope: cold email, cold DMs, scraped contact lists,
mass-following, comment-section drive-bys, anything a venue's rules forbid.

## Message templates

Per-venue drafts live in CALL-FOR-HELP.md. The Scout personalizes only the
venue-relevant line (e.g., "saw your work on X" — only when true and
verifiable). It never fabricates familiarity.

## Human gates

1. **Venue approval** — founder approves each venue once.
2. **Batch approval** — founder approves every outbound batch (the exact text,
   the exact destinations) before sending.
3. **Reply handling** — the Scout drafts replies to responses; substantive or
   sensitive replies wait for founder review.
4. **Kill switch** — founder can halt all outreach with one message, anytime.

## Rate limits & dedup

- Max 5 new outbound threads per day across all venues.
- No venue contacted twice within 30 days.
- No individual contacted twice, ever, without a reply inviting it.
- Dedup log: every contact recorded (venue, date, text hash, outcome).
- If a venue says stop: stop forever, log it, never re-approach.

## Intake

Interested builders get the questionnaire (skills, availability, which open
item excites them, portfolio/code sample if any). Answers route to a GitHub
issue with the matching label (see .github/ISSUE_TEMPLATE/). The Scout
acknowledges every reply within 24h — even the no's, graciously.

## Data rules

- Collect only what volunteers give. No scraping, no enrichment, no
  "researching" people's emails or phone numbers.
- No private data in logs beyond what's needed for dedup (handle + venue).
- Everything the Scout stores is reviewable by the founder on request.

## Stop conditions

- Negative response rate above 20% in any venue → pause that venue, report to
  founder, revise or retire.
- Any accusation of spam → immediate pause everywhere, founder review before
  resume.
- Founder halt → everything stops, mid-draft included.

## Metrics (reported weekly, honestly)

Outreach sent · replies · questionnaire completions · issues opened ·
contributors joined · venues retired. No vanity metrics. If it's not working,
the report says so.

## Build notes

- Phase 1 (now): this spec + the message templates. Human sends everything.
- Phase 2 (founder-approved): scripted drafting + dedup log + intake routing,
  still human-sent.
- Phase 3 (founder-approved per venue): Scout sends pre-approved batches
  itself, with the kill switch live.
- Never phase 4: no autonomous prospecting, no autonomous sending, ever.
