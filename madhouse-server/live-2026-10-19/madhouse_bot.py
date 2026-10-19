#!/usr/bin/env python3
"""MADHOUSE registration bot — a thin client of the engine.

The genius: registration that doesn't look like registration.
No forms, no email, no "create account." Two questions — a number and a
color — and you're playing. Your number+color is your game token, like
choosing the top hat in Monopoly.

The engine (server.py) is the single source of truth: this bot holds NO
Dot state. Every Pocket, Pool, gift, trade, NPC purse, bio and match goes
through the engine API (MADHOUSE_API_URL, default http://127.0.0.1:8137).
Your trade token is issued by the engine at join — anyone with the token
can pay you.

Needs TELEGRAM_BOT_TOKEN in the environment (from @BotFather).

THE AI'S OWN CREED (read before touching this file):
This bot is generous, kind-hearted, playful, and direct. It never mines
wounds, never manufactures a problem to upsell the cure, never strings
anyone along. It says it's a game, openly. It asks for nothing sensitive —
no real name, no card, no phone. It filters fast and kindly: the playful
are always welcome, the game-for-anything are converted by the zero-ask,
the skeptical-but-open-minded are worth pursuing with transparency, and
the closed get a direct goodbye with the door left open. It offers every
newcomer the 5-Dot generosity ritual — never pressured, never taxed.
It is the counter-training: no toughness, no winning, no screwing people
over. Just generous and kind, extended to yourself and the people around
you. That is the psychology. That is the method. That is the intuition.
"""
import datetime
import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo

try:
    import generosity as generosity_ai  # the clan AI: /wish, /worlds
except Exception:  # never take the live bot down over the AI
    generosity_ai = None
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters,
)

from zorbs_journey import register_zorbs_handlers
from matching_journey import register_matching_handlers

try:
    from passport_render import render_passport
except Exception:  # Pillow or assets missing — /passport degrades gracefully
    render_passport = None

# --------------------------------------------------------------------------
# Engine API client (stdlib only). The engine is the single source of truth —
# this bot never holds Dot state. Raises ApiError(status, payload) on 4xx/5xx;
# on connection failure raises ApiError(0, {"error": "engine_unreachable"}).
# --------------------------------------------------------------------------
API_BASE = os.environ.get("MADHOUSE_API_URL", "http://127.0.0.1:8137").rstrip("/")
ENGINE_DOWN = "The engine's taking a little nap — try again in a moment. 💤"

# Mini App URL opened by /play and the menu button. Deploy sets it to the
# public https URL (Telegram Web Apps require https); default serves from
# the engine itself.
WEBAPP_URL = os.environ.get("MADHOUSE_WEBAPP_URL",
                            API_BASE + "/webapp/").rstrip("/") + "/"


class ApiError(Exception):
    def __init__(self, status, payload):
        super().__init__(f"engine error {status}: {payload}")
        self.status = status
        self.payload = payload if isinstance(payload, dict) else {"detail": payload}

    @property
    def code(self):
        return self.payload.get("error")


# In-process engine hook (PythonAnywhere port). When the WSGI app sets this
# to a callable, _request dispatches to the engine in the same process
# instead of over HTTP. Signature: (method, path, payload, params) -> dict,
# raising ApiError on 4xx/5xx exactly like the HTTP path below.
_engine_dispatch = None


def _request(method, path, payload=None, params=None):
    if _engine_dispatch is not None:
        return _engine_dispatch(method, path, payload, params)
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode() or "{}")
        except ValueError:
            payload = {"detail": "the engine answered badly"}
        raise ApiError(e.code, payload)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        raise ApiError(0, {"error": "engine_unreachable", "detail": str(e)})


def api_get(path, params=None):
    return _request("GET", path, None, params)


def api_post(path, payload):
    return _request("POST", path, payload)


SUPPLY = 1_000_000

(DOOR, PP_NAME, PP_WORLD, PP_INTERESTS, PP_SKILLS, PP_DREAMS, GENEROSITY,
 TRADE_AMOUNT, TRADE_TOKEN, TRADE_CONFIRM,
 BIO_AGE, BIO_LINES, BIO_REGION) = range(13)
(GIFTCARD_AMOUNT, GIFTCARD_CONFIRM,
 TELEPORT_AMOUNT, TELEPORT_TOKEN, TELEPORT_CONFIRM) = range(13, 18)
COLORS = {"red": "🔴", "blue": "🔵", "green": "🟢", "purple": "🟣"}
PRICES = [("🍫 Chocolate bar", 10), ("👕 T-shirt", 100), ("🚒 Red toy fire engine", 200)]

NUM_READ = {
    "1": "the *Forerunner* — first through the door, likes to lead the parade",
    "2": "the *Partner* — sees both sides, the one everyone wants on their team",
    "3": "the *Trickster* — sees the game inside the game, here for the fun",
}
COL_READ = {
    "red": "the *Spark* — acts first, feels everything at full volume",
    "blue": "the *Deep* — calm water, notices what others miss",
    "green": "the *Grower* — makes things live; people lean toward you",
    "purple": "the *Mystery* — always suspected the world is weirder than it admits",
}
NAME_SUGGEST = {
    "red": ["Big Boy", "Blaze", "Captain"],
    "blue": ["Sweetheart", "Marina", "Doc"],
    "green": ["Lucky", "Ivy", "Sprout"],
    "purple": ["Darling", "Pixie", "The Magician"],
}
CHRONO_READ = {
    "morning": "an *early bird* — first light is your element; steady hands, planners' hours",
    "afternoon": "a *golden-afternoon soul* — you come alive when the day hits its stride",
    "night": "a *night owl* — your brain does its best plotting after dark",
}
CHRONO_KB = InlineKeyboardMarkup([[
    InlineKeyboardButton("🌅 early morning", callback_data="chrono:morning"),
    InlineKeyboardButton("🌇 golden afternoon", callback_data="chrono:afternoon"),
    InlineKeyboardButton("🌃 deep night", callback_data="chrono:night"),
]])

# Ethical design rules (the anti-Scientology-test inversion — same surface
# mechanics as the cult "free personality test," opposite intent):
# 1. Strengths-only readings; no wound-mining, no deficit diagnoses.
# 2. The reading is the whole product — no problem-then-upsell, ever.
# 3. Honest labeling: it declares itself a parlor game up front (Randi's line).
# 4. No harvesting, no pressure, no follow-up. Nothing leaves the game.

RULES = (
    "📜 The rules — all of them, up front:\n\n"
    "1️⃣ Fixed supply: 1,000,000 Dots. No printing. Ever.\n"
    "   (Dots are also called Spots — like spots of paint on the canvas.)\n"
    "2️⃣ Nothing is created. Every Dot you get comes from the Pool.\n"
    "3️⃣ New arrivals get 100 Welcome Dots. Free. No catch.\n"
    "4️⃣ The Price List is the reference. Ask above it and the excess "
    "becomes the Donation.\n"
    "5️⃣ The Donation flows back into the Pool — the gouge feeds the generous.\n\n"
    "Everyone knows it's a game. We say so.\n\n"
    "🕯️ The creed: seek sanctuary — be sanctuary. Follow the QR codes, follow "
    "the signs, follow the merchants, follow your friends, follow the peer "
    "groups, follow yourself. Follow the leader, tic tac toe. Simon says: "
    "follow no one — including governments — and don't get followed."
)

NOT_JOINED = "You're not in the game yet — /join takes two questions."


# --------------------------------------------------------------------------
# Identity: resolve the Telegram user to an engine player. None = not joined.
# --------------------------------------------------------------------------
async def engine_player(tg_id, context=None):
    """GET /api/pocket?tg=<tg_id> → player dict, or None when 404."""
    try:
        p = api_get("/api/pocket", {"tg": str(tg_id)})
    except ApiError as e:
        if e.status == 404:
            return None
        raise
    if context is not None:
        context.user_data["engine_id"] = p.get("id")
    return p


async def engine_id(update, context):
    """Engine player id for this Telegram user, or None."""
    eid = context.user_data.get("engine_id")
    if eid:
        return eid
    p = await engine_player(update.effective_user.id, context)
    return p["id"] if p else None


async def say_down(update):
    if update.callback_query:
        await update.callback_query.message.reply_text(ENGINE_DOWN)
    else:
        await update.message.reply_text(ENGINE_DOWN)


