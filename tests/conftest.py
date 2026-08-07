"""Pytest configuration + shared fixtures (audit §11).

Tests run against a throwaway SQLite database so the real
`backend/instance/dinner.db` is never touched. `DATABASE_URL` is set BEFORE the
app is imported (python-dotenv's `load_dotenv()` does not override existing
env vars, so this wins).
"""

import os
import tempfile

# §11.1 — isolate the test DB before importing the app.
_TMP_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_TMP_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB.name}"
# The app no longer uses OpenAI; pop any stray key so tests are deterministic.
os.environ.pop("OPENAI_API_KEY", None)

import pytest  # noqa: E402

from app import app as flask_app, db as _db  # noqa: E402
from limiter import limiter  # noqa: E402


# Test-only route that always raises, registered ONCE before the app handles its
# first request so the generic 500 handler (§8.7) can be exercised.
@flask_app.route("/__raise__")
def _raise():  # pragma: no cover - only used by tests
    raise RuntimeError("boom")


@pytest.fixture()
def app():
    """A Flask app backed by a fresh temp DB schema for each test."""
    flask_app.config["TESTING"] = True
    # Keep TESTING's exception propagation OFF so our custom 500 handler is exercised.
    flask_app.config["PROPAGATE_EXCEPTIONS"] = False
    limiter.reset()  # clear rate-limit counters so each test starts from zero

    with flask_app.app_context():
        _db.create_all()

    yield flask_app

    with flask_app.app_context():
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def pytest_sessionfinish(session, exitstatus):
    """Clean up the temp DB file after the whole run."""
    try:
        os.unlink(_TMP_DB.name)
    except OSError:
        pass
