
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, send_from_directory, flash
)
from authlib.integrations.flask_client import OAuth
from flask_session import Session
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, timedelta
from werkzeug.middleware.proxy_fix import ProxyFix
import fitz  # PyMuPDF
import os, uuid, hashlib, sqlite3, sys, glob

# ---------- Paths & helpers ----------
BASE_DIR = os.path.dirname(__file__)
UPLOAD_ROOT = os.path.join(BASE_DIR, "uploads")
SESSIONS_DIR = os.path.join(BASE_DIR, ".flask_sessions")
DB_PATH = os.path.join(BASE_DIR, "data.db")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
WATERMARK_TXT = os.path.join(BASE_DIR, "watermark.txt")

def log(*args):
    print("[DocVerify]", *args, file=sys.stdout, flush=True)

def load_okta_config(path: str):
    cfg = {}
    if not os.path.exists(path):
        raise RuntimeError(
            f"Missing Okta config file: {path}. Create it (see okta_config.txt.example)."
        )
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()

    for key in ("OKTA_ISSUER_BASE_URL", "OKTA_CLIENT_ID", "OKTA_CLIENT_SECRET"):
        if key not in cfg or not cfg[key]:
            raise RuntimeError(f"Okta config missing required key: {key}")

    if not cfg.get("OKTA_REDIRECT_URI"):
        cfg["OKTA_REDIRECT_URI"] = None
    return cfg

