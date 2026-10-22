# Media transport — 2026-10-22 bright set

The 23 treated (brightened) media files for the bot/engine, carried as
base64 text because the connector push route takes text only. Each
`<path>.b64` decodes byte-for-byte to the file that belongs at `<path>`
in the server app (paths mirror the app bundle: `assets/…`, `currents/…`).
`SHA256SUMS.txt` lists the sha256 of each DECODED file, relative to the
app root, so the server can verify with `sha256sum -c` after decoding.
Source audit: files/bot-media-treatment-2026-10-22/AUDIT.md (local).