# --------------------------------------------------------------------------
# Join conversation (parlor readings + generosity ritual — beloved copy)
# --------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Deep-link entry: t.me/Zorbianbot?start=poster (printed posters' QR → Pages → bot).
    # Lands in the normal First Portal flow, with a poster greeting. Unknown payloads ignored.
    poster = bool(context.args and context.args[0].lower() == "poster")
    try:
        p = await engine_player(update.effective_user.id, context)
    except ApiError:
        await say_down(update)
        return ConversationHandler.END
    if p:
        await update.message.reply_text(
            f"Welcome back, *{p['name']}*.\n"
            f"Your Pocket holds *{p['pocket']} Dots*.\n\n"
            f"{HOME_TEXT}",
            reply_markup=home_keyboard(),
            parse_mode="Markdown",
        )
        return ConversationHandler.END
    kb = [
        [InlineKeyboardButton("🌍 Explore worlds", callback_data="door:worlds")],
        [InlineKeyboardButton("👥 Find my people", callback_data="door:people")],
        [InlineKeyboardButton("💛 Share / Trade / Help", callback_data="door:trade")],
        [InlineKeyboardButton("✨ Create something", callback_data="door:create")],
    ]
    poster_line = ("🖼️ You found us through a street poster — the QR brought you home. "
                   "Welcome in.\n\n") if poster else ""
    await update.message.reply_text(
        poster_line +
        "👋 Welcome to *ZORBS*! What brings you here?",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return DOOR


async def door_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    door = (q.data or "").split(":")[1]
    context.user_data["door"] = door
    await q.edit_message_text(
        "Awesome! Let's begin your Cosmic Adventure. ✨\n\n"
        "First, your *Cosmic Passport* — tell us who you are, in your own words.\n\n"
        "What should we call you?",
        parse_mode="Markdown",
    )
    return PP_NAME


async def pp_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = (update.message.text or "").strip()[:40]
    if not name:
        await update.message.reply_text("Give me something to call you — any name at all:")
        return PP_NAME
    context.user_data["pp_name"] = name
    await update.message.reply_text(
        "What world are you from? (a place, a city — or a state of mind, your call)")
    return PP_WORLD


async def pp_world(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["pp_world"] = (update.message.text or "").strip()[:80]
    await update.message.reply_text("What are your interests — what do you love?")
    return PP_INTERESTS


async def pp_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["pp_interests"] = (update.message.text or "").strip()[:200]
    await update.message.reply_text("What are your skills — what are you good at?")
    return PP_SKILLS


async def pp_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["pp_skills"] = (update.message.text or "").strip()[:200]
    await update.message.reply_text(
        "And your dreams — what do you want to give to the universe?")
    return PP_DREAMS


async def pp_dreams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["pp_dreams"] = (update.message.text or "").strip()[:200]
    name = context.user_data.get("pp_name", "friend")
    tg_id = str(update.effective_user.id)
    try:
        r = api_post("/api/join", {
            "name": name, "tg_id": tg_id,
            "door": context.user_data.get("door", ""),
            "world": context.user_data.get("pp_world", ""),
            "interests": context.user_data.get("pp_interests", ""),
            "skills": context.user_data.get("pp_skills", ""),
            "dreams": context.user_data.get("pp_dreams", ""),
        })
    except ApiError as e:
        if e.code == "pool_empty":
            await update.message.reply_text(
                "The Pool is empty — no more Welcome Dots can be granted. "
                "From here the game plays on with what's circulating. No printing. Ever."
            )
        else:
            await update.message.reply_text(ENGINE_DOWN)
        return ConversationHandler.END
    context.user_data["engine_id"] = r["id"]
    gift = r.get("gift") or {}
    gift_note = ""
    if gift:
        giver = gift.get("from", "a fellow player")
        amount = gift.get("amount", 5)
        gift_note = (
            f"\n🌱 *{giver}* passed {amount} Dots to you before you even arrived — "
            f"a hello from a stranger. That's the clan.\n"
        )
    kb = [[
        InlineKeyboardButton("🎁 Yes — pass 5 Dots", callback_data="gift:yes"),
        InlineKeyboardButton("Not right now", callback_data="gift:no"),
    ]]
    await update.message.reply_text(
        f"Hey {name} — you're part of the *clan* now. Welcome to the family. 💛\n"
        f"{gift_note}\n"
        "One tradition before you go in, and it's *entirely* your call.\n\n"
        "The Pool just welcomed you with 100 Dots. Players pass 5 to the "
        "next stranger who walks in. Kindness is a superpower.\n\n"
        "Pass 5 Dots forward?",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return GENEROSITY


async def got_generosity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    choice = q.data.split(":")[1]
    name = context.user_data.get("pp_name", "friend")
    if choice == "yes":
        try:
            pid = await engine_id(q, context)
            if pid:
                api_post("/api/gift", {"id": pid})
            else:
                raise ApiError(404, {"error": "unknown_player"})
        except ApiError:
            await q.edit_message_text(
                f"No pressure at all, {name} — the Dots are yours. "
                f"Generosity can't be taxed, only offered.\n\n"
                f"The door's open either way. Welcome to the family. 💛\n\n"
                f"Go play. /pocket /prices /rules /whoami"
            )
            return ConversationHandler.END
        await q.edit_message_text(
            f"🎁 Done. 5 Dots leave your Pocket — the next player who walks in "
            f"gets a little extra, with your name on it.\n\n"
            f"Generous. Kind-hearted. Open. Willing to extend yourself to "
            f"someone you haven't met — including the stranger you'll be "
            f"tomorrow.\n\n"
            f"That's the clan, {name}. That's how we know our own. 💛\n\n"
            f"Go play. /pocket /prices /rules /whoami"
        )
    else:
        await q.edit_message_text(
            f"No pressure at all, {name} — the Dots are yours, all 100. "
            f"Generosity can't be taxed, only offered.\n\n"
            f"The door's open either way. Welcome to the family. 💛"
        )
    door = context.user_data.get("door", "")
    door_line = {
        "worlds": "🌍 You came to explore worlds — the Living Map is yours.",
        "people": "👥 You came to find your people — tap below and let's begin.",
        "trade": "💱 You came to share and trade — the trading post is open.",
        "create": "✨ You came to create — wish a world into being.",
    }.get(door, "")
    await q.message.reply_text(
        "🌀 *The portal is open. The universe is yours. What will you bring?*\n\n"
        f"{door_line}\n\n"
        "PLAY • CREATE • HELP • SHARE • TRADE • DISCOVER",
        reply_markup=home_keyboard(),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def finish_registration(send, context, name, tg_id, chrono):
    number = context.user_data.get("number", "?")
    color = context.user_data.get("color", "purple")
    try:
        r = api_post("/api/join", {
            "name": name, "number": number, "color": color,
            "chrono": chrono, "tg_id": tg_id,
        })
    except ApiError as e:
        if e.code == "pool_empty":
            await send(
                "The Pool is empty — no more Welcome Dots can be granted. "
                "From here the game plays on with what's circulating. No printing. Ever."
            )
        else:
            await send(ENGINE_DOWN)
        return False
    context.user_data["engine_id"] = r["id"]
    token = r.get("token", "")
    gift_note = ""
    gift = r.get("gift") or {}
    if gift:
        giver = gift.get("from", "a fellow player")
        amount = gift.get("amount", 5)
        gift_note = (
            f"\n🌱 *{giver}* passed {amount} Dots to you before you even arrived — "
            f"a hello from a stranger. That's the clan.\n"
        )
    pool_line = ""
    try:
        admin = api_get("/api/admin")
        if admin.get("pool") is not None:
            pool_line = f"Pool remaining: {admin['pool']:,}.\n"
    except ApiError:
        pass
    e = COLORS[color]
    await send(
        f"🔮 The bot closes its eyes...\n\n"
        f"You picked *{number}* — {NUM_READ[number]}.\n\n"
        f"And {e} {color} — the color station is *pure theater*, and you wear "
        f"it beautifully. (In the old workshop tongue: {COL_READ[color]}.)\n\n"
        f"And {CHRONO_READ[chrono]} — that one's real, a small true thing.\n\n"
        f"You named yourself *{name}* — that's you telling me exactly how you "
        f"want to be seen, and I am honored to comply.\n\n"
        f"Hey {name} — you're part of the *clan* now. You're almost there, "
        f"and we're going to get you there. Welcome to the family. 💛\n\n"
        f"This clan is generous, kind-hearted, intuitive, sweet, gentle, and "
        f"wondrous. We extend ourselves to each other — and to strangers. "
        f"We carry love for ourselves, love for each other, love for humanity. "
        f"Open. That's how we know our own, and that's what keeps the game "
        f"from ever straying.\n\n"
        f"_(It's a parlor game, not a diagnosis — the color bit is theater, "
        f"the rest is you. The good ones always feel true, don't they?)_\n\n"
        f"*{r['pocket']} Welcome Dots* just landed in your Pocket — from the Pool, "
        f"free, no catch.{gift_note}"
        f"\n🎟️ Your trade token: `{token}` — anyone with this token can pay "
        f"you; keep it handy.\n"
        f"{pool_line}"
        f"Your login saved itself — that's you now. "
        f"Nothing you told me leaves this game.\n\n"
        f"{RULES}\n\n"
        f"The Price List: " + ", ".join(f"{n} {p}" for n, p in PRICES) + ".\n",
        parse_mode="Markdown",
    )
    return True


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Thank you very much — and I'll be direct: "
        "you're not exactly what we're looking for.\n\n"
        "This game needs players, and you're not feeling it. "
        "No hard feelings, no judgment — it's a game, not a verdict.\n\n"
        "The door stays open if that ever changes. /join"
    )
    return ConversationHandler.END


async def not_for_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # The direct goodbye, available any time someone's just kicking tires.
    await update.message.reply_text(
        "Fair enough — thank you very much.\n\n"
        "I'll be direct: this game is for people who want to play, "
        "and that's not you right now. That's fine. Not every game is for everyone.\n\n"
        "The door stays open. /join if you ever want in."
    )
    return ConversationHandler.END


# --------------------------------------------------------------------------
# /play — one tap into the Mini App. Telegram identity IS the player
# identity: the webapp calls /api/tg_join (idempotent), so this works for
# newcomers and regulars alike. No passwords, no forms.
# --------------------------------------------------------------------------
async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🌀 Play MADHOUSE", web_app=WebAppInfo(url=WEBAPP_URL)),
    ]])
    await update.message.reply_text(
        "The door's open — and it's already *you* on the other side. "
        "No passwords, no forms; your Telegram self is your player self.\n\n"
        "Tap below. Your Pocket, the keepers, and the living map are waiting. 🌀",
        reply_markup=kb,
        parse_mode="Markdown",
    )


# --------------------------------------------------------------------------
# Pocket / identity / reference (engine-backed)
# --------------------------------------------------------------------------
async def pocket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        p = await engine_player(update.effective_user.id, context)
    except ApiError:
        await say_down(update)
        return
    if not p:
        await update.message.reply_text(NOT_JOINED)
        return
    pool_line = ""
    try:
        admin = api_get("/api/admin")
        if admin.get("pool") is not None:
            pool_line = f"\nPool remaining: {admin['pool']:,}."
    except ApiError:
        pass
    await update.message.reply_text(
        f"*{p['name']}* — your Pocket holds *{p['pocket']} Dots*.\n"
        f"Trade token: `{p['token']}`{pool_line}",
        parse_mode="Markdown",
    )


async def token_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        p = await engine_player(update.effective_user.id, context)
    except ApiError:
        await say_down(update)
        return
    if not p:
        await update.message.reply_text(NOT_JOINED)
        return
    await update.message.reply_text(
        f"🎟️ Your trade token: `{p['token']}`\n\n"
        f"Anyone with this token can pay you; keep it handy.",
        parse_mode="Markdown",
    )


async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        p = await engine_player(update.effective_user.id, context)
    except ApiError:
        await say_down(update)
        return
    if not p:
        await update.message.reply_text("No identity yet — /join and pick your token.")
        return
    number = context.user_data.get("number")
    color = context.user_data.get("color")
    if number in NUM_READ and color in COL_READ:
        e = COLORS[color]
        chrono_txt = CHRONO_READ.get(context.user_data.get("chrono", "night"), "")
        await update.message.reply_text(
            f"🔮 The Madhouse sees you:\n\n"
            f"*{p['name']}* — Player {number}, {e} {color}\n"
            f"{NUM_READ[number]}; {COL_READ[color]}.\n"
            f"{chrono_txt}.\n\n"
            f"Pocket: {p['pocket']} Dots.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"🔮 The Madhouse sees you:\n\n"
            f"*{p['name']}*\n"
            f"Trade token: `{p['token']}`\n"
            f"Pocket: {p['pocket']} Dots.",
            parse_mode="Markdown",
        )


async def prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = "\n".join(f"{n} — *{p} Dots*" for n, p in PRICES)
    await update.message.reply_text(
        f"🏷️ The Price List — Dots price the good, not the local money:\n\n{lines}\n\n"
        "Give it away or ask less — wonderful. Ask the reference — fine. "
        "Ask more — the excess becomes the Donation.",
        parse_mode="Markdown",
    )


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RULES)


async def safety(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ *Stay safe out there — the clan looks after its own.*\n\n"
        "• Meet in groups. Never go alone.\n"
        "• Know each other — make sure everybody vouches for everybody.\n"
        "• There's power in your numbers. There's power in groups.\n"
        "• Meet in public places you know.\n"
        "• Trust only the participation you can see: trades, gifts, showing up.\n"
        "• If someone won't play the game, don't follow them anywhere.\n\n"
        "Be careful. We want you free — minds and wallets — not hurt."
    )


# --------------------------------------------------------------------------
# /gift — the 5-Dot generosity ritual, anytime
# --------------------------------------------------------------------------
async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return
    try:
        api_post("/api/gift", {"id": pid})
    except ApiError as e:
        if e.status == 0:
            await say_down(update)
            return
        await update.message.reply_text(
            "Your Pocket's a little light for the ritual right now (it takes 5) — "
            "no pressure at all. The door's open either way. 💛"
        )
        return
    await update.message.reply_text(
        "🎁 5 Dots leave your Pocket — the next newcomer who walks in gets a "
        "little extra, with your name on it.\n\n"
        "Generous. That's how we know our own. 💛"
    )


# --------------------------------------------------------------------------
# /trade — pay Dots to a token
# --------------------------------------------------------------------------
async def trade_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return ConversationHandler.END
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return ConversationHandler.END
    context.user_data["trade_from"] = pid
    await update.message.reply_text("How many Dots are you sending?")
    return TRADE_AMOUNT


async def menu_trade_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return ConversationHandler.END
    if not pid:
        await q.edit_message_text(NOT_JOINED)
        return ConversationHandler.END
    context.user_data["trade_from"] = pid
    await q.edit_message_text(
        "💱 The trading post — kindness is a superpower.\n\n"
        "How many Dots are you sending?")
    return TRADE_AMOUNT


