#!/usr/bin/env python3
"""Cosmic Passport renderer — faithful port of Josh's 2022 createPassport,
grown into the player's PROFILE.

Original: wave-8-zorbs-master-code/source/utils/canvas.js
  - 3000x3000 canvas over media/images/passport/inside.jpg
  - #74037b purple text, sans-serif, shrink-to-fit from 70px
  - Field positions, verbatim: givenname (670,2000), surname (1220,2000),
    nationality (670,2250), birthDate (670,2480), gender (670,2695),
    birthPlace (1220,2695)
  - Purple border stroke around the whole canvas
  - The template itself carries "Certified by the Order of ZOrbs" and the
    red wax seal — we don't redraw what Josh already drew.

MADHOUSE additions (the passport is the profile):
  - THE FACE IS THE PLAYER'S CHOICE (founder, 2026-10-19): their own photo,
    a chibi from assets/chibis/, or the deterministic avatar. NPC faces
    stay chibi — this choice is for people only.
  - The 2020 verbatim copy, centered under the ZOrbs mark:
    "Zorbs passports are your way to discover new worlds. These passports
    are energy passports and everyone is entitled to their free Zorbs
    passport. The multiverse and universes are open to all beings.
    Everyone is equal. Everyone unique."
  - The Dots balance stamped into the template's empty stamp box
    (top-right of the data section).
  - Worlds claimed, with deed card ids, as a centered line under the copy.
  - No stat is ever invented: dots/worlds render only when supplied.

Pillow is vendored (vendor/PIL) so this runs on the server. Every PIL
import stays inside functions so the module imports cleanly without it.
"""
import hashlib
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "assets", "passport", "inside.jpg")
CHIBI_DIR = os.path.join(HERE, "assets", "chibis")

PURPLE = (0x74, 0x03, 0x7B)
INK = (0x2B, 0x2B, 0x33)
CANVAS = 3000

# Photo box, measured from the template (black rectangle, right side).
PHOTO_BOX = (1797, 1695, 2276, 2318)  # x0, y0, x1, y1

# The template's empty stamp box, top-right of the data section
# (outline measured: x 1805-2200, y 1592-1658). Made for the Dots balance.
STAMP_BOX = (1805, 1592, 2200, 1658)

# Card bounds (the white passport card on its black surround).
CARD_X0, CARD_X1 = 589, 2462
CARD_CX = (CARD_X0 + CARD_X1) // 2  # 1525

# Clean chibi portraits (character renders; screenshots, character centered).
CHIBIS = [
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

CHIBI_LABELS = [
    "Dylan", "Alexander", "Toby", "Hunter", "Red Cap",
    "Puffer", "Shades", "Peace", "Peace Crop",
]

# The 2020 words, verbatim. They live ON the passport, under the ZOrbs mark.
CREED_2020 = (
    "Zorbs passports are your way to discover new worlds. "
    "These passports are energy passports and everyone is entitled "
    "to their free Zorbs passport. The multiverse and universes are "
    "open to all beings. Everyone is equal. Everyone unique."
)

# Josh's field coordinates, verbatim. max_w keeps text clear of the photo box.
FIELDS = [
    # (key, x, y, max_width)
    ("givenname", 670, 2000, 1020),
    ("surname", 1220, 2000, 470),
    ("nationality", 670, 2250, 1020),
    ("birthDate", 670, 2480, 1020),
    ("gender", 670, 2695, 420),
    ("birthPlace", 1220, 2695, 470),
]

_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/local/share/fonts/DejaVuSans.ttf",
    "DejaVuSans.ttf",  # last resort: let PIL search
]


def _font(size):
    """DejaVu Sans at size, with graceful fallback to PIL's default."""
    from PIL import ImageFont
    for path in _FONT_PATHS:
        try:
            if os.path.isfile(path) or path == "DejaVuSans.ttf":
                return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _fit_font(draw, text, max_width, start=70):
    """Josh's applyText: shrink from 70px until the text fits."""
    size = start
    while size > 14:
        font = _font(size)
        try:
            w = draw.textlength(text, font=font)
        except Exception:
            w = len(text) * size * 0.6
        if w <= max_width:
            return font
        size -= 10
    return _font(14)


