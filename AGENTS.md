# AGENTS.md — Dinner Menu Generator

> Guidance for AI assistants and new developers working in this codebase.

## Project Summary

**Dinner Menu Generator** is a local-first desktop app that answers one question:
**"What's for dinner tonight?"**

It maintains a personal database of meals (name + ingredients), generates random 7-day
weekly menus with no repeated days, lets you reroll individual days, builds categorized
grocery lists from the menu, and supports OCR image upload to auto-import meals from
photos of menus/handwritten notes. It also has a "Quick Pick" feature that randomly
suggests either a home meal or a takeout spot.

## Tech Stack

| Layer   | Technology                                   |
|---------|----------------------------------------------|
| Backend | Python / Flask / SQLAlchemy / SQLite         |
| Frontend| React 19 / Vite (served by Flask in prod)    |
| OCR     | Tesseract + OpenCV + Pillow                  |
| Packager| PyInstaller (single-file executable)         |

## Architecture

```
dinner-menu-generator/
├── backend/
│   ├── app.py            # Thin entrypoint (app factory + blueprint registration + frontend serve)
│   ├── config.py          # Config object (DB URI, CORS, upload limits)
│   ├── models.py          # SQLAlchemy models + unbound db instance
│   ├── utils.py           # Pure helpers + constants (ingredient normalization, OCR helpers)
│   ├── routes/
│   │   ├── meals.py       # Meal CRUD + /upload-menu (OCR import)
│   │   ├── menu.py        # /menu/today, /takeout, /decide, /week, /reroll/<day>
│   │   ├── grocery.py     # /grocery
│   │   └── data.py        # /export, /import, /import-file, /fix-data, /init-db
│   └── services/
│       ├── menu_service.py      # Menu generation + daily-pick logic
│       └── grocery_service.py   # Grocery-list aggregation/categorisation
├── frontend/
│   └── src/
│       ├── api.js         # Shared apiFetch + MEALS_PER_PAGE
│       ├── App.jsx        # Component orchestrator (state + layout)
│       └── components/    # Menu, GroceryList, AddMeal
├── requirements.txt
├── example.env
├── README.md
└── .gitignore
```

Backend and frontend were both monolithic before; **§4.1 modularization is complete** —
all logic now lives in the modules above and the original monolith files were rewritten
as thin coordinators.

## Development Commands

### Prerequisites
- Python 3.11+
- Node.js 22+
- Tesseract OCR (for image upload feature — add to system PATH)

### Run Backend (Development)
```bash
cd backend
pip install -r ../requirements.txt
python app.py
```
Server starts at `http://127.0.0.1:5000` and auto-opens the browser. The backend also
serves the built frontend if `frontend/dist/` exists.

### Database Migrations (audit §4.8)
Schema changes are managed with Flask-Migrate (Alembic). The `migrations/` folder
(baseline revision `6c296b498bf1`; `7a9c4f2e1b86` adds `Meal.category`; `8b1c2d3e4f5a`
 stores weekly menus as meal-id references so edits propagate — see §5.13) is committed to the repo.

```bash
cd backend
python -m flask --app app db init        # once — creates migrations/
python -m flask --app app db migrate -m "DESCRIPTION"   # after a model change
python -m flask --app app db upgrade    # apply pending revisions to dinner.db
python -m flask --app app db current    # show the applied revision
```

`python app.py` runs `flask db upgrade` automatically on startup, so the dev server and
the packaged exe both keep the schema current. The frozen exe bundles `migrations/`
(see Package step below); if the bundle is ever missing it falls back to `db.create_all()`
and best-effort `stamp` so existing data is never lost.

### Run Frontend (Hot Reload)
```bash
cd frontend
npm install
npm run dev
```
Vite dev server at `http://localhost:5173`. Note: the app currently calls the backend at
`http://localhost:5000` (hardcoded), so the backend must also be running.

### Build Frontend for Production
```bash
cd frontend
npm run build      # outputs to frontend/dist/
```

### Lint Frontend
```bash
cd frontend
npm run lint
```