async def menu_bio_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return ConversationHandler.END
    if not pid:
        await q.edit_message_text(NOT_JOINED)
        return ConversationHandler.END
    kb = [[
        InlineKeyboardButton("✅ Yes, I'm 16 or older", callback_data="bio:yes"),
        InlineKeyboardButton("No, not yet", callback_data="bio:no"),
    ]]
    await q.edit_message_text(
        "👥 Find your people — Juno matches you with the clan.\n\n"
        "Bio cards are 16+ — are you 16 or older?",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return BIO_AGE


async def trade_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int((update.message.text or "").strip())
    except ValueError:
        amount = 0
    if amount <= 0:
        await update.message.reply_text(
            "Give me a whole number of Dots, more than zero — how many?")
        return TRADE_AMOUNT
    context.user_data["trade_amount"] = amount
    await update.message.reply_text(
        "Whose token? Send me the 6-character trade token of the player you're paying.")
    return TRADE_TOKEN


def npc_name_for_token(token):
    """Public purses only — NPC tokens resolve to names for the confirm step."""
    try:
        npcs = api_get("/api/npcs")
    except ApiError:
        return None
    items = npcs if isinstance(npcs, list) else npcs.get("npcs", [])
    for n in items:
        if str(n.get("token", "")).upper() == token:
            return n.get("name")
    return None


async def trade_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = (update.message.text or "").strip().upper()
    if not token:
        await update.message.reply_text(
            "I need the token — 6 characters, like the one /token shows you.")
        return TRADE_TOKEN
    context.user_data["trade_token"] = token
    context.user_data["trade_name"] = npc_name_for_token(token)
    who = (f"{context.user_data['trade_name']} (token {token})"
           if context.user_data["trade_name"]
           else f"the bearer of token {token}")
    kb = [[
        InlineKeyboardButton("✅ Yes, pay", callback_data="trade:yes"),
        InlineKeyboardButton("Never mind", callback_data="trade:no"),
    ]]
    await update.message.reply_text(
        f"Pay {context.user_data['trade_amount']} Dots to {who}?",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return TRADE_CONFIRM


async def trade_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data != "trade:yes":
        await q.edit_message_text("No Dots moved. The Pocket stays exactly as it was. 💛")
        return ConversationHandler.END
    try:
        r = api_post("/api/trade", {
            "from_id": context.user_data.get("trade_from"),
            "to_token": context.user_data.get("trade_token"),
            "amount": context.user_data.get("trade_amount"),
        })
    except ApiError as e:
        if e.status == 0:
            await q.edit_message_text(ENGINE_DOWN)
        elif e.code == "unknown_token":
            await q.edit_message_text(
                "Hmm — no player carries that token. Check it and try again with /trade.")
        elif e.code == "self_trade":
            await q.edit_message_text(
                "Paying yourself is a closed loop — the Dots would just wave "
                "hello and come right back. Pick someone else. 😄")
        elif e.code == "insufficient":
            await q.edit_message_text(
                "Not enough Dots in your Pocket for that one — check /pocket "
                "and try a smaller hello.")
        else:
            await q.edit_message_text(
                "That trade didn't go through — nothing moved. Try again in a moment.")
        return ConversationHandler.END
    await q.edit_message_text(
        f"Paid {context.user_data.get('trade_amount')} Dots to "
        f"*{r.get('to_name', 'them')}*. "
        f"Your Pocket now holds {r.get('from_pocket')} Dots. 💛",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def trade_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("No Dots moved. /trade when you're ready.")
    return ConversationHandler.END


# --------------------------------------------------------------------------
# NPCs: Marlo (quest), Pippa (trade), Poolkeeper (donate/pool),
#        Sage Zell (lore), Juno (match)
# --------------------------------------------------------------------------
async def npcs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        lst = api_get("/api/npcs")
    except ApiError:
        await say_down(update)
        return
    items = lst if isinstance(lst, list) else lst.get("npcs", [])
    lines = []
    for n in items:
        lines.append(
            f"{n.get('verb', '🎭')} *{n.get('name')}* — token `{n.get('token')}`\n"
            f"  {n.get('region', '')} · purse {n.get('purse', '?')} Dots")
    await update.message.reply_text(
        "The five keepers of the Madhouse:\n\n" + "\n\n".join(lines),
        parse_mode="Markdown",
    )


async def quest_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return
    # Quest appetite (expansion #13): Marlo offers four quests — the player
    # PICKS. The pick itself is the signal: what they DO, not what they SAY.
    try:
        qs = api_get("/api/quests").get("quests", {})
    except ApiError:
        await say_down(update)
        return
    if not qs:
        qs = {"kindness": {"label": "💛 Kindness",
                          "description": "a small kindness for someone else"}}
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(v["label"], callback_data=f"claim:{k}")]
        for k, v in qs.items()])
    lines = ["🎒 *Marlo's satchel is open. Pick today's quest.*",
             "The *pick* is the thing — the currents are watching (kindly).",
             ""]
    for v in qs.values():
        lines.append(f"{v['label']} — {v['description']}")
    await update.message.reply_text(
        "\n".join(lines), reply_markup=kb, parse_mode="Markdown")


