"""Shared pure helpers and constants for the Dinner Menu Generator backend.

These were inline in `app.py` and are centralised here so routes/services stay thin
(audit §4.1). No helper here imports `app` or Flask, so there are no circular imports.
"""

import json
import os
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


# audit §5.19 — configurable meal-name typo fixes (extensible via meal_name_fixes.json).
_NAME_FIXES = None


def _load_name_fixes():
    """Load the typo-correction map once and cache it (module global)."""
    global _NAME_FIXES
    if _NAME_FIXES is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meal_name_fixes.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                _NAME_FIXES = json.load(f)
        except (OSError, json.JSONDecodeError):
            _NAME_FIXES = {}  # best-effort: no fixes applied if the file is missing/ invalid
    return _NAME_FIXES


def clean_meal_name(name):
    if not name:
        return name

    name = name.strip()

    # remove extra spaces
    name = " ".join(name.split())

    # fix casing (Title Case)
    name = name.title()

    # configurable typo fixes (audit §5.19); mapping is keyed on the Title-Cased name
    return _load_name_fixes().get(name, name)


def _is_skip_token(token):
    """True if a single cleaned token should be dropped (blank, 'ingredient…' prefix, junk)."""
    return not token or token.startswith("ingredient") or len(token) < 2 or token in IGNORE_WORDS


def _singularize(token):
    """Naive trailing-s stripper used by the original tokeniser (audit §5.8)."""
    return token[:-1] if token.endswith("s") and len(token) > 3 else token


def _match_keep_together(normalized_item):
    """Return the first KEEP_TOGETHER phrase found in `normalized_item`, else None.

    Phrases are matched as substrings so multi-word phrases like "ground beef" are kept
    whole (audit §5.8 refactor of the previous two overlapping loops).
    """
    for phrase in KEEP_TOGETHER:
        normalized_phrase = " ".join(phrase.lower().split())
        if normalized_phrase in normalized_item:
            return normalized_phrase
    return None


def normalize_ingredients(ingredients):
    """Normalise a list of ingredient strings into a flattened, singularised list.

    Refactored in clear stages (audit §5.8) — behaviour is unchanged: for each item,
    guard the angel-hair special-case, match a KEEP_TOGETHER phrase, otherwise split on
    commas then spaces and clean each token (drop blanks/junk, singularise, merge).
    """
    result = []
    items = ingredients if isinstance(ingredients, list) else [ingredients]

    for item in items:
        if not item:
            continue

        item = item.lower().strip()
        normalized_item = " ".join(item.replace(",", " ").split())

        # "angel ... hair ..." -> canonical "angel hair pasta"
        if "angel" in normalized_item and "hair" in normalized_item:
            result.append("angel hair pasta")
            continue

        # keep multi-word phrases whole
        phrase = _match_keep_together(normalized_item)
        if phrase:
            result.append(phrase)
            continue

        # fall back to comma/space tokenisation of the original (lowercased) item
        for part in item.split(","):
            for token in part.split(" "):
                cleaned = token.strip()
                if _is_skip_token(cleaned):
                    continue
                cleaned = _singularize(cleaned)
                cleaned = merge_ingredient(cleaned)
                result.append(cleaned)

    return result


_INGREDIENT_RULES = None


