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

    # --- Ollama / local LLM integration (§16) ---
    # Optional enhancement layer: when enabled the app calls the locally-running
    # Ollama daemon (http://localhost:11434) to enhance grocery lists, nutrition
    # insights, and generate meal suggestions.  All traffic is 100 % local.
    USE_OLLAMA: bool = os.environ.get("OLLAMA_ENABLED", "false").lower() in ("1", "true", "yes")
    OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
    OLLAMA_URL: str = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
    OLLAMA_TIMEOUT: int = int(os.environ.get("OLLAMA_TIMEOUT", "15"))
