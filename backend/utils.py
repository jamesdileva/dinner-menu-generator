"""Shared pure helpers and constants for the Dinner Menu Generator backend.

These were inline in `app.py` and are centralised here so routes/services stay thin
(audit §4.1). No helper here imports `app` or Flask, so there are no circular imports.
"""

import re
import shutil

import pytesseract

# --- OCR engine availability (audit §4.5) ---------------------------------
# Resolved once at startup. The `/upload-menu` route checks this before running OCR.
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

# --- Ingredient normalization tables ---------------------------------------
IGNORE_WORDS = [
    "mix",
    "premade",
    "or",
    "white",
    "sub",
    "sandwich"
]
IGNORE_WORDS.append("sauce")
IGNORE_WORDS.extend([
    "and"
])
KEEP_TOGETHER = [
    "pancake mix",
    "tomato sauce",
    "soy sauce",
    "hot sauce",
    "bbq sauce",
    "premade lasagna",
    "lasagna",
    "rice pilaf",
    "angel hair pasta",
    "ground beef",
    "tri tip",
    "pork chop",
    "white rice",
]

INGREDIENT_MAP = {
    "chicken breast": "chicken",
    "chicken thigh": "chicken",
    "ground beef": "beef",
    "steak": "beef",
    "shredded cheese": "cheese",
    "mozzarella cheese": "cheese",
    "white rice": "rice",
    "brown rice": "rice",
    "tri tip": "beef",
    "tri": "beef",
    "tip": "beef",
    "angelhair": "pasta",
    "noodle": "pasta"
}
INGREDIENT_MAP.update({
    "potatoe": "potato",
    "veggie": "vegetable",
    "meat": "beef",
    "roast": "pork",
    "stew": "beef stew",
    "green": "green chili",
    "chili": "green chili",
    "pancake": "pancake mix",
})
KEEP_TOGETHER.extend([
    "green chili",
    "chicken burritos",
    "pork roast",
    "beef tacos",
    "veggie stir fry",
    "angel hair pasta",
    "pancake mix",
    "beef stew",
])

fast_food_spots = [
    {"name": "McDonald's", "type": "Fast Food"},
    {"name": "Chipotle", "type": "Mexican"},
    {"name": "Pizza Hut", "type": "Pizza"},
    {"name": "Subway", "type": "Sandwiches"},
    {"name": "Chick-fil-A", "type": "Chicken"}
]


def merge_ingredient(name):
    return INGREDIENT_MAP.get(name, name)


def normalize_name(name):
    return name.strip().lower()


def clean_meal_name(name):
    if not name:
        return name

    name = name.strip()

    # remove extra spaces
    name = " ".join(name.split())

    # fix casing (Title Case)
    name = name.title()

    # quick typo fixes (you can expand this later)
    fixes = {
        "Lasagnaa": "Lasagna",
        "Taco Boowl": "Taco Bowl",
        "Veggistir- Fry": "Veggie Stir Fry"
    }

    return fixes.get(name, name)


def normalize_ingredients(ingredients):
    result = []

    if isinstance(ingredients, list):
        items = ingredients
    else:
        items = [ingredients]

    for item in items:
        if not item:
            continue

        item = item.lower().strip()

        # 🔥 check protected phrases FIRST
        normalized_item = " ".join(item.lower().replace(",", " ").split())

        # 💥 catch angel hair FIRST
        if "angel" in normalized_item and "hair" in normalized_item:
            result.append("angel hair pasta")
            continue

        # 💥 check KEEP_TOGETHER BEFORE splitting
        matched = False
        for phrase in KEEP_TOGETHER:
            normalized_phrase = " ".join(phrase.lower().split())

            if normalized_phrase in normalized_item:
                result.append(normalized_phrase)
                matched = True
                break

        if matched:
            continue

        # ✅ ONLY NOW split
        parts = normalized_item.split()

        matched = False
        for phrase in KEEP_TOGETHER:
            if phrase in normalized_item:
                result.append(phrase)
                matched = True
                break

        if matched:
            continue

        # normal splitting
        parts = item.split(",")

        for part in parts:
            sub_parts = part.split(" ")

            for p in sub_parts:
                cleaned = p.strip()

                if not cleaned:
                    continue

                if cleaned.startswith("ingredient"):
                    continue

                if len(cleaned) < 2:
                    continue

                # ignore junk words EARLY
                if cleaned in IGNORE_WORDS:
                    continue

                # singular fix
                if cleaned.endswith("s") and len(cleaned) > 3:
                    cleaned = cleaned[:-1]

                # merge AFTER normalization
                cleaned = merge_ingredient(cleaned)

                result.append(cleaned)

    return result


