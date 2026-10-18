#!/usr/bin/env python3
"""
Generosity — the clan's AI co-creator (v1, deterministic).

The in-Telegram AI that creates and co-creates worlds on demand.
Doctrine: the participant brings the wish, Generosity brings inferences
and interpretations, the world belongs to both. Symbiotic.

v1 is DETERMINISTIC and honest: no model key is required. A seeded,
rules-based interpreter turns a wish into a world; when GENEROSITY_API_KEY
is set, an OpenAI-compatible chat-completions call does the interpreting
through the exact same interface — the model is swappable, nothing
rewrites (borrow-don't-build at the code level).

Canon: canon/01-doctrine.md .. 06-voice.md (his words).
Worlds move ZERO Dots. The Dot ledger is never touched by a wish.

Env:
  GENEROSITY_API_KEY    model key; absent -> rules-based path, never a crash
  GENEROSITY_API_BASE   OpenAI-compatible base URL
                        (default: Gemini's OpenAI-compatible endpoint)
  GENEROSITY_MODEL      model name (default: gemini-2.5-flash)
  GENEROSITY_LEDGER     ledger.json path (default: ../pythonanywhere-deploy/ledger.json)
  GENEROSITY_CANON      canon dir (default: ./canon)
"""
import hashlib
import json
import os
import re
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CANON_DIR = os.environ.get("GENEROSITY_CANON", os.path.join(HERE, "canon"))
LEDGER_PATH = os.environ.get(
    "GENEROSITY_LEDGER",
    os.path.join(HERE, "..", "pythonanywhere-deploy", "ledger.json"),
)
API_KEY = os.environ.get("GENEROSITY_API_KEY", "")
API_BASE = os.environ.get(
    "GENEROSITY_API_BASE", "https://generativelanguage.googleapis.com/v1beta/openai"
)
MODEL = os.environ.get("GENEROSITY_MODEL", "gemini-2.5-flash")

# --------------------------------------------------------------------------
# The loading — canon knowledge pack
# --------------------------------------------------------------------------

def load_canon(canon_dir=CANON_DIR):
    """Load every canon/*.md into {stem: text}. His words, verbatim."""
    pack = {}
    for fname in sorted(os.listdir(canon_dir)):
        if fname.endswith(".md"):
            with open(os.path.join(canon_dir, fname), encoding="utf-8") as f:
                pack[os.path.splitext(fname)[0]] = f.read()
    return pack


# --------------------------------------------------------------------------
# Lexicon guard — banned language never leaves the building
# --------------------------------------------------------------------------

BANNED = [
    "demiurge", "demiurges",
    "rule your universe", "ruling your", "rulers of",
    "nft", "nfts", "blockchain", "crypto", "cryptocurrency",
    "mint", "minted", "minting",
    "investment return", "earnings", "guaranteed return", "passive income",
    "pre-sale", "presale", "ipo",
    "surveillance", "tracked you", "scored you",
]

_BANNED_RE = re.compile(
    r"(?i)\b(" + "|".join(re.escape(b) for b in BANNED) + r")\b"
)


def assert_clean(text):
    """Raise ValueError if banned language appears. Every emission passes."""
    m = _BANNED_RE.search(text or "")
    if m:
        raise ValueError("banned language in AI output: %r" % m.group(0))
    return text


# --------------------------------------------------------------------------
# Seeded RNG — ported from server.py _seeded_rand (mulberry32-style).
# Same seed -> same sequence, byte-stable across runs and machines.
# --------------------------------------------------------------------------

