# **Dinner Menu Generator**

## **Complete Project Guide, Architecture Notes, and Study Cheat Sheet**

---

# **1\. Project Overview**

Dinner Menu Generator is a desktop application that helps users:

* Store meals and ingredients  
* Generate random weekly meal plans  
* Build grocery lists automatically  
* Upload photos of handwritten or printed menus using OCR  
* Export and import data  
* Run as a standalone Windows executable

### **Tech Stack**

| Layer | Technology |
| ----- | ----- |
| Frontend | React \+ Vite |
| Backend | Flask |
| Database | SQLite |
| OCR | Tesseract OCR |
| Packaging | PyInstaller |
| Distribution | GitHub Releases |

---

# **2\. Core Problem Solved**

Planning meals manually is repetitive and time consuming.

This app automates:

1. Meal selection  
2. Grocery generation  
3. Ingredient normalization  
4. OCR menu extraction  
5. Data persistence

---

# **3\. High-Level Architecture**

User  
  ↓  
React Frontend  
  ↓ HTTP API Calls  
Flask Backend  
  ↓ ORM  
SQLAlchemy  
  ↓  
SQLite Database

### **Optional OCR Flow**

Image Upload  
  ↓  
PIL  
  ↓  
OpenCV Preprocessing  
  ↓  
Tesseract OCR  
  ↓  
Text Cleanup  
  ↓  
Meal Records

---

# **4\. Project Structure**

DinnerMenuGenerator/  
│  
├── backend/  
│   ├── app.py  
│   ├── app.spec  
│   ├── config.py  
│   ├── models.py  
│   ├── routes/  
│   └── services/  
│  
├── frontend/  
│   ├── src/  
│   ├── public/  
│   └── dist/  
│  
├── requirements.txt  
├── README.md  
└── DinnerMenuGenerator.exe

---

# **5\. Data Models**

## **Meal**

Represents a single recipe.

class Meal(db.Model):  
    id \= db.Column(db.Integer, primary\_key=True)  
    name \= db.Column(db.String(100))  
    ingredients \= db.Column(db.JSON)

Example:

{  
  "name": "Chicken Alfredo",  
  "ingredients": \["chicken", "cream", "pasta"\]  
}

## **WeeklyMenu**

Stores a generated 7-day menu.

class WeeklyMenu(db.Model):  
    id \= db.Column(db.Integer, primary\_key=True)  
    meals \= db.Column(db.JSON)

---

# **6\. API Routes**

## **Meal Management**

| Route | Purpose |
| ----- | ----- |
| GET /meals | Get all meals |
| POST /meal | Add a meal |
| PUT /meal/ | Update a meal |
| DELETE /meal/ | Delete a meal |

## **Menu Generation**

| Route | Purpose |
| ----- | ----- |
| GET /menu/week | Generate 7-day menu |
| GET /menu/today | Random meal |
| POST /menu/reroll/ | Replace one day |
| GET /menu/decide | Home vs takeout |
| GET /menu/takeout | Random takeout |

## **Grocery**

| Route | Purpose |
| ----- | ----- |
| GET /grocery | Generate categorized grocery list |

## **OCR**

| Route | Purpose |
| ----- | ----- |
| POST /upload-menu | Upload image and extract meals |

## **Data Backup**

| Route | Purpose |
| ----- | ----- |
| GET /export | Export all data |
| POST /import | Import backup |
| GET /import-file | Import backup.json |

## **Maintenance**

| Route | Purpose |
| ----- | ----- |
| GET /init-db | Create database tables |
| GET /fix-data | Normalize and clean existing data |

---

# **7\. Weekly Menu Generation Algorithm**

## **Goal**

Generate 7 unique meals and avoid repeating the previous week's meals.

## **Steps**

1. Load all meals.  
2. Ensure at least 7 exist.  
3. Load last saved weekly menu.  
4. Build set of previously used meals.  
5. Filter those out.  
6. If fewer than 7 remain, use all meals.  
7. Randomly sample 7\.  
8. Save the result.  
9. Return JSON.

---

# **8\. Grocery List Generation**

## **Process**

1. Load latest weekly menu.  
2. Collect all ingredients.  
3. Normalize similar names.  
4. Count quantities.  
5. Categorize items.  
6. Return grouped JSON.

### **Categories**

* Protein  
* Produce  
* Dairy  
* Grains  
* Other

---

# **9\. Ingredient Normalization**

This is one of the most valuable systems in the project.

## **Problem**

Different names can represent the same ingredient.

Examples:

* ground beef → beef  
* white rice → rice  
* mozzarella cheese → cheese

