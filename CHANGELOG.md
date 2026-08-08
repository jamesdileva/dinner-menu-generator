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