def _wrap(draw, text, font, max_width):
    """Greedy word wrap. Returns a list of lines."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        try:
            tw = draw.textlength(trial, font=font)
        except Exception:
            tw = len(trial) * 30
        if tw <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def chibi_for(player_id):
    """Deterministic chibi face for a player id. Same player, same face."""
    n = int(hashlib.sha256(str(player_id).encode()).hexdigest()[:8], 16)
    return CHIBIS[n % len(CHIBIS)]


def resolve_face(face, player_id=""):
    """Resolve a face choice to ("chibi", filename) or ("photo", path).

    face may be None (→ deterministic avatar), {"kind": "avatar"},
    {"kind": "chibi", "file": name}, or {"kind": "photo", "path": path}.
    Anything unknown or missing falls back to the avatar. Never raises.
    """
    try:
        if not face or face.get("kind") in (None, "avatar"):
            return ("chibi", chibi_for(player_id))
        if face.get("kind") == "chibi":
            name = os.path.basename(str(face.get("file") or ""))
            if name in CHIBIS and os.path.isfile(os.path.join(CHIBI_DIR, name)):
                return ("chibi", name)
            return ("chibi", chibi_for(player_id))
        if face.get("kind") == "photo":
            path = str(face.get("path") or "")
            if path and os.path.isfile(path):
                return ("photo", path)
            return ("chibi", chibi_for(player_id))
    except Exception:
        pass
    return ("chibi", chibi_for(player_id))


def _paste_cover(canvas, img, box):
    """Paste img into box with cover-fit (center crop to aspect)."""
    from PIL import Image
    x0, y0, x1, y1 = box
    box_w, box_h = x1 - x0, y1 - y0
    w, h = img.size
    target = box_w / box_h
    if w / h > target:
        nw = int(h * target)
        off = (w - nw) // 2
        img = img.crop((off, 0, off + nw, h))
    else:
        nh = int(w / target)
        off = (h - nh) // 2
        img = img.crop((0, off, w, off + nh))
    img = img.resize((box_w, box_h), Image.LANCZOS)
    canvas.paste(img, (x0, y0))


def _paste_chibi(canvas, chibi_file):
    """Composite a chibi portrait into the template's photo box."""
    from PIL import Image
    face = Image.open(os.path.join(CHIBI_DIR, chibi_file)).convert("RGB")
    w, h = face.size
    # Character sits in the middle band of the phone screenshots; the top
    # and bottom are UI chrome. Crop the character first, then cover-fit.
    face = face.crop((int(w * 0.18), int(h * 0.36),
                      int(w * 0.82), int(h * 0.84)))
    _paste_cover(canvas, face, PHOTO_BOX)


def _paste_photo(canvas, photo_path):
    """Composite the player's own photo into the photo box (cover-fit)."""
    from PIL import Image
    try:
        photo = Image.open(photo_path).convert("RGB")
    except Exception:
        return False
    _paste_cover(canvas, photo, PHOTO_BOX)
    return True


def _draw_centered(draw, cx, y, text, font, fill):
    try:
        w = draw.textlength(text, font=font)
    except Exception:
        w = len(text) * 30
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


def render_passport(player_name, joined_at=None, player_id="", face=None,
                    dots=None, worlds=None):
    """Render the Cosmic Passport — now the player's profile.

    Returns a BytesIO of PNG bytes (3000x3000).

    player_name: the Zorbian name from /join.
    joined_at: ISO timestamp (becomes the passport's date of birth);
               falls back to "the First Day" when unknown.
    player_id: picks the deterministic avatar face.
    face: None | {"kind": "avatar"} | {"kind": "chibi", "file": name}
          | {"kind": "photo", "path": path}. The player's choice; anything
          odd falls back to the avatar. Never raises for a bad face.
    dots: the player's Dots balance (int) or None to omit.
    worlds: list of {"world_name":..., "card_id":...}; up to 3 shown with
            deed ids, then "+N more". None/empty omits the line.
    """
    from PIL import Image, ImageDraw

    if not os.path.isfile(TEMPLATE):
        raise FileNotFoundError("passport template missing: %s" % TEMPLATE)

    canvas = Image.open(TEMPLATE).convert("RGB")
    if canvas.size != (CANVAS, CANVAS):
        canvas = canvas.resize((CANVAS, CANVAS), Image.LANCZOS)
    draw = ImageDraw.Draw(canvas)

    # Purple border stroke, like the original.
    draw.rectangle([0, 0, CANVAS - 1, CANVAS - 1], outline=PURPLE, width=8)

    # The face: the player's choice — photo, chibi, or avatar.
    kind, ref = resolve_face(face, player_id)
    if kind == "photo":
        if not _paste_photo(canvas, ref):
            _paste_chibi(canvas, chibi_for(player_id))
    else:
        _paste_chibi(canvas, ref)

    # --- the 2020 creed, centered under the ZOrbs mark -------------------
    creed_font = _font(52)
    creed_lines = _wrap(draw, CREED_2020, creed_font, CARD_X1 - CARD_X0 - 260)
    cy = 1010
    for line in creed_lines[:5]:
        _draw_centered(draw, CARD_CX, cy, line, creed_font, PURPLE)
        cy += 66

    # --- worlds claimed, with deed ids ----------------------------------
    worlds = [w for w in (worlds or [])
              if isinstance(w, dict) and w.get("world_name")]
    if worlds:
        shown = worlds[:3]
        bits = ["%s %s" % (w["world_name"][:26], w.get("card_id") or "")
                for w in shown]
        line = "WORLDS  " + "   ·   ".join(bits)
        if len(worlds) > 3:
            line += "   (+%d more)" % (len(worlds) - 3)
        wf = _fit_font(draw, line, CARD_X1 - CARD_X0 - 320, start=44)
        _draw_centered(draw, CARD_CX, cy + 18, line, wf, INK)

    # --- the Dots balance, stamped into the template's stamp box ---------
    if dots is not None:
        try:
            stamp = "◆ {:,} DOTS".format(int(dots))
        except Exception:
            stamp = None
        if stamp:
            sx0, sy0, sx1, sy1 = STAMP_BOX
            sf = _fit_font(draw, stamp, (sx1 - sx0) - 24, start=54)
            _draw_centered(draw, (sx0 + sx1) / 2, sy0 + 8, stamp, sf, PURPLE)

    # --- Josh's fields, verbatim ----------------------------------------
    if joined_at:
        try:
            birth = str(joined_at).split("T")[0]
        except Exception:
            birth = "the First Day"
    else:
        birth = "the First Day"

    values = {
        "givenname": str(player_name or "Traveler")[:40],
        "surname": "of the Clan",
        "nationality": "Zorbian",
        "birthDate": birth,
        "gender": "",
        "birthPlace": "The First Portal",
    }
    for key, x, y, max_w in FIELDS:
        text = values.get(key, "")
        if not text:
            continue
        font = _fit_font(draw, text, max_w)
        draw.text((x, y), text, font=font, fill=PURPLE)

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    buf.seek(0)
    buf.name = "passport.png"
    return buf


