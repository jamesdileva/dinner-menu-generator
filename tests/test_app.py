"""End-to-end smoke + regression tests against an isolated temp SQLite DB (audit §11).

These cover the behaviours we've been building this week:
- §4.4 health, §5.18 search/pagination, §5.14 category, §5.13 menu+grocery flow,
- §8.3 CSRF header check, §8.7 generic 404/500 error responses,
- §9.1 indexes (implicitly, via the queries that use them), §5.21 rate limiting.
- B3a grocery extras + Snacks bucket, B2 /insights macro flags.
"""

import pytest

# Every state-changing request carries the CSRF header apiFetch sends (§8.3/§5.22).
HDR = {"X-Requested-With": "XMLHttpRequest"}


def _add(client, name, ingredients=None, category=None):
    payload = {"name": name, "ingredients": ingredients or []}
    if category:
        payload["category"] = category
    return client.post("/meal", json=payload, headers=HDR)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_404_is_generic(client):
    r = client.get("/nope")
    assert r.status_code == 404
    assert r.get_json() == {"error": "Not Found"}


def test_500_is_generic(client):
    # §8.7 — unhandled exception must NOT leak internals to the client.
    r = client.get("/__raise__")
    assert r.status_code == 500
    body = r.get_json()
    assert body == {"error": "Internal server error"}
    assert "RuntimeError" not in r.data.decode()


def test_csrf_rejects_missing_header(client):
    # §8.3 — a forged cross-site POST (no custom header) is rejected.
    r = client.post("/meal", json={"name": "NoHeader"})
    assert r.status_code == 403
    assert r.get_json() == {"error": "CSRF verification failed"}


def test_meal_crud_with_header(client, app):
    from models import Meal, db

    assert _add(client, "Burger", ["beef"], category="Dinner").status_code == 200
    with app.app_context():
        m = Meal.query.filter(Meal.name == "Burger").first()
        mid = m.id

    # update
    assert (
        client.put(
            f"/meal/{mid}",
            json={"name": "Cheeseburger", "ingredients": ["beef", "cheese"]},
            headers=HDR,
        ).status_code
        == 200
    )
    with app.app_context():
        assert db.session.get(Meal, mid).name == "Cheeseburger"

    # delete
    assert client.delete(f"/meal/{mid}", headers=HDR).status_code == 200
    with app.app_context():
        assert db.session.get(Meal, mid) is None


def test_meals_search_and_category(client, app):
    # §5.18 search + §5.14 category filter
    for i in range(3):
        _add(client, f"Meal {i}", ["rice"], category="Dinner")
    _add(client, "Salad", ["lettuce"], category="Lunch")

    r = client.get("/meals?search=meal 1")
    assert r.status_code == 200
    data = r.get_json()
    assert data["total"] == 1
    assert data["meals"][0]["name"] == "Meal 1"

    r = client.get("/meals?category=dinner")
    assert r.get_json()["total"] == 3

    r = client.get("/meals?search=zzzznope")
    assert r.get_json()["total"] == 0

    r = client.get("/meals/categories")
    assert set(r.get_json()["categories"]) == {"Dinner", "Lunch"}


