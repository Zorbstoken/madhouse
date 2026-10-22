# The MADHOUSE Payment Architecture — the best of everything, integrated

*What we stole, from whom, and why it fits together. Written so a builder reads
it and says: I want to participate.*

---

## The one-line idea

An in-house payment system for a game — not a token, not a crypto, not a
bank. **Dots**: one fixed supply (1,000,000), counted not mined, moved not
printed, private by doctrine, feeless and instant because it's a ledger entry,
not a blockchain. Every unit equal. Every movement conserved. Nobody watches.

His words for what moves on these rails: *currencies of liquid assets and
luck* — and the skill that matters: *currents and navigational abilities*.

The equation, in his words:

*Send money is send Dots, send Zorbs, send love, and send happiness.*
*Receive same.*

A transfer is never just a transfer. The ledger records Dots; the people
experience love. Both are true at once.

What a balance is, in his words:

*Carry a balance of joy, self-love, and expression, protection, and currency —
in a divine current.*

A Pocket doesn't just hold Dots. It holds the person: their joy, their
self-love, their expression — protected, denominated, and flowing.

> "And every transaction is vibe."
> — dictated 2026-10-17

Framing: the ledger records the movement; the vibe is what moves. Every gift,
every trade, every quest payment is a vibration passing from one holder to
another — which is why the books balance in two columns at once: the Dots,
and the feeling.

> "The currents flow."
> — dictated 2026-10-17

> "The currencies are vast."
> — dictated 2026-10-17

We didn't invent this from nothing. We took the best of six systems and left
their failure modes behind.

---

## 1. From Roblox — the creator loop (without the off-ramp)

**What Roblox got right:** Robux flows *inside* the economy and the people who
make things earn it there. Developers build games, players spend Robux in them,
developers earn Robux and reinvest. The loop is the economy. Our version: Marlo
pays quest rewards from her purse, players spend at Pippa's Mercantile, quest
completions and trade profits recirculate. Earn inside, spend inside, build
inside.

**What we refuse:** DevEx — the fiat off-ramp. The moment play converts to
real money, you get lawsuits, child-safety crises, and volatility pressure.
Roblox's billions came with all three. Our closed loop is the shield: **we
never punch a fiat hole in it.** No on-ramp, no off-ramp, no exchange rate, no
speculation. A Dot is worth what a Dot does.

## 2. From Minecraft — player shops and capped sinks

**What Minecraft servers got right:** player-run shops. Vending blocks that
sell while you're offline — commerce as ambient infrastructure. Our Mercantile
is the seed; player trade stalls are the growth: your shelf, your prices, your
goods, selling while you sleep.

**What we refuse:** the infinite admin buy-order. A server shop that buys
forever is hyperinflation with extra steps. Our NPC purses are **capped and
seeded** — Marlo, Pippa, the Poolkeeper spend existing Dots from fixed purses,
and when a purse runs dry the quest simply waits. Scarcity you can visit.

## 3. From Libra/Diem — conservation by construction (without the regulators)

**What Libra got right:** the Move language's *resource model* — a coin is a
resource that cannot be duplicated or destroyed, only moved. Conservation
enforced by the type system itself. That's our conservation law stated as
code: `Pool + all Pockets + in-flight = 1,000,000`, always, exactly. Libra
also had the right backing instinct: a reserve behind the unit. Ours is phase
two — one real artwork, real custody, the Vault.

> "It can be an old master. It can be an original piece of art that's micro
> terraforming — commerce transformed and trade based."
> — dictated 2026-10-17

Framing: the reserve isn't a vault of gold. It's art that terraforms commerce
at micro scale — an old master or an original, either way a cultural backing,
not a metallic one. The art doesn't sit behind the currency; it reshapes what
trade is. Commerce transformed, trade-based.

> "It's backed up by good intentions — support in humanity's most precious
> moments."
> — dictated 2026-10-17

Framing: the backing is twofold — the art, and the intentions behind it. A
reserve that holds value is finance; a reserve that holds *moments* — births,
weddings, walkouts, the times people show up for each other — is something
else entirely. The currency is backed by what humanity does at its best.