def read_motd(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "Upload a PDF, finish processing to generate the processed PDF, then download it."

# ---------- App & Config ----------
OKTA_CFG = load_okta_config(os.path.join(BASE_DIR, "okta_config.txt"))

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
@app.route("/favicon.ico")
def favicon():
    # serve from your static dir
    return send_from_directory(
        app.static_folder,
        "favicon.ico",
        mimetype="image/x-icon",
        max_age=60 * 60 * 24 * 30  # 30 days
    )
app.config.update(
    {
        "SECRET_KEY": "change-me-dev-secret",
        **OKTA_CFG,
        "SESSION_TYPE": "filesystem",
        "SESSION_FILE_DIR": SESSIONS_DIR,
        "SESSION_PERMANENT": True,
        "PERMANENT_SESSION_LIFETIME": timedelta(days=30),
        "TEMPLATES_AUTO_RELOAD": True,
    }
)
os.makedirs(UPLOAD_ROOT, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)
Session(app)

# ---------- Database (SQLite) ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            owner_email TEXT,
            filename TEXT NOT NULL,
            path TEXT NOT NULL,
            hash TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            processed_path TEXT,
            processed_kind TEXT
        );
        """
    )
    conn.commit()
    conn.close()
init_db()

# ---------- Okta OAuth ----------
oauth = OAuth(app)
def _server_metadata_url():
    base = app.config["OKTA_ISSUER_BASE_URL"].rstrip("/")
    return f"{base}/.well-known/openid-configuration"
oauth.register(
    name="okta",
    client_id=app.config["OKTA_CLIENT_ID"],
    client_secret=app.config["OKTA_CLIENT_SECRET"],
    server_metadata_url=_server_metadata_url(),
    client_kwargs={"scope": "openid profile email"},
)

@app.before_request
def make_session_permanent():
    session.permanent = True

# ---------- Auth utils ----------
def current_user_id():
    return session.get("user_id")

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user_id():
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

# ---------- Jinja filters ----------
@app.template_filter("ts")
def format_ts(iso_str: str):
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return iso_str

# ---------- Small helpers ----------
def ensure_user_dir(uid: str) -> str:
    user_dir = os.path.join(UPLOAD_ROOT, uid)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def is_pdf_upload(file_storage) -> bool:
    filename = (file_storage.filename or "").lower()
    if not filename.endswith(".pdf"):
        return False
    pos = file_storage.stream.tell()
    head = file_storage.stream.read(5)
    file_storage.stream.seek(pos)
    try:
        return head.startswith(b"%PDF-")
    except Exception:
        return False

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as rf:
        for chunk in iter(lambda: rf.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def read_watermark_text() -> str:
    # Read watermark from watermark.txt; fallback to a sane default if missing/empty.
    try:
        with open(WATERMARK_TXT, "r", encoding="utf-8") as f:
            txt = f.read().strip()
            if txt:
                return txt
    except Exception:
        pass
    return "CONFIDENTIAL - SUNSHINE LABORATORIES 2025"

def find_unicode_font() -> str | None:
    # Prefer DejaVuSans explicitly if present, else first TTF in fonts/
    preferred = os.path.join(FONTS_DIR, "DejaVuSans.ttf")
    if os.path.isfile(preferred):
        return preferred
    for name in ["NotoSans-Regular.ttf","Arial Unicode.ttf","ArialUnicodeMS.ttf"]:
        p = os.path.join(FONTS_DIR, name)
        if os.path.isfile(p):
            return p
    for p in glob.glob(os.path.join(FONTS_DIR, "*.ttf")):
        return p
    return None

UNICODE_FONT = find_unicode_font()

def create_encoded_pdf_preserving_layout(src_pdf_path: str, dest_pdf_path: str):
    """Pure watermarking step: no cipher layer at all.
       - Copies the visual PDF 1:1
       - Inserts an invisible watermark string from watermark.txt
         * Prepend (overlay=False) on page 1 (first in content stream)
         * Append  (overlay=True)  on the last page (last in content stream)
    """
    wm_text = read_watermark_text()
    log("processing ->", src_pdf_path, "->", dest_pdf_path, "| watermark:", wm_text[:60], "...")

    src = fitz.open(src_pdf_path)
    out = fitz.open()
    out.insert_pdf(src)  # copy visuals 1:1

    # Embed Unicode font for the watermark if available
    font_alias = "wmfont"
    if UNICODE_FONT:
        try:
            out.insert_font(fontname=font_alias, fontfile=UNICODE_FONT)
        except Exception as e:
            log("insert_font failed, fallback to helv:", e)
            font_alias = "helv"
    else:
        font_alias = "helv"

    tmp_path = dest_pdf_path + ".tmp"

    n_pages = len(out)
    if n_pages == 0:
        out.save(tmp_path)
        out.close(); src.close()
        os.replace(tmp_path, dest_pdf_path)
        return

    # Insert watermark at the absolute beginning (page 1) and end (last page)
    first_page = out[0]
    first_page.insert_text(
        fitz.Point(18, 18),
        wm_text,
        fontsize=9,
        fontname=font_alias,
        color=(1, 1, 1),
        render_mode=3,     # invisible but extractable
        overlay=False,     # PREPEND: first in content stream
    )

    last_page = out[-1]
    last_page.insert_text(
        fitz.Point(last_page.rect.width - 18, last_page.rect.height - 18),
        wm_text,
        fontsize=9,
        fontname=font_alias,
        color=(1, 1, 1),
        render_mode=3,
        overlay=True,      # APPEND: last in content stream
    )

    out.save(tmp_path)
    out.close(); src.close()
    os.replace(tmp_path, dest_pdf_path)
    log("processed pdf saved:", dest_pdf_path, "exists=", os.path.isfile(dest_pdf_path))

# ---------- Routes ----------
@app.route("/")
def root():
    if current_user_id():
        return redirect(url_for("home"))
    return redirect(url_for("login"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login/okta")
def login_okta():
    redirect_uri = app.config.get("OKTA_REDIRECT_URI") or url_for(
        "auth_callback", _external=True
    )
    return oauth.okta.authorize_redirect(redirect_uri=redirect_uri)

@app.route("/auth/callback")
def auth_callback():
    token = oauth.okta.authorize_access_token()
    userinfo = token.get("userinfo") or oauth.okta.parse_id_token(token)
    session["user_id"] = (
        userinfo.get("sub") or userinfo.get("uid") or userinfo.get("email")
    )
    session["user_email"] = userinfo.get("email")
    session["user_name"] = (
        userinfo.get("name")
        or userinfo.get("preferred_username")
        or session.get("user_email")
    )
    flash(f"Welcome, {session.get('user_name', 'user')}!", "success")
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/home")
@login_required
def home():
    uid = current_user_id()
    conn = get_db()
    rows = conn.execute(
        """
        SELECT id, filename, status, created_at, hash
        FROM documents
        WHERE owner_id = ?
        ORDER BY datetime(created_at) DESC
        LIMIT 5
        """,
        (uid,),
    ).fetchall()
    conn.close()
    recent = [dict(r) for r in rows]
    motd = read_motd(os.path.join(BASE_DIR, "motd.txt"))
    return render_template("home.html", recent=recent, motd=motd)

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        f = request.files.get("file")
        if not f or not f.filename.strip():
            flash("Choose a file to upload.", "error")
            return redirect(url_for("upload"))

        if not is_pdf_upload(f):
            flash("Only PDF documents are allowed.", "error")
            return redirect(url_for("upload"))

        uid = current_user_id()
        user_dir = ensure_user_dir(uid)

        doc_id = str(uuid.uuid4())[:8]
        safe_name = secure_filename(os.path.basename(f.filename)) or "upload.pdf"
        save_path = os.path.join(user_dir, f"{doc_id}__{safe_name}")
        f.save(save_path)

        file_hash = sha256_file(save_path)
        created_iso = datetime.utcnow().replace(microsecond=0).isoformat()

        conn = get_db()
        conn.execute(
            """
            INSERT INTO documents (id, owner_id, owner_email, filename, path, hash, status, created_at, processed_path, processed_kind)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                uid,
                session.get("user_email"),
                safe_name,
                save_path,
                file_hash,
                "uploaded",
                created_iso,
                None,
                None,
            ),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("processing", doc_id=doc_id))

    return render_template("upload.html")

