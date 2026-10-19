#!/usr/bin/env python3
"""MADHOUSE on PythonAnywhere — one Flask app, zero background processes.

What lives here:
  * The game engine (server.py), called in-process via handle() — no HTTP
    to self, no second process. Same dispatch code as the stdlib server,
    same fixed-supply doctrine, same fail-closed behavior.
  * The Telegram bot (madhouse_bot.py + journeys) in webhook mode: Telegram
    POSTs updates to /tg-webhook, which verifies the secret header and
    feeds the update to the PTB Application running on its own asyncio
    loop in a background thread.
  * The webapp/ static files under the same /webapp/* paths as before.

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
import queue
import threading

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
# Telegram bot: one PTB Application, driven by one dedicated worker thread.
#
# The worker owns its thread, its event loop, and its Application. It blocks
# on a plain threading queue (no asyncio involved) and drives its loop
# synchronously with run_until_complete. Nothing ever crosses threads into
# the loop, and the loop is never closed, so the bot's HTTP client always
# runs on its home loop. (A previous design ran each update on a fresh
# per-update loop against one shared Application; the shared HTTP client
# then died with "Event loop is closed" on every reply.)
# ---------------------------------------------------------------------------
def _secret_configured(name):
    v = os.environ.get(name, "")
    return bool(v) and "__PASTE__" not in v


_bot_app = None
_bot_init_error = None
_bot_updates = queue.Queue()


async def _bot_error_handler(update, context):
    log.exception("madhouse: bot handler error: %s", context.error)


def _bot_worker():
    global _bot_app
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        _bot_app = madhouse_bot.build_application(
            os.environ["TELEGRAM_BOT_TOKEN"])
        _bot_app.add_error_handler(_bot_error_handler)
        loop.run_until_complete(_bot_app.initialize())
    except Exception as exc:  # noqa: BLE001 - import must never crash
        _bot_app = None
        _bot_init_error = str(exc)
        log.warning("madhouse: telegram bot initialize failed: %s", exc)
        return
    log.warning("madhouse: telegram bot initialized")
    while True:
        update = _bot_updates.get()
        try:
            loop.run_until_complete(
                asyncio.wait_for(_bot_app.process_update(update), 30))
        except Exception:
            log.exception("madhouse: background process_update failed")


if _secret_configured("TELEGRAM_BOT_TOKEN"):
    _bot_thread = threading.Thread(target=_bot_worker, name="tg-worker",
                                   daemon=True)
    _bot_thread.start()
else:
    _bot_init_error = "TELEGRAM_BOT_TOKEN not configured"

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
    if _bot_app is None:
        return {"error": "bot_not_initialized",
                "detail": _bot_init_error}, 503
    try:
        data = request.get_json(force=True)
    except Exception:
        return {"error": "bad_update"}, 400
    if not isinstance(data, dict):
        return {"error": "bad_update"}, 400
    try:
        update = Update.de_json(data, _bot_app.bot)
    except Exception as exc:
        log.warning("madhouse: bad update payload: %s", exc)
        return {"error": "bad_update"}, 400
    # Answer Telegram at once; the update is queued for the single bot
    # worker thread, which processes updates one at a time on its own
    # private event loop. The webhook never waits, so a stuck update can
    # never wedge a web worker.
    _bot_updates.put(update)
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
