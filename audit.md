# Audit: Dinner Menu Generator

**Date:** 2026-07-24  
**Auditor:** opencode  
**Scope:** Full codebase (backend + frontend)  
**Overall Health:** Functional but needs significant cleanup and hardening before production use

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Summary](#2-architecture-summary)
3. [Critical Bugs](#3-critical-bugs)
4. [High-Priority Issues](#4-high-priority-issues)
5. [Medium-Priority Issues](#5-medium-priority-issues)
6. [Low-Priority / Polish Issues](#6-low-priority--polish-issues)
7. [Dead Code & Scaffolding](#7-dead-code--scaffolding)
8. [Security Concerns](#8-security-concerns)
9. [Performance & Scalability](#9-performance--scalability)
10. [Code Quality & Conventions](#10-code-quality--conventions)
11. [Testing](#11-testing)
12. [Documentation](#12-documentation)
13. [High-Value Features to Add](#13-high-value-features-to-add)
14. [Quick Wins (1-2 hour fixes)](#14-quick-wins-1-2-hour-fixes)
15. [Recommended Roadmap](#15-recommended-roadmap)

---

## 1. Project Overview

**Dinner Menu Generator** is a local-first desktop app (Flask backend + React/Vite frontend, packaged with PyInstaller) that lets users:

- Maintain a database of meals (name + ingredients)
- Generate random weekly menus (7 days, no repeats)
- Reroll individual days
- Generate categorized grocery lists from the weekly menu
- Upload images of menus (OCR via Tesseract + OpenCV) to auto-import meals
- Quick-pick: random home meal or random takeout spot

**Tech Stack:**
- Backend: Python / Flask / SQLAlchemy / SQLite
- Frontend: React 19 / Vite
- OCR: Tesseract + OpenCV + Pillow
- Packaging: PyInstaller (single-file executable)

---

## 2. Architecture Summary

```
dinner-menu-generator/
├── backend/
│   ├── app.py          # 856-line monolith: routes, models, services, utils all in one file
│   ├── config.py       # EMPTY
│   ├── models.py       # EMPTY
│   ├── app.spec        # PyInstaller spec
│   ├── backup.json     # Sample data (60+ weekly menus)
│   ├── routes/         # ALL EMPTY (meals.py, menu.py, grocery.py)
│   ├── services/       # ALL EMPTY (menu_service.py, grocery_service.py)
│   ├── instance/       # SQLite DB (gitignored)
│   └── dist/           # Compiled exe (gitignored)
├── frontend/
│   ├── src/
│   │   ├── App.jsx     # 315-line single-component app (all logic + UI)
│   │   ├── api.js      # EMPTY
│   │   ├── main.jsx    # Standard Vite entry
│   │   ├── components/ # ALL EMPTY (AddMeal.jsx, GroceryList.jsx, Menu.jsx)
│   │   └── styles.css  # EMPTY
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── dist/           # Built assets (gitignored)
├── requirements.txt
├── example.env
├── README.md
└── .gitignore
```

**Key architectural observation:** The project was clearly mid-refactor. Empty `routes/`, `services/`, `config.py`, `models.py`, `components/`, and `api.js` files suggest an intent to split the monolith into modular files, but the work was never completed. All logic still lives in `backend/app.py` and `frontend/src/App.jsx`.

---

## 3. Critical Bugs

### 3.1 Duplicate `loadMenu` function in App.jsx (frontend/src/App.jsx:66-83)

- [x] **FIXED 2026-08-03** — removed the shadowed first declaration; single `loadMenu` with grocery reset remains.

`loadMenu` is declared **twice** — once at line 66 (without grocery reset) and once at line 78 (with grocery reset). In JavaScript, the second declaration shadows the first, making the first one dead code. While this doesn't cause a runtime error, it's confusing and the first version's behavior is lost.

**Fix:** Remove the duplicate at lines 66-70.

### 3.2 `reroll_day` crashes with only 1 meal (backend/app.py:503-529)

- [x] **FIXED 2026-08-03** — returns 400 `"No other meals available"` when no alternatives exist.

If there is only 1 meal in the database and it's the current meal for the requested day, `available` will be an empty list, and `random.choice(available)` will raise `IndexError: Cannot choose from an empty sequence`.

```python
available = [m for m in meals if m.name != current_meal_name]
new_meal = random.choice(available)  # CRASHES if available is empty
```

**Fix:** Add a guard: if `len(available) == 0`, return an error or allow the same meal.

### 3.3 `decide` endpoint crashes with no meals (backend/app.py:466-478)

- [x] **FIXED 2026-08-03** — returns 400 `"No meals available"` when the DB is empty.

When `choice == "home"` and `Meal.query.all()` returns an empty list, `random.choice(meals)` raises `IndexError`.

```python
meals = Meal.query.all()
meal = random.choice(meals)  # CRASHES if meals is empty
```

**Fix:** Add a check: `if not meals: return jsonify({"error": "No meals available"}), 400`.

### 3.4 Hardcoded Tesseract path breaks on non-Windows (backend/app.py:25)

- [x] **FIXED 2026-08-03** — now uses `shutil.which("tesseract")` for cross-platform support.

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

This is hardcoded to a Windows path. On macOS or Linux, Tesseract is typically at `/usr/local/bin/tesseract` or `/usr/bin/tesseract`, and this line will cause OCR to fail silently (or crash) on those platforms.

**Fix:** Detect the platform or let Tesseract use its default PATH resolution:
```python
import shutil
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
```

### 3.5 Frontend fetches hardcoded to `localhost:5000` (frontend/src/App.jsx)

- [x] **FIXED 2026-08-03** — relative URLs everywhere + Vite dev proxy (`vite.config.js`) for all API paths.

Every API call uses `http://localhost:5000/...`. This works in dev mode but breaks when:
- The app is packaged as a desktop exe (the Flask server runs on a random port or embedded)
- The port is changed
- The app is deployed behind a reverse proxy

**Fix:** Use relative URLs (e.g., `/menu/week`) or read the base URL from an environment variable.

### 3.6 No input validation on `/meal` POST (backend/app.py:618-647)

- [x] **FIXED 2026-08-03** — uses `data.get("name")` with non-empty validation; returns 400 on missing/invalid name.

```python
raw_name = data["name"]  # KeyError if "name" is missing
```

If the request body doesn't contain `name`, this raises an unhandled `KeyError` and returns a 500 error. Same issue with `/import` (line 723: `data["meals"]`).

**Fix:** Use `data.get("name")` with validation, or use a schema validation library like Pydantic or marshmallow.

### 3.7 `import_data` doesn't check for duplicates (backend/app.py:721-736)

- [x] **FIXED 2026-08-03** — case-insensitive duplicate skip in `/import`; response now reports `added` count.

The `/import` endpoint blindly adds all meals and menus without checking for duplicates, unlike `/upload-menu` which does check. This can lead to duplicate meals in the database.

**Fix:** Add duplicate checking similar to the `/upload-menu` endpoint.

### 3.8 Grocery list quantity parsing fails on mixed numbers (backend/app.py:768-782)

- [x] **FIXED 2026-08-03** — new `parse_quantity` helper handles mixed numbers (`1 1/2` → 1.5, `2 3/4` → 2.75).

The regex `^([0-9\./\s]+)` matches "1 1/2" but the fraction parser only handles simple fractions like "1/2". Mixed numbers like "1 1/2" will be parsed as `float("1 1/2")` which raises `ValueError`, falling back to `qty = 1.0`.

**Fix:** Parse mixed numbers properly (e.g., split on space, handle whole + fraction parts).

### 3.9 `used_today` set is lost on restart (backend/app.py:455-459)

- [x] **FIXED 2026-08-03** — new `UsedMeal` DB table keyed by date; picks persist across restarts, stale rows pruned.

The `used_today` set is in-memory only. Restarting the app resets it, meaning the "avoid repeats" feature for `/menu/today` doesn't persist. Users could get the same meal twice in one day across restarts.

**Fix:** Persist `used_today` in the database or use a timestamp-based approach.

### 3.10 `current_week` global is never used (backend/app.py:27-28)

- [x] **FIXED 2026-08-03** — removed the dead global; duplicate `import random` / `used_today` declarations cleaned up (§5.1).

```python
global current_week
current_week = []
```

This variable is declared but never read or written anywhere else in the codebase. It's dead code.

---

## 4. High-Priority Issues

### 4.1 All logic in single files (app.py: 856 lines, App.jsx: 315 lines)

The backend `app.py` contains models, routes, utility functions, OCR processing, ingredient normalization, grocery list generation, and data import/export — all in one 856-line file. The frontend `App.jsx` contains all UI, state management, and API calls in one component.

**Impact:** Extremely difficult to maintain, test, or extend. The empty `routes/`, `services/`, `models.py`, `config.py` files show this was the intended direction but was never completed.

**Fix:** Complete the modularization:
- Move models to `models.py`
- Move routes to `routes/` (meals.py, menu.py, grocery.py, data.py)
- Move services to `services/` (menu_service.py, grocery_service.py)
- Move config to `config.py`
- Split frontend into components

- [x] **FIXED 2026-08-04** — backend split: thin `app.py` entrypoint registers 4 blueprints
  (`routes/meals.py`, `menu.py`, `grocery.py`, `data.py`); business logic moved to
  `services/menu_service.py` + `services/grocery_service.py`; models/config/utils centralized.
  Frontend split: `App.jsx` → `components/{Menu,GroceryList,AddMeal}.jsx` + `api.js`.
  Verified via Flask test client (all endpoints) + `py_compile` (10 modules) + npm lint/build.

### 4.2 No error handling on fetch calls (App.jsx)

- [x] **FIXED 2026-08-04** — centralised `apiFetch` helper (throws on non-2xx) + `withLoading` wrapper; global error banner + loading spinner added.

None of the fetch calls in App.jsx have try/catch blocks. If the server is down, the user gets an unhandled promise rejection and no feedback. There are also no loading states.

```javascript
async function loadMenu() {
    const res = await fetch("http://localhost:5000/menu/week");
    const data = await res.json();
    setMenu(data);
}
```

**Fix:** Wrap all fetch calls in try/catch, add loading states, and handle HTTP errors (e.g., `if (!res.ok) throw new Error(...)`).

### 4.3 CORS is wide open (backend/app.py:30)

- [x] **FIXED 2026-08-04** — `CORS(app, origins=["http://localhost:5173"])` (prod is same-origin).

```python
CORS(app)
```

No origin restrictions. Any website can make requests to the API. While this is a local app, it's still a security concern if the app is ever exposed.

**Fix:** Restrict CORS to specific origins or disable it entirely for the desktop app.

### 4.4 No health check endpoint

- [x] **FIXED 2026-08-04** — added `GET /health` returning `{"status": "ok"}`.

- [x] **FIXED 2026-08-04** — added `GET /health` returning `{"status": "ok"}`.

There's no `/health` or `/ping` endpoint. This makes it impossible to check if the server is running without hitting a real endpoint.

**Fix:** Add a simple `/health` endpoint returning `{"status": "ok"}`.

### 4.5 Tesseract not checked at startup

- [x] **FIXED 2026-08-04** — startup warns if `tesseract` not in PATH; `/upload-menu` returns 503 with a friendly message only after file-level validations pass.

If Tesseract is not installed or not in PATH, the app starts fine but crashes on any OCR request. The user gets a 500 error with no helpful message.

**Fix:** Check for Tesseract at startup and log a warning, or return a helpful error message on OCR endpoints.

### 4.6 No file upload validation (backend/app.py:532-616)

- [x] **FIXED 2026-08-04** — validates: file present, MIME allowlist (png/jpg/jpeg), 5 MB size cap, dimension guard (4000px), and corrupt-image handling (returns 400, not 500).

The `/upload-menu` endpoint:
- Doesn't check file type (accepts any file)
- Doesn't check file size (could be used for DoS)
- Doesn't check image dimensions
- Doesn't handle corrupt images gracefully

**Fix:** Validate file type (e.g., check magic bytes), enforce a size limit, and handle image processing errors.

### 4.7 No pagination on `/meals` (backend/app.py:679-682)

- [x] **FIXED 2026-08-04** — backend `?page`/`?limit` (1–100 clamp) returning `{meals, page, limit, total, pages}`; frontend "All Meals" list is now paginated (20/page) with Prev/Next + counts.

Returns all meals at once. If the database grows large, this could be slow and memory-intensive.

**Fix:** Add pagination parameters (`?page=1&limit=50`).

### 4.8 No database migration strategy

Uses `db.create_all()` which only creates tables if they don't exist. It doesn't handle schema changes (e.g., adding a new column). If the schema changes, users would need to delete their database and lose all data.

**Fix:** Use Flask-Migrate (Alembic) for proper migrations.

- [x] **FIXED 2026-08-04** — added `Flask-Migrate` (+ `alembic`/`Mako` pins);
  `Migrate(app, db, directory=<abs>)` wired in `app.py`; `migrations/` baseline generated
  (revision `6c296b498bf1` = current schema); `app.py` startup now runs `upgrade()` with a
  `create_all()` + `stamp("head")` fallback. PyInstaller `app.spec` + package command bundle
  `migrations/`. **Verified:** `flask db init/migrate/stamp/upgrade/current` all run;
  `upgrade()` against a fresh DB creates `meal`/`used_meal`/`weekly_menu` + `alembic_version`;
  real `dinner.db` stamped at head with the 3 sample meals (Sushi/Burger/Pizza) intact; test-client smoke green.

### 4.9 OpenAI dependency included but unused (requirements.txt:24)

- [x] **FIXED 2026-08-04** — removed `openai==2.30.0` (+ pydantic/pydantic_core graph) from `requirements.txt`.

`openai==2.30.0` is in requirements.txt but is never imported or used in `app.py`. The README mentions "AI meal suggestions" as a future idea, but the dependency was included prematurely.

**Fix:** Remove from requirements.txt until it's actually needed.

### 4.10 psycopg2-binary included but unused (requirements.txt:29)

- [x] **FIXED 2026-08-04** — removed `psycopg2-binary==2.9.11`; also removed unused `requests` (§7.3).

`psycopg2-binary==2.9.11` is included for PostgreSQL, but the app uses SQLite. This is an unnecessary dependency that adds bloat to the packaged exe.

**Fix:** Remove from requirements.txt.

---

## 5. Medium-Priority Issues

### 5.1 Duplicate `import random` and `used_today` declarations (backend/app.py:4, 453, 457, 455, 459)

- [x] **FIXED 2026-08-03** — duplicates removed as part of the §3 fixes.

```python
import random  # line 4
...
import random  # line 453
used_today = set()  # line 455
import random  # line 457
used_today = set()  # line 459
```

Three `import random` statements and two `used_today` declarations. The duplicates are harmless (Python handles re-imports gracefully) but indicate sloppy code organization.

### 5.2 Debug print statements in production code (backend/app.py)

Numerous `print()` statements throughout the code:
- Line 35: `print("🚀 RUNNING THIS FILE")`
- Lines 108-109: Import path debugging
- Lines 403-404: Frontend build path debugging
- Line 409: Index path debugging
- Line 557: `print("RAW OCR:", text)`
- Line 708: `print("❌ ERROR /menu/week:", e)`
- Line 837: `print("❌ ERROR /grocery:", e)`
- Lines 847-849: Route listing

**Fix:** Replace with proper logging using Python's `logging` module.

- [x] **FIXED 2026-08-05** — All `print()` calls replaced with level-appropriate logger calls across
  `app.py` (Tesseract warning→`logger.warning`, frontend-build + route listing→`logger.info`,
  Alembic fallback→`logger.warning`) and the four route modules (`routes/menu.py`,
  `grocery.py`, `meals.py`, `data.py` — errors→`logger.exception(...)`, OCR raw text→
  `logger.debug`, import diagnostics→`logger.info`). No `print()` remains in `backend/`.

### 5.3 No logging framework

The app uses `print()` for all output. There's no structured logging, no log levels, no log file output.

**Fix:** Use Python's `logging` module with appropriate levels (DEBUG, INFO, WARNING, ERROR).

- [x] **FIXED 2026-08-05** — `logging.basicConfig(level=INFO, format=...)` in `app.py` (the single
  entrypoint) configures the root logger with timestamped, levelled records; every module
  reads its own logger via `logging.getLogger(__name__)` (app→`dinner`, routes→per-module).
  Exception paths use `logger.exception(...)` so ERROR-level messages include a traceback;
  OCR raw text is `logger.debug` (off by default); startup diagnostics are `INFO`/`WARNING`.
  Verified: `import app` emits properly formatted `WARNING`/`INFO` log lines instead of bare prints.

### 5.4 `import_file` endpoint reads from hardcoded path (backend/app.py:101-140)

```python
path = os.path.join(os.path.dirname(__file__), "backup.json")
```

The `/import-file` endpoint always reads from `backup.json` in the backend directory. There's no way to specify a different file.

**Fix:** Accept a file upload or a file path parameter.

- [x] **FIXED 2026-08-04** — `/import-file` now accepts `?path=<json file>` (GET), a
  multipart `file` upload (POST), or falls back to the legacy `backend/backup.json`.
  Missing files return 404 JSON; invalid JSON returns 400 JSON (was an unhandled 500).
  Ingestion logic shared (case-insensitive dedupe) with `/import` via `routes/data.py`
  `_ingest()`. **Verified:** test-client sweep — path-param (2 meals/1 menu), legacy
  fallback, 404 for missing file, 400 for bad JSON, multipart upload, and `/import` POST
  all green against a throwaway temp DB; real `dinner.db` untouched.

### 5.5 `fix_data` endpoint is a maintenance tool exposed in production (backend/app.py:420-447)

This endpoint modifies all meal data (backfills ingredients, cleans names, removes duplicates). It's a maintenance tool that should not be exposed in production.

**Fix:** Either remove it, protect it with authentication, or move it to a CLI command.

- [x] **FIXED 2026-08-04** — `fix_data` moved out of HTTP into a `flask --app app fix-data` CLI
  command (`backend/cli.py`); the `/fix-data` route was removed. Verified the cleanse logic
   runs on a temp DB copy (3 sample meals untouched on the real `dinner.db`).

### 5.6 `init_db` endpoint is exposed (backend/app.py:449-452)

Anyone can hit `/init-db` to create database tables. While `create_all()` is idempotent, this endpoint shouldn't be publicly accessible.

**Fix:** Remove or protect this endpoint.

- [x] **FIXED 2026-08-04** — `init_db` moved to a `flask --app app init-db` CLI command
  (`backend/cli.py`); the `/init-db` route was removed. Verified `flask init-db` runs
  idempotently on the real `dinner.db`.

### 5.7 No environment variable loading (backend/app.py)

The app doesn't use `python-dotenv` to load `.env` files, even though it's in requirements.txt and there's a `.env` file with `OPENAI_API_KEY`.

**Fix:** Add `from dotenv import load_dotenv; load_dotenv()` at the top of `app.py`.

- [x] **FIXED 2026-08-05** — Added `load_dotenv()` at the top of `app.py` (after the import block,
  before `from config import Config`) so `.env` values populate `os.environ` at startup. Also
  made `SQLALCHEMY_DATABASE_URI` env-overridable in `config.py`
  (`os.environ.get("DATABASE_URL", "sqlite:///dinner.db")`), so users can point the dev server
  at a different DB via `.env` without code changes while keeping the default. `python-dotenv`
  was already in `requirements.txt`. Verified the import succeeds and a `DATABASE_URL` env var
  is honoured when set before `import app`.

### 5.8 `normalize_ingredients` has complex, overlapping logic (backend/app.py:278-357)

The function has multiple code paths that check `KEEP_TOGETHER` phrases, with some redundant checks. The logic is hard to follow and may produce unexpected results for edge cases.

**Fix:** Refactor into smaller, well-named helper functions with clear logic.

- [x] **FIXED 2026-08-05** — Refactored `normalize_ingredients` (in `utils.py`, not `app.py`) into
  staged, single-responsibility helpers: `_is_skip_token`, `_singularize`, `_match_keep_together`,
  then a clean phrase-guard → KEEP_TOGETHER → comma/space-token path. Removed the two dead
  `parts = ...` assignments and the redundant second KEEP_TOGETHER loop. Regression-verified
  via the original `git HEAD` implementation across 15 ingredient cases (identical output).

### 5.9 `generate_ingredients` is a simple keyword matcher (backend/utils.py:188-234)

The function uses a series of `if "keyword" in name` checks to guess ingredients. This doesn't scale and will miss many meal types.

**Fix:** Consider a more robust approach, such as:
- A configurable mapping file (JSON/YAML)
- Integration with an ingredient database API
- Machine learning model for ingredient prediction

- [x] **FIXED 2026-08-05** — Replaced the inline `if "keyword" in name` chain (in `utils.py`,
  not `app.py`) with a config-driven model: `backend/ingredient_rules.json` defines an ordered
  `pasta_base` (exclusive) + `flavor_additions` (additive) keyword map, loaded once by
  `_load_ingredient_rules()` with a safe fallback if the file is missing (PyInstaller-bundled
  via `app.spec` `datas`). Added rules for `ramen`, `curry`, `kebab`, `poke`, `pad thai`,
  `wrap`, `chili` so those meals now produce richer ingredients (e.g. Ramen →
  `['ramen','pork','bean sprout','green onion']`). Verified that the 11 meals without a new
  rule are **byte-identical** to the original matcher; only the 4 newly-ruled meals change.

### 5.10 `categorize_ingredient` has limited coverage (backend/utils.py:329-359)

Only handles a small set of ingredients. Many common ingredients fall through to "Other".

**Fix:** Expand the category mappings or use a more sophisticated approach.

- [x] **FIXED 2026-08-05** — Rewrote `categorize_ingredient` in `backend/utils.py` as a keyword
  list + substring matcher (`_match_any`) so plural / multi-word tokens bucket correctly
  instead of falling through to `Other`. Added keyword tuples `_PROTEIN_WORDS`,
  `_PRODUCE_WORDS`, `_DAIRY_WORDS`, `_GRAIN_WORDS` (the latter extended with common pasta
  shapes: spaghetti, macaroni, lasagna, penne, fettuccine, etc.) and first-match-wins
  ordering. Now `tomatoes`→Produce, `ground beef`→Protein, `black beans`→Produce,
  `shredded cheese`→Dairy, `whole milk`→Dairy, `chicken breast`→Protein. Verified via a
  Python check: all 16 representative ingredients bucket correctly (Produce 8, Protein 3,
  Dairy 2, Grains 2, Other 0) and an end-to-end `/grocery` run on a temp DB places
  spaghetti in Grains with no items in Other.

### 5.11 Grocery list doesn't handle "count" unit display properly (backend/app.py:825-827)

```python
qty_str = f"{display_qty}" if unit == "count" else f"{display_qty} {unit}"
if unit != "count" and display_qty > 1:
    qty_str += "s"  # re-add plural to unit if relevant
```

The pluralization logic is simplistic (just adds "s") and doesn't handle irregular plurals (e.g., "1 lb" -> "2 lbs" is correct, but "1 tomato" -> "2 tomatoes" is wrong).

- [x] **FIXED 2026-08-04** — count-unit items now pluralize the *item name* (not just append "s"
  to a unit) via `pluralize_word()` in `utils.py` (irregulars: tomato→tomatoes,
  potato→potatoes; mass nouns left unchanged: cheese/rice/pepper; regular suffix rules:
  radish→radishes, y→ies, o→oes, +s). Unit pluralization (lb→lbs, can→cans) is unchanged.
  **Verified:** all pluralize_word cases + end-to-end `build_grocery_list` on a temp DB
  renders `Tomatoes 8`, `Potato 1`, `Cheese 2`, `Beef 2 lbs`.

### 5.12 No undo/redo for meal actions

Once a meal is deleted or a day is rerolled, there's no way to undo. The frontend uses `prompt()` for editing, which is not user-friendly.

**Fix:** Add undo functionality or use proper modal dialogs instead of `prompt()`.

- [x] **FIXED 2026-08-05** — Added a time-limited Undo toast in `App.jsx`: rerolling a day is
  reversible via a new `PUT /menu/<day>` endpoint (`set_menu_day` in `menu_service.py`);
  deleting a meal is reversible via recreate on undo; and meal editing now uses an
  inline form instead of `prompt()` (`editMeal`/`cancelEdit`/`saveEdit`). The backend
  `PUT /menu/<day>` route validates the meal payload (`{name, ingredients}`, else 400)
  and is exercised by the test client.

### 5.13 Weekly menu stores snapshot, not reference (backend/app.py:684-705)

When generating a weekly menu, the full meal dict (including ingredients) is stored as JSON. If a meal is later edited, the menu still shows the old version.

**Fix:** Store only the meal ID and fetch the current meal data when displaying.

- [x] **FIXED 2026-08-05** — `WeeklyMenu.meals` now stores **meal ids** (`generate_week` /
  `reroll_day` / `set_menu_day` in `menu_service.py`), and meals are resolved to their
  *current* data at read time via `expand_menu()` (`GET /menu/week`, `POST /menu/reroll`,
  `PUT /menu/<day>`) and inside `grocery_service.build_grocery_list()` — so editing a meal
  is now reflected in the grocery list and menu display. New Alembic revision `8b1c2d3e4f5a`
  backfills existing snapshot menus (`{day: {id,name,ingredients}}` → `{day: id}`); verified
  on a temp DB via the Flask test client + `flask db upgrade` (backfill + live reflection +
  reroll/set-menu-day store ids + export expands). `expand_menu()` keeps a backward-compat
  shim for any legacy full-snapshot menu (e.g. from `/import`). The frontend API contract is
  unchanged (still full meal dicts), so no frontend changes were needed.

### 5.14 No meal categories or tags

Meals are just names with ingredients. There's no way to categorize meals (e.g., "Italian", "Mexican", "Vegetarian", "Quick", "Expensive").

**Fix:** Add a `category` or `tags` field to the Meal model.

- [x] **FIXED 2026-08-05** — Added an optional `category` (String(50)) column to `Meal` (new
  Alembic revision `7a9c4f2e1b86` off `6c296b498bf1`); `POST /meal`, `PUT /meal/<id>`, and
  the `_ingest()` shared by `/import` + `/import-file` now accept + sanitize it
  (reusing §8.6 `sanitize_text`). Added `GET /meals/categories` (distinct, non-null list) and
  `?category=` filter on `/meals` (case-insensitive partial). Frontend: category selector in
  `AddMeal`, in the inline-edit row, and a category filter dropdown on the "All Meals" list;
  category is shown inline next to each meal name. Verified via Flask test client on a temp DB
  (column + migration apply, create/update/import/filter + categories endpoint) and
  `npm run lint` + `npm run build` are green. `dinner.db` was not modified.

### 5.15 No meal history tracking

Old weekly menus are stored in the database but there's no UI to view them. The README says "Weekly menus reset as new ones are generated" but this is misleading — they're actually stored.

**Fix:** Add a menu history view in the frontend.

- [x] **FIXED 2026-08-05** — Added `GET /menus` (new `list_menus()` in
  `backend/services/menu_service.py`, route in `backend/routes/menu.py`) returning every
  saved `WeeklyMenu` newest-first, with each menu's stored meal ids resolved to full meal
  dicts via the existing `expand_menu()` (§5.13) so the history reflects current meals.
  Frontend: new `History.jsx` component wired into `App.jsx` (fetches `/menus` on demand;
  shows each saved menu's day→meal rows). Verified on a temp DB via the Flask test client:
  `GET /menus` returns 200 with the expected count and expanded meals, newest-first;
  `npm run lint` + `npm run build` green. `dinner.db` was not modified.

### 5.16 No way to export grocery list

The grocery list can only be viewed in the app. There's no way to export it as text, PDF, or print it.

**Fix:** Add an export button (text/CSV/PDF).

- [x] **FIXED 2026-08-05** — Added `GET /grocery/export?format=csv|text` returning a
  `Content-Disposition: attachment` download (CSV with `Category,Item,Quantity` rows;
  plain text grouped by category), plus "Download CSV" / "Download Text" links in
  `GroceryList.jsx` (shown after the list is generated). PDF/print left for the browser;
  CSV+text cover the practical export need.

### 5.17 No meal detail view in frontend

The weekly menu shows meal names but not ingredients. Users have to go to the "All Meals" section to see ingredients.

**Fix:** Add a meal detail view or tooltip showing ingredients.

- [x] **FIXED 2026-08-05** — `Menu.jsx` now shows each day's **ingredients inline**: clicking a
  meal name toggles an expandable sublist of its ingredients (state: `openDay` in the component),
  so users no longer need to jump to "All Meals" just to see what a planned meal contains.
  Ingredients come from the already-expanded meal dict (§5.13 `expand_menu()`). Verified:
  `npm run lint` + `npm run build` pass with the new toggle markup.

### 5.18 No search/filter for meals

The "All Meals" list shows all meals with no search or filter functionality.

**Fix:** Add a search bar and category filters.

- [x] **FIXED 2026-08-05** — Backend `GET /meals?search=<term>` filters by name
  (case-insensitive `ilike` substring, length-capped/sanitized via §8.6 `sanitize_text`); the
  existing category filter already covered §5.18's "category filters". Frontend: a "Search meals…"
  input in the *All Meals* card (`App.jsx`) appends `&search=` to the paginated fetch and resets
  to page 1 on change. Verified on an isolated temp DB: `/meals?search=chicken` → 1 result,
  `/meals?search=xyz` (no match) → 0 total; `npm run lint` + `npm run build` green.

### 5.19 `clean_meal_name` typo fixes are hardcoded (backend/app.py:257-276)

```python
fixes = {
    "Lasagnaa": "Lasagna",
    "Taco Boowl": "Taco Bowl",
    "Veggistir- Fry": "Veggie Stir Fry"
}
```

This is not extensible. New typos require code changes.

**Fix:** Use a more general approach (e.g., fuzzy matching, or a configurable mapping file).

- [x] **FIXED 2026-08-05** — Typo fixes moved out of source into a data file:
  `backend/meal_name_fixes.json` (extensible, human-editable). `clean_meal_name` in
  `utils.py` now loads it once (cached in `_NAME_FIXES`, file missing → empty map, no crash)
  and applies the Title-Cased lookup after normalising whitespace/casing. The mapping covers
  the original 3 typos plus common OCR ones (Lasagnaa→Lasagna, Taco Boowl→Taco Bowl,
  Veggistir-Fry→Veggie Stir Fry, Spaghet→Spaghetti, Burgur->Burger, Chiken->Chicken,
  Pico De Gall→Pico de Gallo). Verified: `clean_meal_name("Lasagnaa")`→"Lasagna",
  `clean_meal_name("taco boowl")`→"Taco Bowl". The data file is also included in the PyInstaller
  bundle (`--add-data`) so OCR import keeps working in the packaged exe.

### 5.20 No graceful shutdown handling

The Flask app doesn't handle SIGINT/SIGTERM gracefully. When packaged as an exe, closing the window might not cleanly shut down the server.

**Fix:** Add signal handlers for graceful shutdown.

- [x] **FIXED 2026-08-05** — Added SIGINT/SIGTERM handlers in `app.py`
  (`_handle_shutdown` logs the signal and raises `SystemExit(0)`; `_register_signal_handlers`
  installs them in the main thread only). Handlers are registered in `__main__` so the
  packaged exe and dev server both shut down cleanly on close/Ctrl-C. Verified at import time:
  both `signal.SIGINT` and `signal.SIGTERM` have non-default handlers installed.

### 5.21 No rate limiting

No rate limiting on any endpoints. A malicious script could spam the API.

**Fix:** Add rate limiting using Flask-Limiter.

- [x] **FIXED 2026-08-05** — Added `Flask-Limiter` (pinned in `requirements.txt`:
  `Flask-Limiter==4.1.1` + transitive `limits`, `ordered-set`, `deprecated`, `wrapt`) via a
  dedicated `backend/limiter.py` (avoids the app↔routes import cycle): global `default_limits`
  of `120 per minute` on all routes, plus a stricter `5/minute` decorator on the OCR-heavy
  `POST /upload-menu`. In-memory storage suits the single-process desktop exe. Verified on an
  isolated temp DB: a burst of 125 requests to `/health` returns 200 for the first 119 and
  429 on the 121st, confirming the limit is enforced.

### 5.22 No CSRF protection

POST/PUT/DELETE endpoints have no CSRF protection. While this is a local app, it's still a concern if the app is ever exposed.

**Fix:** Add CSRF protection using Flask-WTF or similar.

- [x] **FIXED 2026-08-05** — Implemented CSRF defense via **custom-header verification** (the OWASP
  "custom request header" pattern, which is the appropriate mitigation for this no-cookie JSON
  API rather than Flask-WTF form-token CSRF):
  - Backend (`app.py`): a `@app.before_request` hook (`_csrf_protect`) rejects any
    `POST/PUT/PATCH/DELETE` that does not carry the header `X-Requested-With: XMLHttpRequest`,
    returning `403 {"error": "CSRF verification failed"}`. `GET/HEAD/OPTIONS/TRACE` are exempt
    (and CORS preflights are not blocked).
  - Frontend (`api.js`): `apiFetch` now attaches `X-Requested-With: XMLHttpRequest` (via
    `new Headers(...)`) to every request, preserving existing `Content-Type` headers for
    JSON and not breaking `FormData` uploads.
  Rationale: in production the app is same-origin (Flask serves the React frontend) and uses no
  cookies/sessions, so a cross-site browser can only issue a *plain* cross-origin POST/PUT/DELETE
  — which cannot set the custom header without explicit CORS permission (prod grants none) → 403.
  Verified on an isolated temp DB: `GET /health`→200, `POST /meal` w/o header→403, `POST /meal`
  w/header + bad body→400 (CSRF passes, validation applies), `POST /meal` w/header + valid→200
  + persisted. `dinner.db` untouched.

---

## 6. Low-Priority / Polish Issues

### 6.1 Emoji in code comments and strings

The code uses emojis extensively in comments and print statements (e.g., `print("🚀 RUNNING THIS FILE")`, `# ✅ MODEL FIRST`, `# 🔥 convert to OpenCV format`). While this is a style choice, it can cause issues with some terminals and makes the code harder to search.

- [x] **FIXED 2026-08-07** — All backend `.py` emoji removed from comments/strings (verified: 0 emoji
  characters remain in `backend/**/*.py`). The print-statement emojis were already gone (§5.2/§5.3 logging);
  the remaining ones were 7 leading `# ❌` comment markers in `utils.py` (OCR junk filter), now plain `# …`
  comments. Scope deliberately **limited to backend prose comments/strings** — frontend emoji are intentional
  UI icons (🍽/✏️/🔄/✕ close buttons in `App.jsx`/`Menu.jsx`) and are left intact.


### 6.2 Inconsistent code formatting

The backend code has inconsistent indentation, spacing, and naming conventions. Some functions use camelCase, others use snake_case. The frontend uses inline styles exclusively instead of CSS classes.

### 6.3 No `.editorconfig`

No editor configuration file. Different developers may use different indentation, line endings, etc.

**Fix:** Add a `.editorconfig` file.

- [x] **FIXED 2026-08-07** — Added `.editorconfig` (4-space for Python, 2-space for JS/CSS/markdown,
  UTF-8, LF, trailing-newline + trim-whitespace).


### 6.4 No pre-commit hooks

No pre-commit hooks for linting, formatting, or testing.

**Fix:** Add pre-commit hooks using `pre-commit` framework.

### 6.5 Frontend uses inline styles exclusively

All styling in `App.jsx` is done via inline style objects. This makes the code verbose and hard to maintain. There's no CSS file being imported (the `App.css` and `styles.css` files exist but `styles.css` is empty and `App.css` is from the Vite template).

- [x] **NOTE 2026-08-07** — Stale as written. `main.jsx` **does** import `./index.css` (the active
  light/dark theme + `#root` layout), and `App.css` was **never** imported → removed as dead code (§6.9,
  §7.1). The app remains inline-style-based by design.


**Fix:** Move styles to CSS files or use a CSS-in-JS library.

### 6.6 No dark mode toggle

The frontend has a dark color scheme hardcoded (`#121212` background, `#1e1e1e` cards) but there's no toggle. The `index.css` has dark mode styles but they're not connected to the app.

**Fix:** Add a dark/light mode toggle.

### 6.7 No responsive design

The frontend has a `maxWidth: "900px"` but no media queries or responsive breakpoints. It will look bad on mobile devices.

**Fix:** Add responsive design with media queries.

### 6.8 No favicon being used

The frontend has a `favicon.svg` in `public/` but it's not referenced in `index.html`.

- [x] **FIXED 2026-08-07** — Already satisfied (stale as written): `frontend/public/favicon.svg` exists
  and `frontend/index.html` line 5 references it via `<link rel="icon" href="/favicon.svg" />`.


### 6.9 `index.css` is from Vite template

The `index.css` file contains Vite template styles (hero, counters, etc.) that are not used by the app. The app uses inline styles instead.

- [x] **FIXED 2026-08-07** — Stale premise: `index.css` is **not** unused Vite-template junk. It is
  imported by `main.jsx` and is the active light/dark theme (`:root` vars consumed by its own `body`/
  `#root` rules; `#root { width: 1126px; max-width: 100%; margin: auto }` centers the app and is relied
  on by the inline-styled frontend). Left intact; the genuinely-dead `App.css` (never imported) was
  removed instead.


### 6.10 No error boundaries in React

If any component throws an error, the entire app crashes with no fallback UI.

**Fix:** Add error boundaries.

### 6.11 No loading states in frontend

When fetching data, there's no loading indicator. The UI just appears/disappears.

### 6.12 `prompt()` used for editing meals

The `editMeal` function uses `window.prompt()` for input, which is not user-friendly and can't be styled.

**Fix:** Use a proper modal dialog.

- [x] **FIXED 2026-08-05** — `prompt()` replaced by an inline edit form inside each meal
  row in `App.jsx` (name + ingredients inputs with Save/Cancel); see §5.12.

### 6.13 No confirmation for destructive actions

Deleting a meal or rerolling a day has no confirmation dialog.

**Fix:** Add confirmation dialogs.

- [x] **FIXED 2026-08-05** — Destructive actions (delete meal, reroll day) now show a
  6-second Undo toast instead of acting irreversibly (see §5.12). A pre-action confirm
  dialog is still a possible future polish but the actions are now reversible.

### 6.14 No keyboard shortcuts

No keyboard shortcuts for common actions (e.g., Enter to add a meal, Escape to cancel).

### 6.15 No accessibility attributes

The frontend has no ARIA labels, no semantic HTML, no keyboard navigation support.

---

## 7. Dead Code & Scaffolding

### 7.1 Empty files (all zero bytes)

| File | Intended Purpose |
|------|-----------------|
| `backend/config.py` | Configuration management |
| `backend/models.py` | Database models |
| `backend/routes/meals.py` | Meal-related routes |
| `backend/routes/menu.py` | Menu-related routes |
| `backend/routes/grocery.py` | Grocery list routes |
| `backend/services/menu_service.py` | Menu generation logic |
| `backend/services/grocery_service.py` | Grocery list logic |
| `frontend/src/api.js` | API client |
| `frontend/src/components/AddMeal.jsx` | Add meal form |
| `frontend/src/components/GroceryList.jsx` | Grocery list display |
| `frontend/src/components/Menu.jsx` | Weekly menu display |
| `frontend/src/styles.css` | App styles |

These files were created as part of a refactoring effort but were never populated. They serve as scaffolding that was never completed.

### 7.2 Unused global variable

`current_week` (backend/app.py:27-28) is declared but never used.

- [x] **FIXED 2026-08-05** — `current_week` no longer exists anywhere in `backend/` (the §4.1
  modularization removed the monolith that declared it). Verified via grep: zero matches.

### 7.3 Unused imports

- [x] **FIXED 2026-08-05** — Resolved. The listed imports were all stale line references to the
  old ~950-line monolith `app.py`; the §4.1 split moved OCR imports (`cv2`, `numpy`,
  `PIL.Image`) into `routes/meals.py` and removed the unused `requests` (§4.9). The only
  leftover unused import in the current thin `app.py` was `import shutil` (no call site) — removed;
  everything else (`os`, `sys`, `signal`, `logging`, `threading`, `webbrowser`, `load_dotenv`,
  `Flask`/`jsonify`/`send_from_directory`/`request`, `HTTPException`, `CORS`, `Migrate`/`upgrade`/`stamp`,
  `pytesseract`, `Config`/`db`/`tesseract_path`, the four blueprints, `limiter`, `register_cli`)
  is used. Verified by grep.

### 7.4 Build artifacts in repository

- `backend/build/` — PyInstaller build artifacts
- `backend/dist/` — Compiled executables
- `backend/instance/dinner.db` — SQLite database (gitignored but present)

These should not be in the repository. The `.gitignore` correctly ignores them, but they're present in the working directory.

### 7.5 `backup.json` in repository

The `backup.json` file (backend/backup.json) contains 60+ weekly menus and is used by the `/import-file` endpoint. It's sample/test data that shouldn't be in the main repository.

---

## 8. Security Concerns

### 8.1 No authentication or authorization

All endpoints are publicly accessible. The maintenance endpoints (`/fix-data`, `/init-db`, `/import-file`) have no protection.

**Risk:** Anyone who can reach the server can modify or delete all data.

**Fix:** Add authentication (even a simple password) for maintenance endpoints, or remove them from production builds.

- [x] **FIXED 2026-08-04** — `/fix-data` and `/init-db` are removed from the HTTP surface
  entirely and are now `flask --app app {fix-data|init-db}` CLI commands only, so they
  cannot be reached by anyone who can reach the server. `/import-file` is retained as a
  non-destructive (additive + deduping) user-facing import feature per §5.4, not a
  maintenance operation.

### 8.2 CORS is wide open (backend/app.py:30)

```python
CORS(app)
```

**Risk:** Any website can make cross-origin requests to the API.

**Fix:** Restrict to specific origins or disable CORS for the desktop app.

- [x] **FIXED 2026-08-04** — duplicate of §4.3: `app.py` now uses
  `CORS(app, origins=app.config["CORS_ORIGINS"])` (dev = `localhost:5173`; prod is same-origin
  since Flask serves the frontend, so no CORS is needed there). The stale "wide open"
  docstring/code referenced in this issue is gone.

### 8.3 No CSRF protection

POST/PUT/DELETE endpoints have no CSRF tokens.

**Risk:** If the app is ever exposed to the internet, a malicious website could trick users into making unwanted changes.

**Fix:** Add CSRF protection using Flask-WTF or similar.

- [x] **FIXED 2026-08-05** — Same as §5.22: custom-header verification — a `before_request` hook
  403s any `POST/PUT/PATCH/DELETE` lacking `X-Requested-With: XMLHttpRequest`, and `apiFetch`
  attaches it to every request. Appropriate for this no-cookie, same-origin JSON API (see §5.22).

### 8.4 No rate limiting

**Risk:** The API can be spammed, potentially causing denial of service.

**Fix:** Add rate limiting using Flask-Limiter.

- [x] **FIXED 2026-08-05** — Same as §5.21: Flask-Limiter with a 120/min default limit on all
  routes and a 5/min limit on `POST /upload-menu`. Verified via a 125-request burst (429 at
  the 121st).

### 8.5 Secrets in `.env` file

The `.env` file contains `OPENAI_API_KEY=your_key_here` (a placeholder). If a real key is added, it should never be committed to the repository. The `.gitignore` correctly ignores `.env` files, but the `example.env` file is in the repository with a placeholder.

**Risk:** Low (placeholder is not a real key), but the pattern should be followed.

- [x] **FIXED 2026-08-05** — Removed the stale `OPENAI_API_KEY=your_key_here` placeholder from
  `example.env` (OpenAI is no longer used by the backend — §4.9); the file now documents the
  one real override, `DATABASE_URL=sqlite:///dinner.db` (read by §5.7). Kept `.env`
  gitignored (`.env` / `.env.*` / `*.env`) and **fixed** `.gitignore` to explicitly *track*
  the `example.env` template via a `!example.env` negation (previously `*.env` accidentally
  ignored the template). Verified with `git check-ignore`: `example.env` is no longer ignored,
  while `.env` and `instance/dinner.db` remain ignored.

### 8.6 No input sanitization

User input (meal names, ingredients) is stored in the database without sanitization. While SQLAlchemy parameterizes queries (preventing SQL injection), the stored data could contain XSS payloads if displayed in the frontend without escaping.

**Risk:** Stored XSS if the frontend doesn't properly escape data.

**Fix:** Sanitize input on the backend and ensure the frontend escapes all user-generated content.

- [x] **FIXED 2026-08-05** — Added `sanitize_text()` / `sanitize_ingredients()` in `utils.py`
  (strips NUL + ASCII control chars, collapses whitespace, caps length) and applied them in
  `POST /meal`, `PUT /meal/<id>`, and the `_ingest()` shared by `/import` + `/import-file`.
  Verified via Flask test client on a temp DB: control chars/whitespace trimmed, 100-char
  name cap enforced, PUT update sanitized, and imported payloads sanitized + empties skipped.
  Frontend risk is already mitigated: the app uses no `dangerouslySetInnerHTML`, so React
  escapes all user text by default; the `<script>alert(1)</script> burger` case is shown,
  not executed.

### 8.7 Debug mode is off but no error handling

`app.run(debug=False)` is correct for production, but there's no custom error handler. Unhandled exceptions return a generic 500 error with the exception message, which could leak sensitive information.

**Fix:** Add custom error handlers that return generic error messages in production.

- [x] **FIXED 2026-08-05** — Registered two `@app.errorhandler`s in `app.py`:
  `HTTPException` → returns `{"error": <e.name>}` with the proper status (404→"Not Found",
  405→"Method Not Allowed", etc.); catch-all `Exception` → `logger.exception(...)` (full
  traceback stays **server-side**) and returns `{"error": "Internal server error"}` with 500,
  so no exception text/paths reach the client. The route-level `except` blocks in
  `routes/{menu,grocery,meals}.py` now log via `logger.exception` and return the same generic
  500 message instead of `str(e)`. Verified on an isolated temp DB: a route that raises
  `RuntimeError("SECRET INTERNAL: ...hunter2...")` returns 500 `{"error":"Internal server
  error"}` with the secret **not** present in the response body; 404 returns
  `{"error":"Not Found"}`.

---

## 9. Performance & Scalability

### 9.1 No database indexing

The `Meal` model has no indexes beyond the primary key. Queries like `Meal.query.filter(db.func.lower(Meal.name) == name_lower)` could be slow with large datasets.

**Fix:** Add indexes on frequently queried columns (e.g., `name`).

### 9.2 No pagination on list endpoints

The `/meals` endpoint returns all meals at once. With a large database, this could be slow.

**Fix:** Add pagination.

### 9.3 No caching

No caching is used anywhere. Repeated requests for the same data (e.g., `/meals`) hit the database every time.

**Fix:** Add caching using Flask-Caching.

### 9.4 OCR processing is synchronous

The `/upload-menu` endpoint processes images synchronously. Large images or many uploads could block the server.

**Fix:** Use a task queue (e.g., Celery) for OCR processing.

### 9.5 No connection pooling

SQLAlchemy uses a single connection by default. With concurrent requests, this could be a bottleneck.

**Fix:** Configure connection pooling in SQLAlchemy.

### 9.6 Weekly menu generation uses `random.sample`

`random.sample(meals, 7)` loads all meals into memory and samples from them. With a very large database, this could be slow.

- [x] **FIXED 2026-08-05** — `menu_service.generate_week` now fetches 7 random meals at the DB level
  (`db.session.query(Meal).order_by(db.func.random()).limit(7).all()`) with a single `COUNT` guard
  (`db.session.query(db.func.count()).select_from(Meal).scalar() < 7`) instead of `Meal.query.all()`
  + `random.sample`. SQLite `RANDOM()` returns distinct rows, so the no-internal-repeats guarantee
  (§2) is preserved; `random` is still imported (used by `pick_takeout`/`decide`/`reroll_day`/`pick_today`).
  Verified: `test_menu_and_grocery_flow` (which exercises `/menu/week`) still passes → 200, 7 days, ingredients.

---

## 10. Code Quality & Conventions

### 10.1 No code style guide for Python

There's no `pyproject.toml`, `setup.cfg`, or `.flake8` file. No `black`, `isort`, or `flake8` configuration.

**Fix:** Add `pyproject.toml` with formatting and linting configuration.

### 10.2 No code style guide for JavaScript

The `eslint.config.js` exists but the rules are minimal. There's no `prettier` configuration.

**Fix:** Add Prettier and expand ESLint rules.

### 10.3 Inconsistent naming conventions

- Backend: Mix of snake_case (Python convention) and some camelCase
- Frontend: Mix of camelCase (JavaScript convention) and some PascalCase for components
- Database: `WeeklyMenu` (PascalCase), `meal.name` (snake_case)

### 10.4 No type hints in Python

The backend code has no type hints, making it harder to understand and maintain.

**Fix:** Add type hints to all functions.

### 10.5 No docstrings

No function has a docstring. The code relies on inline comments (often emoji-prefixed) for documentation.

**Fix:** Add docstrings to all public functions.

### 10.6 Inline styles in frontend

All styles are inline objects in `App.jsx`. This makes the code verbose and hard to maintain.

**Fix:** Move styles to CSS files or use a CSS-in-JS library.

### 10.7 Emoji in comments

While a style choice, the extensive use of emoji in comments (e.g., `# 🔥 convert to OpenCV format`, `# ✅ check duplicate`) makes the code harder to search and can cause issues in some environments.

### 10.8 Duplicate code patterns

- `import random` appears 3 times
- `used_today = set()` appears 2 times
- `loadMenu` function is duplicated in frontend
- `normalize_ingredients` and `merge_ingredient` have overlapping logic

### 10.9 No constants file

Magic strings and numbers are scattered throughout the code (e.g., day names, category names, OCR config strings).

**Fix:** Extract constants into a separate file.

---

## 11. Testing
### 11.1 No tests exist

There are zero test files in the entire codebase. No `tests/` directory, no `test_*.py` files, no `*.test.jsx` files.

**Risk:** Any change could introduce regressions without detection.

**Fix:** Add tests for:

- Backend: API endpoints, utility functions (ingredient normalization, grocery list generation, OCR filtering)
- Frontend: Component rendering, user interactions

- [x] **FIXED 2026-08-05** — Added a `pytest` test harness run against a throwaway temp SQLite DB (via `DATABASE_URL` set before `import app`, so `dinner.db` is never touched). `tests/conftest.py` provides `app`/`client` fixtures with per-test `create_all`/`drop_all` and per-test `limiter.reset()`; `frontend/...` `tests/test_app.py` covers `/health`, `404`/`500` generic errors (§8.7), CSRF header check (§8.3), meal CRUD, search + category (§5.18/§5.14), the menu+grocery flow (§5.13/§5.10), and rate limiting (§5.21, `@pytest.mark.slow`, deselected by default). Run with `pip install -r requirements-dev.txt` then `pytest` (or `pytest -m slow` for the rate-limit test). All 8 tests green.

### 11.2 No test framework configured

No `pytest`, `unittest`, `jest`, or `vitest` configuration.

**Fix:** Add `pytest` for backend and `vitest` for frontend.

- [x] **FIXED 2026-08-05** — Added `pytest.ini` (with `pythonpath = backend`, `testpaths = tests`,
  and a default `-m "not slow"` marker) plus `requirements-dev.txt` (pinning `pytest==7.4.3`).
  The frontend still has **no** test runner (Vite is build-only); adding `vitest` for
  component tests is deferred as low-priority — the backend now has a real regression net.

### 11.3 No CI/CD pipeline

No GitHub Actions, GitLab CI, or other CI/CD configuration.

**Fix:** Add a CI pipeline that runs tests and linting on every push.

---

## 12. Documentation

### 12.1 README is incomplete

The README has:
- A "Getting Started" section that's cut off (no actual setup instructions)
- No API documentation
- No explanation of the data model
- No troubleshooting section
- No contribution guidelines

**Fix:** Complete the README with:
- Full setup instructions (backend + frontend)
- API endpoint documentation
- Data model description
- Troubleshooting guide
- Contribution guidelines

### 12.2 No API documentation

There's no OpenAPI/Swagger spec, no Postman collection, no API documentation.

**Fix:** Add an OpenAPI spec or use `flask-smorest` for auto-generated API docs.

### 12.3 No CONTRIBUTING.md

No contribution guidelines.

**Fix:** Add a `CONTRIBUTING.md` file.

### 12.4 No LICENSE file

The README says "MIT (or whatever you want)" but there's no actual LICENSE file.

**Fix:** Add an MIT LICENSE file.

### 12.5 No CHANGELOG

No changelog to track changes between versions.

**Fix:** Add a `CHANGELOG.md` file.

### 12.6 No architecture documentation

No diagrams, no architecture decision records (ADRs), no explanation of how the components interact.

**Fix:** Add architecture documentation.

### 12.7 `example.env` is minimal

Only contains `OPENAI_API_KEY` and `DATABASE_URL`, but the app doesn't use either of these.

**Fix:** Update `example.env` to reflect actual configuration needs.

### 12.8 No AGENTS.md or similar

No file documenting how to work with the codebase for AI assistants or new developers.

**Fix:** Add an `AGENTS.md` or `CLAUDE.md` file.

---

## 13. High-Value Features to Add

### 13.1 Meal Categories / Tags

**Value:** High | **Effort:** Medium

Allow users to tag meals with categories (e.g., "Italian", "Mexican", "Vegetarian", "Quick", "Comfort Food"). This enables:
- Filtering meals by category
- Generating menus with category diversity (e.g., "at least one vegetarian meal per week")
- Better meal organization

**Implementation:** Add a `category` or `tags` field to the Meal model, add a category filter in the frontend.

### 13.2 Meal History

**Value:** High | **Effort:** Low

Show past weekly menus so users can revisit old plans or avoid repeating meals too soon.

**Implementation:** Add a "Menu History" view in the frontend that fetches all `WeeklyMenu` records.

### 13.3 Grocery List Checkoff

**Value:** High | **Effort:** Low

Allow users to check off items as they shop. This is a core use case for a grocery list app.

**Implementation:** Add a `purchased` boolean to grocery list items, add checkboxes in the frontend.

### 13.4 Meal Detail View

**Value:** High | **Effort:** Low

Show ingredients and other details when viewing a meal in the weekly menu, without navigating to the "All Meals" section.

**Implementation:** Add a modal or expandable section in the menu view showing meal details.

### 13.5 Search & Filter Meals

**Value:** High | **Effort:** Low

As the meal database grows, finding specific meals becomes difficult.

**Implementation:** Add a search bar and category filters to the "All Meals" section.

### 13.6 Dietary Preferences / Restrictions

**Value:** High | **Effort:** Medium

Allow users to mark meals as vegetarian, vegan, gluten-free, etc., and filter menus accordingly.

**Implementation:** Add dietary tags to meals, add preference settings.

### 13.7 Meal Ratings & Favorites

**Value:** Medium | **Effort:** Medium

Let users rate meals and prioritize favorites when generating menus.

**Implementation:** Add a `rating` field to Meal, add a "favorites" filter.

### 13.8 Export Grocery List

**Value:** Medium | **Effort:** Low

Export the grocery list as text, CSV, or PDF for printing or sharing.

**Implementation:** Add an export button that formats the grocery list as text/CSV.

### 13.9 Custom Weekly Menu Days

**Value:** Medium | **Effort:** Low

Allow users to choose which days to plan for (e.g., weekdays only, or a custom set of days).

**Implementation:** Add a day selector before generating the menu.

### 13.10 Meal Prep Notes

**Value:** Medium | **Effort:** Low

Allow users to add prep instructions or notes to meals (e.g., "marinate overnight", "pre-cook rice").

**Implementation:** Add a `notes` field to Meal, display in meal detail view.

### 13.11 Shopping List Category Customization

**Value:** Medium | **Effort:** Medium

Let users customize which ingredients go in which category, or add custom categories.

**Implementation:** Add a category management UI, store custom categories in the database.

### 13.12 Meal Photos

**Value:** Medium | **Effort:** Medium

Allow users to add photos to meals for visual reference.

**Implementation:** Add an image upload field to Meal, store images as files or base64.

### 13.13 Dark Mode Toggle

**Value:** Low | **Effort:** Low

The frontend already has a dark color scheme; just add a toggle.

**Implementation:** Add a toggle button that switches CSS classes.

### 13.14 Mobile-Responsive Design

**Value:** Medium | **Effort:** Medium

The frontend is not responsive. Add media queries for mobile devices.

**Implementation:** Add responsive CSS with media queries.

### 13.15 Data Backup Automation

**Value:** Medium | **Effort:** Low

Automatically back up the database to a JSON file on a schedule or on exit.

**Implementation:** Add a backup endpoint, schedule it with a background thread.

### 13.16 Undo/Redo for Actions

**Value:** Medium | **Effort:** Medium

Allow users to undo meal deletions, rerolls, and other actions.

**Implementation:** Add an action history stack, add undo button.

- [x] **FIXED 2026-08-05** — Implemented as a simple time-limited Undo toast (§5.12):
  reroll-day undo via `PUT /menu/<day>`, delete-meal undo via recreate, and inline-edit
  Save/Cancel. A full action-history stack remains future work.

### 13.17 Meal Planning Calendar View

**Value:** Medium | **Effort:** Medium

Show the weekly menu in a calendar format instead of a list.

**Implementation:** Add a calendar component to the frontend.

- [x] **FIXED 2026-08-07** — Added a read-only `Calendar.jsx` (audit B1): a Mon–Sun grid per saved
  `WeeklyMenu`, newest first, powered by the existing `GET /menus` (meals already expanded server-side,
  §5.13) — **no backend/DB changes**. Clicking a meal name expands its ingredients inline (mirrors
  `Menu.jsx`'s toggle); meals with no current food show "—". Wired into `App.jsx` as a tab that reuses
  the same `menuHistory`/`loadHistory` fetch as `History` (one fetch, two views). Verified:
  `npm run lint` clean + `npm run build` OK (22 modules); `dinner.db` untouched (Sushi/Burger/Pizza, 0 menus).
  An editable (dated) calendar is deferred — menus are currently relative Mon–Sun, not dated.

### 13.18 Nutrition Tracking

**Value:** Low | **Effort:** High

Track nutrition information for meals and the weekly menu.

**Implementation:** Integrate with a nutrition API (e.g., Spoonacular, Edamam).

- [x] **FIXED 2026-08-07** — Added a local-first, presence-based (v1) insight view (audit B2):
  `backend/nutrition_rules.json` (53 curated ingredients → macro tags: protein/veg/dairy/carbs/fiber/healthy_fat
  + `_targets_per_week`) + `services/nutrition_service.py` (`insights()` aggregates the last 4 `WeeklyMenu`s via
  `expand_menu`, tallies macro occurrences, compares to ×N-week targets to raise `low <macro>` flags, and emits
  rule-based swap suggestions — e.g. beef-heavy + low veg → "swap beef for chicken + greens"; low dairy/fiber →
  additions). New `GET /insights`. Frontend: `Insights.jsx` tab (macro progress bars + flags + suggestions).
  Unmapped ingredients are omitted (no network). Verified: `pytest` — `test_insights_requires_menu` (400 on empty)
  + `test_insights_low_dairy_flag` (Steak×7 ×2 weeks → `low dairy` flag + dairy suggestion) pass; `npm run lint`
  + `npm run build` OK; `dinner.db` upgraded to head with the 3 sample meals intact (extras column added).
  A full per-100g quantity-aware macro model (option B) is deferred as higher-effort future work.

### 13.19 Cloud Sync

**Value:** Low | **Effort:** High

Sync data across devices using a cloud backend.

**Implementation:** Add a sync endpoint, implement conflict resolution.

### 13.20 AI Meal Suggestions

**Value:** Low | **Effort:** High

Use AI (OpenAI API) to suggest meals based on ingredients on hand, dietary preferences, or past ratings.

**Implementation:** Integrate with OpenAI API, add a "Suggest Meals" button.

---

## 14. Quick Wins (1-2 hour fixes)

These are high-impact, low-effort fixes that should be done first:

1. **Remove duplicate `loadMenu` function** in App.jsx (lines 66-70)
2. **Add guard for empty meals in `reroll_day`** — return error if only 1 meal exists
3. **Add guard for empty meals in `decide`** — return error if no meals exist
4. **Fix hardcoded Tesseract path** — use `shutil.which("tesseract")` for cross-platform support
5. **Replace hardcoded API URLs** in frontend with relative URLs
6. **Add try/catch to all frontend fetch calls** with error feedback
7. **Remove duplicate `import random`** statements in app.py
8. **Remove unused `current_week` global** variable
9. **Remove unused dependencies** from requirements.txt (`openai`, `psycopg2-binary`)
10. **Add `/health` endpoint** for monitoring
11. **Add input validation** to `/meal` POST endpoint
12. **Add confirmation dialog** for meal deletion
13. **Add loading states** to frontend fetch calls
14. **Replace `prompt()` with a proper modal** for meal editing
   - [x] **FIXED 2026-08-05** — replaced with an inline edit form in the meal list (§5.12/§6.12).
15. **Add a LICENSE file** (MIT)
16. **Remove debug print statements** or convert to proper logging
17. **Add `.editorconfig`** for consistent formatting
18. **Fix `import_file` to accept a file path parameter** instead of hardcoded path

---

## 15. Recommended Roadmap

### Phase 1: Stabilize (1-2 weeks)
- Fix all critical bugs (Section 3)
- Add error handling to frontend fetch calls
- Add input validation to backend endpoints
- Fix cross-platform Tesseract path
- Remove unused dependencies
- Add health check endpoint
- Add basic logging

### Phase 2: Refactor (2-3 weeks)
- Complete the modularization (move code from app.py to routes/, services/, models.py, config.py)
- Split frontend into components
- Add type hints to Python code
- Add proper logging framework
- Add database migrations (Flask-Migrate)
- Add rate limiting
- Add CORS restrictions

### Phase 3: Test & Document (1-2 weeks)
- Add test framework (pytest + vitest)
- Write tests for backend API and utility functions
- Write tests for frontend components
- Add CI/CD pipeline
- Complete README with API docs
- Add CONTRIBUTING.md and LICENSE
- Add architecture documentation

### Phase 4: Enhance (Ongoing)
- Add meal categories/tags
- Add meal history view
- Add grocery list checkoff
- Add search/filter for meals
- Add meal detail view
- Add dark mode toggle
- Add responsive design
- Add export grocery list feature

### Phase 5: Future (Long-term)
- Nutrition tracking
- Cloud sync
- AI meal suggestions
- Mobile app
- Meal photos

---

## Summary

The Dinner Menu Generator is a functional but rough-around-the-edges application. The core features work, but the codebase has significant issues:

- **3 critical bugs** that can crash the app
- **10+ high-priority issues** including no error handling, security concerns, and no testing
- **20+ medium-priority issues** including code quality, performance, and maintainability problems
- **12 empty scaffold files** showing an incomplete refactoring effort
- **No tests, no CI/CD, minimal documentation**

The project would benefit from a structured refactoring effort, starting with the critical bug fixes and error handling, followed by completing the modularization that was started but never finished.

The most impactful improvements would be:
1. Fix the 3 critical bugs
2. Add error handling to frontend fetch calls
3. Complete the modularization (routes, services, models)
4. Add tests
5. Add meal categories/tags (high-value feature)

The codebase shows clear intent to be well-structured (the empty route/service/model files prove this), but the execution was left incomplete. With focused effort, this could be a solid, maintainable application.