## **Solution**

Use `INGREDIENT_MAP` and phrase preservation rules.

---

# **10\. KEEP\_TOGETHER Logic**

Some phrases must remain intact.

Examples:

* angel hair pasta  
* tomato sauce  
* pancake mix  
* beef stew

Without this logic:

angel hair pasta → angel, hair, pasta

With this logic:

angel hair pasta

---

# **11\. OCR Pipeline**

## **Flow**

Image  
 → PIL  
 → NumPy  
 → OpenCV grayscale  
 → Contrast adjustment  
 → Gaussian blur  
 → Thresholding  
 → Tesseract OCR  
 → Line filtering  
 → Meal cleanup  
 → Database insertion

## **OCR Filters**

Reject:

* Very short text  
* Too many words  
* Special character noise  
* Non-letter heavy strings  
* Junk words (menu, week, notes)

---

# **12\. Automatic Ingredient Generation**

When OCR finds a meal, ingredients are inferred from keywords.

Examples:

* Alfredo → chicken, cream, parmesan  
* Taco → beef, tortilla, cheese, lettuce  
* Pizza → dough, cheese, tomato sauce

---

# **13\. Export / Import System**

## **Export**

Creates a full JSON backup containing:

* Meals  
* Weekly menus

## **Import**

Restores all saved data.

## **Use Cases**

* Migration from PostgreSQL  
* Sharing data  
* Restoring after accidental deletion  
* Bundling preloaded data into releases

---

# **14\. Database Location**

SQLite database is usually created in the same directory as the executable.

Example:

DinnerMenuGenerator.exe  
DinnerMenuGenerator.db

This allows:

* Portable usage  
* User-owned data  
* Easy backup

---

# **15\. Local Development Workflow**

## **Backend**

cd backend  
python app.py

## **Frontend Build**

cd frontend  
npm install  
npm run build

After building, Flask serves `frontend/dist`.

---

# **16\. Production Packaging**

## **Build Frontend**

cd frontend  
npm run build

## **Build Executable**

cd backend  
pyinstaller app.spec

Executable output:

backend/dist/DinnerMenuGenerator.exe

---

# **17\. PyInstaller Concepts**

## **`sys._MEIPASS`**

Temporary extraction folder used by PyInstaller.

if hasattr(sys, '\_MEIPASS'):  
    FRONTEND\_BUILD \= os.path.join(sys.\_MEIPASS, 'frontend/dist')

## **Why It Matters**

The executable cannot use normal relative paths.

---

# **18\. Serving React Through Flask**

@app.route('/')  
def serve():  
    return send\_from\_directory(FRONTEND\_BUILD, 'index.html')

Assets are served separately.

---

# **19\. Common Debugging Lessons**

## **404 at /**

Cause:

* React build missing  
* Wrong `FRONTEND_BUILD`  
* Route not registered

## **no such table**

Cause:

* Database not initialized

Fix:

with app.app\_context():  
    db.create\_all()

## **JSON.parse Unexpected Character**

Cause:

* Backend returned HTML error page instead of JSON

## **Missing Modules**

Cause:

* Dependency absent from `requirements.txt`

---

# **20\. Requirements File**

Generate with:

pip freeze \> requirements.txt

Typical packages:

* Flask  
* Flask-CORS  
* Flask-SQLAlchemy  
* pillow  
* pytesseract  
* opencv-python  
* numpy  
* requests  
* pyinstaller

---

# **21\. Git Best Practices**

## **Useful Commands**

git status  
git ls-files  
git add .  
git commit \-m "message"  
git push

## **Ignore**

* `__pycache__/`  
* `node_modules/`  
* `dist/`  
* `*.db`  
* `venv/`

---

# **22\. Release Packaging Strategy**

Recommended release contents:

DinnerMenuGenerator-v1.0.0.zip  
├── DinnerMenuGenerator.exe  
├── backup.json (optional preloaded meals)  
├── README.md  
└── LICENSE

---

# **23\. Startup Flow**

Launch EXE  
 → Create tables if needed  
 → Open browser  
 → Serve React UI  
 → Load meals  
 → User interacts with API

---

# **24\. Design Patterns Used**

## **REST API**

Frontend communicates via HTTP endpoints.

## **ORM**

SQLAlchemy maps Python classes to tables.

## **Data Normalization**

Cleans inconsistent ingredient names.

## **Fallback Logic**

If OCR or history filters fail, safe defaults are used.

---

# **25\. Most Important Concepts to Remember**

