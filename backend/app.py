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
import shutil
import webbrowser
import threading

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate, upgrade, stamp

import pytesseract

from config import Config
from models import db
from utils import tesseract_path
from routes.meals import meals_bp
from routes.menu import menu_bp
from routes.grocery import grocery_bp
from routes.data import data_bp
from cli import register_cli

# --- PyInstaller-aware frontend build dir ---------------------------------
if hasattr(sys, "_MEIPASS"):
    FRONTEND_BUILD = os.path.join(sys._MEIPASS, "frontend/dist")
else:
    FRONTEND_BUILD = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../frontend/dist")
    )

# --- OCR engine availability (audit §4.5) ---------------------------------
if not tesseract_path:
    print("⚠️  WARNING: Tesseract not found in PATH — image upload (OCR) will not work.")
    print("   Install Tesseract: https://github.com/tesseract-ocr/tesseract")
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

print("FRONTEND_BUILD:", FRONTEND_BUILD)
print("FILES:", os.listdir(FRONTEND_BUILD) if os.path.exists(FRONTEND_BUILD) else "MISSING")


def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    with app.app_context():
        # audit §4.8 — apply Alembic migrations first. For a fresh install `upgrade()`
        # creates the tables; for an existing dinner.db that is already stamped it is a
        # no-op. The create_all() fallback (plus a best-effort `stamp head`) covers legacy
        # DBs that predate the migration bundle, so existing users never lose data.
        try:
            upgrade()
        except Exception as e:
            print("⚠️  Alembic upgrade unavailable, falling back to db.create_all():", e)
            db.create_all()
            try:
                stamp("head")
            except Exception:
                pass

    print("📍 ROUTES REGISTERED:")
    for rule in app.url_map.iter_rules():
        print(rule)

    threading.Timer(1.5, open_browser).start()
    app.run(debug=False)
