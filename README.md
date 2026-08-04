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
- **Grocery List** — Auto-generate a categorized shopping list (Produce, Protein, Dairy,
  Grains, Other) straight from your weekly menu.
- **Quick Pick** — Can't decide? The app picks either a random home-cooked meal or a
  random takeout spot.
- **OCR Meal Import** — Upload an image of a handwritten menu or restaurant menu and the
  app extracts meal names automatically (requires Tesseract OCR).
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
```

#### 3. Run the backend

```bash
python app.py
```

The server starts at `http://127.0.0.1:5000` and opens your browser automatically.

> If you've already built the frontend (step 4 below), the app serves it from `frontend/dist/`.
> Otherwise, continue to step 4 to run the dev server with hot reloading.

#### 4. (Optional) Run the frontend with hot reload

```bash
cd ../frontend
npm install
npm run dev
```

Vite starts at `http://localhost:5173`. The frontend is hardcoded to call the backend at
`http://localhost:5000`, so keep the backend running.

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
  --add-data "../frontend/dist;frontend/dist" app.py
```

The compiled `.exe` appears in `backend/dist/`.

---

## How It Works

1. **Add meals** to your database using the "Add Meal" form, or let OCR extract them
   from an uploaded image.
2. **Generate a weekly menu** — the app picks 7 random meals with no repeats.
3. **Build a grocery list** — ingredients from the current week's meals are grouped into
   categories (Produce, Protein, Dairy, Grains, Other).
4. **Quick Pick** — when you can't decide, the app randomly suggests cooking at home or
   ordering takeout.
5. **Reroll** any day if you want to swap out a meal. New menus are saved as snapshots —
   previous weekly menus are retained in the database.

### No duplicates across weeks

Each weekly menu is stored as its own record. `random.sample(meals, 7)` ensures the 7
meals within a single week are all different. When you generate a new menu, it becomes a
new entry — old menus are not overwritten.

---

## API Reference

| Method | Path                | Description                                              |
|--------|---------------------|----------------------------------------------------------|
| GET    | `/health`           | Health check                                             |
| GET    | `/`                 | Serves the React frontend                                |
| GET    | `/menu/today`       | Pick a random home meal (avoids repeats today, in-memory)|
| GET    | `/menu/takeout`     | Pick a random takeout spot                               |
| GET    | `/menu/decide`      | Random choice: home meal or takeout                      |
| POST   | `/menu/reroll/<day>`| Reroll a specific day in the last weekly menu            |
| GET    | `/menu/week`        | Generate a 7-day weekly menu (7 distinct meals)          |
| GET    | `/meals`            | List all meals (sorted by name)                          |
| POST   | `/meal`             | Add a new meal (`{"name": "...", "ingredients": [...]}`) |
| PUT    | `/meal/<id>`        | Update a meal by ID                                      |
| DELETE | `/meal/<id>`        | Delete a meal by ID                                      |
| POST   | `/upload-menu`      | Upload an image for OCR meal import                      |
| GET    | `/grocery`          | Generate a categorized grocery list from last menu       |
| GET    | `/export`           | Export all meals and menus as JSON                       |
| POST   | `/import`           | Import meals and menus from a JSON body                  |
| GET    | `/import-file`      | Import from `backend/backup.json`                        |

### Data model

- **Meal** — `id`, `name`, `ingredients` (JSON list)
- **WeeklyMenu** — `id`, `meals` (JSON keyed by day name: Mon, Tue, …, Sun)

Weekly menus store meal data as snapshots. Editing a meal after a menu is generated
will **not** retroactively change past menus.

---

## Data Storage & Backup

- The database lives at `backend/instance/dinner.db` (SQLite).
- It's created automatically on first run.
- Use `GET /export` and `POST /import` to back up and restore your data as JSON.
- The `/import-file` endpoint loads data from the bundled `backend/backup.json` sample file.

---

## Development Notes

- **Monolith architecture** — all backend logic (models, routes, OCR, utilities) lives in
  `backend/app.py`. All frontend logic lives in `frontend/src/App.jsx`. The project has
  empty scaffold files (`routes/`, `services/`, `models.py`, `components/`, etc.) that
  were part of an unfinished refactor — they are **not in use**. New code should be
  added to `app.py` and `App.jsx` to match the existing pattern.
- **CORS** is currently wide open (`CORS(app)` with no origin restrictions). This is fine
  for a local desktop app but should be restricted if the server is ever exposed.
- **Tesseract** is hardcoded to a Windows path in `app.py`. On macOS/Linux, install
  Tesseract and add it to your system `PATH`. See [audit.md](./audit.md) for details.
- See [audit.md](./audit.md) for a comprehensive list of known issues, bugs, and a
  recommended roadmap.

---

## License

MIT
