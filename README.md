# 🍽 Dinner Planner

A simple local app to plan weekly meals, generate grocery lists, and quickly decide what to eat.

## Features

* 📅 Generate a 7-day meal plan
* 🛒 Auto-generate grocery lists by category
* 🍽 "What should I eat?" quick picker
* 📸 Upload menu images (OCR support)
* ✏️ Edit and manage meals
* 🔄 Reroll individual days

## Tech Stack

* Frontend: React
* Backend: Flask
* Database: PostgreSQL
* OCR: Tesseract

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Build Executable

```bash
pip install pyinstaller
pyinstaller --onefile app.py
```

## Notes

* OCR works best with clear images
* Poor quality images may require manual cleanup

## Future Ideas

* Favorites system
* Ingredient exclusions
* Meal tagging (quick / healthy / etc.)

---

Built for real-life daily use 🍽