def test_menu_and_grocery_flow(client, app):
    # §5.13 menu stores meal ids; §5.17 ingredients shown from the expanded menu.
    for i in range(7):
        _add(client, f"Meal {i}", ["rice", "chicken", "tomato"])
    r = client.get("/menu/week")
    assert r.status_code == 200
    week = r.get_json()
    assert set(week) == {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
    # each day's meal now carries ingredients (§5.17)
    assert week["Mon"]["ingredients"] == ["rice", "chicken", "tomato"]

    r = client.get("/grocery")
    assert r.status_code == 200
    g = r.get_json()
    # tomato -> Produce, chicken -> Protein, rice -> Grains (§5.10 categorize)
    assert "Produce" in g and "Protein" in g and "Grains" in g


def test_categorize_snacks_bucket():
    # §5.10 / B3a — snack items bucket as Snacks; plain cereal stays Grains.
    from utils import categorize_ingredient

    assert categorize_ingredient("oreos") == "Snacks"
    assert categorize_ingredient("cookies") == "Snacks"
    assert categorize_ingredient("rice krispies") == "Snacks"
    assert categorize_ingredient("cereal bar") == "Snacks"
    assert categorize_ingredient("cereal") == "Grains"
    assert categorize_ingredient("rice") == "Grains"


def test_grocery_extras_and_snacks(client):
    # B3a — custom extras persist and fold into the categorized /grocery list + export.
    for i in range(7):
        _add(client, f"Meal {i}", ["rice", "chicken"])
    assert client.get("/menu/week").status_code == 200

    r = client.put("/grocery/extras", json={"items": ["oreos", "cereal"]}, headers=HDR)
    assert r.status_code == 200
    assert r.get_json()["extras"] == ["oreos", "cereal"]

    e = client.get("/grocery/extras").get_json()
    assert e == {"extras": ["oreos", "cereal"]}

    g = client.get("/grocery").get_json()
    assert "Snacks" in g and "Oreos" in [i["item"] for i in g["Snacks"]]  # oreos -> Snacks
    assert "Grains" in g and "Cereal" in [i["item"] for i in g["Grains"]]  # cereal -> Grains

    txt = client.get("/grocery/export?format=text").get_data(as_text=True)
    assert "Oreos" in txt and "Cereal" in txt and "Snacks" in txt

    csv_data = client.get("/grocery/export?format=csv").get_data(as_text=True)
    assert "Purchased" in csv_data


def test_grocery_checkoff_toggle(client):
    # §13.3 — toggle a single item's checked-off state, persisted per menu.
    for i in range(7):
        _add(client, f"Meal {i}", ["rice", "chicken"])
    assert client.get("/menu/week").status_code == 200

    g = client.get("/grocery").get_json()
    assert "Grains" in g and "Rice" in [i["item"] for i in g["Grains"]]
    item = g["Grains"][0]
    assert item["purchased"] is False

    # toggle on
    r = client.post("/grocery/purchased/Rice", headers=HDR)
    assert r.status_code == 200
    assert r.get_json() == {"item": "rice", "purchased": True}

    # grocery list reflects the change
    g2 = client.get("/grocery").get_json()
    rice_item = [i for i in g2["Grains"] if i["item"] == "Rice"]
    assert rice_item and rice_item[0]["purchased"] is True

    # toggle off
    r2 = client.post("/grocery/purchased/Rice", headers=HDR)
    assert r2.get_json() == {"item": "rice", "purchased": False}


def test_insights_requires_menu(client):
    # B2 — no menus yet -> 400, not a 500.
    r = client.get("/insights")
    assert r.status_code == 400
    assert r.get_json() == {"error": "Generate a menu first"}


def test_insights_low_dairy_flag(client):
    # B2 — beef/potato/broccoli meals, no dairy -> "low dairy" flag + suggestion.
    for i in range(7):
        _add(client, f"Steak {i}", ["beef", "potato", "broccoli"])
    client.get("/menu/week")
    client.get("/menu/week")

    r = client.get("/insights")
    assert r.status_code == 200
    data = r.get_json()
    assert data["weeks_reviewed"] == 2
    assert "low dairy" in data["flags"]
    assert any("dairy" in s.lower() for s in data["suggestions"])


@pytest.mark.slow
def test_rate_limit_429(client):
    # §5.21/§8.4 — default 120/min; the 121st request is rejected.
    for _ in range(120):
        assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 429


def test_saving_catalog_crud(client):
    # §13.3b — full lifecycle: list (empty) → create → list → idempotent re-save → delete → list
    r0 = client.get("/savings")
    assert r0.status_code == 200
    assert r0.get_json() == {"savings": []}

    r1 = client.post("/saving", json={"name": "Oreos"}, headers=HDR)
    assert r1.status_code == 201
    s = r1.get_json()
    assert s["created"] is True
    assert s["saving"]["name"] == "Oreos"
    # §13.3b — auto-grouped as "snacks" (matches _SNACKS_WORDS)
    assert s["saving"]["group"] == "snacks"

    r2 = client.get("/savings")
    assert r2.status_code == 200
    savings = r2.get_json()["savings"]
    assert len(savings) == 1
    saving_id = savings[0]["id"]

    # idempotent: re-adding the same name returns 200, created=false
    r3 = client.post("/saving", json={"name": "oreos"}, headers=HDR)  # case-insensitive match
    assert r3.status_code == 200
    assert r3.get_json()["created"] is False

    # delete
    r4 = client.delete(f"/saving/{saving_id}", headers=HDR)
    assert r4.status_code == 200

    # deleting again -> 404
    r5 = client.delete(f"/saving/{saving_id}", headers=HDR)
    assert r5.status_code == 404

    # empty again
    assert client.get("/savings").get_json() == {"savings": []}


def test_saving_groups_snacks_vs_staples(client):
    # §13.3b — snacks (oreos, cookies) auto-grouped vs staples (ketchup, milk)
    oreos = client.post("/saving", json={"name": "Oreos"}, headers=HDR).get_json()["saving"]
    ketchup = client.post("/saving", json={"name": "Ketchup"}, headers=HDR).get_json()["saving"]
    milk = client.post("/saving", json={"name": "Milk"}, headers=HDR).get_json()["saving"]

    assert oreos["group"] == "snacks"
    assert ketchup["group"] == "staples"
    assert milk["group"] == "staples"


def test_saving_missing_name(client):
    r = client.post("/saving", json={"name": ""}, headers=HDR)
    assert r.status_code == 400


def test_promote_extra_to_saving(client):
    # §13.3b — add an ad-hoc extra to the week, then promote it to the saved grocery catalog
    for i in range(7):
        _add(client, f"Meal {i}", ["rice", "chicken"])
    client.get("/menu/week")

    # step 1: type an extra "pretzels"
    r1 = client.put("/grocery/extras", json={"items": ["pretzels"]}, headers=HDR)
    assert r1.get_json()["extras"] == ["pretzels"]

    # step 2: promote it — now it exists in the catalog
    r2 = client.post("/saving", json={"name": "pretzels"}, headers=HDR)
    assert r2.status_code == 201
    savings = client.get("/savings").get_json()["savings"]
    assert any(s["name"] == "pretzels" for s in savings)

    # step 3: the extra is still in the week's extras (no duplicate)
    extras = client.get("/grocery/extras").get_json()["extras"]
    assert "pretzels" in extras


def test_saving_click_adds_to_extras(client):
    # §13.3b — clicking a saved grocery badge appends it to the current week's extras
    client.post("/saving", json={"name": "Hummus"}, headers=HDR)
    for i in range(7):
        _add(client, f"Meal {i}", ["rice", "chicken"])
    client.get("/menu/week")

    # current extras (before)
    before = client.get("/grocery/extras").get_json()["extras"]

    # simulate clicking the badge: add "Hummus" to extras
    next_extras = list(before) + ["Hummus"]
    r = client.put("/grocery/extras", json={"items": next_extras}, headers=HDR)
    assert "Hummus" in r.get_json()["extras"]