1. React builds static files.  
2. Flask serves those files.  
3. SQLAlchemy manages the database.  
4. SQLite stores data locally.  
5. PyInstaller bundles everything.  
6. OCR converts images to text.  
7. Ingredient normalization keeps data consistent.  
8. Export/import preserves user data.

---

# **26\. Business Value**

This project demonstrates:

* Full-stack development  
* Desktop app packaging  
* OCR integration  
* Data modeling  
* Algorithm design  
* Product distribution

These skills transfer directly to SaaS and desktop software products.

---

# **27\. Possible Monetization**

* Premium recipe packs  
* Family planner subscription  
* Nutrition integration  
* Shopping delivery integrations  
* Mobile version

---

# **28\. Future Roadmap**

## **Phase 2**

* Drag-and-drop calendar editing  
* Nutrition facts  
* Cost estimation  
* Shopping mode

## **Phase 3**

* Cloud sync  
* User accounts  
* Shared family plans

## **Phase 4**

* AI recipe suggestions  
* Smart substitutions  
* Budget optimization

---

# **29\. Product Ideas Derived From This Project**

The same architecture can power:

* Contractor estimators  
* Sports simulators  
* Security checklist tools  
* OSRS trading analyzers  
* Betting simulation engines

---

# **30\. Key Technical Skills Learned**

## **Python**

* Flask  
* SQLAlchemy  
* OCR  
* Packaging

## **JavaScript**

* React  
* Vite  
* API integration

## **Data**

* SQLite  
* JSON serialization

## **Deployment**

* GitHub Releases  
* PyInstaller

---

# **31\. Mental Model**

Think of the app as four engines:

1. Storage Engine (SQLite)  
2. API Engine (Flask)  
3. UI Engine (React)  
4. Intelligence Engine (OCR \+ normalization)

---

# **32\. Performance Notes**

Current scale supports thousands of meals easily.

Potential optimizations:

* Add indexes  
* Cache grocery lists  
* Background OCR jobs

---

# **33\. Security Notes**

For a local desktop app, security needs are minimal.

If moved to cloud:

* Authentication  
* Rate limiting  
* Input validation  
* HTTPS

---

# **34\. Backup Strategy**

Best practice:

* Export data regularly  
* Keep `backup.json`  
* Version your releases

---

# **35\. Recommended Development Cycle**

1. Design feature  
2. Update models  
3. Add route  
4. Connect frontend  
5. Test locally  
6. Build frontend  
7. Package executable  
8. Create release

---

# **36\. Testing Checklist**

* Add meal  
* Edit meal  
* Delete meal  
* Upload image  
* Generate weekly menu  
* Generate grocery list  
* Export data  
* Import data  
* Launch EXE in clean folder

---

# **37\. Lessons Learned During Development**

* Running multiple app instances can cause confusion.  
* `db.create_all()` only creates missing tables.  
* Git cleanup can accidentally remove local databases.  
* Backup/export systems are essential.  
* 500 errors often produce frontend JSON parsing errors.

---

# **38\. Resume Description**

Built a full-stack desktop meal planning application using React, Flask, SQLite, OCR, and PyInstaller. Features include image-based menu extraction, automated weekly planning, grocery list generation, and standalone Windows distribution.

---

# **39\. Elevator Pitch**

Dinner Menu Generator is a desktop app that automatically builds weekly meal plans and grocery lists from your saved recipes and even extracts meals from images using OCR.

---

# **40\. Final Project Summary**

This project combines:

* Frontend engineering  
* Backend API development  
* Database design  
* OCR and computer vision  
* Data cleaning  
* Packaging and distribution  
* Product thinking

It is a strong end-to-end software project and an excellent foundation for future SaaS and desktop products.

---

# **41\. Quick Command Reference**

## **Run Locally**

cd backend  
python app.py

## **Build Frontend**

cd frontend  
npm install  
npm run build

## **Build EXE**

cd backend  
pyinstaller app.spec

## **Export Data**

http://127.0.0.1:5000/export

## **Import Data**

http://127.0.0.1:5000/import-file

## **Git Push**

git add .  
git commit \-m "Release v1.0.0"  
git push

---

# **42\. Final Takeaways**

The most important engineering ideas demonstrated:

* Data models define application structure.  
* APIs connect frontend and backend.  
* Normalization improves data quality.  
* Automation creates user value.  
* Packaging turns code into a product.  
* Backups protect user data.

---

# **43\. Version 1.0 Achievement**

You successfully built a real, distributable desktop product with:

* Persistent storage  
* OCR intelligence  
* Automated planning  
* Data backup  
* GitHub release support

That is a complete software product lifecycle from concept to release.

