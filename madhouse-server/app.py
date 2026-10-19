#!/usr/bin/env python3
"""MADHOUSE on PythonAnywhere — one Flask app, zero background processes.

What lives here:
  * The game engine (server.py), called in-process via handle() — no HTTP
    to self, no second process. Same dispatch code as the stdlib server,
    same fixed-supply doctrine, same fail-closed behavior.
  * The Telegram bot (madhouse_bot.py + journeys) in webhook mode: Telegram
    POSTs updates to /tg-webhook, which verifies the secret header and
    processes the update synchronously on the bot's own asyncio loop.
  * The webapp/ static files under the same /webapp/* paths as before.

Threading model (2026-10-19 fix): NO background threads, NO queues.
The bot's event loop and PTB Application are created LAZILY on the first
webhook request, inside the requesting worker process/thread. This is
deliberate: uWSGI forks workers after importing the app, and any thread,
loop, or queue created at import time does not survive the fork intact
(the Oct 19 outage: a background worker thread + queue wedged every
request with no error logged). With lazy per-worker init there is nothing
at import time that can break across the fork.

WSGI entry point: `application` (see pythonanywhere_wsgi.py).

Environment (set on the Web tab / in the WSGI file, never in code):
  TELEGRAM_BOT_TOKEN      from @BotFather
  TELEGRAM_WEBHOOK_SECRET any long random string; must match the
                          secret_token given to Telegram's setWebhook
  MADHOUSE_WEBAPP_URL     public https URL of /webapp/ (optional;
                          defaults to the engine's own /webapp/)

"Nothing is real until it's real."
"""
import asyncio
import json
import logging
import os

from flask import Flask, Response, request
from telegram import Update

import server as engine
import madhouse_bot
import matching_journey

log = logging.getLogger("madhouse")

# ---------------------------------------------------------------------------
# In-process engine transport: the bot calls the engine the way it always
# did (api_get/api_post -> _request), but _request now runs handle()
# directly instead of going over HTTP. API shapes and error semantics are
# unchanged: 4xx/5xx become ApiError(status, payload), transport failure
# becomes ApiError(0, engine_unreachable).
# ---------------------------------------------------------------------------
def _make_engine_dispatch(api_error_cls):
    def _dispatch(method, path, payload=None, params=None):
        body = json.dumps(payload).encode() if payload is not None else b""
        try:
            status, _headers, resp_body = engine.handle(
                method, path, params,
                {"Content-Type": "application/json"},
                body, client_ip="127.0.0.1")
        except Exception as exc:  # fail closed, like a dead connection
            raise api_error_cls(
                0, {"error": "engine_unreachable", "detail": str(exc)})
        try:
            data = json.loads(resp_body.decode() or "{}")
        except ValueError:
            data = {"detail": "the engine answered badly"}
        if status >= 400:
            raise api_error_cls(status, data)
        return data
    return _dispatch


madhouse_bot._engine_dispatch = _make_engine_dispatch(madhouse_bot.ApiError)
matching_journey._engine_dispatch = _make_engine_dispatch(
    matching_journey.ApiError)

# ---------------------------------------------------------------------------
# Telegram bot: lazy, synchronous, per-worker.
#
# _get_bot() builds ONE PTB Application on ONE asyncio loop, on first use,
# in whatever process/thread serves the first webhook request. The webhook
# then drives process_update() to completion on that same loop before
# answering Telegram. No threads, no queues, no cross-thread wakeups, and
# nothing created at import time — so uWSGI's fork cannot break it.
# Slow handlers simply make that one webhook call take longer (Telegram
# waits up to 60s); the 55s guard keeps us inside that budget.
# ---------------------------------------------------------------------------
def _secret_configured(name):
    v = os.environ.get(name, "")
    return bool(v) and "__PASTE__" not in v


_bot_loop = None
_bot_app = None
_bot_init_error = None


async def _bot_error_handler(update, context):
    log.exception("madhouse: bot handler error: %s", context.error)


def _get_bot():
    """Return the initialized Application, building it on first call."""
    global _bot_loop, _bot_app, _bot_init_error
    if _bot_app is not None:
        return _bot_app
    if not _secret_configured("TELEGRAM_BOT_TOKEN"):
        _bot_init_error = "TELEGRAM_BOT_TOKEN not configured"
        return None
    try:
        _bot_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_bot_loop)
        _bot_app = madhouse_bot.build_application(
            os.environ["TELEGRAM_BOT_TOKEN"])
        _bot_app.add_error_handler(_bot_error_handler)
        _bot_loop.run_until_complete(_bot_app.initialize())
        log.warning("madhouse: telegram bot initialized")
    except Exception as exc:  # noqa: BLE001 - a dead bot must not kill /health
        _bot_app = None
        _bot_loop = None
        _bot_init_error = str(exc)
        log.warning("madhouse: telegram bot initialize failed: %s", exc)
    return _bot_app


# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__)
application = app  # WSGI entry point


@app.route("/health", methods=["GET"])
def health():
    return {"ok": True}


@app.route("/tg-webhook", methods=["POST"])
def tg_webhook():
    """Telegram delivers bot updates here. Secret-verified, fail-closed."""
    secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
    presented = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not _secret_configured("TELEGRAM_WEBHOOK_SECRET") or presented != secret:
        return {"error": "forbidden"}, 403
    bot_app = _get_bot()
    if bot_app is None:
        return {"error": "bot_not_initialized",
                "detail": _bot_init_error}, 503
    try:
        data = request.get_json(force=True)
    except Exception:
        return {"error": "bad_update"}, 400
    if not isinstance(data, dict):
        return {"error": "bad_update"}, 400
    try:
        update = Update.de_json(data, bot_app.bot)
    except Exception as exc:
        log.warning("madhouse: bad update payload: %s", exc)
        return {"error": "bad_update"}, 400
    try:
        _bot_loop.run_until_complete(
            asyncio.wait_for(bot_app.process_update(update), 55))
    except Exception:
        log.exception("madhouse: process_update failed")
        return {"error": "handler_failed"}, 500
    return {"ok": True}


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "OPTIONS"])
def engine_dispatch(path):
    """Every other path goes to the game engine, unchanged."""
    full_path = "/" + path
    status, headers, body = engine.handle(
        request.method,
        full_path,
        request.query_string.decode("latin-1") or None,
        dict(request.headers),
        request.get_data(),
        client_ip=request.remote_addr or "127.0.0.1",
    )
    resp = Response(body, status=status)
    for key, value in headers.items():
        # Flask sets Content-Length itself; copying the engine's would risk
        # a mismatch if a proxy alters the body.
        if key.lower() == "content-length":
            continue
        resp.headers[key] = value
    return resp
