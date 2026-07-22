# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Lidl++ is a hackathon project: a Flask backend + React frontend that takes a list of grocery items from
a store manager, and returns an optimal-ordering map of a 2D store layout for picking those items.
The "AI model" (store-layout optimization pipeline) is plain Python, not an actual ML model despite the
naming (`gemini_slop.py`).

## Commands

### Backend (Python/Flask)
- Run backend: `./run_backend.sh` (equivalent to `python3 main.py`), serves on port 6969
- Uses a venv at `./venv` — activate with `source venv/bin/activate` before running pip/python manually
- No test suite, linter, or requirements.txt exists for the Python side. Key deps observed in the venv:
  Flask, flask-cors, numpy, opencv-python, Pillow

### Frontend (React/Vite)
All frontend commands run from `frontend/`:
- Install deps: `npm install`
- Dev server: `npm run dev` (or `./run_frontend.sh` from repo root)
- Build: `npm run build`
- Lint: `npm run lint` (oxlint, config in `frontend/.oxlintrc.json`)
- Preview production build: `npm run preview`

## Architecture

### Backend (`main.py`, `gemini_slop.py`)
- `main.py` is the Flask app. It instantiates `gemini_slop.StoreOptimizationPipeline` once at startup, then
  exposes a single POST endpoint `/submit` that accepts form-encoded fields `product` (comma-separated item
  names) and `mapId`. Note: the current implementation doesn't actually route through the pipeline for the
  response — it just reads `shelves.png` from disk, base64-encodes it, and returns it as `map_url` along with
  the parsed `items` list.
- `gemini_slop.py` defines `StoreOptimizationPipeline`, which is the intended core logic:
  - Loads a store layout as a binary numpy mask (`bin_mask.npy`; 1 = shelf/obstacle, 0 = walkable) via
    `load_store_layout`.
  - Loads customer purchase histories from a comma-separated text file (`train_data/data.txt`) via
    `load_customer_demands` — used for demand analysis (`get_top_items`) rather than per-request logic.
  - `load_item_coordinates` / `calculate_picking_locations` map item names to grid coordinates on the mask,
    intended to translate a submitted shopping list into physical picking locations.
- `generate_shelves.py` is a standalone script (not imported by the app) that procedurally draws a store
  layout image (`shelves.png`) and derives the corresponding binary occupancy grid (`bin_mask.npy`) used by
  the pipeline. Re-run it if the shelf layout needs to change.
- `train_data/shoping_card_generator.py` is a standalone script that generates synthetic shopping baskets
  (random subsets of a fixed product list) and appends them to `train_data/data.txt`, one basket per line.

### Frontend (`frontend/src`)
- Single-page app: `App.jsx` holds all UI state (typed product, selected map id, loading, returned map image).
- `api.js` is the only place that talks to the backend — `submitProduct(productName, mapId)` POSTs
  `FormData` (fields `product`, `mapId`) to `http://localhost:6969/submit` and returns the parsed JSON. The
  backend's `map_url` is a raw base64 string (no data URI prefix), so callers must prepend
  `data:image/png;base64,` themselves before using it as an `<img src>` — `App.jsx` does this.
- `maps_ids.json` is a static list of `{id, name}` map options populated into a dropdown; there is currently
  only one entry. The backend receives the selected `mapId` but `main.py` does not yet use it to pick a
  different layout image.
- Frontend and backend are decoupled only by convention — the backend host/port (`localhost:6969`) is
  hardcoded in `api.js`, and CORS is opened via `flask-cors` in `main.py`.

## Known gaps (don't be surprised)
- `mapId` selection on the frontend has no effect on the backend response — `shelves.png` is always returned.
- `StoreOptimizationPipeline` is instantiated in `main.py` but the `/submit` route never calls into it, so
  `load_store_layout`/`load_customer_demands`/`calculate_picking_locations` are currently dead code from the
  route's perspective.
- No automated tests exist for either backend or frontend.
