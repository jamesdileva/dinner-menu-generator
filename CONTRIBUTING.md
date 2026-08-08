# Contributing

Thanks for your interest in contributing to the Dinner Menu Generator!

This is a local-first desktop app (Flask backend + React frontend). The
[`audit.md`](./audit.md) file tracks the development roadmap and known issues —
check it before starting work to see what's already planned or in progress.

---

## Development Setup

```bash
# 1. Clone
git clone https://github.com/yourusername/dinner-menu-generator.git
cd dinner-menu-generator

# 2. Backend
cd backend
pip install -r ../requirements.txt
pip install -r ../requirements-dev.txt   # pytest

# 3. Frontend (optional, for UI work)
cd ../frontend
npm install
```

### Running locally

- **Full app (backend serves built frontend):**
  ```bash
  cd backend
  # Build frontend first if you want it served by Flask:
  cd ../frontend && npm run build && cd ../backend
  python app.py
  ```
  Visit `http://127.0.0.1:5000`.

- **Backend + frontend dev server with hot reload:**
  - Terminal 1: `cd backend && python app.py` (Flask on `:5000`)
  - Terminal 2: `cd frontend && npm run dev` (Vite on `:5173`)

### Database migrations

```bash
cd backend
python -m flask --app app db migrate -m "Add ..."
python -m flask --app app db upgrade
```

The `migrations/` folder is committed to the repo (audit §4.8).

---

## Code Style

### Backend (Python)

- **Black** for formatting (line-length 100, configured in `pyproject.toml`).
- **isort** for import sorting (configured in `pyproject.toml`).
- **flake8** for linting (`.flake8` config; `migrations/` is excluded).
- Run all three:
  ```bash
  cd backend
  python -m black .
  python -m isort .
  python -m flake8 .
  ```
- **Type hints** are encouraged on all public functions (audit §10.4).
- `app.py` is a thin entrypoint — business logic goes in `routes/`, `services/`,
  `models.py`, `utils.py`, `config.py` (audit §4.1).

### Frontend (React/Vite)

- **ESLint** (`npm run lint`).
- Inline styles only — no CSS modules or external stylesheets (project convention).
- Components live in `frontend/src/components/`; shared API calls use `apiFetch`
  from `frontend/src/api.js`.

---

## Testing

```bash
# From repo root
pytest              # non-slow tests (temp DB, never touches dinner.db)
pytest -m slow      # includes the rate-limit test
```

- Backend tests use an isolated temp SQLite DB (via `DATABASE_URL` in
  `tests/conftest.py`). They never touch `backend/instance/dinner.db`.
- No frontend test runner is configured (audit §11.2 — Vitest is future work).

---

## Pull Request Workflow

1. Fork the repo and create a branch: `git checkout -b fix/my-feature`
2. Make your changes.
3. Run the linters and tests:
   ```bash
   cd backend && python -m black --check . && python -m flake8 . && \
   cd ../frontend && npm run lint && npm run build && \
   cd .. && pytest
   ```
4. Commit with a clear message.
5. Push and open a PR. Reference the relevant `audit.md` section if applicable.

---

## Where Help Is Needed

See [`audit.md`](./audit.md) §6–§15 for the full backlog. Key areas:

- **§10.4** Type hints on remaining backend functions
- **§6.7** Responsive design for the frontend
- **§6.10** React error boundaries
- **§6.14** Keyboard shortcuts
- **§12.2** OpenAPI / Swagger spec
- **§13.x** Feature ideas (grocery checkoff, meal photos, dietary tags, etc.)
