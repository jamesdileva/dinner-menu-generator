"""Local LLM (Ollama) helper for optional AI enhancements (§16).

Provides a single ``call_ollama`` function that POSTs to the locally-running
Ollama daemon (``http://localhost:11434/api/generate``).  All traffic is
100 % local — no cloud dependency.  On any error (daemon not running,
timeout, non-200 response, or ``USE_OLLAMA`` is falsy in config) the function
returns ``None`` so callers can fall back to their rule-based logic.

Usage::

    from flask import current_app
    from services.llm_service import call_ollama

    text = call_ollama("List three dinner ideas", timeout=10)
    if text is None:
        return fallback_result()
"""

import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


def _is_enabled() -> bool:
    """Check whether Ollama is enabled in app config (must be called in app context)."""
    try:
        from flask import current_app
        return bool(current_app.config.get("USE_OLLAMA", False))
    except RuntimeError:
        # Not in an app context — treat as disabled
        return False


def _model() -> str:
    try:
        from flask import current_app
        return current_app.config.get("OLLAMA_MODEL", "llama3.1:8b")
    except RuntimeError:
        return "llama3.1:8b"


def _url() -> str:
    try:
        from flask import current_app
        return current_app.config.get("OLLAMA_URL", "http://localhost:11434/api/generate")
    except RuntimeError:
        return "http://localhost:11434/api/generate"


def _timeout() -> int:
    try:
        from flask import current_app
        return int(current_app.config.get("OLLAMA_TIMEOUT", 15))
    except (RuntimeError, ValueError, TypeError):
        return 15


def call_ollama(prompt: str, timeout: Optional[int] = None) -> Optional[str]:
    """Send *prompt* to the local Ollama daemon and return the generated text.

    Returns ``None`` when:
    - ``USE_OLLAMA`` is ``False`` in config
    - Ollama daemon is not running / not reachable
    - the request times out
    - the response is malformed

    Callers should treat ``None`` as "fall back to rule-based output".
    """
    if not _is_enabled():
        return None

    t = timeout if timeout is not None else _timeout()

    try:
        resp = httpx.POST(
            _url(),
            json={"model": _model(), "prompt": prompt, "stream": False},
            timeout=httpx.Timeout(t),
        )
        if resp.status_code != 200:
            logger.warning("Ollama returned status %s — falling back to rule-based.", resp.status_code)
            return None

        data = resp.json()
        text = data.get("response", "").strip()
        if not text:
            logger.warning("Ollama returned empty response — falling back to rule-based.")
            return None
        return text

    except (httpx.ConnectError, httpx.TimeoutException, ConnectionError, OSError) as e:
        logger.info("Ollama unreachable (%s) — falling back to rule-based.", type(e).__name__)
        return None
    except (json.JSONDecodeError, ValueError, Exception) as e:
        logger.warning("Ollama response error (%s) — falling back to rule-based.", e)
        return None


def parse_json_list(text: str) -> Optional[list]:
    """Best-effort parse of a JSON array from LLM text.

    Strips markdown code fences, leading/trailing whitespace, and trailing
    commas before parsing.  Returns ``None`` if parsing fails.
    """
    if not text:
        return None

    cleaned = text.strip()

    # strip markdown code fences
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    # strip trailing comma (common LLM habit in the last array element)
    cleaned = cleaned.rstrip(",")

    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            # wrap single object in a list
            return [result]
    except (json.JSONDecodeError, ValueError):
        pass

    # last resort: try to find the first [...] block
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            result = json.loads(cleaned[start : end + 1])
            if isinstance(result, list):
                return result
        except (json.JSONDecodeError, ValueError):
            pass

    return None
