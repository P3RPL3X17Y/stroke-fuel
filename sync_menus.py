"""Pull Purdue dining menus + nutrition facts into compact JSON files, one per (date, location).

Usage: python sync_menus.py OUT_DIR [START_DATE YYYY-MM-DD] [DAYS]
Each output file becomes one document in the tracker's `menus` collection.
"""
import json, re, sys, datetime as dt
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
from urllib.parse import quote

API = "https://api.hfs.purdue.edu/menus/v2"
# Nutrient label -> short key used by the app
KEYS = {
    "Calories": "kcal", "Protein": "p", "Total Carbohydrate": "c", "Total fat": "f",
    "Saturated fat": "sf", "Dietary Fiber": "fb", "Sugar": "su", "Added Sugar": "as",
    "Sodium": "na", "Cholesterol": "ch", "Calcium": "ca", "Iron": "fe",
    "Potassium": "k", "Vitamin D": "vd", "Vitamin A": "va", "Vitamin C": "vc",
}


def get(url):
    with urlopen(url, timeout=30) as r:
        return json.load(r)


def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")


def item_facts(item_id):
    try:
        d = get(f"{API}/items/{item_id}")
    except Exception:
        return None
    out, serving = {}, ""
    for n in d.get("Nutrition") or []:
        name = n.get("Name")
        if name == "Serving Size":
            serving = n.get("LabelValue") or ""
        elif name in KEYS and n.get("Value") not in (None, ""):
            out[KEYS[name]] = round(float(n["Value"]), 1)
        elif name in KEYS and n.get("DailyValue"):
            out[KEYS[name] + "%"] = n["DailyValue"]
    return {"sv": serving, **out}


def main():
    out_dir = sys.argv[1]
    start = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else dt.date.today()
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    import os
    os.makedirs(out_dir, exist_ok=True)

    locs = [(l["Name"], l.get("Type", "")) for l in get(f"{API}/locations")["Location"]]
    menus, ids = [], set()
    for i in range(days):
        date = (start + dt.timedelta(days=i)).isoformat()
        for name, kind in locs:
            try:
                m = get(f"{API}/locations/{quote(name)}/{date}")
            except Exception:
                continue
            menus.append((date, name, kind, m))
            for meal in m.get("Meals") or []:
                for st in meal.get("Stations") or []:
                    for it in st.get("Items") or []:
                        if it.get("NutritionReady"):
                            ids.add(it["ID"])

    with ThreadPoolExecutor(16) as ex:
        facts = dict(zip(ids, ex.map(item_facts, ids)))

    written = 0
    for date, name, kind, m in menus:
        meals = []
        for meal in m.get("Meals") or []:
            if meal.get("Status") != "Open" or not meal.get("Stations"):
                continue
            h = meal.get("Hours") or {}
            items = []
            for st in meal["Stations"]:
                for it in st.get("Items") or []:
                    f = facts.get(it["ID"])
                    if not f or "kcal" not in f:
                        continue
                    flags = {a["Name"]: a.get("Value") for a in it.get("Allergens") or []}
                    allergens = [k for k, v in flags.items() if v and k not in ("Vegetarian", "Vegan")]
                    items.append({"n": it["Name"], "st": st["Name"], "veg": bool(it.get("IsVegetarian")),
                                  "vgn": bool(flags.get("Vegan")), "al": allergens, **f})
            if items:
                meals.append({"name": meal["Name"],
                              "start": (h.get("StartTime") or "")[:5], "end": (h.get("EndTime") or "")[:5],
                              "items": items})
        doc = {"date": date, "hall": name, "kind": kind, "meals": meals}
        with open(os.path.join(out_dir, f"{date}_{slug(name)}.json"), "w", encoding="utf-8") as fh:
            json.dump(doc, fh, separators=(",", ":"))
        written += 1
    print(f"{written} menu docs, {len(ids)} items -> {out_dir}")


if __name__ == "__main__":
    main()
