"""Rate-limiting for the Dinner Menu Generator backend (audit §5.21 / §8.4).

Kept in its own module so both ``app.py`` (init_app) and route modules (decorators)
can import `limiter` without forming an import cycle (routes <-> app).
Uses Flask-Limiter's in-memory storage by default — fine for a single-process local
desktop executable; swap to Redis only if the app is ever multi-process/exposed.
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120 per minute"],  # audit §8.4 — sane guard against runaway loops
    storage_uri="memory://",
    strategy="fixed-window",
)
