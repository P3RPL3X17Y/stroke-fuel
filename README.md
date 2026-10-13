# Stroke Fuel

A phone-first nutrition tracker for a collegiate rower at Purdue. It logs meals against the real dining-court menus, times fueling around practice, and recommends where and what to eat.

It runs as a Claude artifact: the page uses Claude for photo analysis and coaching, and stores data in the artifact's own database.

## Features

- **Photo logging.** Snap a plate and Claude matches it to that day's Purdue dining menu, with official nutrition facts.
- **Restaurants and drinks.** Log chains near campus (Chick-fil-A, Chipotle and others), plus one-tap drinks and quick fuel such as electrolytes, coffee, protein shakes and honey.
- **Targets.** Calories, macros, fiber, calcium, iron, sodium, potassium, fluids and caffeine. Targets scale with each day's training minutes.
- **Day plan.** Pre- and post-practice fueling windows built from your practice schedule.
- **Where to eat.** Dining courts ranked for your next meal, an "Ask Claude" plate builder and restaurant order suggestions.
- **Coach chat.** Ask for swaps or add-ons. It respects your food preferences and allergen filters.

## Files

| File | What it is |
|---|---|
| `stroke-fuel.html` | The app (a single page published as a Claude artifact) |
| `sync_menus.py` | Pulls menus and nutrition from Purdue's public dining API into one JSON file per location per day |

## Refreshing menus

```bash
python sync_menus.py menus 2026-10-12 7
```

This writes `menus/<date>_<location>.json`. Each file is uploaded as a document in the artifact's `menus` collection. A weekly scheduled task does this automatically.

Menu data comes from Purdue Housing & Food Services' public dining API (`api.hfs.purdue.edu`). This project isn't affiliated with Purdue.

Nutrition targets are general sports-nutrition estimates, not medical advice.
