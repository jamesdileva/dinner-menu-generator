# 🍽 Dinner Planner

A simple, local-first dinner planning app that helps you decide what to eat, generate weekly meal plans, and build grocery lists — with optional OCR to scan meal ideas from images.

---

## ✨ Features

* 🗓 Generate a weekly dinner menu
* 🔄 Reroll individual days
* 🛒 Automatically generate a categorized grocery list
* 🍽 Quick pick (eat at home or takeout)
* 📸 Upload images of menus (OCR-powered)
* 🧠 Smart ingredient normalization & grouping
* 💾 Local database (no accounts, no cloud required)

---

## 🖥 Tech Stack

* Frontend: React (Vite)
* Backend: Flask
* Database: SQLite
* OCR: Tesseract + OpenCV

---

## 🚀 Getting Started (Dev Mode)

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/dinner-planner.git
cd dinner-planner
```

---
## 📦 Run as Desktop App (Recommended)

Download the latest release from the **Releases** section:

👉 Run:

```
app.exe
```

No setup required.


## 🚀 Running Locally

### Backend (full app)

```bash
cd backend
pip install -r ../requirements.txt
python app.py
```

Then open:

http://127.0.0.1:5000

---

No frontend setup required — the app serves the built UI automatically.

---

## ⚠️ Requirements (for OCR)

To use image upload:

* Install Tesseract OCR
* Add it to your system PATH

Download: https://github.com/tesseract-ocr/tesseract

---

## 💾 Data Storage

* Uses a local SQLite database (`dinner.db`)
* Automatically created on first run
* No internet required

---

## 🔄 Backup / Restore (Optional)

You can export/import your data using JSON if needed.

---

## 📌 Notes

* Weekly menus reset as new ones are generated
* Duplicate meals are automatically filtered
* OCR works best with clean, high-contrast images

---

## 🧠 Future Ideas

* AI meal suggestions
* Nutrition tracking
* Cloud sync
* Mobile version

---

## 📄 License

MIT (or whatever you want)

---

## 👤 Author

Built by you 😄