### Run Tests (audit §11)
```bash
pip install -r requirements-dev.txt   # once: installs pytest (backend)
pytest                                # runs backend test suite (temp DB, dinner.db untouched)
pytest -m slow                        # also runs the rate-limit test (§5.21)
# (optional, from repo root) pytest -m "not slow" -q
```
Backend tests run against a throwaway SQLite DB (`DATABASE_URL` set in `tests/conftest.py`
before `app` is imported) — they never touch `backend/instance/dinner.db`.

### Package as Desktop Executable
```bash
cd frontend
npm run build
cd ../backend
python -m PyInstaller --noconfirm --onefile --windowed \
  --add-data "../frontend/dist;frontend/dist" \
  --add-data "migrations;migrations" \
     --add-data "ingredient_rules.json;." \
     --add-data "meal_name_fixes.json;." \
     --add-data "nutrition_rules.json;." \
     --add-data "backup.json;." \
     --exclude-module torch --exclude-module torchvision --exclude-module torchaudio \
     --exclude-module ultralytics --exclude-module xformers --exclude-module accelerate \
     --exclude-module kokoro --exclude-module optimum \
     app.py
```
The `--add-data` JSON lines bundle the config-driven ingredient rules (§5.9), the
meal-name typo map (§5.19), and `backup.json` (§13.22 auto-import) into the frozen
`_MEIPASS` directory so OCR import + name cleaning + sample data all work in the
packaged exe. The `--exclude-module` flags prevent PyInstaller from bundling stray
heavy packages (torch, ultralytics, etc.) that may be present in the global
site-packages but are not project dependencies — without these the build can take
10+ minutes and produce a 300+ MB binary.

### Typecheck / Backend Lint
- No backend linter is configured. `.env` is now loaded in `app.py` via `python-dotenv`
  (`load_dotenv()`); `SQLALCHEMY_DATABASE_URI` is env-overridable (`DATABASE_URL`).