# --------------------------------------------------------------------------
# Face choices — the player's own decision, kept on disk so it survives
# restarts. data/faces/<pid>.json holds {"kind": "avatar"|"chibi"|"photo",
# "file": chibi-name}; a photo choice also stores <pid>.jpg.
# --------------------------------------------------------------------------
import re as _re

FACE_DIR = os.path.join(HERE, "data", "faces")


def _safe_pid(pid):
    return _re.sub(r"[^A-Za-z0-9_-]", "", str(pid or ""))[:64]


def save_face_choice(pid, choice, photo_bytes=None):
    """Persist a face choice. choice: {"kind": "avatar"|"chibi"|"photo",
    "file": chibi-filename}. photo_bytes required for kind "photo".
    Returns True on success. Never raises."""
    try:
        spid = _safe_pid(pid)
        if not spid:
            return False
        os.makedirs(FACE_DIR, exist_ok=True)
        kind = (choice or {}).get("kind") or "avatar"
        if kind == "photo":
            if not photo_bytes or len(photo_bytes) > 12_000_000:
                return False
            head = bytes(photo_bytes[:4])
            if not (head[:2] == b"\xff\xd8"
                    or head[:4] == b"\x89PNG"
                    or head[:4] == b"RIFF"):
                return False
            with open(os.path.join(FACE_DIR, spid + ".jpg"), "wb") as f:
                f.write(bytes(photo_bytes))
        elif kind == "chibi":
            name = os.path.basename(str((choice or {}).get("file") or ""))
            if name not in CHIBIS:
                return False
        else:
            kind = "avatar"
        rec = {"kind": kind}
        if kind == "chibi":
            rec["file"] = os.path.basename(str(choice.get("file")))
        with open(os.path.join(FACE_DIR, spid + ".json"), "w",
                   encoding="utf-8") as f:
            import json as _json
            _json.dump(rec, f)
        return True
    except Exception:
        return False


def load_face_choice(pid):
    """Load a face choice as a render_passport `face` argument.
    Returns None (→ deterministic avatar) when nothing valid is stored.
    Never raises."""
    try:
        import json as _json
        spid = _safe_pid(pid)
        if not spid:
            return None
        with open(os.path.join(FACE_DIR, spid + ".json"),
                  encoding="utf-8") as f:
            rec = _json.load(f)
        kind = rec.get("kind") or "avatar"
        if kind == "photo":
            path = os.path.join(FACE_DIR, spid + ".jpg")
            if os.path.isfile(path):
                return {"kind": "photo", "path": path}
            return None
        if kind == "chibi":
            name = os.path.basename(str(rec.get("file") or ""))
            if name in CHIBIS:
                return {"kind": "chibi", "file": name}
            return None
        return None  # "avatar" → deterministic
    except Exception:
        return None