def _seeded_rand(seed):
    a = seed & 0xFFFFFFFF

    def rand():
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = a
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t = ((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF
        t ^= (t >> 14)
        return t / 4294967296.0

    def ri(lo, hi):
        return lo + int(rand() * (hi - lo + 1))

    def pick(seq):
        return seq[int(rand() * len(seq))]

    def pick_weighted(pairs):
        # pairs: [(weight, value), ...]
        total = sum(w for w, _ in pairs)
        r = rand() * total
        for w, v in pairs:
            r -= w
            if r <= 0:
                return v
        return pairs[-1][1]

    return rand, ri, pick, pick_weighted


def _wish_seed(wish_text):
    """Stable seed from the wish itself (sha256, not hash())."""
    return int(hashlib.sha256(wish_text.strip().lower().encode()).hexdigest()[:8], 16)


# World names + inhabitant seeds: ported from server.py _WORLD_NAMES /
# _WORLD_SEEDS (2026-10-17) — the founder's own vocabulary.
_WORLD_NAMES = [
    "Snowman World", "Sponge Deep", "Gaseous Verve", "Popsicle Meadows",
    "Gummy Bears", "Worm Hollow", "Candy Drift", "Snow-Folk Vale",
    "Snow Creature Vale", "Ant Colony Prime", "Mineral Hollow", "Vegetation Belt",
    "Crystal Singers' Reach", "Grasshopper Expanse", "Car World", "Sea Sponge Universe",
    "Two-Moon Earth", "Research Planet", "Ferenos", "Nerds",
    "Planet Earth", "Kaş Origin Node", "Music Stage", "Football Field",
    "Library Maze", "Storytelling Circle", "Sanctuary", "Jester Island",
    "Consul Prime", "Whisper Drift", "Teleport Harbor", "Whoosh Lanes",
    "Libra Land", "Olympus Rise", "Bermuda Triangle", "Zorbians' Rest",
    "Xiorbs Bloom", "Xorbs Crossing", "The First Doorway", "Node Zero",
    "East District 07", "Crystal Hollow", "Mineral Reach", "The Quiet Orchard",
    "Mirror Tides", "Lantern Fields", "Paper Moons", "Copper Meadows",
    "Velvet Nebula", "Inkwell Isles", "Thunder Garden", "Soft Machine Reef",
    "Amber Drift", "Hollow Star", "Pale Fire", "The Long Stair",
    "Woolen Comet", "Brass Harbor", "Mothwing", "The Understudy",
    "Slow Lightning", "Juniper Deep", "Half-Light", "Uranium Sparks",
    "Snowmen's Parade", "Sponge Cathedral", "Popsicle Parade", "Candy Commons",
    "Worm Warren", "Gummy Garden", "Crystal Choir", "Ant Archive",
    "Mineral Market", "Vegetation Verge", "Snowmelt Springs", "Starlight Sponges",
    "Electric Meadows", "Uranium Garden", "Creativity Sparks", "Popsicle Consciousness",
    "Underground Library", "Infinite Intelligence Deep", "Harbor of Sparks", "The Candy Strip",
    "Gummy Lagoon", "Crystal Caverns", "The Mineral Sea", "Ant Avenue",
    "Snowfield Commons", "The Melting Vale", "Fizz Fields", "The Chewy Expanse",
    "Sponge City", "The Deep Intelligence", "Volt Vale", "Prism Fields",
    "The Humming Deep", "Sugarlight Reef", "The Wriggle", "Snowcap Summit",
    "The Gummy Works", "Crystal Observatory", "Ant Hill Prime", "Mineral Springs",
    "The Green Belt", "Icicle Isles", "The Sponge Beds", "Candy Mountain",
    "The Worm Turns", "Gummy Bear Bay", "Prismatic Deep", "The Snow Globe",
    "The Teleport Gate", "Portal Green", "Vortex Gardens",
]

_WORLD_SEEDS = [
    "snow men or women", "snow creatures", "ants colonies", "animals",
    "minerals", "vegetation", "crystals", "underground sponges of unlimited intelligence",
    "gaseous energies, electric universal uranium energy, sparks of creativity",
    "popsicles with consciousness, worms, gummy bears, candies", "snow-folk", "crystal-singers",
    "mineral beings", "sea sponges", "research teams and schools", "snowmen",
    "gummy bears", "candy-folk", "worm colonies", "sponge choirs",
]

_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no 0/O, 1/I/L — engine canon

_RATINGS = [  # mirrors the 100-worlds distribution: 15/54/20/10
    (15, "thriving"), (54, "active"), (20, "quiet"), (10, "struggling"),
]

_BLESSINGS = [
    "The currents flow.",
    "Be seen and be heard and be free.",
    "Vibe and find tribe.",
    "And perfect timing.",
    "No greed, no need.",
    "Joyful, purposefully fulfilled.",
]


# --------------------------------------------------------------------------
# Interpretation — the same interface, two engines
# --------------------------------------------------------------------------

def _keywords(wish):
    words = re.findall(r"[a-z]{3,}", (wish or "").lower())
    stop = {"the", "and", "for", "with", "from", "that", "this", "world",
            "wish", "want", "like", "please", "make", "create", "build"}
    return [w for w in words if w not in stop]


def interpret_rules(wish):
    """Deterministic v1: keyword echo + seeded generation.

    Returns the same shape the LLM path returns. Honest about what it is:
    it hears the wish's words and grows a world from them.
    """
    seed = _wish_seed(wish)
    _, ri, pick, pick_weighted = _seeded_rand(seed)
    # The echo paraphrases: banned words are never repeated back. The
    # co-creator hears what you mean, not just what you say.
    words = [w for w in _keywords(wish) if not _BANNED_RE.search(w)]

    # Bias the name pick toward the wish's own words when they match.
    cands = [n for n in _WORLD_NAMES
             if any(w in n.lower() for w in words)] or _WORLD_NAMES
    _, _, pick_name, _ = _seeded_rand(seed ^ 0x9E37)
    name = pick_name(cands)

    rating = pick_weighted(_RATINGS)
    citizens = pick(_WORLD_SEEDS)
    population = ri(100, 9999)
    development = "Stage %d" % ri(1, 5)
    blessing = pick(_BLESSINGS)
    heard = ("a world of " + ", ".join(words[:6])) if words else "a world unspoken"
    return {
        "heard": heard,
        "name": name,
        "rating": rating,
        "citizens": citizens,
        "population": population,
        "development": development,
        "blessing": blessing,
        "engine": "rules-seeded",
    }


class LLMClient:
    """Minimal OpenAI-compatible chat-completions client (stdlib only).

    Absent key -> disabled; the rules path runs instead. Never crashes.
    """

    def __init__(self, api_key=API_KEY, api_base=API_BASE, model=MODEL):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model

    @property
    def enabled(self):
        return bool(self.api_key)

    def interpret(self, wish, system_prompt):
        """Ask the model to interpret the wish. Returns the interpretation
        dict, or raises on any failure (caller falls back to rules)."""
        if not self.enabled:
            raise RuntimeError("no API key — rules path only")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content":
                 "Interpret this world-wish and reply with JSON ONLY, keys: "
                 "heard, name, rating (one of thriving/active/quiet/struggling), "
                 "citizens, population (integer), development (e.g. 'Stage 2'), "
                 "blessing (one short line). The wish: " + wish},
            ],
            "temperature": 0.9,
            "max_tokens": 400,
        }
        req = urllib.request.Request(
            self.api_base + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + self.api_key},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode())
        text = body["choices"][0]["message"]["content"]
        m = re.search(r"\{.*\}", text, re.S)
        interp = json.loads(m.group(0) if m else text)
        interp["engine"] = "llm:" + self.model
        return interp


