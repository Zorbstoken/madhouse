# FIVERR BRIEF #2 — In-House Game Payment Systems Designer (copy-paste ready)

## Title for the gig posting
Payment systems designer for a game's in-house currency: fixed-supply ledger, gifting & participation economy (no crypto, no tokens, no fiat ramps)

## What the system is (paste this)
MADHOUSE is a meeting engine disguised as a game. Its in-house money is **Dots**: a fixed supply of 1,000,000 units, counted not mined, moved not printed. Players earn Dots by participating (quests), move them by gifting and trading (unique six-character tokens, never by name), and spend them at NPC shops. There is no blockchain, no token sale, no fiat on-ramp, no off-ramp, no exchange rate. Admin sees aggregates only — never individual pockets. The conservation law is absolute: Pool + all Pockets + in-flight balances = 1,000,000, always, exactly. You are designing the *payment system inside the game* — the transference layer — not a cryptocurrency.

## What exists (you'll receive all of this)
- Single-ledger engine (JSON), conservation-tested to the Dot — 614 tests green
- Four movement kinds, all built: grants (Pool→Pocket), gifts (5-Dot ritual + gift queue), trades (token-matched), purchases (Pocket→NPC purse)
- Five NPCs on seeded purses that never mint; fail-closed on empty Pool; overdrafts refused everywhere
- API contract v6 (join/gift/trade/shop/quest/offer/need/wish/matches)
- A comparative architecture study we're proud of: best-of extractions from Roblox (creator loop, no off-ramp), Minecraft (player shops, capped sinks), Libra/Diem (conservation by construction, no fiat ramps), Monero (fungibility, privacy-by-doctrine), Bitcoin Cash (feeless instant P2P, social on the rails), HTTP (payments as native web actions)

## What we need from you
1. **Stress-test the transference layer.** Four movement kinds — is that the right set? What's missing (a plain "send"? NPC-vs-player payment verbs)? Where does it stagnate, where could it leak?
2. **Name things.** The transference layer itself has no name. The full verb set is undeclared. Propose the lexicon — every money-movement gets one clear verb.
3. **Design the gifting program's growth.** The 5-Dot door ritual works for arrival; design gifting as a lifelong mechanic — wish contributions, generosity chains, peer thanks that can never become surveillance.
4. **Design the contribution/participation program's economics.** 202 quests pay from Marlo's visible purse today. Model the purse dynamics at 100, 1,000, and 10,000 players: when does it run dry, what refills it, what breaks?
5. **Player trade stalls.** Design the ambient commerce layer: your shelf, your prices, selling while offline — with capped sinks so it can't hyperinflate.
6. **The anti-farming line.** One account = one 100-Dot grant is trivially farmable. Design the lightest defense that stays invisible to honest players.
7. **Write it as architecture.** Deliverable is a payment-system architecture document: movement taxonomy, conservation proofs, purse dynamics model, verb lexicon, and the ranked gap list — plain words, no jargon.

## Hard constraints (non-negotiable)
- Fixed supply sacred: no minting, no replenishment, no negative balances, NPCs never print
- No fiat on-ramp or off-ramp — nothing to convert, nothing to regulate
- Admin aggregate-only — no feature may expose individual pockets
- No loot boxes, gacha, pay-to-win, or randomness sold as gameplay
- Under-16 gates on anything leading to real contact

## Deliverable
One payment-system architecture document (Markdown): the seven sections above, each with verdict (sound/fix/redesign), fixes as smallest shippable steps, and the lexicon proposed as final. Plus a one-page "why a builder should care" summary.

## Budget & timeline note (edit before posting)
Fixed-price engagement for the architecture document. State your price and turnaround. In-house game currency experience (Roblox, Minecraft economies, virtual-world systems) strongly preferred; crypto background welcome only if you can leave the chain at the door.