@app.route("/upload/<doc_id>/processing")
@login_required
def processing(doc_id):
    uid = current_user_id()
    conn = get_db()
    r = conn.execute(
        "SELECT * FROM documents WHERE id = ? AND owner_id = ?", (doc_id, uid)
    ).fetchone()
    conn.close()
    if not r:
        flash("Document not found.", "error")
        return redirect(url_for("home"))
    doc = dict(r)
    return render_template("processing.html", doc=doc)

@app.route("/upload/<doc_id>/finish", methods=["POST"])
@login_required
def finish(doc_id):
    uid = current_user_id()
    conn = get_db()
    r = conn.execute(
        "SELECT * FROM documents WHERE id = ? AND owner_id = ?", (doc_id, uid)
    ).fetchone()
    if not r:
        conn.close()
        flash("Document not found.", "error")
        return redirect(url_for("home"))
    doc = dict(r)

    processed_name = f"{doc_id}__encoded.pdf"
    processed_path = os.path.join(os.path.dirname(doc["path"]), processed_name)
    try:
        create_encoded_pdf_preserving_layout(doc["path"], processed_path)
    except Exception as e:
        conn.close()
        flash(f"Failed to build processed PDF: {e}", "error")
        return redirect(url_for("processing", doc_id=doc_id))

    if not os.path.isfile(processed_path):
        conn.close()
        flash(f"Processed PDF was not created at: {processed_path}", "error")
        return redirect(url_for("processing", doc_id=doc_id))

    conn.execute(
        """
        UPDATE documents
        SET processed_path = ?, processed_kind = ?, status = 'processed'
        WHERE id = ? AND owner_id = ?
        """
        ,
        (processed_path, "pdf", doc_id, uid),
    )
    conn.commit()
    conn.close()

    flash("Processing complete — processed PDF is ready.", "success")
    return redirect(url_for("doc_detail", doc_id=doc_id))