def _load_ingredient_rules():
    """Load the keyword -> ingredient map from `ingredient_rules.json` (audit §5.9).

    Falls back to an empty ruleset if the file is missing (e.g. inside a PyInstaller
    bundle without the data file), so OCR import keeps working instead of crashing.
    """
    global _INGREDIENT_RULES
    if _INGREDIENT_RULES is None:
        path = os.path.join(os.path.dirname(__file__), "ingredient_rules.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                _INGREDIENT_RULES = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            _INGREDIENT_RULES = {}
    return _INGREDIENT_RULES


# audit B2 — load the curated nutrition macro tags (mirror _load_ingredient_rules so the
# data file resolves correctly inside a PyInstaller bundle too).
_NUTRITION_RULES = None


def load_nutrition_rules():
    """Load `nutrition_rules.json` (ingredient -> {tags:[...]}).

    Falls back to `{}` if the file is missing/corrupt so this feature never crashes the app.
    """
    global _NUTRITION_RULES
    if _NUTRITION_RULES is None:
        path = os.path.join(os.path.dirname(__file__), "nutrition_rules.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                _NUTRITION_RULES = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            _NUTRITION_RULES = {}
    return _NUTRITION_RULES


def generate_ingredients(meal_name):
    """Guess ingredients for a meal from its name (audit §5.9: now config-driven).

    Walks an ordered `pasta_base` list (first match wins, exclusive), then appends from
    `flavor_additions` for every matching keyword, then falls back to meaningful words
    from the meal name. All ingredients run through `normalize_ingredients` afterwards.
    """
    name = meal_name.lower()
    rules = _load_ingredient_rules()
    ingredients = []

    # mutually exclusive base (e.g. pasta type)
    for keyword, adds in rules.get("pasta_base", []):
        if keyword in name:
            ingredients += adds
            break

    # additive flavor keywords
    for keyword, adds in rules.get("flavor_additions", []):
        if keyword in name:
            ingredients += adds

    # fallback: extract words longer than the configured minimum
    if not ingredients:
        min_len = rules.get("fallback_min_word_len", 3)
        ingredients += [w for w in name.split() if len(w) > min_len]

    return normalize_ingredients(ingredients)


def is_valid_meal(text):
    text = text.strip()

    if not text:
        return False

    lower = text.lower()

    # length guard
    if len(text) < 3 or len(text) > 35:
        return False

    # must contain letters
    if not any(c.isalpha() for c in text):
        return False

    words = lower.split()

    # too many words = paragraph junk
    if len(words) > 5:
        return False

    # reject heavy symbol lines
    bad_chars = ["|", "/", "\\", "{", "}", "[", "]", "=", "+", "_"]
    if any(c in text for c in bad_chars):
        return False

    # too many non-letters (OCR garbage)
    letter_ratio = sum(c.isalpha() for c in text) / len(text)
    if letter_ratio < 0.6:
        return False

    # reject obvious junk words
    junk_words = ["week", "menu", "day", "notes", "grocery"]
    if any(j in lower for j in junk_words):
        return False

    # reject repeated weird patterns
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


# --- Grocery ingredient categorisation (audit §5.10) -----------------------
# `categorize_ingredient` receives lowercase tokens that are often plural or multi-word
# ('tomatoes', 'ground beef', 'black beans'). The old code used exact-match sets, which
# sent most items to "Other". We now substring-match on singular keywords so plurals and
# phrases bucket correctly. Order matters: the first matching bucket wins.
_PROTEIN_WORDS = (
    "chicken", "turkey", "beef", "ground beef", "pork", "pork chop", "steak",
    "hamburger", "meatball", "carne", "fish", "salmon", "tuna", "shrimp", "crab",
    "lobster", "clam", "mussel", "oyster", "egg", "sausage", "bacon", "lamb", "duck",
)
_PRODUCE_WORDS = (
    "lettuce", "cabbage", "spinach", "kale", "broccoli", "mushroom", "avocado",
    "cucumber", "celery", "carrot", "bell pepper", "squash", "zucchini", "radish",
    "onion", "garlic", "tomato", "potato", "pepper", "lime", "lemon", "cilantro",
    "parsley", "green bean", "corn", "bean", "sprout", "scallion", "green onion",
)
_DAIRY_WORDS = (
    "milk", "cheese", "cheddar", "parmesan", "mozzarella", "ricotta", "feta",
    "butter", "cream", "yogurt", "sour cream",
)
_GRAIN_WORDS = (
    "rice", "pasta", "noodle", "bread", "bun", "tortilla", "pilaf", "quinoa", "oats",
    "flour", "cereal", "barley", "couscous", "spaghetti", "macaroni", "lasagna",
    "penne", "fettuccine", "linguine", "rigatoni", "gnocchi",
)

# audit B3a — snack-y grocery items the user may add by hand (or that don't fit the
# aisles above). Checked BEFORE Grains so "rice krispies"/"cereal bar" bucket as Snacks,
# while plain "cereal"/"rice" still fall to Grains.
_SNACKS_WORDS = (
    "oreo", "cookie", "crisp", "cracker", "chip", "rice krispie", "cereal bar",
)


def _match_any(words, item):
    """True if any keyword is a substring of `item` (handles plurals/phrases)."""
    return any(word in item for word in words)


def categorize_ingredient(item):
    """Bucket a (lowercase) grocery ingredient into a shopping aisle (audit §5.10)."""
    if not item:
        return "Other"
    if _match_any(_PROTEIN_WORDS, item):
        return "Protein"
    if _match_any(_PRODUCE_WORDS, item):
        return "Produce"
    if _match_any(_DAIRY_WORDS, item):
        return "Dairy"
    if _match_any(_SNACKS_WORDS, item):
        return "Snacks"
    if _match_any(_GRAIN_WORDS, item):
        return "Grains"
    return "Other"


# --- Grocery display pluralization (audit §5.11) ---------------------------
# `normalize_ingredients` stores ingredients in singular lowercase form, so the grocery
# list has to pluralize again for display. The old code only ever appended "s" to units
# (lb->lbs, fine) but left count items singular ("Tomato (2)"). These fix the count
# items: true irregulars, mass/collective nouns (never pluralized), and regular suffixes.
MASS_NOUNS = {
    "cheese", "rice", "bread", "milk", "butter", "flour", "dough",
    "lettuce", "spinach", "garlic", "soup", "sauce", "ketchup",
    "syrup", "oil", "salt", "sugar", "water", "pepper",
}

IRREGULAR_PLURALS = {
    "tomato": "tomatoes",
    "potato": "potatoes",
}


def pluralize_word(word):
    """Return the plural form of a singular grocery item word (audit §5.11)."""
    if not word:
        return word

    lower = word.lower()

    # mass / collective nouns stay the same
    if lower in MASS_NOUNS:
        return word

    # true irregulars (tomato -> tomatoes, potato -> potatoes)
    if lower in IRREGULAR_PLURALS:
        return IRREGULAR_PLURALS[lower]

    # consonant + sh/ch/x/z/s -> +es (radish -> radishes, peach -> peaches)
    if lower.endswith(("sh", "ch", "x", "z", "s")):
        return word + "es"

    # consonant + y -> ies (celery -> celeries)
    if lower.endswith("y") and len(lower) > 1 and lower[-2] not in "aeiou":
        return word[:-1] + "ies"

    # consonant + o -> oes (tomatoes/potatoes handled above; catch others like "hero")
    if lower.endswith("o") and len(lower) > 1 and lower[-2] not in "aeiou":
        return word + "es"

    return word + "s"


# --- Input sanitization (audit §8.6) -----------------------------------------
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def sanitize_text(value, max_len=200):
    """Normalise a user-supplied string before it is stored (audit §8.6).

    - strips NUL and other ASCII control characters (newlines, tabs, etc.)
    - collapses internal whitespace to single spaces and trims the ends
    - caps the length

    HTML is *not* escaped here because the React frontend renders all user-supplied
    values as text (no `dangerouslySetInnerHTML` is used anywhere), so a `<script>` tag
    is displayed, never executed. This helper is about storage hygiene + length bounds,
    not output escaping.
    """
    if value is None:
        return ""
    s = str(value)
    s = _CONTROL_CHARS.sub("", s)
    s = " ".join(s.split())
    if max_len and len(s) > max_len:
        s = s[:max_len]
    return s


def sanitize_ingredients(ingredients, max_count=100, max_len=200):
    """Sanitize a list of ingredient strings; drops empty entries and bounds the count."""
    if ingredients is None:
        return []
    if isinstance(ingredients, str):
        items = [ingredients]
    else:
        items = ingredients
    out = []
    for item in items:
        cleaned = sanitize_text(item, max_len=max_len)
        if cleaned:
            out.append(cleaned)
        if len(out) >= max_count:
            break
    return out
