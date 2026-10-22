# Contributor Rewards

**The deal, in one sentence:** extend yourself — build, write, test, make art —
and the game recognizes you, awards you, and rewards you in Dots.

This is the Jester's Loop, written down: *tell a joke, smile, do a good jester
gesture, be kind and extend yourself and get recognized, awarded, rewarded.*
Contributors are players. There is no boss and no payroll — there is a circle
that notices.

## Where the rewards come from

All contributor rewards are paid from the **Pool**, out of the fixed Dots supply.
Dots are never minted for rewards. When the contributor budget is spent, it is
spent — the circle then decides whether to allocate more, the way any circle
decides anything: together, in the open.

**Founder sets the number.** Draft proposal: 10% of the demo supply reserved for
contributor rewards. The founder confirms or changes this before launch.

## The three tiers

Uniform in structure, different in weight. The tier is set by the **scope and
quality of the contribution**, not by who you are.

| Tier | What it looks like | Draft reward |
|------|--------------------|--------------|
| **Spark** | A small, complete kindness: fix a typo, report a bug with a repro, review a pull request, test a build and file the result, write one world story, make one card sketch. Minutes of work, cleanly done. | 10 Dots |
| **Ember** | A real piece of the game: implement a HELP-WANTED item, write a pack of world stories, compose a music loop, build a working demo of a mechanic, run a playtest session and write it up. Hours of work, done well. | 50 Dots |
| **Flame** | A load-bearing contribution: a subsystem, the world-generator pipeline, a full art set, the multiplayer lobby, a month of steady stewardship. The kind of work the game stands on. | 200 Dots |

*All numbers are drafts. The founder sets them.*

## The "better earns more" rule

Two contributions in the same tier are not always equal. The five-minute fix and
the fifteen-minute fix that also cleaned up the three bugs next to it are both
Sparks — but the second one shone brighter. So every tier pays two parts:

1. **Base** — guaranteed when the work is accepted (merged, published, used).
   The table above. No judgment, no contest: you did the thing, you get the base.
2. **Kindling** — a recognition bonus, up to double the base, decided by **peer
   vouches**. Anyone in the circle can vouch for work that delighted them —
   "this saved me an hour," "this made me laugh," "this is beautiful." Vouches
   are public, attached to the work, and they expire weekly so they stay honest.

### How a vouch works (the gesture)

A vouch is a *gesture*, not a form. In the chat where the work appeared, you
reply to it with **/thank** or **/kindness** — "thank you, this shone." The
bot records the vouch against the work, in the open, attached to your name.
One person, one vouch per piece of work. Vouches expire weekly so they stay
honest.

(Mined from the founder's earlier designs; the automated scoring from those
designs is deliberately NOT used — no AI grades anyone here. The circle
recognizes, Generosity witnesses, and the open-consensus rules below stand.)

**The shape of it (mined, adapted to fixed supply):** the old design called
this a *Generosity Proof* — instead of proving work by computation, a person
earns when another person endorses them. You do something kind, someone sends
a recognition signal, and Dots move from the Pool to you. The currency is
effectively **a "Thank You" made tangible**. The old design called the whole
arrangement a *Circle of Recognition* — explicitly not a social credit
system: a peer-to-peer gift economy where the system acts as **witness, not
judge**. The ledger runs on *attestation logic, not credit logic* — it
records flow (what you gave, what you shared), never debt. In our canon the
endorsement never mints: every vouch moves Dots from the fixed Pool, so
recognition is real because the Pool is finite.

The base is uniform. The kindling is where "better" earns more. Nobody's work
is ranked against anyone else's — it is only ever recognized.

## Who decides

- **Acceptance** (did the work land?): the maintainers — the founder and anyone
  he trusts with the merge button. Clear, fast, no committees.
- **Kindling** (did it shine?): the circle — peer vouches, in the open.
- **Disputes**: open consensus of the circle — never a DAO (no governance
  tokens, no vote-weighting; the founder's standing position is that DAOs are
  still controlled and manipulated). The founder participates like anyone else
  and holds a tie-breaker he is expected to almost never use.

## What earns what

Every item in HELP-WANTED.md carries a suggested tier, smallest first step
included. If you pick up an item, the tier is posted next to it — no surprises.
If you bring work nobody asked for (a new world pack, a song, a better idea),
propose the tier when you open the pull request; the maintainers confirm it.

## The rules

