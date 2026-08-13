"""Nutrition macro insight service (audit B2).

Presence-based (v1) analysis, local-first — no network.  For the last few saved
weekly menus, each meal's ingredients are looked up in ``nutrition_rules.json``
(macro themes: protein / veg / dairy / carbs / fiber / healthy_fat). Ingredients
not in the file are omitted (graceful, never an error). The aggregate is compared
to per-week targets to surface deficiency flags + rule-based swap suggestions.

§16.3 — When ``USE_OLLAMA`` is enabled, the rule-based result is sent to the local
Ollama daemon to produce more nuanced, meal-specific guidance.  On any Ollama error
the rule-based result is returned unchanged.

Pure DB reads / no writes.  Read via ``GET /insights`` (routes/menu.py).
"""

import json
import logging
from typing import Any, Dict, List, Tuple, Union

from flask import current_app
from models import WeeklyMenu
from services.llm_service import call_ollama
from services.menu_service import expand_menu
from utils import sanitize_text, load_nutrition_rules

logger = logging.getLogger(__name__)

_WINDOW = 4  # review the most recent N weekly menus (a "few weeks")


def _tags_for(ingredient: str, rules: Dict[str, Any]) -> List[str]:
    """Macro tags for an ingredient token (exact, then plural/substring tolerant)."""
    ing = rules.get("ingredients", {})
    token = (ingredient or "").lower().strip()
    if not token:
        return []
    if token in ing:
        return ing[token].get("tags", [])
    for key, val in ing.items():
        if key and key in token:
            return val.get("tags", [])
    return []


def _targets(rules: Dict[str, Any]) -> Dict[str, int]:
    """Per-week macro targets: JSON `_targets_per_week` merged over safe defaults."""
    defaults: Dict[str, int] = {
        "protein": 3,
        "veg": 7,
        "dairy": 2,
        "carbs": 4,
        "fiber": 3,
        "healthy_fat": 2,
    }
    defaults.update(rules.get("_targets_per_week", {}))
    return defaults


def insights() -> Union[Dict[str, Any], Tuple[Dict[str, str], int]]:
    """Aggregate macro presence over the last `_WINDOW` weekly menus.

    Returns a dict ({weeks_reviewed, weekly_targets, totals, weeks, flags,
    suggestions}) or (error, status) when no menus exist yet.
    """
    menus = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).limit(_WINDOW).all()
    if not menus:
        return {"error": "Generate a menu first"}, 400

    rules = load_nutrition_rules()
    targets_per_week = _targets(rules)
    macros: List[str] = list(targets_per_week.keys())

    totals: Dict[str, int] = {m: 0 for m in macros}
    counts: Dict[str, int] = {}  # normalized ingredient -> occurrence count (for swap suggestions)
    weeks: List[Dict[str, Any]] = []

    for menu in menus:
        week: Dict[str, int] = {m: 0 for m in macros}
        expanded = expand_menu(menu.meals) or {}
        for day, meal in expanded.items():
            if not isinstance(meal, dict):
                continue
            for raw in meal.get("ingredients") or []:
                tags = _tags_for(raw, rules)
                if not tags:
                    continue
                norm = sanitize_text(raw).lower()
                counts[norm] = counts.get(norm, 0) + 1
                for t in tags:
                    if t in totals:
                        totals[t] += 1
                        week[t] += 1
        weeks.append({"id": menu.id, "tags": week})

    weeks_in_window = len(weeks)
    targets = {m: targets_per_week.get(m, 0) * weeks_in_window for m in macros}

    flags = [f"low {m}" for m in macros if totals.get(m, 0) < targets.get(m, 0)]
    suggestions = _suggest(totals, targets, counts)

    return {
        "weeks_reviewed": weeks_in_window,
        "weekly_targets": targets_per_week,
        "totals": totals,
        "weeks": weeks,
        "flags": flags,
        "suggestions": suggestions,
    }


def _suggest(
    totals: Dict[str, int],
    targets: Dict[str, int],
    counts: Dict[str, int],
) -> List[str]:
    """Rule-based swap suggestions derived from the aggregate (audit B2)."""
    suggestions: List[str] = []
    flag_set = {f"low {m}" for m, t in targets.items() if totals.get(m, 0) < t}

    beef_like = counts.get("beef", 0) + counts.get("steak", 0) + counts.get("ground beef", 0)
    if beef_like >= 3 and totals.get("veg", 0) < targets.get("veg", 0):
        suggestions.append("Swap one beef-heavy dish for chicken breast + leafy greens.")
    if "low protein" in flag_set:
        suggestions.append("Add beans, lentils, eggs, or fish for protein.")
    if "low dairy" in flag_set:
        suggestions.append("Add cheese, yogurt, or milk for dairy/calcium.")
    if "low fiber" in flag_set:
        suggestions.append("Add beans, lentils, broccoli, or berries for fiber.")
    if "low carbs" in flag_set:
        suggestions.append("Add rice, pasta, bread, or potato for carbs.")
    if "low healthy_fat" in flag_set:
        suggestions.append("Add avocado, nuts, or olive oil for healthy fats.")
    if not suggestions and not flag_set:
        suggestions.append("Looks balanced — keep it up!")
    return suggestions


def enhanced_insights() -> Union[Dict[str, Any], Tuple[Dict[str, str], int]]:
    """Run rule-based ``insights()`` then optionally enhance via Ollama (§16.3).

    On any Ollama error or timeout, returns the rule-based result unchanged.
    When ``USE_OLLAMA`` is disabled in config, returns the rule-based result
    with an extra ``ai_suggestions: null`` field so the frontend can show the
    "Enhance with AI" button.
    """
    base = insights()
    if isinstance(base, tuple):
        return base  # propagate error: {"error": "Generate a menu first"}, 400

    if not current_app.config.get("USE_OLLAMA", False):
        base["ai_suggestions"] = None
        return base

    # gather raw weekly menu meals for context
    menus = WeeklyMenu.query.order_by(WeeklyMenu.id.desc()).limit(_WINDOW).all()
    meals_context = []
    for menu in menus:
        expanded = expand_menu(menu.meals) or {}
        for day, meal in expanded.items():
            if isinstance(meal, dict) and meal.get("name"):
                meals_context.append(
                    {"day": day, "name": meal["name"], "ingredients": meal.get("ingredients", [])}
                )

    prompt = (
        f"Here is this week's planned menu and a rule-based nutrition analysis.\n\n"
        f"Macro totals: {json.dumps(base.get('totals', {}))}\n"
        f"Weekly targets: {json.dumps(base.get('weekly_targets', {}))}\n"
        f"Deficiency flags: {json.dumps(base.get('flags', []))}\n"
        f"Rule-based suggestions: {json.dumps(base.get('suggestions', []))}\n\n"
        f"This week's meals: {json.dumps(meals_context)}\n\n"
        f"Provide 2-3 more specific improvement suggestions. For each, reference a "
        f"specific meal from this week's plan and suggest a concrete ingredient swap, "
        f"additional side dish, or meal modification to address the flagged deficiencies. "
        f"Return each suggestion as a single line of text, no markdown headers, no numbering."
    )

    ollama_text = call_ollama(prompt, timeout=current_app.config.get("OLLAMA_TIMEOUT", 15))
    if ollama_text is None:
        base["ai_suggestions"] = None
        return base

    # split into lines, filter blanks
    ai_lines = [line.strip() for line in ollama_text.split("\n") if line.strip()]
    base["ai_suggestions"] = ai_lines if ai_lines else None
    return base
