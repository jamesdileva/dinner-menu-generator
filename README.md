# Dinner Menu Generator

A simple, local-first dinner planning app that answers **"What's for dinner tonight?"**

Add your favorite meals, spin up a random 7-day weekly menu with no repeated days,
build a categorized grocery list, or let the app decide: cook at home or order takeout.
You can even snap a photo of a menu and import the meals via OCR.

---

## Features

- **Weekly Menu** — Generate a random 7-day dinner plan. Each week uses 7 distinct meals
  so you never get repeats within the same week.
- **Reroll a Day** — Don't like Monday's pick? Hit the reroll button for just that day.
  An Undo toast appears so you can revert.
- **Grocery List** — Auto-generate a categorized shopping list (Produce, Protein, Dairy,
  Grains, Snacks, Other) straight from your weekly menu. Download as CSV or text, or
  email it.
- **Quick Pick** — Can't decide? The app picks either a random home-cooked meal or a
  random takeout spot.
- **OCR Meal Import** — Upload an image of a handwritten menu or restaurant menu and the
  app extracts meal names automatically (requires Tesseract OCR).
- **Menu History** — Past weekly menus are saved. Browse them in a list or a calendar
  view.
- **Nutrition Insights** — A local-first macro overview over your last few menus flags
  deficiencies (e.g. "low dairy") with swap suggestions.
- **Local Database** — All data stays on your machine. No accounts, no cloud, no internet
  required (after the first setup).

---

## Tech Stack

| Layer   | Technology              |
|---------|-------------------------|
| Backend | Python / Flask / SQLAlchemy / SQLite |
| Frontend| React 19 / Vite         |
| OCR     | Tesseract + OpenCV + Pillow |
| Packaging| PyInstaller (single-file executable) |

### Architecture

```
backend/
├── app.py              # Thin entrypoint: app factory, blueprint registration, frontend serve
├── config.py           # Config object (DB URI, CORS, upload limits)
├── models.py           # SQLAlchemy models (Meal, WeeklyMenu, UsedMeal)
├── utils.py            # Pure helpers + constants (ingredient normalization, OCR helpers)
├── limiter.py          # Rate-limiting (Flask-Limiter wrapper, avoids import cycle)
├── cli.py              # CLI commands: init-db, fix-data
├── routes/             # Flask Blueprints:
│   ├── meals.py        # Meal CRUD + /upload-menu (OCR import)
│   ├── menu.py         # /menu/today, /takeout, /decide, /week, /reroll/<day>, /menus, /insights
│   ├── grocery.py      # /grocery, /grocery/export, /grocery/extras
│   └── data.py         # /export, /import, /import-file
├── services/
│   ├── menu_service.py     # Menu generation + daily-pick logic
│   ├── grocery_service.py  # Grocery-list aggregation/categorisation
│   └── nutrition_service.py# Macro insight analysis
└── migrations/         # Alembic migrations (Flask-Migrate, audit §4.8)

frontend/
├── src/
│   ├── api.js          # Shared apiFetch + CSRF header + MEALS_PER_PAGE
│   ├── App.jsx         # State + layout orchestrator (header badges + 2-col grids)
│   ├── main.jsx        # Entry: applies data-theme, renders App
│   ├── index.css       # Light/dark theme vars + shared component classes
│   └── components/
│       ├── Menu.jsx            # Weekly menu card + reroll + email
│       ├── GroceryList.jsx     # Grocery list card + export/email/extras/checkoff
│       ├── ManageMeals.jsx     # All Meals list with Meals/Snacks/Staples tabs
│       ├── Modal.jsx           # Reusable modal overlay (AddMeal form)
│       ├── QuickPickBadge.jsx  # Header badge: Home/Takeout quick pick
│       ├── History.jsx         # Menu history list view (scrollable)
│       ├── Calendar.jsx        # Menu history calendar view
│       ├── Insights.jsx        # Nutrition insights card
│       └── ErrorBoundary.jsx   # React error boundary (§6.10)
├── index.html
├── package.json
├── vite.config.js
└── dist/               # Built assets (gitignored)
```

Backend and frontend are **modularized** — business logic lives in `routes/`, `services/`,
`models.py`, `utils.py`, `config.py`. The original monolithic `app.py` (~950 lines) and
`App.jsx` (~315 lines) were split as thin coordinators (audit §4.1).