def generate_ingredients(meal_name):
    name = meal_name.lower()

    ingredients = []

    # 🔥 detect keywords FIRST (specific → general)
    if "angel hair" in name:
        ingredients.append("angel hair pasta")
    elif "spaghetti" in name:
        ingredients.append("spaghetti pasta")
    elif "pasta" in name:
        ingredients.append("pasta")

    if "alfredo" in name:
        ingredients += ["chicken", "cream", "parmesan"]

    if "taco" in name:
        ingredients += ["beef", "tortilla", "cheese", "lettuce"]

    if "burrito" in name:
        ingredients += ["chicken", "rice", "tortilla", "cheese"]

    if "pizza" in name:
        ingredients += ["dough", "cheese", "tomato sauce"]

    if "burger" in name:
        ingredients += ["beef", "bun", "cheese"]

    if "salad" in name:
        ingredients += ["lettuce", "tomato", "dressing"]

    if "rice" in name:
        ingredients += ["rice"]

    if "shrimp" in name:
        ingredients += ["shrimp", "garlic", "butter"]

    if "stew" in name:
        ingredients += ["beef", "potato", "carrot"]

    # 🧠 fallback: extract useful words
    if not ingredients:
        words = [w for w in name.split() if len(w) > 3]
        ingredients += words

    # 🔥 normalize everything through your pipeline
    return normalize_ingredients(ingredients)


def is_valid_meal(text):
    text = text.strip()

    if not text:
        return False

    lower = text.lower()

    # ❌ length guard
    if len(text) < 3 or len(text) > 35:
        return False

    # ❌ must contain letters
    if not any(c.isalpha() for c in text):
        return False

    words = lower.split()

    # ❌ too many words = paragraph junk
    if len(words) > 5:
        return False

    # ❌ reject heavy symbol lines
    bad_chars = ["|", "/", "\\", "{", "}", "[", "]", "=", "+", "_"]
    if any(c in text for c in bad_chars):
        return False

    # ❌ too many non-letters (OCR garbage)
    letter_ratio = sum(c.isalpha() for c in text) / len(text)
    if letter_ratio < 0.6:
        return False

    # ❌ reject obvious junk words
    junk_words = ["week", "menu", "day", "notes", "grocery"]
    if any(j in lower for j in junk_words):
        return False

    # ❌ reject repeated weird patterns
    if any(word * 2 in lower for word in words):
        return False

    return True


def parse_quantity(num_str):
    """Parse quantity strings like "2", "1.5", "1/2", "1 1/2" into floats.

    Moved here from `app.py` (audit §3.8) so it is reusable by the grocery service.
    """
    num_str = num_str.strip()

    # mixed number: "1 1/2" -> whole + fraction
    parts = num_str.split()
    if len(parts) == 2 and "/" in parts[1]:
        try:
            whole = float(parts[0])
            numerator, denominator = parts[1].split("/")
            return whole + float(numerator) / float(denominator)
        except ValueError:
            pass

    # simple fraction: "1/2"
    if "/" in num_str:
        try:
            numerator, denominator = num_str.split("/")
            return float(numerator) / float(denominator)
        except ValueError:
            pass

    # plain decimal or integer
    try:
        return float(num_str)
    except ValueError:
        return 1.0


def categorize_ingredient(item):
    item = item.lower()

    if any(word in item for word in [
        "chicken",
        "beef",
        "pork",
        "egg",
        "shrimp",
        "sausage",
        "bacon",
        "meatball",
        "carne",
        "hamburger",
        "steak",
        "ground beef",
        "beef stew",
        "pork chop",
    ]):
        return "Protein"

    if item in ["lettuce", "tomato", "onion", "garlic", "pepper", "potato", "vegetable"]:
        return "Produce"

    if item in ["milk", "cheese", "butter", "cream"]:
        return "Dairy"

    if any(word in item for word in ["rice", "pasta", "bread", "bun", "tortilla", "pilaf"]):
        return "Grains"

    return "Other"