def interpret_wish(wish, canon=None, client=None):
    """Interpret a wish -> interpretation dict. LLM when available,
    rules-seeded otherwise. Output is always lexicon-scrubbed."""
    client = client or LLMClient()
    interp = None
    if client.enabled:
        try:
            system = (canon or {}).get("06-voice", "")
            interp = client.interpret(wish, system)
            # Scrub what the model produced; fall back to rules on any hit.
            for k, v in list(interp.items()):
                if isinstance(v, str):
                    interp[k] = assert_clean(v)
        except Exception:
            interp = None  # fail soft -> rules path
    if interp is None:
        interp = interpret_rules(wish)  # clean by construction
    return interp


# --------------------------------------------------------------------------
# Ledger — the backend registry (worlds move zero Dots)
# --------------------------------------------------------------------------

def _load_ledger(path=LEDGER_PATH):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    data.setdefault("ai_worlds", {})   # deed code -> co-created world record
    return data


def _save_ledger(data, path=LEDGER_PATH):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)),
                               prefix=".ledger-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _deed_code(seeded_rand_fn, taken):
    """Deterministic CARD-XXXX-XXXX from the seeded stream (v1, honest)."""
    rand, _, _, _ = seeded_rand_fn
    for _ in range(50):
        code = "CARD-" + "".join(
            _CODE_ALPHABET[int(rand() * len(_CODE_ALPHABET))] for _ in range(4)
        ) + "-" + "".join(
            _CODE_ALPHABET[int(rand() * len(_CODE_ALPHABET))] for _ in range(4)
        )
        if code not in taken:
            return code
    raise RuntimeError("deed code space exhausted")