---

## Quick Start

### As a pre-built desktop app

Download the latest release from the **Releases** section and run `app.exe`.
No installation required.

### From source (development)

#### Prerequisites

- Python 3.11+
- Node.js 22+
- Tesseract OCR (only needed for image upload) — [install guide](https://github.com/tesseract-ocr/tesseract)

#### 1. Clone the repo

```bash
git clone https://github.com/yourusername/dinner-menu-generator.git
cd dinner-menu-generator
```

#### 2. Install backend dependencies

```bash
cd backend
pip install -r ../requirements.txt
pip install -r ../requirements-dev.txt  # for pytest (optional, for running tests)
```

#### 3. Run the backend

```bash
python app.py
```

The server starts at `http://127.0.0.1:5000` and opens your browser automatically.
The backend serves the built frontend from `frontend/dist/` if it exists; otherwise
continue to step 4 for the dev server with hot reloading.

> **First run:** the app auto-creates and migrates the SQLite database
> (`backend/instance/dinner.db`) on startup via Flask-Migrate (audit §4.8).

#### 4. (Optional) Run the frontend with hot reload

```bash
cd ../frontend
npm install
npm run dev
```

Vite starts at `http://localhost:5173`. The backend's CORS is configured to allow
`localhost:5173` during development (audit §4.3).

#### 5. Build for production

```bash
cd frontend
npm run build
```

Output goes to `frontend/dist/`. The backend will serve it on the next restart.

### Package as a desktop executable

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
  app.py
```

The compiled `.exe` appears in `backend/dist/`.

---

## How It Works

1. **Add meals** to your database using the "Add Meal" form, or let OCR extract them
   from an uploaded image.
2. **Generate a weekly menu** — the app picks 7 random meals with no repeats. Meals are
   stored as IDs and resolved at read time, so editing a meal updates the menu and grocery
   list (audit §5.13).
3. **Build a grocery list** — ingredients from the current week's meals are grouped into
   categories (Produce, Protein, Dairy, Grains, Snacks, Other).
4. **Quick Pick** — when you can't decide, the app randomly suggests cooking at home or
   ordering takeout.
5. **Reroll** any day if you want to swap out a meal. New menus are saved as snapshots —
   previous weekly menus are retained in the database and viewable in Menu History.

---

## API Reference

### Query params

- `GET /meals?page=1&limit=50` — paginate (limit clamped to 1–100).
- `GET /meals?search=chicken` — case-insensitive name search.
- `GET /meals?category=Dinner` — case-insensitive category filter.

### Endpoints

| Method | Path                  | Description                                              |
|--------|-----------------------|----------------------------------------------------------|
| GET    | `/health`             | Health check → `{"status": "ok"}`                        |
| GET    | `/`                   | Serves the React frontend                                |
| GET    | `/menu/today`         | Pick a random home meal (no repeats today, persisted)    |
| GET    | `/menu/takeout`       | Pick a random takeout spot                               |
| GET    | `/menu/decide`        | Random choice: home meal or takeout                      |
| POST   | `/menu/reroll/<day>`  | Reroll a specific day in the last weekly menu            |
| PUT    | `/menu/<day>`         | Set/undo-set a specific day's meal (payload: meal dict)  |
| GET    | `/menu/week`          | Generate a 7-day weekly menu (7 distinct meals)          |
| GET    | `/menus`              | List all saved weekly menus (history view, newest first) |
| GET    | `/insights`           | Macro overview + deficiency flags + swap suggestions     |
| GET    | `/meals`              | List all meals (paginated, sorted by name)               |
| GET    | `/meals/categories`   | Distinct non-null meal categories                        |
| POST   | `/meal`               | Add a new meal                                           |
| PUT    | `/meal/<id>`          | Update a meal by ID                                      |
| DELETE | `/meal/<id>`          | Delete a meal by ID                                      |
| POST   | `/upload-menu`        | Upload an image for OCR meal import (rate-limited 5/min) |
| GET    | `/grocery`            | Generate a categorized grocery list from last menu       |
| GET    | `/grocery/export`     | Download last grocery list as CSV or text                |
| GET/PUT| `/grocery/extras`     | Get/replace user-added grocery items on the last menu    |
| GET    | `/export`             | Export all meals and menus as JSON                       |
| POST   | `/import`             | Import meals and menus from a JSON body                  |
| GET/POST| `/import-file`        | Import from `?path=<file>`, multipart upload, or legacy  |

### Security headers

All state-changing requests (`POST`/`PUT`/`PATCH`/`DELETE`) require the
`X-Requested-With: XMLHttpRequest` header (CSRF protection, audit §5.22).
The frontend's `apiFetch` attaches this automatically.

### Rate limiting

- Default: 120 requests/minute per IP (audit §5.21).
- `POST /upload-menu`: 5/minute (OCR is CPU-heavy).

### Data model

| Table         | Key fields                                                       |
|---------------|------------------------------------------------------------------|
| **Meal**      | `id` (PK), `name` (String 100), `ingredients` (JSON list), `category` (String 50, opt) |
| **WeeklyMenu**| `id` (PK), `meals` (JSON keyed by day: Mon–Sun, storing meal IDs), `extras` (JSON list, opt) |
| **UsedMeal**  | `id` (PK), `date` (String YYYY-MM-DD), `meal_id` (int)           |

Weekly menus store **meal IDs** (not full snapshots); meals are resolved fresh at read
time (grocery lists, `/menu/week`, `/export`, `/menus`). Editing a meal is reflected in
menus generated after the edit, including the grocery list. `expand_menu()` in
`menu_service.py` transparently handles legacy full-snapshot menus too.

**Indexes** (audit §9.1): `ix_meal_name`, `ix_meal_category`, `ix_used_meal_date`.

---

## Data Storage & Backup

- The database lives at `backend/instance/dinner.db` (SQLite, gitignored).
- It's created automatically on first run; schema is managed via Flask-Migrate/Alembic
  (`backend/migrations/`).
- **Export:** `GET /export` returns all meals + menus as JSON.
- **Import:** `POST /import` accepts a JSON body `{"meals": [...], "menus": [...]}`.
  Existing meals (case-insensitive name match) are skipped (idempotent).
- **File import:** `GET/POST /import-file?path=<file>` loads from any JSON path; POST accepts
  a multipart `file` upload; GET without `path` falls back to `backend/backup.json`.
- **Maintenance:** `flask --app app init-db` (create tables) and
  `flask --app app fix-data` (normalise/dedupe) are CLI-only (audit §5.5/§5.6).

---

## Configuration

Copy `example.env` to `.env` (gitignored):

```bash
cp example.env .env
```

| Variable        | Default              | Description                              |
|-----------------|----------------------|------------------------------------------|
| `DATABASE_URL`  | `sqlite:///dinner.db`| Override the SQLite database path.       |

Config lives in `backend/config.py` and is loaded via `python-dotenv` at startup.

---

## Development

### Backend

```bash
cd backend
pip install -r ../requirements.txt
pip install -r ../requirements-dev.txt  # pytest
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev       # hot-reload dev server at http://localhost:5173
npm run lint      # eslint
npm run build     # production build -> frontend/dist/
```

### Database migrations

```bash
cd backend
python -m flask --app app db migrate -m "DESCRIPTION"
python -m flask --app app db upgrade
```

### Tests

```bash
pytest                # runs non-slow tests (temp DB, never touches dinner.db)
pytest -m slow        # also runs the rate-limit test
```

### Code style

- **Black** (`pyproject.toml`, line-length 100) + **isort** + **flake8** (`.flake8`).
- Pre-commit hooks: `pip install pre-commit && pre-commit install`
- Frontend lint: `npm run lint` in `frontend/`.

---

## Troubleshooting

- **OCR "OCR not available" error:** Install Tesseract and add it to your system `PATH`,
  or set `pytesseract.pytesseract.tesseract_cmd` manually. The app logs a warning at
  startup if Tesseract is not found.
- **Backend won't start:** Ensure Python 3.11+ and `pip install -r requirements.txt`.
- **Frontend can't reach backend:** The dev frontend is hardcoded to
  `http://localhost:5000`. Make sure the backend is running. In production, the backend
  serves the frontend directly (same origin).
- **Database issues:** Delete `backend/instance/dinner.db` and restart — it's auto-recreated.
  Or restore from an export: `POST /import` with your JSON backup.

---

## License

MIT — see [LICENSE](./LICENSE).

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).
