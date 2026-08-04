"""Application configuration for the Dinner Menu Generator backend.

Centralised here during the §4.1 modularization so `app.py` stays a thin entrypoint
(see audit.md §4.1). Loaded with `app.config.from_object(Config)`.
"""


class Config:
    # --- Database ---
    SQLALCHEMY_DATABASE_URI = "sqlite:///dinner.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- CORS (audit §4.3) ---
    # Dev only: the Vite dev server. Production is same-origin (Flask serves the frontend)
    # so no CORS is needed there.
    CORS_ORIGINS = ["http://localhost:5173"]

    # --- Upload limits (audit §4.6) ---
    MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
    MAX_IMAGE_DIMENSION = 4000  # px, either side