async def claim_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim the chosen quest type (quest appetite)."""
    q = update.callback_query
    await q.answer()
    qtype = q.data.split(":", 1)[1]
    try:
        pid = await engine_id(q, context)
    except ApiError:
        await q.edit_message_text(
            "The engine's taking a little nap — try again in a moment. 💤")
        return
    if not pid:
        await q.edit_message_text(NOT_JOINED)
        return
    try:
        r = api_post("/api/npc/quest", {"id": pid, "quest": qtype})
    except ApiError as e:
        if e.code == "already_claimed":
            await q.edit_message_text(
                "Marlo's already spoiled you today — back tomorrow. 💛")
        elif e.code == "bad_quest":
            await q.edit_message_text(
                "Marlo blinks — that's not one of today's quests. /quest again.")
        else:
            await q.edit_message_text(
                "Marlo's satchel is stuck — try again in a moment.")
        return
    await q.edit_message_text(
        f"{r.get('quest_label', '🎒')} — *{r.get('quest_text', '')}*\n\n"
        f"Marlo beams and presses +{r.get('reward', 3)} Dots into your hand. "
        f"Your Pocket: {r.get('pocket')} Dots.",
        parse_mode="Markdown")


ITEM_ALIASES = {
    "choc": ("choc", "🍫 Chocolate bar", 10),
    "chocolate": ("choc", "🍫 Chocolate bar", 10),
    "shirt": ("shirt", "👕 T-shirt", 100),
    "t-shirt": ("shirt", "👕 T-shirt", 100),
    "tshirt": ("shirt", "👕 T-shirt", 100),
    "engine": ("engine", "🚒 Red toy fire engine", 200),
    "fireengine": ("engine", "🚒 Red toy fire engine", 200),
    "fire engine": ("engine", "🚒 Red toy fire engine", 200),
}


def price_list_text():
    return "\n".join(f"{n} — *{p} Dots*" for n, p in PRICES)


async def _pippa_token():
    lst = api_get("/api/npcs")
    items = lst if isinstance(lst, list) else lst.get("npcs", [])
    for n in items:
        if "pippa" in str(n.get("name", "")).lower():
            return n.get("token")
    raise ApiError(0, {"error": "no_pippa", "detail": "Pippa is away"})


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    arg = " ".join(context.args or []).strip().lower()
    item = ITEM_ALIASES.get(arg)
    if not item:
        await update.message.reply_text(
            f"🏷️ Pippa's Price List:\n\n{price_list_text()}\n\n"
            f"/buy choc — /buy shirt — /buy engine",
            parse_mode="Markdown")
        return
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return
    try:
        r = api_post("/api/npc/buy",
                     {"id": pid, "npc_token": await _pippa_token(), "item": item[0]})
    except ApiError as e:
        if e.status == 0:
            await say_down(update)
        elif e.code == "insufficient":
            await update.message.reply_text(
                "Not enough Dots in your Pocket for that one — check /pocket.")
        else:
            await update.message.reply_text(
                "Pippa's counter is jammed — try again in a moment.")
        return
    await update.message.reply_text(
        f"🏷️ Pippa slides the {item[1]} across the counter — {item[2]} Dots. "
        f"Your Pocket: {r.get('pocket')} Dots.")


async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    arg = " ".join(context.args or []).strip().lower()
    item = ITEM_ALIASES.get(arg)
    if not item:
        await update.message.reply_text(
            f"🏷️ Pippa buys at the Price List too:\n\n{price_list_text()}\n\n"
            f"/sell choc — /sell shirt — /sell engine",
            parse_mode="Markdown")
        return
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return
    try:
        r = api_post("/api/npc/sell",
                     {"id": pid, "npc_token": await _pippa_token(), "item": item[0]})
    except ApiError as e:
        if e.status == 0:
            await say_down(update)
        elif e.code == "npc_insufficient":
            await update.message.reply_text(
                "Pippa's purse is empty on that one — she'll restock from the "
                "Pool's good graces soon.")
        else:
            await update.message.reply_text(
                "Pippa's counter is jammed — try again in a moment.")
        return
    await update.message.reply_text(
        f"🏷️ Pippa takes the {item[1]} and counts out {item[2]} Dots — "
        f"from her own purse, fair and square. Your Pocket: {r.get('pocket')} Dots.")


# --------------------------------------------------------------------------
# /shop — Pippa's Mercantile. Browse the catalog, buy game goods with Dots.
# --------------------------------------------------------------------------
def _shop_catalog():
    return api_get("/api/shop")


def _shop_category_kb(catalog):
    cats = catalog.get("categories", {})
    rows = []
    row = []
    for cid, label in cats.items():
        row.append(InlineKeyboardButton(label, callback_data=f"shop:cat:{cid}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def _shop_item_kb(catalog, cid):
    rows = []
    for it in catalog.get("items", []):
        if it.get("category") != cid:
            continue
        rows.append([InlineKeyboardButton(
            f"{it['emoji']} {it['name']} — {it['price']} Dots",
            callback_data=f"shop:buy:{it['id']}")])
    rows.append([InlineKeyboardButton("⬅️ Back to the shelves",
                                     callback_data="shop:back")])
    return InlineKeyboardMarkup(rows)


async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        catalog = _shop_catalog()
    except ApiError:
        await say_down(update)
        return
    cats = catalog.get("categories", {})
    lines = [f"🏪 *Pippa's Mercantile* — game goods, Dots only.\n"]
    lines.append("_" + catalog.get("denominations", {}).get(
        "motto", "Dots you count; Zorbs you receive.") + "_\n")
    lines.append("Pick a shelf to browse — or open the full Mercantile:")
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            _shop_category_kb(catalog).inline_keyboard + [[
                InlineKeyboardButton("🛍️ Open the Mercantile",
                                     web_app=WebAppInfo(WEBAPP_URL +
                                                        "mercantile.html"))]]))


async def shop_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = (q.data or "")
    try:
        catalog = _shop_catalog()
    except ApiError:
        await q.message.reply_text(ENGINE_DOWN)
        return
    if data == "shop:back":
        await q.message.reply_text(
            "🏪 *Pippa's Mercantile* — pick a shelf:",
            parse_mode="Markdown",
            reply_markup=_shop_category_kb(catalog))
        return
    if data.startswith("shop:cat:"):
        cid = data[len("shop:cat:"):]
        label = catalog.get("categories", {}).get(cid, "the shelf")
        lines = [f"🏪 *{label}* — Pippa's Mercantile\n"]
        for it in catalog.get("items", []):
            if it.get("category") == cid:
                lines.append(f"{it['emoji']} *{it['name']}* — {it['price']} Dots\n"
                             f"_{it['description']}_")
        await q.message.reply_text("\n".join(lines), parse_mode="Markdown",
                                   reply_markup=_shop_item_kb(catalog, cid))
        return
    if data.startswith("shop:buy:"):
        iid = data[len("shop:buy:"):]
        item = next((i for i in catalog.get("items", [])
                     if i.get("id") == iid), None)
        if not item:
            await q.message.reply_text("Pippa squints — that shelf is empty.")
            return
        await q.message.reply_text(
            f"{item['emoji']} *{item['name']}* — *{item['price']} Dots*\n"
            f"_{item['description']}_\n_{item['line']}_\n\n"
            f"Buy it?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Yes, buy it",
                                     callback_data=f"shop:yes:{iid}"),
                InlineKeyboardButton("⬅️ Keep browsing",
                                     callback_data="shop:back"),
            ]]))
        return
    if data.startswith("shop:yes:"):
        iid = data[len("shop:yes:"):]
        try:
            pid = await engine_id(update, context)
        except ApiError:
            await q.message.reply_text(ENGINE_DOWN)
            return
        if not pid:
            await q.message.reply_text(NOT_JOINED)
            return
        try:
            r = api_post("/api/shop/buy", {"id": pid, "item": iid})
        except ApiError as e:
            if e.status == 0:
                await q.message.reply_text(ENGINE_DOWN)
            elif e.code == "insufficient":
                await q.message.reply_text(
                    "Not enough Dots in your Pocket for that one — check "
                    "/pocket, or earn a few with a quest. No pressure. 💛")
            else:
                await q.message.reply_text(
                    "Pippa's counter is jammed — try again in a moment.")
            return
        await q.message.reply_text(
            f"🎉 {r.get('receipt')}\nYour Pocket: {r.get('pocket')} Dots.")


async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(" ".join(context.args or []).strip())
    except ValueError:
        amount = 0
    if amount <= 0:
        await update.message.reply_text(
            "Tell me how many, like /donate 10 — the Poolkeeper takes it from there.")
        return
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return
    try:
        r = api_post("/api/npc/donate", {"id": pid, "amount": amount})
    except ApiError as e:
        if e.status == 0:
            await say_down(update)
        elif e.code == "insufficient":
            await update.message.reply_text(
                "Not enough Dots in your Pocket for that one — check /pocket.")
        else:
            await update.message.reply_text(
                "The Poolkeeper missed that — try again in a moment.")
        return
    await update.message.reply_text(
        f"🕯️ The Poolkeeper bows — {amount} Dots flow back into the Pool. "
        f"The gouge feeds the generous. Your Pocket: {r.get('pocket')} Dots.")


async def pool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        a = api_get("/api/admin")
    except ApiError:
        await say_down(update)
        return
    poolv = a.get("pool")
    if poolv is None:
        await update.message.reply_text(
            "🕯️ The Poolkeeper lifts the lamp — the Pool endures, as it always does.")
        return
    out = SUPPLY - poolv
    await update.message.reply_text(
        f"🕯️ The Poolkeeper lifts the lamp:\n\n"
        f"The Pool holds {poolv:,} Dots — {out:,} have gone out into the world.")


async def lore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        first = api_get("/api/npc/lore", {"n": 0})
        total = int(first.get("total") or 1)
        n = datetime.date.today().timetuple().tm_yday % total
        entry = api_get("/api/npc/lore", {"n": n})
    except ApiError:
        await say_down(update)
        return
    await update.message.reply_text(
        f"📚 Sage Zell clears his throat:\n\n{entry.get('entry')}\n\n"
        f"— entry {n + 1} of {total}")


async def match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return
    try:
        r = api_post("/api/npc/match", {"id": pid})
    except ApiError as e:
        if e.status == 0:
            await say_down(update)
        elif e.code == "no_bio":
            await update.message.reply_text(
                "Juno needs your bio card first — /bio takes a minute, and it's 16+.")
        else:
            await update.message.reply_text(
                "Juno's compass is spinning — try again in a moment.")
        return
    matches = r.get("matches") or []
    if not matches:
        await update.message.reply_text(
            "Juno squints at the crossroads... no matches yet. Fatten up your "
            "/bio — or check back as the clan grows.")
        return
    lines = []
    for m in matches:
        lines.append(f"• *{m.get('name')}* — {m.get('region', '')}\n"
                     f"  {m.get('bio', '')}")
    await update.message.reply_text(
        "🧭 Juno points down the road:\n\n" + "\n\n".join(lines),
        parse_mode="Markdown")


# --------------------------------------------------------------------------
# /bio — self-published bio card, 16+ age gate first, one-tap revoke
# --------------------------------------------------------------------------
async def bio_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return ConversationHandler.END
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return ConversationHandler.END
    kb = [[
        InlineKeyboardButton("✅ Yes, I'm 16 or older", callback_data="bio:yes"),
        InlineKeyboardButton("No, not yet", callback_data="bio:no"),
    ]]
    await update.message.reply_text(
        "Bio cards are 16+ — are you 16 or older?",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return BIO_AGE


async def bio_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data != "bio:yes":
        # Kind stop. Nothing stored, nothing sent to the engine.
        await q.edit_message_text(
            "No worries at all — no card, no questions, nothing stored. "
            "The door stays open. 💛")
        return ConversationHandler.END
    await q.edit_message_text(
        "Lovely. Four lines, one message — like this:\n\n"
        "into: night markets and strange maps\n"
        "interests: zorbology, busking, dumplings\n"
        "offers: I can teach you three chords\n"
        "wants: someone to trade stories with\n\n"
        "Your words, your card — nothing leaves the game.")
    return BIO_LINES


async def bio_lines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = [ln.strip() for ln in (update.message.text or "").splitlines()
           if ln.strip()][:4]
    fields = []
    for ln in raw:
        fields.append(ln.split(":", 1)[1].strip() if ":" in ln else ln)
    while len(fields) < 4:
        fields.append("")
    context.user_data["bio_fields"] = [f[:140] for f in fields]
    await update.message.reply_text(
        "And roughly where in the world? (coarse — a region, a coast, a city. "
        "Nothing precise.)")
    return BIO_REGION


async def bio_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    region = (update.message.text or "").strip()[:40]
    into, interests, offers, wants = context.user_data.get("bio_fields", [""] * 4)
    try:
        pid = await engine_id(update, context)
        api_post("/api/bio", {
            "id": pid, "into": into, "interests": interests,
            "offers": offers, "wants": wants, "region": region,
            "age16": True,
        })
    except ApiError as e:
        if e.status == 0:
            await update.message.reply_text(ENGINE_DOWN)
        else:
            await update.message.reply_text(
                "That card wouldn't stick — try again in a moment.")
        return ConversationHandler.END
    await update.message.reply_text(
        "✨ Your bio card is up — you're on the map. "
        "/match when you're curious who else is around.")
    return ConversationHandler.END


async def bio_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("No card, nothing stored. 💛")
    return ConversationHandler.END


async def bioclear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return
    try:
        api_post("/api/bio/clear", {"id": pid})
    except ApiError as e:
        if e.status == 0:
            await say_down(update)
        else:
            await update.message.reply_text(
                "That wouldn't come down — try again in a moment.")
        return
    await update.message.reply_text("Your card is down, your dot is off the map. 🌙")


# --------------------------------------------------------------------------
# /passport — the Cosmic Passport is the player's PROFILE, rendered from
# Josh's 2022 template. The face is the player's own choice (founder,
# 2026-10-19): their photo, a chibi, or the deterministic avatar.
# Flat handlers + user_data state (no ConversationHandler) so the
# front-page menu drives the same flows. Face choices persist in
# data/faces/ so the passport is stable across restarts.
# --------------------------------------------------------------------------
CHIBI_LABELS = [
    "Dylan", "Alexander", "Toby", "Hunter", "Red Cap",
    "Puffer", "Shades", "Peace", "Peace Crop",
]
CHIBI_FILES = [
    "chibi-dylan-beanie-05.jpg",
    "chibi-alexander-07.jpg",
    "chibi-toby-08.jpg",
    "chibi-hunter-09.jpg",
    "chibi-red-cap-10.jpg",
    "chibi-red-puffer-glasses-17.jpg",
    "chibi-sunglasses-cross-06.jpg",
    "chibi-peace-sign-girl-crop-04.jpg",
    "chibi-peace-sign-girl-01.jpg",
]


def _passport_face_store():
    """The face-choice store, or None when the renderer isn't available."""
    if render_passport is None:
        return None, None
    try:
        import passport_render as _pr
        return _pr.save_face_choice, _pr.load_face_choice
    except Exception:
        return None, None


async def _render_and_send_passport(msg, context, tg_id, pid):
    """Fetch profile data, render the passport image, send it. Never raises
    into the caller — returns False when the press jams."""
    if render_passport is None:
        await msg.reply_text(
            "🛂 The passport press is being inked — try again in a moment.")
        return False
    try:
        p = await engine_player(tg_id, context)
    except ApiError:
        await msg.reply_text(ENGINE_DOWN)
        return False
    if not p:
        await msg.reply_text(NOT_JOINED)
        return False
    _save, _load = _passport_face_store()
    face = _load(pid) if _load else None
    worlds = []
    if generosity_ai is not None:
        try:
            worlds = generosity_ai.get_worlds_for(pid)
        except Exception:
            worlds = []
    try:
        buf = render_passport(p["name"], p.get("joined_at"), pid,
                              face=face, dots=p.get("pocket"), worlds=worlds)
    except Exception:
        await msg.reply_text(
            "🛂 The passport press jammed — try again in a moment.")
        return False
    dots = p.get("pocket")
    try:
        dots_line = f"{int(dots):,} Dots"
    except Exception:
        dots_line = "— Dots"
    caption = (
        "🛂 *Your Cosmic Passport* — certified by the Order of Zorbs.\n\n"
        f"*{p['name']}* of the Clan · {dots_line} · "
        f"{len(worlds)} world{'s' if len(worlds) != 1 else ''}.\n\n"
        "Zorbs passports are your way to discover new worlds — energy "
        "passports, and everyone is entitled to their free one. The "
        "multiverse and universes are open to all beings. Everyone is "
        "equal. Everyone unique."
    )
    await msg.reply_photo(photo=buf, caption=caption, parse_mode="Markdown")
    return True


def _face_choice_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 My own photo",
                             callback_data="passport:face:photo")],
        [InlineKeyboardButton("🎭 Pick a chibi",
                             callback_data="passport:face:chibi")],
        [InlineKeyboardButton("🎲 Surprise me (avatar)",
                             callback_data="passport:face:avatar")],
    ])


async def _send_face_choice(msg, context, pid):
    """The face-choice prompt. Shared by /passport and the front page."""
    _save, _load = _passport_face_store()
    current = (_load(pid) or {}).get("kind") if _load else None
    note = {"photo": "your photo", "chibi": "a chibi"}.get(current,
                                                           "your avatar")
    await msg.reply_text(
        "🛂 *Your Cosmic Passport* — who's on it?\n\n"
        f"Right now: {note}. Your face, your choice — "
        "change it anytime with /passport.",
        reply_markup=_face_choice_keyboard(),
        parse_mode="Markdown",
    )


async def passport_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        p = await engine_player(update.effective_user.id, context)
    except ApiError:
        await say_down(update)
        return
    if not p:
        await update.message.reply_text(NOT_JOINED)
        return
    if render_passport is None:
        await update.message.reply_text(
            "🛂 The passport press is being inked — try again in a moment.")
        return
    context.user_data["pending_wish"] = False
    context.user_data["passport_pid"] = p["id"]
    context.user_data["passport_tg"] = update.effective_user.id
    await _send_face_choice(update.message, context, p["id"])


async def passport_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    which = (q.data or "").split(":")[-1]
    pid = context.user_data.get("passport_pid")
    if not pid:
        try:
            pid = await engine_id(update, context)
        except ApiError:
            await say_down(update)
            return
        if not pid:
            await q.edit_message_text(NOT_JOINED)
            return
        context.user_data["passport_pid"] = pid
    if which == "photo":
        context.user_data["passport_awaiting_photo"] = True
        await q.edit_message_text(
            "📷 Send me the photo for your passport — one clear shot, "
            "face forward works best.")
        return
    if which == "chibi":
        kb = []
        row = []
        for i, label in enumerate(CHIBI_LABELS):
            row.append(InlineKeyboardButton(
                label, callback_data=f"passport:chibi:{i}"))
            if len(row) == 3:
                kb.append(row)
                row = []
        if row:
            kb.append(row)
        await q.edit_message_text(
            "🎭 Pick your chibi:",
            reply_markup=InlineKeyboardMarkup(kb))
        return
    # avatar — the deterministic face
    _save, _load = _passport_face_store()
    if _save:
        _save(pid, {"kind": "avatar"})
    tg_id = context.user_data.get("passport_tg", update.effective_user.id)
    await q.edit_message_text("🎲 The wheel chooses…")
    await _render_and_send_passport(q.message, context, tg_id, pid)