@app.route("/docs")
@login_required
def docs():
    uid = current_user_id()
    conn = get_db()
    rows = conn.execute(
        """
        SELECT id, filename, status, created_at, hash
        FROM documents
        WHERE owner_id = ?
        ORDER BY datetime(created_at) DESC
        """,
        (uid,),
    ).fetchall()
    conn.close()
    items = [dict(r) for r in rows]
    return render_template("docs.html", items=items)

@app.route("/docs/<doc_id>")
@login_required
def doc_detail(doc_id):
    uid = current_user_id()
    conn = get_db()
    r = conn.execute(
        "SELECT * FROM documents WHERE id = ? AND owner_id = ?", (doc_id, uid)
    ).fetchone()
    conn.close()
    if not r:
        flash("Document not found.", "error")
        return redirect(url_for("docs"))
    doc = dict(r)
    if doc.get("processed_path") and not os.path.isfile(doc["processed_path"]):
        flash(f"Processed PDF missing on disk: {doc['processed_path']}", "error")
    return render_template("doc_detail.html", doc=doc)

@app.route("/docs/<doc_id>/delete", methods=["POST"])
@login_required
def doc_delete(doc_id):
    uid = current_user_id()
    conn = get_db()
    r = conn.execute(
        "SELECT * FROM documents WHERE id = ? AND owner_id = ?", (doc_id, uid)
    ).fetchone()
    if not r:
        conn.close()
        flash("Document not found.", "error")
        return redirect(url_for("docs"))
    doc = dict(r)
    for p in [doc.get("path"), doc.get("processed_path")]:
        if p and os.path.isfile(p):
            try:
                os.remove(p)
            except Exception:
                pass
    conn.execute("DELETE FROM documents WHERE id = ? AND owner_id = ?", (doc_id, uid))
    conn.commit()
    conn.close()
    flash("Document deleted.", "success")
    return redirect(url_for("docs"))

@app.route("/download/<doc_id>")
@login_required
def download(doc_id):
    uid = current_user_id()
    conn = get_db()
    r = conn.execute(
        "SELECT path FROM documents WHERE id = ? AND owner_id = ?", (doc_id, uid)
    ).fetchone()
    conn.close()
    if not r:
        flash("Document not found.", "error")
        return redirect(url_for("docs"))
    path = r["path"]
    if not os.path.isfile(path):
        flash(f"Original file not found on disk: {path}", "error")
        return redirect(url_for("docs"))
    return send_from_directory(
        os.path.dirname(path), os.path.basename(path), as_attachment=True
    )

@app.route("/download/<doc_id>/processed")
@login_required
def download_processed(doc_id):
    uid = current_user_id()
    conn = get_db()
    r = conn.execute(
        "SELECT path, processed_path FROM documents WHERE id = ? AND owner_id = ?",
        (doc_id, uid),
    ).fetchone()
    conn.close()
    if not r:
        flash("Document not found.", "error")
        return redirect(url_for("docs"))
    orig_path = r["path"]
    proc_path = r["processed_path"]
    if not proc_path or not os.path.isfile(proc_path):
        # auto-regenerate on demand
        try:
            processed_name = f"{doc_id}__encoded.pdf"
            proc_path = os.path.join(os.path.dirname(orig_path), processed_name)
            create_encoded_pdf_preserving_layout(orig_path, proc_path)
        except Exception as e:
            flash(f"Processed file not available and regeneration failed: {e}", "error")
            return redirect(url_for("doc_detail", doc_id=doc_id))
    if not os.path.isfile(proc_path):
        flash(f"Processed file not found on disk: {proc_path}", "error")
        return redirect(url_for("doc_detail", doc_id=doc_id))
    return send_from_directory(
        os.path.dirname(proc_path), os.path.basename(proc_path), as_attachment=True
    )

if __name__ == "__main__":
    # In production, set debug=False and run behind a proper WSGI server.
    app.run(host="0.0.0.0", port=5000, debug=True)