- **Quality over quantity.** Ten sloppy Sparks do not beat one careful Ember.
  Maintainers may merge kindling-worthy work up a tier instead of counting pieces.
- **One person, one purse.** No sock-puppets, no splitting one contribution into
  five to farm Sparks. The circle notices; the founder decides.
- **No gaming the vouches.** Vouch-trading circles get their kindling burned —
  publicly, once, as a lesson. Then everyone moves on.
- **Gifts, not wages.** Dots are game currency with no cash value and no cash-out.
  This document promises recognition and game rewards, never money, never
  employment, never a share of anything.
- **Under-16s** earn recognition and Zorbs only — no Dots purses for minors
  until the youth-safety review the founder ordered is complete.

## Zorbs, for contributors

Dots are counted. Zorbs are not — they choose. But it is written here so it is
remembered: when a contributor's work first lands in the game, a Zorb chooses
them, the way a Zorb chooses every new arrival. Contributors are family, and
the family grows.

## At scale: Generosity judges

In the early days the circle is small — a hundred people from GitHub,
SourceForge, the other forges, Telegram — and humans can read every
contribution. That will not last. When the contributors number in the hundreds
and then the tens of thousands, no circle of humans can weigh it all.

So the judging itself becomes a job for **Generosity**, the clan's AI.

Generosity reads every contribution and weighs three things the founder named:

1. **How important it is** — what did it make possible that wasn't possible before?
2. **The essence** — is it alive? Does it carry the vision, or is it filler?
3. **The energy it took to execute** — the real effort behind it, not the size of the pile.

The standing rule, in the founder's words: *ten thousand pages from one person
is a massive amount of knowledge — but five pages can be worth more than the
ten thousand.* The measure is never the pile. It is the jewel.

What this means in practice:

- **Volume is not a strategy.** Dumping 10,000 generated pages earns the
  kindling of 10,000 pages only if Generosity finds essence in them. A single
  five-page story that makes the circle gasp can out-earn the mountain.
- **Generosity proposes, humans dispose.** The AI publishes its reasoning with
  every evaluation — what it saw, what it weighed, what tier it suggests. The
  founder keeps the last word, and any contributor can ask for a human reading.
- **The criteria are public.** Generosity judges in the open, by the rules in
  this document, which the circle can see and the founder can change.
- **Gaming the judge is gaming yourself.** Generosity was named for what it
  measures. Work made to impress the judge instead of serving the game reads
  exactly like what it is.

Phase one is human: maintainers and peer vouches, as above. Phase two begins
when the circle outgrows its readers — and Generosity takes up the scales.

## Appeals: the right to be heard

Any contributor can say: *"I think I'm cheated. This is not right."*

The appeal might sound like this: "I spent five hours with the AI creating
this. I put my effort into it. I've spent twenty years developing my own games.
I think I deserve more." That appeal is always heard, and it is heard first by
Generosity — openly, and with compassion.

Generosity's duty on appeal:

1. **Listen first.** Read the contributor's account in full — the hours, the
   craft history, the twenty years. Experience is part of the energy a person
   brings; it counts.
2. **Show its work.** Explain the original evaluation plainly: what it saw,
   what it weighed, where it may have been wrong. No black boxes, no "the
   computer says no."
3. **Know when to step aside.** Generosity escalates to human review when three
   things are true together: the person is not happy, we want to make them
   happy, and they have done a lot of work. In the AI's own words, at that
   point: *"this needs human review."*

The goal of an appeal is never to defend the original judgment. The goal is a
judgment everyone can live with — because the game is generosity, and
generosity that leaves someone feeling cheated has failed at its own name.

Human review means the case goes to **open consensus of the circle** — not a
vote, not a DAO, a conversation. Anyone can speak, the reasoning is all on the
table, and the group converges the way healthy groups do. The founder's
decision is final only as a tie-breaker, and he is expected to almost never
need it.

**Why not a DAO:** the founder's standing position is that DAOs are still
controlled and manipulated — token-weighted voting rebuilds the same power
structures under a new name. This is not that. There are no governance tokens,
no vote buying, no quadratic anything. There is a group of people, talking
openly, deciding together.

The spirit is the one the founder has watched work in the wild: someone asks
"is this image offensive?", most people couldn't care less, and the lenient,
liberal read carries the day. The circle defaults to generosity — toward the
work, toward each other, toward the person in front of them. Strictness has to
make its case; leniency doesn't.