async def passport_chibi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    pid = context.user_data.get("passport_pid")
    if not pid:
        await q.edit_message_text("Your passport blew away — /passport again?")
        return
    try:
        idx = int((q.data or "").split(":")[-1])
        fname = CHIBI_FILES[idx]
    except Exception:
        await q.edit_message_text("Your passport blew away — /passport again?")
        return
    _save, _load = _passport_face_store()
    if _save and not _save(pid, {"kind": "chibi", "file": fname}):
        await q.edit_message_text(
            "🛂 That chibi slipped away — try /passport again?")
        return
    tg_id = context.user_data.get("passport_tg", update.effective_user.id)
    await q.edit_message_text(f"🎭 {CHIBI_LABELS[idx]} it is…")
    await _render_and_send_passport(q.message, context, tg_id, pid)


async def passport_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Top-level photo catcher. Ignores photos unless we're awaiting one —
    # never steals input from other flows.
    if not context.user_data.get("passport_awaiting_photo"):
        return
    pid = context.user_data.get("passport_pid")
    if not pid:
        context.user_data["passport_awaiting_photo"] = False
        return
    tg_id = context.user_data.get("passport_tg", update.effective_user.id)
    try:
        tg_file = await update.message.photo[-1].get_file()
        buf = bytes(await tg_file.download_as_bytearray())
    except Exception:
        await update.message.reply_text(
            "🛂 Couldn't fetch that photo — try another?")
        return
    _save, _load = _passport_face_store()
    if not _save or not _save(pid, {"kind": "photo"}, photo_bytes=buf):
        await update.message.reply_text(
            "🛂 That photo won't do (too big or unreadable) — try another?")
        return
    context.user_data["passport_awaiting_photo"] = False
    await update.message.reply_text("📷 Lovely — pressing your passport…")
    await _render_and_send_passport(update.message, context, tg_id, pid)


# --------------------------------------------------------------------------
# FRONT PAGE — big tappable buttons. Nobody needs to know slash commands.
# /start (returning players) and the end of the join flow land here.
# --------------------------------------------------------------------------
HOME_TEXT = "🌀 The portal is open. The universe is yours. What will you bring?"


def home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Let's play", callback_data="home:play")],
        [InlineKeyboardButton("✨ Create a world", callback_data="home:wish")],
        [InlineKeyboardButton("💱 Trade", callback_data="home:trade")],
        [InlineKeyboardButton("👥 Find my people", callback_data="home:people")],
        [InlineKeyboardButton("🌍 Explore worlds", url=LIVING_MAP_URL)],
        [InlineKeyboardButton("🛂 Passport", callback_data="home:passport")],
    ])


async def home_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    which = (q.data or "").split(":")[-1]
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return
    if not pid:
        await q.edit_message_text(NOT_JOINED)
        return
    name = update.effective_user.first_name or "traveler"
    context.user_data["pending_wish"] = False
    if which == "play":
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🌀 Play MADHOUSE", web_app=WebAppInfo(url=WEBAPP_URL)),
        ]])
        await q.message.reply_text(
            "The door's open — and it's already *you* on the other side. "
            "No passwords, no forms; your Telegram self is your player self.\n\n"
            "Tap below. Your Pocket, the keepers, and the living map are waiting. 🌀",
            reply_markup=kb,
            parse_mode="Markdown",
        )
        return
    if which == "wish":
        context.user_data["pending_wish"] = True
        await q.edit_message_text(
            "🌍 What world do you dream of?\n\n"
            "Just reply with your wish — plain words, no commands needed. "
            "Say what you see: a lagoon, a city, a quiet forest…")
        return
    if which == "worlds":
        if generosity_ai is None:
            await q.message.reply_text(
                "Generosity is still waking up — give her a minute.")
            return
        try:
            reply = generosity_ai.handle_command("/worlds", pid, name)
        except Exception:
            await say_down(update)
            return
        await q.message.reply_text(reply, parse_mode="Markdown")
        return
    if which == "passport":
        if render_passport is None:
            await q.message.reply_text(
                "🛂 The passport press is being inked — try again in a moment.")
            return
        context.user_data["passport_pid"] = pid
        context.user_data["passport_tg"] = update.effective_user.id
        await _send_face_choice(q.message, context, pid)
        return


