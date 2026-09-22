# Changelog

All notable changes to the Dinner Menu Generator are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- §5.14 — Meal categories: optional `category` column on `Meal` + `GET /meals/categories` + `?category=` filter + frontend category selector.
- §5.15 — Menu history: `GET /menus` returns all saved weekly menus (newest first) + `History.jsx` list view + `Calendar.jsx` calendar view.
- §5.16 — Grocery export: `GET /grocery/export?format=csv|text` with download links in UI.
- §5.17 — Menu ingredient detail: click a meal name in the weekly menu to toggle its ingredients inline.
- §5.18 — Meal search: `?search=` parameter on `/meals` + search bar in the frontend.
- §13a — UI refresh: dark/light mode toggle, shared CSS classes, responsive Quick Pick buttons, tabbed Past Menus view, "Email this menu" link.
- §13.18 — Local nutrition insights: `GET /insights` + `Insights.jsx` (presence-based macro analysis, flags, swap suggestions).
- §16 — Ollama local LLM integration (opt-in; all traffic stays on `http://localhost:11434`): `USE_OLLAMA`/`OLLAMA_MODEL`/`OLLAMA_URL`/`OLLAMA_TIMEOUT` config (env-overridable, persisted via `GET/POST /settings` to `instance/settings.json`); `services/llm_service.py` (`call_ollama()` returns `None` on any failure so callers fall back to rule-based output).
- §16.2 — AI-enhanced grocery list: `GET /grocery/enhance` reorders categories into store-layout order and suggests missing items; `🧠 Enhance` button shows the AI list side-by-side for comparison.
- §16.3 — AI-enhanced nutrition insights: `/insights` now includes `ai_suggestions` (meal-specific guidance) when Ollama is enabled; rendered in a dedicated `🧠 AI Insights` section.
- §16.4 — AI meal suggestions: `GET /menu/suggest` generates up to 3 ideas with ingredients + recipe; `💡 Suggest Meal` header button opens `SuggestMealModal.jsx` with per-suggestion "Save to Meals" (saved with `AI Suggested` category).
- Two-row sticky header: title + AI/theme toggles (row 1), wrapped action buttons (row 2) — buttons never overflow on narrow screens.
- Scrollable grocery list (`.grocery-scroll`, 480px max height) so long lists don't push the page down.

### Changed
- §4.1 — Backend modularization: `~950`-line `app.py` split into thin `app.py` + `routes/` (4 blueprints) + `services/` (3 modules) + `models.py` + `config.py` + `utils.py` + `cli.py` + `limiter.py`.
- §4.1 — Frontend modularization: `~315`-line `App.jsx` split into `components/{Menu,GroceryList,AddMeal,History,Calendar,Insights}.jsx` + `api.js`.
- §5.13 — Weekly menus now store meal IDs (not full snapshots); `expand_menu()` resolves them at read time so meal edits propagate to menus and grocery lists.
- §5.11 — Grocery count items now pluralize the item name (tomato→tomatoes, potato→potatoes) with proper irregular/suffix rules.
- §5.10 — `categorize_ingredient` rewritten as a keyword-substring matcher with expanded vocabularies.

### Removed
- `/fix-data` and `/init-db` HTTP endpoints — now CLI-only (`flask --app app fix-data|init-db`).
- `openai` and `psycopg2-binary` unused dependencies from `requirements.txt`.
- Dead `App.css` (never imported), dead `current_week` global, duplicate `import random`/`used_today` declarations.

### Fixed
- §16 — All three AI features (grocery enhance, nutrition insights, meal suggest) silently did nothing: `llm_service.call_ollama()` and `_check_ollama_available()` called `httpx.POST`/`httpx.GET` (nonexistent — httpx only has lowercase `post`/`get`), so every call raised `AttributeError`, was caught, and fell back to `None`/`False`. Now uses `httpx.post`/`httpx.get`; regression tests cover the success path, non-200, connection error, and availability probe.
- §16 — `OLLAMA_TIMEOUT` default raised 15s → 60s so the first AI call after a cold boot (model load into RAM) doesn't time out and force a double-click.
- Test isolation — `USE_OLLAMA` is now forced `False` per-test via `monkeypatch.setitem` in the `app` fixture (tests that need it on opt in explicitly and are auto-restored); previously one test's flag assignment leaked into later tests and could trigger real Ollama calls mid-suite.

---

## [1.0.0] — 2026-07-24

### Added
- Initial release: 7-day random weekly menu generation (no internal repeats).
- Quick Pick: random home meal or takeout spot.
- Grocery list generation with basic ingredient categories.
- OCR meal import via Tesseract (upload image → extract meal names).
- Meal CRUD: add, update, delete, list meals.
- Daily "no-repeat" meal picking (in-memory, reset on restart).
- Data export/import as JSON (`backup.json`).
