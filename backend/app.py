"""Dinner Menu Generator — backend entrypoint (audit §4.1).

This file used to be a ~950-line monolith holding models, utils, services *and* routes.
It is now a thin bootstrapper: create the Flask app, load :class:`config.Config`,
init SQLAlchemy via ``db.init_app``, register the four blueprints under ``routes/``
and serve the bundled frontend. All real logic lives in:

    models.py            SQLAlchemy models + unbound ``db``
    config.py            Config object
    utils.py             pure helpers + constants (ingredient normalisation, OCR helpers)
    services/*.py        business logic (menu / grocery)
    routes/*.py          Flask blueprints (meals / menu / grocery / data)
"""

import os
import sys
import signal
import logging
import threading
import webbrowser

from dotenv import load_dotenv  # audit §5.7 (python-dotenv already in requirements.txt)

from flask import Flask, jsonify, send_from_directory, request
from werkzeug.exceptions import HTTPException
from flask_cors import CORS
from flask_migrate import Migrate, upgrade, stamp

import pytesseract

# audit §5.7 — load .env into os.environ *before* Config reads it (e.g. DATABASE_URL).
load_dotenv()

# audit §5.3 — structured logging instead of bare print() (§5.2). One place to configure
# levels/handlers; every module reads its own logger via logging.getLogger(__name__).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("dinner")


def _handle_shutdown(signum, frame):
    """audit §5.20 — log and exit cleanly on SIGINT/SIGTERM (desktop exe close, Ctrl-C)."""
    logger.info("Received signal %s — shutting down gracefully.", signum)
    raise SystemExit(0)


def _register_signal_handlers():
    # signal handlers can only be installed from the main thread
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handle_shutdown)
        except (ValueError, OSError):
            pass


from config import Config  # noqa: E402 — must follow load_dotenv() (audit §5.7)
from models import db  # noqa: E402 — must follow load_dotenv() (audit §5.7)
from utils import tesseract_path  # noqa: E402
from limiter import limiter  # noqa: E402 — rate limiting (audit §5.21 / §8.4)
from routes.meals import meals_bp  # noqa: E402
from routes.menu import menu_bp  # noqa: E402
from routes.grocery import grocery_bp  # noqa: E402
from routes.data import data_bp  # noqa: E402
from cli import register_cli  # noqa: E402


# --- PyInstaller-aware frontend build dir ---------------------------------
if hasattr(sys, "_MEIPASS"):
    FRONTEND_BUILD = os.path.join(sys._MEIPASS, "frontend/dist")
else:
    FRONTEND_BUILD = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/dist"))

# --- OCR engine availability (audit §4.5) ---------------------------------
if not tesseract_path:
    logger.warning("Tesseract not found in PATH — image upload (OCR) will not work.")
    logger.warning("Install Tesseract: https://github.com/tesseract-ocr/tesseract")
else:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

# --- Application factory --------------------------------------------------
app = Flask(__name__)
app.config.from_object(Config)
CORS(app, origins=app.config["CORS_ORIGINS"])
db.init_app(app)

# Point Alembic at an absolute migrations dir so it is found both in a dev
# checkout (backend/migrations) and inside a PyInstaller build (_MEIPASS/migrations).
if hasattr(sys, "_MEIPASS"):
    _MIGRATIONS_DIR = os.path.join(sys._MEIPASS, "migrations")
else:
    _MIGRATIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "migrations"))
Migrate(app, db, directory=_MIGRATIONS_DIR)  # audit §4.8 — Alembic migrations

limiter.init_app(app)  # audit §5.21 / §8.4 — apply default rate limits to all routes


# --- Health check (audit §4.4) -------------------------------------------
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# --- Frontend serving ----------------------------------------------------
@app.route("/")
def serve():
    index_path = os.path.join(FRONTEND_BUILD, "index.html")
    if not os.path.exists(index_path):
        return f"Missing index.html at {index_path}", 500
    return send_from_directory(FRONTEND_BUILD, "index.html")


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(os.path.join(FRONTEND_BUILD, "assets"), filename)


# --- Register blueprints (audit §4.1) ------------------------------------
app.register_blueprint(meals_bp)
app.register_blueprint(menu_bp)
app.register_blueprint(grocery_bp)
app.register_blueprint(data_bp)

# --- Maintenance CLI commands (audit §5.5/§5.6/§8.1) ---------------------
# fix-data / init-db are CLI-only now (no longer exposed over HTTP).
register_cli(app)


# --- CSRF protection (audit §8.3 / §5.22) ---------------------------------
# The app is same-origin in production (Flask serves the frontend) and uses no cookies /
# sessions, so classic CSRF is low-risk here. As defense-in-depth we still reject any state-
# changing request (POST/PUT/PATCH/DELETE) that does NOT carry the custom header
# `X-Requested-With: XMLHttpRequest`. A browser cannot attach a custom header to a
# cross-origin request without explicit CORS permission (which prod does not grant), so a
# malicious third-party page can only issue a plain cross-site POST/PUT/DELETE — which we
# now 403. GET/HEAD/OPTIONS/TRACE are exempt. See audit.md §5.22.
@app.before_request
def _csrf_protect():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        if request.headers.get("X-Requested-With") != "XMLHttpRequest":
            return jsonify({"error": "CSRF verification failed"}), 403


# --- Custom error handlers (audit §8.7) ----------------------------------
# In production the app must NOT echo exception messages back to the client (they can
# leak internals / DB schema / file paths). We log the real error server-side and return a
# generic JSON message. HTTP errors (404/405/…) keep their status code; everything else
# becomes a 500 "Internal server error".
@app.errorhandler(HTTPException)
def _handle_http_exception(e):
    return jsonify({"error": e.name}), e.code


@app.errorhandler(Exception)
def _handle_unhandled_exception(e):
    logger.exception("Unhandled exception: %s", e)
    return jsonify({"error": "Internal server error"}), 500


logger.info("Frontend build dir: %s", FRONTEND_BUILD)
logger.info(
    "Frontend files: %s",
    os.listdir(FRONTEND_BUILD) if os.path.exists(FRONTEND_BUILD) else "MISSING",
)


def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    _register_signal_handlers()  # audit §5.20 — graceful SIGINT/SIGTERM handling
    with app.app_context():
        # audit §4.8 — apply Alembic migrations first. For a fresh install `upgrade()`
        # creates the tables; for an existing dinner.db that is already stamped it is a
        # no-op. The create_all() fallback (plus a best-effort `stamp head`) covers legacy
        # DBs that predate the migration bundle, so existing users never lose data.
        #
        # NOTE: flask_migrate/alembic raise SystemExit (not Exception) on some errors in
        # a frozen PyInstaller bundle where the migrations directory is missing. SystemExit
        # is a BaseException subclass — the bare `except Exception` won't catch it — so we
        # catch (Exception, SystemExit) to keep the exe from dying on startup.
        try:
            upgrade()
        except (Exception, SystemExit) as e:
            logger.warning("Alembic upgrade unavailable, falling back to db.create_all(): %s", e)
            db.create_all()
            try:
                stamp("head")
            except (Exception, SystemExit):
                pass

    logger.info("Routes registered:")
    for rule in app.url_map.iter_rules():
        logger.info("  %s", rule)

    threading.Timer(1.5, open_browser).start()
    app.run(debug=False)