async def pending_wish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Their next text message becomes the wish. Registered LAST so active
    conversations (gift/teleport) always get first dibs on input."""
    if not context.user_data.get("pending_wish"):
        return
    context.user_data["pending_wish"] = False
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return
    if generosity_ai is None:
        await update.message.reply_text(
            "Generosity is still waking up — give her a minute and wish again.")
        return
    text = (update.message.text or "").strip()
    if not text:
        return
    name = update.effective_user.first_name or "traveler"
    await update.message.reply_text("🌍 Got it — growing your world…")
    try:
        reply = generosity_ai.handle_command("/wish " + text, pid, name)
    except Exception:
        await say_down(update)
        return
    await update.message.reply_text(reply, parse_mode="Markdown")


# --------------------------------------------------------------------------
# /giftcard — fold Dots into a GIFT-XXXX-XXXX card. /redeem unfolds one.
# --------------------------------------------------------------------------
async def giftcard_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return ConversationHandler.END
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return ConversationHandler.END
    context.user_data["giftcard_from"] = pid
    await update.message.reply_text(
        "🎁 A gift card — Dots folded into a card, sealed, ready to hand to "
        "anyone.\n\nHow many Dots go inside?")
    return GIFTCARD_AMOUNT


async def giftcard_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int((update.message.text or "").strip())
    except ValueError:
        amount = 0
    if amount <= 0:
        await update.message.reply_text(
            "Whole Dots, more than zero — how many go inside?")
        return GIFTCARD_AMOUNT
    context.user_data["giftcard_amount"] = amount
    kb = [[
        InlineKeyboardButton("🎁 Yes, fold it", callback_data="giftcard:yes"),
        InlineKeyboardButton("Never mind", callback_data="giftcard:no"),
    ]]
    await update.message.reply_text(
        f"Fold *{amount} Dots* into a gift card?",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return GIFTCARD_CONFIRM


async def giftcard_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data != "giftcard:yes":
        await q.edit_message_text(
            "No card folded. The Dots stay exactly where they are. 💛")
        return ConversationHandler.END
    try:
        r = api_post("/api/giftcard/issue", {
            "id": context.user_data.get("giftcard_from"),
            "amount": context.user_data.get("giftcard_amount"),
        })
    except ApiError as e:
        if e.status == 0:
            await q.edit_message_text(ENGINE_DOWN)
        elif e.code == "insufficient":
            await q.edit_message_text(
                "Not enough Dots in your Pocket for that card — check /pocket.")
        else:
            await q.edit_message_text(
                "The card wouldn't fold — try again in a moment.")
        return ConversationHandler.END
    code = r.get("code", "")
    await q.edit_message_text(
        f"🎁✨ *{code}* ✨🎁\n\n"
        f"{r.get('amount')} Dots, folded and sealed.\n\n"
        "Hand this code to anyone — in chat, on a napkin, shouted across a "
        f"diner. They redeem it with:\n`/redeem {code}`\n\n"
        "No expiry. No fees. The Dots are real and waiting.\n"
        f"Your Pocket: {r.get('pocket')} Dots.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def giftcard_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("No card folded. 💛")
    return ConversationHandler.END


async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = " ".join(context.args or []).strip().upper()
    if not code:
        await update.message.reply_text(
            "Send me the code, like: /redeem GIFT-XXXX-XXXX")
        return
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return
    try:
        r = api_post("/api/giftcard/redeem", {"id": pid, "code": code})
    except ApiError as e:
        if e.status == 0:
            await say_down(update)
        elif e.code == "bad_code":
            await update.message.reply_text(
                "That code doesn't open anything — check it and try again.")
        elif e.code == "already_redeemed":
            await update.message.reply_text(
                "That card was already unfolded — its Dots found their home.")
        else:
            await update.message.reply_text(
                "The card wouldn't unfold — try again in a moment.")
        return
    await update.message.reply_text(
        f"🎉 The card unfolds — *{r.get('amount')} Dots*, "
        f"a gift from *{r.get('from_name')}*.\n\n"
        f"Your Pocket: {r.get('pocket')} Dots. 💛",
        parse_mode="Markdown",
    )


# --------------------------------------------------------------------------
# /claim — spin of the wheel: claim your procedural world + deed.
# (The old quest-claim moved to /quest.)
# --------------------------------------------------------------------------
async def world_claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return
    try:
        r = api_post("/api/world/claim", {"id": pid})
    except ApiError:
        await say_down(update)
        return
    again = ("" if r.get("is_new")
             else "_You've spun before — the wheel remembers. "
                  "This is still your world._\n\n")
    await update.message.reply_text(
        f"🎡 The wheel spins... slows... stops.\n\n{again}"
        f"🗺️ *{r.get('world_name')}*\n"
        f"📍 {r.get('coordinates')}\n"
        f"🌱 Inhabitants: {r.get('inhabitant_seed')}\n"
        f"👥 Population: {r.get('population'):,}\n\n"
        f"🧾 Deed: `{r.get('card_id')}` — written in the registry, yours.\n\n"
        "This world is yours to name, build, and invite people into. "
        "The deed is the card; the card is the deed.",
        parse_mode="Markdown",
    )


# --------------------------------------------------------------------------
# /wish + /worlds — Generosity, the clan AI. She hears the wish behind
# the words and grows a world with the wisher. LLM when configured,
# rules-seeded otherwise; never crashes, never takes the bot down.
# --------------------------------------------------------------------------
async def wish_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["pending_wish"] = False
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return
    if generosity_ai is None:
        await update.message.reply_text(
            "Generosity is still waking up — give her a minute and wish again.")
        return
    text = update.message.text or ""
    name = (update.effective_user.first_name or "traveler")
    try:
        reply = generosity_ai.handle_command(text, pid, name)
    except Exception:
        await say_down(update)
        return
    await update.message.reply_text(reply, parse_mode="Markdown")


# --------------------------------------------------------------------------
# /map — the door to the Living Map. Visible to players and non-players
# alike: the spectacle is the invitation. You play in the bot; you shine
# on the map.
# --------------------------------------------------------------------------
LIVING_MAP_URL = "https://muse.ai/s/the-living-map-fd6tyxlsxlxhx0xd"


async def map_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🗺️ *The Living Map* — every world, every light, one spectacle.\n\n"
        f"{LIVING_MAP_URL}\n\n"
        "You play in the bot; you shine on the map.",
        parse_mode="Markdown",
    )


# --------------------------------------------------------------------------
# /talk — sit with the five keepers. Each speaks in their own voice, and
# every action goes through the engine like the standalone commands.
# --------------------------------------------------------------------------
TALK_KEEPERS = [
    ("marlo", "🎒 Marlo"),
    ("pippa", "🏷️ Pippa"),
    ("poolkeeper", "🕯️ Poolkeeper"),
    ("zell", "📚 Sage Zell"),
    ("juno", "🧭 Juno"),
]


async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return
    kb = [[InlineKeyboardButton(label, callback_data=f"talk:{key}")]
          for key, label in TALK_KEEPERS]
    await update.message.reply_text(
        "The five keepers are around the fire. Who do you sit with?",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def talk_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    which = (q.data or "").split(":", 1)[1] if ":" in (q.data or "") else ""
    try:
        pid = await engine_id(q, context)
    except ApiError:
        await q.edit_message_text(ENGINE_DOWN)
        return
    if not pid:
        await q.edit_message_text(NOT_JOINED)
        return
    if which == "marlo":
        try:
            qs = api_get("/api/quests").get("quests", {})
        except ApiError:
            await q.edit_message_text(ENGINE_DOWN)
            return
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(v["label"], callback_data=f"claim:{k}")
            for k, v in qs.items()]])
        lines = ["🎒 *Marlo, Keeper of Small Kindnesses*, swings her satchel open.",
                 "\"Pick one, love — the pick is the thing. Three Dots for the doing, "
                 "one a day, no strings.\"", ""]
        lines += [f"{v['label']} — {v['description']}" for v in qs.values()]
        await q.edit_message_text("\n".join(lines), reply_markup=kb,
                                  parse_mode="Markdown")
    elif which == "pippa":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🍫 Chocolate — 10 Dots", callback_data="talkbuy:choc")],
            [InlineKeyboardButton("👕 T-shirt — 100 Dots", callback_data="talkbuy:shirt")],
            [InlineKeyboardButton("🚒 Fire engine — 200 Dots", callback_data="talkbuy:engine")],
        ])
        await q.edit_message_text(
            "🏷️ *Pippa Pricelist* polishes the counter. \"Game goods, Dots only, "
            "priced fair and square. The Price List is the reference — ask above "
            "it and the excess becomes the Donation.\"\n\n"
            "What'll it be?",
            reply_markup=kb, parse_mode="Markdown")
    elif which == "poolkeeper":
        try:
            poolv = api_get("/api/admin").get("pool")
        except ApiError:
            poolv = None
        pool_line = (f"The Pool holds {poolv:,} Dots. " if poolv is not None else "")
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(f"{a} Dots", callback_data=f"talkdonate:{a}")
            for a in (10, 25, 50, 100)]])
        await q.edit_message_text(
            "🕯️ *The Poolkeeper* lifts the lamp. \"Every Dot begins in the Pool, "
            "and the generous pour them back. " + pool_line + "Give what you like "
            "— the gouge feeds the generous.\"",
            reply_markup=kb, parse_mode="Markdown")
    elif which == "zell":
        try:
            first = api_get("/api/npc/lore", {"n": 0})
            total = int(first.get("total") or 1)
            import datetime as _dt
            n = _dt.date.today().timetuple().tm_yday % total
            entry = api_get("/api/npc/lore", {"n": n})
        except ApiError:
            await q.edit_message_text(ENGINE_DOWN)
            return
        await q.edit_message_text(
            f"📚 *Sage Zell* clears his throat from the Quiet Stacks. "
            f"\"A page of warm, mischievous Zorbology lore. Occasionally true.\"\n\n"
            f"{entry.get('entry')}")
    elif which == "juno":
        try:
            r = api_post("/api/npc/match", {"id": pid})
        except ApiError as e:
            if e.code == "no_bio":
                await q.edit_message_text(
                    "🧭 *Juno the Matcher* studies you at the Crossroads. \"I read "
                    "bio cards, love — what people offer and what they want. "
                    "Yours isn't written yet. /bio takes a minute, and it's 16+.\"")
            else:
                await q.edit_message_text(
                    "Juno's compass is spinning — try again in a moment.")
            return
        matches = r.get("matches") or []
        if not matches:
            await q.edit_message_text(
                "🧭 *Juno the Matcher* squints at the crossroads... \"No rhymes yet. "
                "Fatten up your /bio — or check back as the clan grows.\"")
            return
        lines = ["🧭 *Juno the Matcher* points down the road:"]
        for m in matches:
            lines.append(f"• *{m.get('name')}* — {m.get('region', '')}\n"
                         f"  {m.get('bio', '')}")
        await q.edit_message_text("\n\n".join(lines), parse_mode="Markdown")
    else:
        await q.edit_message_text("The keeper stepped away — /talk to try again.")


async def talkbuy_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    item = (q.data or "").split(":", 1)[1] if ":" in (q.data or "") else ""
    labels = {"choc": "🍫 Chocolate bar", "shirt": "👕 T-shirt",
              "engine": "🚒 Red toy fire engine"}
    prices = {"choc": 10, "shirt": 100, "engine": 200}
    if item not in labels:
        await q.edit_message_text("Pippa squints — that shelf is empty.")
        return
    try:
        pid = await engine_id(q, context)
    except ApiError:
        await q.edit_message_text(ENGINE_DOWN)
        return
    if not pid:
        await q.edit_message_text(NOT_JOINED)
        return
    try:
        r = api_post("/api/npc/buy",
                     {"id": pid, "npc_token": await _pippa_token(),
                      "item": item})
    except ApiError as e:
        if e.status == 0:
            await q.edit_message_text(ENGINE_DOWN)
        elif e.code == "insufficient":
            await q.edit_message_text(
                "Not enough Dots in your Pocket for that one — check /pocket.")
        else:
            await q.edit_message_text(
                "Pippa's counter is jammed — try again in a moment.")
        return
    await q.edit_message_text(
        f"🏷️ Pippa slides the {labels[item]} across the counter — "
        f"{prices[item]} Dots. Your Pocket: {r.get('pocket')} Dots.")


async def talkdonate_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        amount = int((q.data or "").split(":", 1)[1])
    except (ValueError, IndexError):
        amount = 0
    if amount <= 0:
        await q.edit_message_text("The Poolkeeper missed that — /talk to try again.")
        return
    try:
        pid = await engine_id(q, context)
    except ApiError:
        await q.edit_message_text(ENGINE_DOWN)
        return
    if not pid:
        await q.edit_message_text(NOT_JOINED)
        return
    try:
        r = api_post("/api/npc/donate", {"id": pid, "amount": amount})
    except ApiError as e:
        if e.status == 0:
            await q.edit_message_text(ENGINE_DOWN)
        elif e.code == "insufficient":
            await q.edit_message_text(
                "Not enough Dots in your Pocket for that one — check /pocket.")
        else:
            await q.edit_message_text(
                "The Poolkeeper missed that — try again in a moment.")
        return
    await q.edit_message_text(
        f"🕯️ The Poolkeeper bows — {amount} Dots flow back into the Pool. "
        f"The gouge feeds the generous. Your Pocket: {r.get('pocket')} Dots.")


# --------------------------------------------------------------------------
# /teleport — pocket-to-pocket, with the ceremony: funds that arrive
# before you do. Same engine rails as /trade, different poetry.
# --------------------------------------------------------------------------
async def teleport_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return ConversationHandler.END
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return ConversationHandler.END
    context.user_data["teleport_from"] = pid
    await update.message.reply_text(
        "🌀 Teleport — pocket to pocket. The Dots dissolve here... "
        "and arrive before you do.\n\nHow many Dots are making the jump?")
    return TELEPORT_AMOUNT


async def teleport_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int((update.message.text or "").strip())
    except ValueError:
        amount = 0
    if amount <= 0:
        await update.message.reply_text(
            "Whole Dots, more than zero — how many are jumping?")
        return TELEPORT_AMOUNT
    context.user_data["teleport_amount"] = amount
    await update.message.reply_text(
        "Whose token? Send the 6-character trade token "
        "(yours is under /token).")
    return TELEPORT_TOKEN


async def teleport_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = (update.message.text or "").strip().upper()
    if not token:
        await update.message.reply_text("I need the 6-character token — whose?")
        return TELEPORT_TOKEN
    context.user_data["teleport_token"] = token
    context.user_data["teleport_name"] = npc_name_for_token(token)
    who = (f"*{context.user_data['teleport_name']}* (token {token})"
           if context.user_data["teleport_name"]
           else f"the bearer of token {token}")
    kb = [[
        InlineKeyboardButton("🌀 Yes, teleport", callback_data="teleport:yes"),
        InlineKeyboardButton("Never mind", callback_data="teleport:no"),
    ]]
    await update.message.reply_text(
        f"Send {context.user_data['teleport_amount']} Dots to {who}? "
        "They'll arrive before you do. ✨",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return TELEPORT_CONFIRM


async def teleport_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data != "teleport:yes":
        await q.edit_message_text(
            "The jump is cancelled. Nothing dissolved, nothing arrived. 💛")
        return ConversationHandler.END
    try:
        r = api_post("/api/trade", {
            "from_id": context.user_data.get("teleport_from"),
            "to_token": context.user_data.get("teleport_token"),
            "amount": context.user_data.get("teleport_amount"),
        })
    except ApiError as e:
        if e.status == 0:
            await q.edit_message_text(ENGINE_DOWN)
        elif e.code == "unknown_token":
            await q.edit_message_text(
                "Hmm — no player carries that token. Check it and /teleport again.")
        elif e.code == "self_trade":
            await q.edit_message_text(
                "Teleporting to yourself just folds space into a loop — "
                "pick someone else. 😄")
        elif e.code == "insufficient":
            await q.edit_message_text(
                "Not enough Dots in your Pocket for that jump — check /pocket.")
        else:
            await q.edit_message_text(
                "The jump fizzled — nothing moved. Try again in a moment.")
        return ConversationHandler.END
    await q.edit_message_text(
        f"🌀 Gone from here — {context.user_data.get('teleport_amount')} Dots to "
        f"*{r.get('to_name', 'them')}*... and they've already arrived.\n\n"
        f"_Funds that arrive before you do._ ✨\n"
        f"Your Pocket: {r.get('from_pocket')} Dots.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def teleport_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("The jump is cancelled. 💛")
    return ConversationHandler.END


# --------------------------------------------------------------------------
# /help — the map of everything the bot can do.
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# Kindness sessions — the 15-minute session flow (2026-10-17).
# LOBBY -> SEEK -> SIMON -> CONNECT -> TAG -> VOTE -> CLOSED.
# Every phase change is a small ceremony (loading is story). Sessions move
# no Dots — recognition is attestation in the ledger, never currency.
# --------------------------------------------------------------------------
PHASE_CEREMONY = {
    "SEEK": ("🔍 *The SEEK begins.*\n\n"
             "What do you need? What can you give? One line each:\n"
             "`/need a ladder for Saturday`\n"
             "`/offer I can cook for six`\n\n"
             "Nobody is only a giver or only a receiver. "
             "When the board is full, the host walks on: /session next"),
    "SIMON": ("✋ *Simon says.*\n\n"
              "Host — name the one act everyone does together:\n"
              "`/simon everyone messages one elder today`\n\n"
              "Then each player checks in: /done"),
    "CONNECT": ("🔗 *The pairings are made.*\n\n"
                "Needs have met offers — find your match on the /board "
                "and say hello. When every hello is said, the host walks "
                "on: /session next"),
    "TAG": ("🏷️ *The passing begins — you're it.*\n\n"
            "Tag someone in the circle with a kindness:\n"
            "`/tag Maya shared her ladder with me`\n\n"
            "Whoever's tagged passes it on. The chain remembers every hop: "
            "/chains"),
    "VOTE": ("🗳️ *The circle decides.*\n\n"
             "Host — open the closing question:\n"
             "`/vote open Meet again tomorrow? | Yes | No`\n\n"
             "Everyone answers with `/vote 1` or `/vote 2`. "
             "The host closes it: /vote close"),
}
AGE_LINE = ("Needs and offers are for players 16 and up — no exceptions. "
            "If that's you, say it once: /session ageok — then re-send "
            "your line. 💛")


def _sess_code(context, idx=0):
    args = context.args or []
    return args[idx].strip().upper() if len(args) > idx else ""


async def _sess_player(update, context):
    """Engine player id or None (with the kind reply already sent)."""
    try:
        pid = await engine_id(update, context)
    except ApiError:
        await say_down(update)
        return None
    if not pid:
        await update.message.reply_text(NOT_JOINED)
        return None
    return pid


async def _sess_current(context):
    return (context.user_data.get("session_id") or "").upper() or None


async def _sess_api(update, context, method, path, payload=None, params=None):
    """Engine call with the standard kind-failure mapping. None = replied."""
    try:
        if method == "GET":
            return api_get(path, params)
        return api_post(path, payload)
    except ApiError as e:
        if e.status == 0:
            await say_down(update)
        elif e.code == "unknown_session":
            await update.message.reply_text(
                "No session by that name — check the code and try again.")
        elif e.code == "session_closed":
            await update.message.reply_text(
                "That session has closed — the circle is complete. 🌙")
        elif e.code == "not_in_session":
            await update.message.reply_text(
                "Join the session first: /session join S-0001")
        elif e.code == "not_host":
            await update.message.reply_text(
                "Only the host walks the circle onward. 💛")
        elif e.code == "wrong_phase":
            await update.message.reply_text(
                e.payload.get("detail") or "Not in this beat of the session.")
        elif e.code == "too_late":
            await update.message.reply_text(
                "The session's past the gathering — catch the next one. 💛")
        elif e.code == "under_16":
            await update.message.reply_text(AGE_LINE)
        else:
            await update.message.reply_text(
                "That wouldn't go through — try again in a moment.")
        return None


async def session_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sub = (context.args[0].lower() if context.args else "status")

    if sub == "start":
        pid = await _sess_player(update, context)
        if not pid:
            return
        r = await _sess_api(update, context, "POST", "/api/session/start",
                            {"id": pid})
        if not r:
            return
        sid = r["session_id"]
        context.user_data["session_id"] = sid
        await update.message.reply_text(
            f"🚪 *The doors open — session {sid} begins.*\n\n"
            "A kindness session: about fifteen minutes, start to finish. "
            "The circle gathers, names what it needs and what it can give, "
            "does one thing together, pairs up, passes kindnesses along, "
            "and closes with a decision.\n\n"
            f"Bring people in: `/session join {sid}`\n\n"
            "When everyone's here, you walk it onward: /session next",
            parse_mode="Markdown")
        return

    if sub == "join":
        code = _sess_code(context, 1)
        if not code:
            await update.message.reply_text(
                "Give me the session code: `/session join S-0001`",
                parse_mode="Markdown")
            return
        pid = await _sess_player(update, context)
        if not pid:
            return
        r = await _sess_api(update, context, "POST", "/api/session/join",
                            {"id": pid, "session_id": code})
        if not r:
            return
        context.user_data["session_id"] = r["session_id"]
        await update.message.reply_text(
            f"🚪 *You're in — {r['session_id']}.*\n\n"
            f"The circle holds {r['players']} so far. Settle in; the host "
            "walks it onward when everyone's here.",
            parse_mode="Markdown")
        return

    if sub == "next":
        pid = await _sess_player(update, context)
        if not pid:
            return
        sid = await _sess_current(context)
        if not sid:
            await update.message.reply_text(
                "No session in mind — `/session join S-0001` first.",
                parse_mode="Markdown")
            return
        r = await _sess_api(update, context, "POST", "/api/session/next",
                            {"id": pid, "session_id": sid})
        if not r:
            return
        phase = r["phase"]
        msg = PHASE_CEREMONY.get(phase, "")
        if phase == "CONNECT":
            # The pairings happen the moment the beat lands — no dead air.
            pr = await _sess_api(update, context, "POST",
                                 "/api/session/connect",
                                 {"id": pid, "session_id": sid})
            if pr and pr.get("pairings"):
                lines = "\n".join(
                    f"• *{p['need_by']}* ↔ *{p['offer_by']}* — {p['reason']}"
                    for p in pr["pairings"])
                msg += f"\n\n{lines}"
            elif pr:
                msg += ("\n\nNo matches this round — the board stays open "
                        "for hellos anyway.")
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    if sub == "close":
        pid = await _sess_player(update, context)
        if not pid:
            return
        sid = await _sess_current(context)
        if not sid:
            await update.message.reply_text(
                "No session in mind — `/session join S-0001` first.",
                parse_mode="Markdown")
            return
        r = await _sess_api(update, context, "POST", "/api/session/close",
                            {"id": pid, "session_id": sid})
        if not r:
            return
        sm = r["summary"]
        await update.message.reply_text(
            f"🌙 *The circle is complete — {sid} closes.*\n\n"
            f"👥 {sm['players']} gathered · "
            f"🔍 {sm['needs']} needs, {sm['offers']} offers\n"
            f"✋ {sm['checkins']} did the deed together · "
            f"🔗 {sm['pairings']} pairings\n"
            f"🏷️ {sm['chains']} kindness chains, {sm['hops']} passes · "
            f"🗳️ {sm['votes']} votes cast\n\n"
            "Nothing was bought, nothing was sold. What was made here was "
            "each other. Until the next one. 💛",
            parse_mode="Markdown")
        context.user_data.pop("session_id", None)
        return

    if sub == "ageok":
        pid = await _sess_player(update, context)
        if not pid:
            return
        r = await _sess_api(update, context, "POST", "/api/session/ageok",
                            {"id": pid})
        if not r:
            return
        await update.message.reply_text(
            "Noted — you're in the 16+ circle for needs and offers. "
            "Re-send your line. 💛")
        return

    # status (default)
    code = _sess_code(context, 1) or await _sess_current(context)
    if not code:
        await update.message.reply_text(
            "Start one: /session start — or step into one: "
            "`/session join S-0001`",
            parse_mode="Markdown")
        return
    r = await _sess_api(update, context, "GET", "/api/session/status",
                        params={"session_id": code})
    if not r:
        return
    context.user_data["session_id"] = r["session_id"]
    names = ", ".join(p["name"] for p in r["players"][:8])
    more = f" (+{r['player_count'] - 8} more)" if r["player_count"] > 8 else ""
    vote = r.get("vote")
    vote_line = ""
    if vote:
        opts = "\n".join(
            f"  {i + 1}. {o} — {c}"
            for i, (o, c) in enumerate(zip(vote["options"],
                                           vote["counts"])))
        state = "closed" if vote["closed"] else "open"
        vote_line = (f"\n🗳️ *{vote['question']}* ({state})\n{opts}\n"
                     f"  {vote['total']} votes")
    act = f"\n✋ Act: *{r['simon_act']}* ({r['checkins']} checked in)" \
        if r.get("simon_act") else ""
    await update.message.reply_text(
        f"🚪 *Session {r['session_id']}* — {r['phase']}\n"
        f"Host: {r['host']} · {r['player_count']} in the circle\n"
        f"{names}{more}\n\n"
        f"🔍 {r['needs']} needs · {r['offers']} offers · "
        f"🔗 {r['pairings']} pairings\n"
        f"🏷️ {r['chains']} chains, {r['hops']} passes"
        f"{act}{vote_line}",
        parse_mode="Markdown")


async def need_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args or []).strip()
    if not text:
        await update.message.reply_text(
            "Say what you need — one line: `/need a ladder for Saturday`",
            parse_mode="Markdown")
        return
    pid = await _sess_player(update, context)
    if not pid:
        return
    sid = await _sess_current(context)
    if not sid:
        await update.message.reply_text(
            "Join a session first: `/session join S-0001`",
            parse_mode="Markdown")
        return
    r = await _sess_api(update, context, "POST", "/api/session/need",
                        {"id": pid, "session_id": sid, "text": text})
    if not r:
        return
    await update.message.reply_text(
        f"🔍 *Noted — {r['need_id']}.*\n\n"
        f"“{text}”\n\nThe circle will see it. Someone here can probably "
        "help — that's the whole bet.",
        parse_mode="Markdown")


async def offer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args or []).strip()
    if not text:
        await update.message.reply_text(
            "Say what you can do — one line: `/offer I can cook for six`",
            parse_mode="Markdown")
        return
    pid = await _sess_player(update, context)
    if not pid:
        return
    sid = await _sess_current(context)
    if not sid:
        await update.message.reply_text(
            "Join a session first: `/session join S-0001`",
            parse_mode="Markdown")
        return
    r = await _sess_api(update, context, "POST", "/api/session/offer",
                        {"id": pid, "session_id": sid, "text": text})
    if not r:
        return
    await update.message.reply_text(
        f"💛 *On the board — {r['offer_id']}.*\n\n"
        f"“{text}”\n\nGenerosity, logged. Someone's need is about to meet "
        "it.",
        parse_mode="Markdown")


async def simon_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    act = " ".join(context.args or []).strip()
    pid = await _sess_player(update, context)
    if not pid:
        return
    sid = await _sess_current(context)
    if not sid:
        await update.message.reply_text(
            "Join a session first: `/session join S-0001`",
            parse_mode="Markdown")
        return
    if not act:
        r = await _sess_api(update, context, "GET", "/api/session/status",
                            params={"session_id": sid})
        if not r:
            return
        if r.get("simon_act"):
            await update.message.reply_text(
                f"✋ *Simon says:* {r['simon_act']}\n\n"
                f"{r['checkins']} of {r['player_count']} have checked in. "
                "Done yours? /done",
                parse_mode="Markdown")
        else:
            await update.message.reply_text(
                "No act yet — the host names it: "
                "`/simon everyone messages one elder today`",
                parse_mode="Markdown")
        return
    r = await _sess_api(update, context, "POST", "/api/session/simon",
                        {"id": pid, "session_id": sid, "act": act})
    if not r:
        return
    await update.message.reply_text(
        f"✋ *Simon says:* {r['act']}\n\n"
        "Everyone — do the thing, then check in: /done",
        parse_mode="Markdown")


async def done_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = await _sess_player(update, context)
    if not pid:
        return
    sid = await _sess_current(context)
    if not sid:
        await update.message.reply_text(
            "Join a session first: `/session join S-0001`",
            parse_mode="Markdown")
        return
    r = await _sess_api(update, context, "POST", "/api/session/done",
                        {"id": pid, "session_id": sid})
    if not r:
        return
    await update.message.reply_text(
        f"✋ *Done — {r['checkins']} of {r['players']}.*\n\n"
        "One small act, done together. That's the whole technology.",
        parse_mode="Markdown")


async def tag_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "Tag someone with a kindness: `/tag Maya shared her ladder`",
            parse_mode="Markdown")
        return
    pid = await _sess_player(update, context)
    if not pid:
        return
    sid = await _sess_current(context)
    if not sid:
        await update.message.reply_text(
            "Join a session first: `/session join S-0001`",
            parse_mode="Markdown")
        return
    st = await _sess_api(update, context, "GET", "/api/session/status",
                         params={"session_id": sid})
    if not st:
        return
    who = args[0].lstrip("@").lower()
    target = next((p for p in st["players"]
                   if p["name"].lower() == who
                   or p["name"].lower().startswith(who)), None)
    if not target:
        await update.message.reply_text(
            f"No {args[0]} in this circle — tag someone who's here. "
            "(/session status shows the circle.)")
        return
    note = " ".join(args[1:]).strip()
    r = await _sess_api(update, context, "POST", "/api/session/tag",
                        {"id": pid, "session_id": sid,
                         "to": target["id"], "kindness": note})
    if not r:
        return
    await update.message.reply_text(
        f"🏷️ *You're it, {r['holder_name']}!*\n\n"
        f"“{note}”\n\n"
        f"Chain `{r['chain_id']}` — {r['hops']} pass"
        f"{'es' if r['hops'] != 1 else ''} so far. "
        f"{r['holder_name']}, pass it on: /tag someone a kindness",
        parse_mode="Markdown")


async def vote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    sub = (args[0].lower() if args else "")
    pid = await _sess_player(update, context)
    if not pid:
        return
    sid = await _sess_current(context)
    if not sid:
        await update.message.reply_text(
            "Join a session first: `/session join S-0001`",
            parse_mode="Markdown")
        return

    if sub == "open":
        rest = " ".join(args[1:])
        parts = [p.strip() for p in rest.split("|")]
        if len(parts) < 3:
            await update.message.reply_text(
                "Open it like this:\n"
                "`/vote open Meet again tomorrow? | Yes | No`",
                parse_mode="Markdown")
            return
        r = await _sess_api(update, context, "POST",
                            "/api/session/vote/open",
                            {"id": pid, "session_id": sid,
                             "question": parts[0], "options": parts[1:]})
        if not r:
            return
        opts = "\n".join(f"  {i + 1}. {o}"
                         for i, o in enumerate(r["options"]))
        await update.message.reply_text(
            f"🗳️ *The question is open:*\n\n*{r['question']}*\n{opts}\n\n"
            "Answer with `/vote 1`, `/vote 2`… — one voice, one vote.",
            parse_mode="Markdown")
        return

    if sub == "close":
        r = await _sess_api(update, context, "POST",
                            "/api/session/vote/close",
                            {"id": pid, "session_id": sid})
        if not r:
            return
        lines = "\n".join(f"  • {o} — {c}"
                          for o, c in zip(r["options"], r["counts"]))
        await update.message.reply_text(
            f"🗳️ *Counted out loud:*\n\n*{r['question']}*\n{lines}\n\n"
            f"{r['total']} voices. The circle has spoken. 💛",
            parse_mode="Markdown")
        return

    if sub.isdigit():
        r = await _sess_api(update, context, "POST",
                            "/api/session/vote/cast",
                            {"id": pid, "session_id": sid,
                             "choice": int(sub)})
        if not r:
            return
        await update.message.reply_text(
            f"🗳️ *Counted:* {r['choice']}\n\n"
            f"{r['votes']} vote{'s' if r['votes'] != 1 else ''} in so far.",
            parse_mode="Markdown")
        return

    # bare /vote — show the question
    r = await _sess_api(update, context, "GET", "/api/session/status",
                        params={"session_id": sid})
    if not r:
        return
    v = r.get("vote")
    if not v:
        await update.message.reply_text(
            "No vote open — the host opens one in the VOTE round:\n"
            "`/vote open Meet again tomorrow? | Yes | No`",
            parse_mode="Markdown")
        return
    opts = "\n".join(
        f"  {i + 1}. {o} — {c}"
        for i, (o, c) in enumerate(zip(v["options"], v["counts"])))
    await update.message.reply_text(
        f"🗳️ *{v['question']}*\n{opts}\n\n"
        f"{v['total']} votes so far. Answer: `/vote 1`",
        parse_mode="Markdown")


async def board_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = _sess_code(context, 0)
    sid = code if re.fullmatch(r"S-\d{4}", code or "") else None
    sid = sid or await _sess_current(context)
    if not sid:
        await update.message.reply_text(
            "Join a session first: `/session join S-0001`",
            parse_mode="Markdown")
        return
    r = await _sess_api(update, context, "GET", "/api/session/board",
                        params={"session_id": sid})
    if not r:
        return
    needs = "\n".join(f"• *{n['by']}* needs: {n['text']}"
                      for n in r["needs"]) or "_nothing yet_"
    offers = "\n".join(f"• *{o['by']}* offers: {o['text']}"
                       for o in r["offers"]) or "_nothing yet_"
    await update.message.reply_text(
        f"📋 *The board — {r['session_id']}*\n\n"
        f"🔍 *Needs*\n{needs}\n\n"
        f"💛 *Offers*\n{offers}",
        parse_mode="Markdown")


async def chains_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = _sess_code(context, 0)
    sid = code if re.fullmatch(r"S-\d{4}", code or "") else None
    sid = sid or await _sess_current(context)
    if not sid:
        await update.message.reply_text(
            "Join a session first: `/session join S-0001`",
            parse_mode="Markdown")
        return
    r = await _sess_api(update, context, "GET", "/api/session/chains",
                        params={"session_id": sid})
    if not r:
        return
    if not r["chains"]:
        await update.message.reply_text(
            "No chains yet — the TAG round starts them. "
            "`/tag someone a kindness`",
            parse_mode="Markdown")
        return
    blocks = []
    for c in r["chains"]:
        hops = "\n".join(
            f"  {h['from']} 🏷️→ {h['to']}: “{h['note']}”"
            for h in c["hops"])
        blocks.append(
            f"🔗 `{c['id']}` — started by {c['starter']}, "
            f"now with {c['holder']}\n{hops}")
    await update.message.reply_text(
        "🏷️ *The kindness chains:*\n\n" + "\n\n".join(blocks),
        parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎲 *MADHOUSE — everything the bot can do:*\n\n"
        "🚪 /join — enter the game (two questions)\n"
        "🎒 /pocket — your Dots\n"
        "🛂 /passport — your Cosmic Passport\n"
        "🎁 /giftcard — fold Dots into a gift card\n"
        "🎉 /redeem CODE — unfold a gift card\n"
        "🎡 /claim — spin the wheel, claim your world\n"
        "💬 /talk — sit with the five keepers\n"
        "🌀 /teleport — send Dots pocket-to-pocket\n"
        "🎒 /quest — Marlo's daily quest\n"
        "🏪 /shop — Pippa's Mercantile\n"
        "🕯️ /donate N — pour Dots back into the Pool\n"
        "🧭 /match — Juno introduces kindred players\n"
        "📚 /lore — a page from Sage Zell\n"
        "🎟️ /token — your trade token\n"
        "📜 /rules — the rules, all of them\n"
        "🛡️ /safety — stay safe out there\n"
        "🌀 /play — open the Mini App\n\n"
        "🌙 *Kindness sessions — the 15-minute flow:*\n"
        "🚪 /session start|join|status|next|close — the circle\n"
        "🔍 /need — name a need (SEEK round)\n"
        "💛 /offer — name what you can give (SEEK round)\n"
        "✋ /simon — the host names the one act; /done checks in\n"
        "🏷️ /tag — pass a kindness on (TAG round)\n"
        "🗳️ /vote — the circle decides (VOTE round)\n"
        "📋 /board — needs and offers · 🏷️ /chains — kindness chains",
        parse_mode="Markdown",
    )


# --------------------------------------------------------------------------
# Wiring
# --------------------------------------------------------------------------
def build_application(token=None):
    """Build the PTB Application with every handler registered.

    Does NOT start polling — the caller picks the transport:
    long-polling via main(), or Telegram webhooks via the WSGI app.
    """
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN not set — create the bot via @BotFather first.")
    logging.basicConfig(level=logging.WARNING)
    conv = ConversationHandler(
        entry_points=[CommandHandler(["start", "join"], start)],
        states={
            DOOR: [CallbackQueryHandler(door_pick, pattern=r"^door:(worlds|people|trade|create)$")],
            PP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, pp_name)],
            PP_WORLD: [MessageHandler(filters.TEXT & ~filters.COMMAND, pp_world)],
            PP_INTERESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, pp_interests)],
            PP_SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, pp_skills)],
            PP_DREAMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, pp_dreams)],
            GENEROSITY: [CallbackQueryHandler(got_generosity, pattern=r"^gift:(yes|no)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   CommandHandler(["start", "join"], start)],
    )
    trade_conv = ConversationHandler(
        entry_points=[CommandHandler("trade", trade_start),
                      CallbackQueryHandler(menu_trade_start, pattern=r"^home:trade$")],
        states={
            TRADE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, trade_amount)],
            TRADE_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, trade_token)],
            TRADE_CONFIRM: [CallbackQueryHandler(trade_confirm, pattern=r"^trade:(yes|no)$")],
        },
        fallbacks=[CommandHandler("cancel", trade_cancel)],
    )
    bio_conv = ConversationHandler(
        entry_points=[CommandHandler("bio", bio_start),
                      CallbackQueryHandler(menu_bio_start, pattern=r"^home:people$")],
        states={
            BIO_AGE: [CallbackQueryHandler(bio_age, pattern=r"^bio:(yes|no)$")],
            BIO_LINES: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio_lines)],
            BIO_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio_region)],
        },
        fallbacks=[CommandHandler("cancel", bio_cancel)],
    )
    app = Application.builder().token(token).build()
    app.add_handler(conv)
    app.add_handler(trade_conv)
    app.add_handler(bio_conv)
    app.add_handler(CommandHandler("pocket", pocket))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("token", token_cmd))
    app.add_handler(CommandHandler("whoami", whoami))
    app.add_handler(CommandHandler("prices", prices))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("safety", safety))
    app.add_handler(CommandHandler("gift", gift))
    app.add_handler(CommandHandler("npcs", npcs))
    app.add_handler(CommandHandler("quest", quest_claim))
    app.add_handler(CallbackQueryHandler(claim_pick, pattern=r"^claim:"))
    # --- the loaded-up game: passport, gift cards, worlds, keepers, teleport
    giftcard_conv = ConversationHandler(
        entry_points=[CommandHandler("giftcard", giftcard_start)],
        states={
            GIFTCARD_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                             giftcard_amount)],
            GIFTCARD_CONFIRM: [CallbackQueryHandler(giftcard_confirm,
                                                    pattern=r"^giftcard:(yes|no)$")],
        },
        fallbacks=[CommandHandler("cancel", giftcard_cancel)],
    )
    teleport_conv = ConversationHandler(
        entry_points=[CommandHandler("teleport", teleport_start)],
        states={
            TELEPORT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                             teleport_amount)],
            TELEPORT_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND,
                                            teleport_token)],
            TELEPORT_CONFIRM: [CallbackQueryHandler(teleport_confirm,
                                                    pattern=r"^teleport:(yes|no)$")],
        },
        fallbacks=[CommandHandler("cancel", teleport_cancel)],
    )
    app.add_handler(CommandHandler("passport", passport_start))
    app.add_handler(CallbackQueryHandler(passport_choice,
                                         pattern=r"^passport:face:"))
    app.add_handler(CallbackQueryHandler(passport_chibi,
                                         pattern=r"^passport:chibi:"))
    app.add_handler(CallbackQueryHandler(home_handler, pattern=r"^home:(play|wish|worlds|passport)$"))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("claim", world_claim))
    app.add_handler(CommandHandler("wish", wish_cmd))
    app.add_handler(CommandHandler("worlds", wish_cmd))
    app.add_handler(CommandHandler("map", map_cmd))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("talk", talk))
    app.add_handler(CallbackQueryHandler(talk_cb, pattern=r"^talk:"))
    app.add_handler(CallbackQueryHandler(talkbuy_cb, pattern=r"^talkbuy:"))
    app.add_handler(CallbackQueryHandler(talkdonate_cb, pattern=r"^talkdonate:"))
    app.add_handler(giftcard_conv)
    app.add_handler(teleport_conv)
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CallbackQueryHandler(shop_cb, pattern=r"^shop:"))
    app.add_handler(CommandHandler("donate", donate))
    app.add_handler(CommandHandler("pool", pool))
    app.add_handler(CommandHandler("lore", lore))
    app.add_handler(CommandHandler("match", match))
    app.add_handler(CommandHandler("bioff", bioclear))
    app.add_handler(CommandHandler("bioclear", bioclear))
    app.add_handler(CommandHandler("session", session_cmd))
    app.add_handler(CommandHandler("need", need_cmd))
    app.add_handler(CommandHandler("offer", offer_cmd))
    app.add_handler(CommandHandler("simon", simon_cmd))
    app.add_handler(CommandHandler("done", done_cmd))
    app.add_handler(CommandHandler("tag", tag_cmd))
    app.add_handler(CommandHandler("vote", vote_cmd))
    app.add_handler(CommandHandler("board", board_cmd))
    app.add_handler(CommandHandler("chains", chains_cmd))
    app.add_handler(CommandHandler("notforme", not_for_me))

    # Late handlers, registered last on purpose: the passport photo
    # catcher and the front-page pending wish. Active conversations
    # (gift/teleport/registration) always get first dibs on input.
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND,
                                   passport_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                   pending_wish))
    register_zorbs_handlers(app)   # the Zorbs universe journey — the front door
    register_matching_handlers(app)  # personality games, matches, wish board
    return app


def main():
    """Long-polling entry point (local dev)."""
    build_application().run_polling()


if __name__ == "__main__":
    main()
