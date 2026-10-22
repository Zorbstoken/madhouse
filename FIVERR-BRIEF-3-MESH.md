# FIVERR BRIEF #3 — Mesh + P2P Networking Expert (copy-paste ready)

## Title for the gig posting
Mesh networking expert (BLE) + P2P: advise and harden the transport layer of a sovereignty-first messenger game

## What the project is (paste this)
MADHOUSE/Tapestry is a meeting engine disguised as a game, built on a simple
thesis: phones should talk to phones without carriers, and young people should
meet each other without surveillance. The transport layer is a Bluetooth mesh
messenger (forked from BitChat — iOS public domain, Android MIT): BLE discovery
and relay, store-and-forward, panic mode, Nostr fallback. On top of it we're
building the purse (an in-house fixed-supply Dot economy), NFC tap + QR
whispers, a dust layer, and key-ceremony UX. The game layer (Telegram bot,
matching, quests, shop) already runs; the mesh is how players find each other
in the physical world — no coordinates, no location tracking, no database to
seize.

## What exists (you'll receive all of this)
- **bitchat-ios fork** (public domain): BLE transport, discovery, relay,
  store-and-forward, panic mode, Nostr fallback — kept as-is
- **bitchat-android fork** (MIT): 40 Kotlin errors across 9 files repaired
  locally (CameraX, audio-buffer/vibrator APIs, Bluetooth scan constants,
  osmdroid offline provider rebuilt) — direct compiler check clean; needs a
  real Gradle build on a normal machine plus two-device physical Mesh Lab
  validation before any release
- **Fork map** (keep / add / leave alone): keep transport, discovery, relay,
  store-and-forward, panic, Nostr — add the purse, packet layer port, NFC tap
  + QR whispers, dust layer, key-ceremony UX — leave routing and crypto alone
- **Distribution doctrine**: sideloaded APKs and direct download are the real
  path (India ordered bitchat off both app stores Oct 2026 — we don't depend
  on stores)

## What we need from you
1. **Review the fork map.** Is the keep/add/leave-alone split right? What did
   we miss?
2. **Harden the transport.** BLE mesh at real-world density: relay storms,
   battery cost, discovery latency, store-and-forward sizing. Name the
   breaking points before our Mesh Lab finds them.
3. **Design the purse's ride on the mesh.** Dots move as ledger entries on the
   server today; design how purse state syncs phone-to-phone over BLE —
   conflict resolution, double-spend resistance without a chain, what happens
   when two phones disagree.
4. **P2P beyond BLE.** NAT traversal, DHT for peer discovery where
   infrastructure exists, Nostr fallback review. Offline-first, always.
5. **The proximity handshake.** "Phones see nearby phones" with per-encounter
   consent — design it on paper before anyone codes it. No coordinates, no
   tracking, revocable.
6. **Write it down.** Deliverable: a transport architecture review — verdicts
   (sound/fix/redesign) per subsystem, fixes as smallest shippable steps, and
   the Mesh Lab test plan (two physical devices, what to measure).

## Hard constraints (non-negotiable)
- No location tracking, no coordinate storage, no central database of who met whom
- Admin aggregate-only extends to the mesh: no feature may report encounters upstream
- Mesh/transfer changes require physical two-device validation — no simulator-only sign-off
- No raw logs, device metadata, or identifiers in any commit or report

## Deliverable
One transport architecture review (Markdown) + the Mesh Lab test plan. Plain
words, no jargon — the founder reads every word.

## Budget & timeline note (edit before posting)
Fixed-price engagement. State your price and turnaround. BLE mesh + P2P
(libp2p or equivalent) experience required; BitChat familiarity a strong plus;
privacy-tooling background welcome.