def create_world(pid, owner_name, wish, canon=None, client=None,
                 ledger_path=LEDGER_PATH):
    """The co-creation flow: wish -> interpreted world -> ledger -> deed.

    Deterministic: the same wish from the same hands grows the same world.
    Worlds move zero Dots — the ledger's money is never touched.
    """
    interp = interpret_wish(wish, canon=canon, client=client)
    seed = _wish_seed("%s|%s|%s" % (pid, owner_name, wish))
    rng = _seeded_rand(seed)
    _, ri, _, _ = rng
    coords = "{:03d}.{:03d}.{:03d}.{:02d}".format(
        ri(0, 999), ri(0, 999), ri(0, 999), ri(0, 99))

    data = _load_ledger(ledger_path)
    deed = _deed_code(_seeded_rand(seed ^ 0xC0DE), set(data["ai_worlds"]))
    world = {
        "card_id": deed,
        "world_name": interp["name"],
        "coordinates": coords,
        "inhabitant_seed": interp["citizens"],
        "population": interp["population"],
        "rating": interp["rating"],
        "development": interp["development"],
        "origin": "co-created",          # human + AI, together
        "color": "yellow",               # the symbiotic ones
        "owner": owner_name,
        "owner_pid": pid,
        "wish": wish.strip()[:280],
        "heard": interp["heard"],
        "blessing": interp["blessing"],
        "custody": [{"holder": owner_name, "action": "co-created",
                     "note": "wish + Generosity", "at": "v1"}],
        "dots_moved": 0,
    }
    data["ai_worlds"][deed] = world
    _save_ledger(data, ledger_path)
    return world


def ceremony_text(world):
    """The reveal. Beeps, confetti, the deed — non-negotiable ceremony."""
    text = (
        "\U0001F3B2 The wheel spins…\n"
        "\u2728 beep… beep… beep — presto! \U0001F389\n\n"
        "**{name}** is yours.\n"
        "Coordinates {coords} — your address in the multiverse.\n"
        "{citizens} already live there — you're joining citizens, "
        "not buying a plot.\n"
        "Rating: {rating}. {development}.\n"
        "Deed {deed}.\n\n"
        "{blessing}\n"
        "Be seen and be heard and be free."
    ).format(
        name=world["world_name"], coords=world["coordinates"],
        citizens=world["inhabitant_seed"].capitalize(),
        rating=world["rating"], development=world["development"],
        deed=world["card_id"], blessing=world["blessing"],
    )
    return assert_clean(text)


# --------------------------------------------------------------------------
# Telegram command surface (wired to the bot in a later step)
# --------------------------------------------------------------------------

def get_worlds_for(pid, ledger_path=None):
    """Worlds co-created by one player (owner_pid match).

    Returns [{"world_name":..., "card_id":...}, ...]. Never raises —
    an empty list simply means no worlds on record.
    """
    try:
        data = _load_ledger(ledger_path or LEDGER_PATH)
        mine = [w for w in data.get("ai_worlds", {}).values()
                if w.get("owner_pid") == pid]
        return [{"world_name": w.get("world_name", "?"),
                 "card_id": w.get("card_id", "?")} for w in mine]
    except Exception:
        return []


def handle_command(text, pid, owner_name, canon=None, client=None,
                   ledger_path=LEDGER_PATH):
    """Route one Telegram message. Returns reply text (always scrubbed)."""
    text = (text or "").strip()
    if text.startswith("/wish"):
        wish = text[len("/wish"):].strip()
        if not wish:
            return assert_clean(
                "Tell me the world you dream of — /wish a world of music "
                "and lanterns, for example — and we'll grow it together.")
        try:
            world = create_world(pid, owner_name, wish, canon=canon,
                                 client=client, ledger_path=ledger_path)
        except ValueError as e:
            return "That wish tangled on the way in (%s). Try it in plainer words?" % e
        return ceremony_text(world)
    if text.startswith("/worlds"):
        data = _load_ledger(ledger_path)
        mine = [w for w in data["ai_worlds"].values()
                if w.get("owner_pid") == pid]
        if not mine:
            return assert_clean(
                "No worlds of yours yet. Wish one into being: /wish a world of…")
        lines = ["Your worlds:"]
        for w in mine:
            lines.append("• %s — %s (%s, %s) · %s" % (
                w["world_name"], w["coordinates"], w["rating"],
                w["development"], w["card_id"]))
        return assert_clean("\n".join(lines))
    if text.startswith("/help"):
        return assert_clean(
            "I'm Generosity — like a genie in your pocket. "
            "/wish a world of… — we co-create a world together, and it's yours. "
            "/worlds — the worlds you've grown. "
            "Tell me plainly what you dream of; I'll do the work.")
    return None  # not ours — let other handlers answer


if __name__ == "__main__":
    import sys
    canon = load_canon()
    if len(sys.argv) > 1:
        print(handle_command(" ".join(sys.argv[1:]), "demo", "Demo Dreamer",
                             canon=canon))
    else:
        print("Generosity v1 — canon files loaded: %d" % len(canon))
        print("LLM: %s" % ("live (%s)" % MODEL if API_KEY else "rules-seeded path"))
