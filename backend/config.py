"""Application configuration for the Dinner Menu Generator backend.

Centralised here during the §4.1 modularization so `app.py` stays a thin entrypoint
(see audit.md §4.1). Loaded with `app.config.from_object(Config)`.
"""

import os
from typing import List


class Config:
    # --- Database (audit §5.7: overridable via .env / env vars) ---
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///dinner.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- CORS (audit §4.3) ---
    # Dev only: the Vite dev server. Production is same-origin (Flask serves the frontend)
    # so no CORS is needed there.
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # --- Upload limits (audit §4.6) ---
    MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024  # 5 MB
    MAX_IMAGE_DIMENSION: int = 4000  # px, either side