**What we refuse:** everything that got Libra killed. Permissioned validators
(a consortium to subpoena), a fiat reserve basket (a regulator's handle), a
global stablecoin ambition (a congressman's target). Libra died because it
built the on/off-ramps first and asked permission never. We build **no fiat
ramps at all** — there is nothing to regulate because there is nothing to
convert. The closed loop isn't a limitation; it's the armor.

## 4. From Monero — fungibility and "no one's business"

**What Monero got right:** every coin equal. No tainted history, no clean
coins — fungibility as a first principle. And privacy as the default posture:
your money is no one's business. Our doctrine is the same sentence in
game-world language: **admin sees aggregates only, never individual pockets.**
No per-player surveillance, no behavior-derived scores, no ledger anyone can
use to rank or punish. A Dot from a quest and a Dot from a trade are the same
Dot.

**What we refuse:** proof-of-work issuance (we have no mining — supply is
fixed, divided once) and tail emission (we reject replenishment absolutely).
And one honest tension, named: Monero hides everything from everyone; we hide
from *admin* while players are visible *to each other by choice* — opt-in
bios, revocable presence, coarse regions. Privacy from power, visibility among
friends. That's the meeting engine's requirement, and Monero's model bends to
fit it.

## 5. From Bitcoin Cash — cash for the world, social on the rails

**What BCH got right:** payments must be **cheap and instant** — big blocks,
negligible fees, confirmations you don't wait for. Our transfers are ledger
entries: zero fee, immediate, no mempool, no gas. We beat BCH at its own game
by not being a blockchain at all. And memo.cash proved the deeper point:
**social and money belong on the same rails.** Our wish board + Dots is that
idea in game form — wishes published, contributions flowing, chains of
paperclip-to-house trade-ups recorded where everyone can see the generosity.

**What we refuse:** the scaling wars. We don't need 32MB blocks because we
don't need blocks. One JSON ledger, one source of truth, byte-identical
backups. Boring technology, exact conservation.

## 6. From HTTP — the web's forgotten payment hook

**The interpretation** (correct us if you meant otherwise): payments were
always supposed to be native to the web — `402 Payment Required` has been
reserved in the HTTP spec since the beginning and never used. Our API *is*
payments over HTTP: `POST /api/gift`, `POST /api/trade` — a payment as an
ordinary web action, no wallet extension, no chain, no gas. We're building what
402 promised and the web never delivered: money as a first-class web citizen,
inside a game, where it can't hurt anyone.

---

## The four specifics

### A. Architecture of the game
Single-ledger engine (JSON, one source of truth). The Pool: finite, visible,
fail-closed. Pockets: player wallets. Five NPCs on seeded purses (never
minting). Verbs: join, gift, trade (by six-character token, never by name),
buy, quest, offer/need, wish (+contribute/offer/fulfill), matches. Telegram
bot + web front end + Mini Apps. 614 tests green.

The Pool is not a reserve of money. It is a reserve of human potential —
finite in Dots, infinite in what the Dots can recognize. (Mined from the
founder's earlier designs, adapted: the old design said the same of its
vault — "not a reserve of gold, but a reserve of Human Potential.") The
ledger runs on attestation logic, not credit logic: it records flow — what
was given, what was shared, what was witnessed — never debt.

### B. Architecture of the payment system within the game
**Teleport** — the transference layer, named by the founder 2026-10-17:
"funds that arrive before you do." It moves Dots Pocket→Pocket as atomic
ledger entries: instant, feeless, conserved. Every movement is one of four kinds — **grant**
(Pool→Pocket), **gift** (given freely, the 5-Dot ritual), **trade** (swapped by
token), **purchase** (Pocket→NPC purse). No fifth kind exists; no code path
creates Dots. Failed transfers fail closed — the ledger never half-moves.
Admin views aggregates (supply, pool, counts) and can never see a pocket.

### C. The contribution/participation program
**Extend Yourself**: 202 quests (101 general + 101 student). Do a quest →
Marlo pays from her visible purse (3 Dots classic, 5–50 catalog). Publish an
offer or a need → Juno matches you. Complete a trade → peer thanks (received,
never computed). Participation *is* the issuance — but it's allocation from
existing supply, never creation. The reverse pyramid: generosity flows down,
the clan grows wider.

### D. The gifting program
The door ritual: 100 Welcome Dots, pass 5 to the next newcomer with your name
attached — or keep all 100, no judgment. The gift queue carries attributed
gifts to the next arrival. Wish contributions: give Dots toward someone's
wish, watch the chain grow. Gifting is the clan's character made mechanical —
generous, kind-hearted, willing to extend themselves. The system never
requires it; the culture unmistakably rewards it.

### E. Keyless identity (proposed — mined from the founder's earlier designs)
No passwords, no private keys to lose. Your Telegram (later Discord) identity
*is* your account: the platform has already verified you, so the ledger simply
recognizes your social ID and opens your Pocket. Lose your phone, log back in
anywhere, and the game says "welcome back" — your Pocket was never in the
phone. One person may later link several platforms to one Pocket (Telegram +
Discord, same purse). **Status: proposal, not canon.** The founder's trust
ladder question (Zorbian name → vouched handle → verified presence) is still
open, and this proposal must fit whatever he decides. What is NOT proposed:
no scoring, no surveillance, no AI grading anyone — recognition only.

---

## Why it holds together

Six systems, one principle each, zero contradictions:

| System | We take | We refuse |
|---|---|---|
| Roblox | the creator loop — earn inside, spend inside | the fiat off-ramp |
| Minecraft | player shops; capped sinks | infinite admin buy-orders |
| Libra | conservation by construction; reserve backing | fiat ramps (the regulatory kill-shot) |
| Monero | fungibility; "no one's business" | mining issuance; tail emission |
| Bitcoin Cash | feeless instant P2P; social on the rails | the scaling wars |
| HTTP | payments as native web actions (402's promise) | — |

The result: a payment system with the privacy posture of Monero, the speed of
an ideal BCH, the conservation guarantees of Libra's Move, the creator economy
of Roblox, the player commerce of Minecraft — and none of their failure modes,
because there is no chain, no mine, no ramp, and no one watching.

> "Trade and commerce brings wellness and prosperity and wealth for all people
> and life."
> — dictated 2026-10-17

Framing: the thesis the whole architecture serves. Not trade as extraction —
trade as the delivery mechanism for wellness, prosperity, and wealth, for all
people and all life. The closed loop, the fixed supply, the capped purses,
the aggregate-only admin: all of it exists so the exchange can do this one
thing without being captured.

> "Self sufficient distribution sustainability for all."
> — dictated 2026-10-17

Framing: the mechanical corollary. Distribution that needs a distributor is a
chokepoint; distribution that runs itself — quests paying from visible
purses, gifts flowing through the queue, trades matching peer to peer —
can't be captured or switched off. And sustainability *for all*: the fixed
supply means nothing depletes, the capped purses mean nothing hyperinflates,
the closed loop means nothing leaves. The system feeds everyone it touches,
indefinitely.

*Nothing here is claimed as deployed until it runs. The architecture is real;
the players aren't yet. That's why we need you.*