- No test framework is configured (see [Audit: Testing](./audit.md#11-testing)).

## API Endpoints

| Method | Path                | Description                                         |
|--------|---------------------|----------------------------------------------------|
| GET    | `/`                 | Serves the React frontend                           |
| GET    | `/health`           | Health check (returns `{"status": "ok"}`)                |
| GET    | `/menu/today`       | Pick a random home meal (no repeats today)          |
| GET    | `/menu/takeout`     | Pick a random takeout spot                          |
| GET    | `/menu/decide`      | Random choice: home or takeout                      |
| POST   | `/menu/reroll/:day` | Reroll a specific day in the last weekly menu       |
| GET    | `/menu/week`        | Generate a 7-day weekly menu (no internal repeats)  |
| PUT    | `/menu/:day`        | Set the meal for a day in the last weekly menu (undo)|
| GET    | `/meals`            | List all meals (sorted by name)                     |
| GET    | `/meals/categories` | Distinct, non-null meal categories (§5.14)          |
| POST   | `/meal`             | Add a new meal                                      |
| PUT    | `/meal/:id`         | Update a meal by ID                                 |
| DEL    | `/meal/:id`         | Delete a meal by ID                                 |
| POST   | `/upload-menu`      | Upload an image for OCR meal import                 |
| GET    | `/grocery`          | Generate a categorized grocery list from last menu  |
| GET    | `/grocery/export`   | Download last grocery list as CSV (default) or text |
| GET,PUT| `/grocery/extras`   | Get/replace user-added shopping items on the last menu (B3a) |
| GET    | `/grocery/purchased`   | List checked-off grocery items (§13.3)                    |
| PUT    | `/grocery/purchased`   | Replace the checked-off items list (§13.3)                |
| POST   | `/grocery/purchased/:item` | Toggle a single item's checked-off state (§13.3)      |
| GET    | `/snacks`              | Alias for `/savings` (backward compat, §13.3b)                  |
| POST   | `/savings`              | Add a saved grocery (auto-groups as snacks/staples, §13.23); accepts optional `group` override (§13.3c)      |
| GET    | `/savings`              | List all saved groceries with group (snacks/staples) (§13.23)    |
| DEL    | `/saving/:id`           | Delete a saved grocery from the catalog (§13.3b)                  |
| GET    | `/insights`         | Macro overview + deficiency flags + swap tips over last menus (B2) |
| GET    | `/export`           | Export all meals and menus as JSON                  |
| POST   | `/import`           | Import meals and menus from JSON body               |
| GET,POST| `/import-file`      | Import from `?path=<file>`, a multipart upload, or legacy `backup.json` (§5.4) |
| POST   | `/shutdown`         | Trigger clean process exit (browser-close beacon, §5.20b)                 |

## Data Model

SQLite database (`dinner.db`, stored in `backend/instance/`). Four tables:

- **Meal** — `id` (int, PK), `name` (string), `ingredients` (JSON list), `category` (string, opt)
- **SavedGrocery** — `id` (int, PK), `name` (string, unique), `group` (string: "snacks"|"staples", auto-assigned), `created_at` (datetime) — §13.3b reusable grocery catalog; backward-compatible `/snack` alias still works
- **WeeklyMenu** — `id` (int, PK), `meals` (JSON, keyed by day name: Mon–Sun), `extras` (JSON list of user-added grocery items, opt), `purchased` (JSON list of checked-off items, opt)
- **UsedMeal** — `id` (int, PK), `date` (string YYYY-MM-DD), `meal_id` (int)
  (tracks which meals were picked today for the `/menu/today` no-repeat rule)

Weekly menus store **meal ids** (not full snapshots); meals are resolved fresh at
read time (grocery lists, `/menu/week`, `/export`). Editing a meal **is reflected** in
menus generated after the edit, including the grocery list built from the latest menu.
`menu_service.expand_menu()` transparently handles legacy full-snapshot menus too.

## Key Design Principles

1. **Local-first** — No accounts, no cloud sync, no internet required.
2. **No-repeats within a week** — `random.sample(meals, 7)` guarantees 7 distinct meals.
3. **Simple** — The app does one thing well. Don't over-engineer.
4. **Desktop-first** — Packaged as an offline executable; web dev server is for development.

## Code Conventions

### Backend (`app.py`)
- Python 3 style: `snake_case` for functions and variables.
- `app.py` is now a thin entrypoint (app + config + blueprint registration + frontend
  serving); business logic lives in `routes/`, `services/`, `models.py`, `utils.py`,
  `config.py`.
- Database models live in `models.py` (bound at startup via `db.init_app(app)` in
  `app.py`); pure helpers in `utils.py`; constants in `config.py`.
- Routes are Flask **Blueprints** declared in `routes/*.py` and registered in `app.py`.
  New endpoints belong in the relevant blueprint, not `app.py`.

### Frontend (`App.jsx`)
- `App.jsx` is now a state/layout orchestrator; view logic lives in
  `components/{Menu,GroceryList,ManageMeals,Modal,QuickPickBadge}.jsx` and shared HTTP in `api.js`.
- Inline styles only — no CSS modules or external stylesheets in use.
- API calls go through `apiFetch` (`src/api.js`) which targets the backend on
  `http://localhost:5000` (hardcoded) — keep that pattern. `apiFetch` includes error
  handling + loading states (audit §4.2), so callers just `await`.

## Known Issues (per `audit.md`)

> **Status: as of 2026-08-05**, the following audit.md issues are FIXED (see `[x]`
> checkmarks): all §3 critical bugs; and §4.1 (monolith split: `app.py` / `App.jsx` →
> `routes/`, `services/`, `models.py`, `config.py`, `utils.py`, `components/`), §4.2
> (frontend error handling + loading states), §4.3 (CORS → `localhost:5173`), §4.4
> (`GET /health`), §4.5 (Tesseract check), §4.6 (upload validation), §4.7 (`/meals`
> pagination incl. frontend), §4.8 (Flask-Migrate), §4.9/§4.10 (unused deps removed),
> §5.2 (debug prints → logging), §5.3 (logging framework), §5.4 (`/import-file` accepts
> `?path=`/upload or legacy `backup.json`), §5.5/§5.6/§8.1 (`/fix-data` and `/init-db`
> moved to Flask CLI commands; `/import-file` kept as a non-destructive import feature),
> §5.7 (`.env` loaded via python-dotenv; `DATABASE_URL` overridable), §5.11 (grocery
> count-item pluralization — irregulars like tomato→tomatoes, mass nouns left alone,
> regular suffix rules), §5.12 (inline edit + Undo toasts for reroll/delete), §5.13
> (weekly menus stored as meal ids, resolved live at read time), §5.14 (Meal.category +
> filter), §5.15 (menu history view / `GET /menus`), §5.16 (`/grocery/export` CSV/text),
> §5.18 (meal search bar + `/meals?search=`), §5.19 (configurable `meal_name_fixes.json`),
> §5.20 (SIGINT/SIGTERM graceful shutdown), §5.21/§8.4 (Flask-Limiter rate limiting),
> §5.22/§8.3 (CSRF protection via custom-header verification), §5.17 (menu ingredient detail
> view), §8.5 (`.env` template cleanup), §8.7 (generic 500 handlers, no exception leak),
> §9.1 (Meal/UsedMeal indexes), §7.2 (current_week removed — gone from `backend/`), §7.3 (unused imports: `shutil` removed, stale monolith refs gone with §4.1), §9.6 (random.sample → DB-level `ORDER BY RANDOM() LIMIT 7` with a single COUNT guard), §11.1–§11.2 (pytest harness + backend tests), §6.1 (backend comment emoji stripped), §6.3 (`.editorconfig`), §6.8 (favicon linked), §6.9 (dead `App.css` removed; `index.css` kept as active theme), §11.3 (GitHub Actions CI), §13.17 (read-only calendar view), §13.18 (presence-based nutrition insight, local-only). Fixed as of
> 2026-08-05.
>
> **Additional fixes through 2026-08-09:** §6.10 (Error Boundary component), §6.14 (keyboard
> shortcuts: Escape/Cancel, Enter/Submit, Space/checkboxes), §13.3 grocery checkoff +
> §13.3b saved grocery palette (renamed Snack→SavedGrocery with group column),
> §13.4 meal search (already §5.18), §13.13 dark mode toggle (§13a.3), §13.14 mobile-
> responsive CSS breakpoints, §13a UI polish (CSS class extraction, shared component
> classes, .editorconfig, black/isort/flake8 configs), App.spec PyInstaller excludes
> persisted, Alembic SystemExit catch in frozen exe.
>
> **Phase D completed through 2026-08-10:** §13.21 (UI layout restructure), §13.22 (auto-import),
> §13.23 (saved groceries tabs), §13.24 (scrollable history), §16 (deferred Ollama features documented).
>
> **Latest fixes through 2026-08-11:** §13.21b (configurable page-size selector 5/10/15/20, default 5, persisted to localStorage), §5.20b (delayed `/shutdown` with 10-second grace period so brief navigations like clicking a `mailto:` link don't kill the server; `mailto:` links changed to `window.open` instead of navigation), §13.3c (`+ Add Snack` / `+ Add Staple` header badges with modal; backend `/saving` accepts optional `group` override).
>
> **Remaining:**
> - (see `audit.md` §6–§11 for the low-priority polish / dead-code / perf / tooling backlog)

## Maintenance CLI Commands (audit §5.5 / §5.6 / §8.1)

The `/fix-data` and `/init-db` endpoints were **removed from HTTP** and are now Flask CLI
commands only (run from `backend/`):

| Command | What it does |
|---------|--------------|
| `flask --app app init-db` | Create tables (`db.create_all()`, idempotent) |
| `flask --app app fix-data` | Backfill/normalise ingredients, clean names, drop duplicate meals |

The frozen exe is unaffected: it provisions tables itself via `flask db upgrade` at
startup (audit §4.8) and neither command was user-facing anyway. `/import-file` is
intentionally kept over HTTP — per §5.4 it is the user-facing data-import feature
(additive + deduping, non-destructive).

## Working Style

- Run `npm run lint` in `frontend/` after frontend changes.
- No backend linter exists; manual review is the norm (§10.1 — a `black`/`isort`/`flake8` config is a future polish).
- Run `pytest` (from repo root) after backend changes; the suite uses a throwaway temp DB so
  `dinner.db` is never modified (see §11). Frontend stays lint-only (no test runner).
- The audit.md file is the single source of truth for known issues and the
  recommended 5-phase roadmap.
