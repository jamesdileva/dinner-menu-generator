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
(baseline revision `6c296b498bf1` = current schema) is committed to the repo.

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

### Package as Desktop Executable
```bash
cd frontend
npm run build
cd ../backend
python -m PyInstaller --noconfirm --onefile --windowed \
  --add-data "../frontend/dist;frontend/dist" \
  --add-data "migrations;migrations" app.py
```

### Typecheck / Backend Lint
- No backend linter is configured. The project relies on `python-dotenv` (in requirements)
  but `.env` loading is not in `app.py`.
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
| GET    | `/meals`            | List all meals (sorted by name)                     |
| POST   | `/meal`             | Add a new meal                                      |
| PUT    | `/meal/:id`         | Update a meal by ID                                 |
| DEL    | `/meal/:id`         | Delete a meal by ID                                 |
| POST   | `/upload-menu`      | Upload an image for OCR meal import                 |
| GET    | `/grocery`          | Generate a categorized grocery list from last menu  |
| GET    | `/export`           | Export all meals and menus as JSON                  |
| POST   | `/import`           | Import meals and menus from JSON body               |
| GET    | `/import-file`      | Import from hardcoded `backup.json`                 |

## Data Model

SQLite database (`dinner.db`, stored in `backend/instance/`). Three tables:

- **Meal** — `id` (int, PK), `name` (string), `ingredients` (JSON list)
- **WeeklyMenu** — `id` (int, PK), `meals` (JSON, keyed by day name: Mon–Sun)
- **UsedMeal** — `id` (int, PK), `date` (string YYYY-MM-DD), `meal_id` (int)
  (tracks which meals were picked today for the `/menu/today` no-repeat rule)

Weekly menus are stored as snapshots (meals JSON embedded at generation time). Editing
a meal after a menu is generated will **not** retroactively update past menus.

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
  `components/{Menu,GroceryList,AddMeal}.jsx` and shared HTTP in `api.js`.
- Inline styles only — no CSS modules or external stylesheets in use.
- API calls go through `apiFetch` (`src/api.js`) which targets the backend on
  `http://localhost:5000` (hardcoded) — keep that pattern. `apiFetch` includes error
  handling + loading states (audit §4.2), so callers just `await`.

## Known Issues (per `audit.md`)

> **Status: as of 2026-08-04**, audit.md §3 critical bugs plus §4.1 (monolith split:
> `app.py` / `App.jsx` → `routes/`, `services/`, `models.py`, `config.py`, `utils.py`,
> `components/`), §4.2 (frontend error handling + loading states), §4.3 (CORS →
> `localhost:5173`), §4.4 (`GET /health`), §4.5 (Tesseract check), §4.6 (upload
> validation), §4.7 (`/meals` pagination incl. frontend), §4.9/§4.10 (unused deps
> removed) are FIXED — see `audit.md` for `[x]` checkboxes. Remaining:

- **§4.8** No DB migration strategy (`db.create_all` only) — adopt Flask-Migrate in a dedicated session.
- §5.4 `import_file` still reads from a hardcoded `backup.json` path.
- §5.5/§5.6/§8.1 maintenance endpoints (`/fix-data`, `/init-db`, `/import-file`) exposed without protection.
- §5.11 grocery unit pluralization is simplistic (`"2 lbs"` ok, `"2 tomatoes"` wrong).

## Working Style

- Run `npm run lint` in `frontend/` after frontend changes.
- No backend linter exists; manual review is the norm.
- No test suite exists; verify manually by running `python app.py` and exercising
  endpoints via browser or curl.
- The audit.md file is the single source of truth for known issues and the
  recommended 5-phase roadmap.
