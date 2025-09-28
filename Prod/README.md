# DocVerify g1 — Persistent + Homoglyph Engine

This build swaps the encoder to match your latest Java (`ProcessDoc` + `DocHash`):
- Only **lowercase letters** are substituted.
- Replacement is a **random homoglyph** from a per-letter list.
- All other characters pass through unchanged.

Other features retained:
- Okta via `okta_config.txt`
- Server-side sessions (filesystem, 30d)
- SQLite for docs
- Per-user upload dirs
- PDF-only upload
- Delete action
- MOTD from `motd.txt`

## Run
```bash
cd docverify_webui_persistent_glyphs
cp okta_config.txt.example okta_config.txt   # fill issuer/client/secret
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
# http://127.0.0.1:5000
```
