# idontlikeai.club
SHELLHACKS 2025 PROJECT ENTRY

https://idontlikeai.club

"SNaiL"
* Slow down the spread of AI using our creations without consent. 

Mission Statement:

The widespread use of AI has become a significant security and privacy concern that is often overlooked.
Generative AI consumes numerous forms of media and content for its training, most of which has never been approved for training. 
AI should be used to facilitate and streamline creativity, without the worry of privacy breaches and unethical uses.
SNaiL seeks to help protect your text files from being detectable by AI models.
While not foolproof, it is enough to take a stand for increased AI laws and regulations.
SNaiL slows down the processing of your PDFs and redirects models away from your data and information.

## 🚀 3,2,1 - GO!

SNaiL is a Flask web app that lets a user authenticate with an OIDC provider (Okta/Auth0), upload a PDF, and download a **processed** copy. Processing preserves exact page layout and injects an **invisible text watermark** into the PDF’s text layer for provenance. Storage and access are **per‑user**, backed by a tiny **SQLite** catalog and persistent **filesystem sessions**.

---

## 🧱 Architecture (at a glance)

```
+-------------------------------+
|           Browser             |
|  - Login via OIDC             |
|  - Upload PDF / Download      |
+---------------+---------------+
                |
         HTTPS  |  Flask (WSGI)
                v
+---------------+----------------------------------------------+
|                    Flask Web App (Python)                    |
|  Routes: /login, /auth/callback, /upload, /docs, /download   |
|                                                              |
|  Auth (OIDC)                PDF Engine (PyMuPDF)             |
|  - Authlib + Okta/Auth0     - Copy page visuals              |
|  - Stores sub/email         - Inject invisible watermark     |
|                             - (Optional) embed Unicode font  |
|                                                              |
|  Sessions (Flask-Session)   Storage                          |
|  - Filesystem persistence    - uploads/<user_sub>/...        |
|  - 30‑day lifetime           - atomic writes                 |
|                                                              |
|  SQLite (data.db)                                           |
|  - documents table (owner, filename, hash, status, paths)    |
+---------------+----------------------------------------------+
                |
                v
+---------------+--------------------+
|  Disk: uploads/, .flask_sessions/  |
|  SQLite: data.db                   |
+------------------------------------+
```

---

## 🔐 Authentication (OIDC: Okta or Auth0)
- **Library:** [Authlib]’s Flask client uses the provider’s OIDC discovery URL.
- **Provider:** Works with **Okta** or **Auth0** (or any OIDC) — just point the issuer base URL and client creds in `okta_config.txt`.
- **Flow:** `/login/okta` → provider login → `/auth/callback` exchanges code and parses ID token.
- **Session content:** `user_id` (usually the OIDC `sub`), `user_email`, `user_name`.

**Config file (`okta_config.txt`)**
```
OKTA_ISSUER_BASE_URL= https://YOUR_DOMAIN/       # Okta or Auth0 issuer
OKTA_CLIENT_ID=       <client_id>
OKTA_CLIENT_SECRET=   <client_secret>
OKTA_REDIRECT_URI=    https://yourapp/callback   # optional, inferred if blank
```

> Why an external file? So secrets aren’t baked into source and can be swapped per environment.

---

## 👤 Per‑user isolation
- Each user has a dedicated directory: `uploads/<user_sub>/`.
- Original uploads are saved as `<doc_id>__<original>.pdf`.
- Processed files are written as `<doc_id>__encoded.pdf` **in the same user folder**.
- The DB and every route always filter by `owner_id = current_user_id()`.

---

## 🗃️ Persistence
- **Sessions:** `Flask‑Session` with `SESSION_TYPE=filesystem`, **30‑day** lifetime by default, survives app restarts (files in `.flask_sessions/`).
- **Database:** `SQLite` file `data.db` (created on first run).

**Schema (simplified)**
```sql
CREATE TABLE documents (
  id            TEXT PRIMARY KEY,
  owner_id      TEXT NOT NULL,
  owner_email   TEXT,
  filename      TEXT NOT NULL,
  path          TEXT NOT NULL,
  hash          TEXT,                -- sha256 of original
  status        TEXT NOT NULL,       -- uploaded | processed
  created_at    TEXT NOT NULL,       -- ISO8601 UTC
  processed_path TEXT,               -- encoded file path
  processed_kind TEXT                -- 'pdf'
);
```

---

## 🧩 PDF processing pipeline (layout‑preserving)
Goal: keep visual structure identical but add an **invisible provenance signal**.

1. **Open source PDF** and **create a new output doc**.
2. **Copy each page’s visuals** into the output (vector art, images, etc.).
3. **Inject watermark text** (default: `CONFIDENTIAL - SUNSHINE LABORATORIES 2025`) as **white text**:
   - Placed in benign positions (e.g., top of first page, bottom of last page).
   - Present in the text layer; visually invisible on white backgrounds.
4. **(Optional) Embed Unicode font** if a TTF exists in `fonts/` (e.g., `DejaVuSans.ttf`) so the watermark survives aggressive text extraction.
5. **Atomic write**: save to `*.tmp` then rename to `<doc_id>__encoded.pdf`.
6. **Missing file auto‑regen**: the download route rebuilds the processed copy if needed.

> In earlier prototypes we also experimented with **glyph substitution** (A/C/D/E/I/O/U/X/Y). The current competition build defaults to **watermark‑only** for maximum portability and reliability across complex PDFs.

---

## 🌐 Key endpoints
| Route | Method | Purpose |
|------|--------|---------|
| `/login/okta` | GET | Start OIDC login (Okta/Auth0). |
| `/auth/callback` | GET | OIDC callback → creates session. |
| `/home` | GET | Dashboard + recent docs (per user). |
| `/upload` | GET/POST | Upload a **PDF‑only** file (extension + `%PDF-` magic header check). |
| `/upload/<doc_id>/finish` | POST | Run processing, update DB. |
| `/docs` | GET | List all docs for the user. |
| `/docs/<doc_id>` | GET | Detail page with download buttons. |
| `/download/<doc_id>` | GET | Download original. |
| `/download/<doc_id>/processed` | GET | Download processed (auto‑regen if missing). |

---

## 🛡️ Security & platform notes
- **Secrets:** never hardcode; use `okta_config.txt` (or env vars in production).
- **Sessions:** server‑side files (no data in browser cookies beyond session id).
- **Upload validation:** enforces PDF extension and `%PDF-` magic header.
- **Least privilege:** DB queries always scoped to the logged‑in `owner_id`.
- **Prod hardening:** set a strong `SECRET_KEY`, add upload size limits, consider AV scanning, and run behind a real WSGI server with TLS.

---

## ⚙️ Local setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install Flask==3.0.3 Authlib==1.3.2 Flask-Session==0.6.0 PyMuPDF==1.24.8
# Add okta_config.txt, optionally fonts/DejaVuSans.ttf and motd.txt/watermark.txt
python app.py  # dev server on http://localhost:5000
```

---

## 📌 Design trade‑offs
- **Why SQLite + filesystem?** Zero‑ops, perfect for hackathons; easy to swap later.
- **Why watermark vs glyph substitution?** Watermark is robust across diverse PDFs and viewers; the glyph route is powerful but can break on edge cases without embedded fonts.
- **Why OIDC?** Portable across Okta/Auth0; vendor‑neutral and secure.

---

## 🗺️ Next steps (post‑hackathon)
- Photo support
