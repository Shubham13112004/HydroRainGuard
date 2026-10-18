# 💧 HYDRO RAIN GUARD

> **Intelligent Rainwater Harvesting & Artificial Groundwater Recharge Assessment System**

An integrated decision-support framework combining **Hydrological
Modelling + Gridded GIS Rainfall Data + Multi-Criteria Decision
Analysis + AR** for sustainable water management.

Every claim below is implemented in code — the gridded rainfall lookup,
the two runoff methods, the AHP ranking and the multi-script PDF are all
real, and each is covered by tests in `backend/tests/`.

**Paper ID: 195 | ICICIS Conference 2026 — ADYPU**  
**Authors:** Dr. Dipali Patil • Shubham Desai • Siddhesh Mahadik • Kaushal Agale • Omkar Kshirsagar  
**Institution:** JSPM's Rajarshi Shahu College of Engineering, Pune

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** — [python.org](https://python.org)
- **Node.js 18+** — [nodejs.org](https://nodejs.org)
- **pip** and **npm** (included with Python and Node.js)

### 1. Start the Backend (FastAPI)

```powershell
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Database tables are created automatically on startup — there is no
manual init step. Copy `backend/.env.example` to `backend/.env` if you
want to change the database or add an OpenWeatherMap key.

The API will be running at: **http://localhost:8000**  
API Docs (Swagger UI): **http://localhost:8000/docs**

### 2. Start the Frontend (Next.js)

Open a new terminal:

```powershell
cd frontend
npm install
npm run dev
```

The app will be running at: **http://localhost:3000**

The frontend calls `/api/*` on its own origin and `next.config.js`
forwards those requests to the backend, so you never have to point
browser code at `localhost:8000` (and CORS never gets involved).
Override with `NEXT_PUBLIC_API_URL` / `API_PROXY_TARGET` if your
backend lives somewhere else.

---

## 🌧️ Rainfall data (no API key needed)

Rainfall comes from a **real gridded global precipitation climatology**,
not a lookup table:

| | |
|---|---|
| Dataset | NOAA PSL **CMAP** — CPC Merged Analysis of Precipitation |
| Native grid | 2.5° × 2.5° (72 × 144 cells), global |
| Period | Monthly long-term means, **1991-01-01 → 2020-12-31** |
| Inputs merged | Rain gauges + 5 satellite estimates (so oceans and deserts are covered too) |
| Licence | Public domain (US Government work) |
| On disk | `backend/data/precip_climatology.bin` (373 KB) + `.json` provenance |

Your coordinates are **bilinearly interpolated** between the four
surrounding cell centres, with longitude wrap-around and no-data
handling. OpenWeatherMap, when a real key is set, adds only current
temperature and humidity — annual rainfall always comes from the grid.

### Rebuilding the grid

```bash
cd backend
python scripts/build_rainfall_grid.py --sqlite /path/to/precip_grid.sqlite
```

### The 2.5° caveat — and the fix

A 2.5° cell is roughly **278 km across**, so the grid cannot resolve
orographic gradients. One cell covers both the high-rainfall crest of
the Western Ghats and the rain-shadow east of it, which is why the grid
reports ~1400 mm for Pune city, whose station normal is ~700 mm.

So the assessment accepts an **`annual_rainfall_override`**. Supply a
local station total (IMD, state groundwater board, or your own gauge)
and the grid's *monthly distribution* is kept while only the annual
total is rescaled. The UI, the PDF and the API all state which of the
two was used.

### Live weather (optional)

OpenWeatherMap adds current temperature and humidity only:

1. Get a free API key at [openweathermap.org/api](https://openweathermap.org/api)
2. Edit `backend/.env`: `OPENWEATHER_API_KEY=your_actual_key_here`
3. Restart the backend

---

## 📁 Project Structure

```
hydro-rain-guard/
├── backend/                    # FastAPI Python backend
│   ├── main.py                 # API routes & app entry point
│   ├── config.py               # Settings (env vars)
│   ├── database.py             # SQLAlchemy async database
│   ├── models/
│   │   ├── schemas.py          # Pydantic request/response models
│   │   └── db_models.py        # SQLAlchemy ORM models
│   ├── services/
│   │   ├── hydrology.py        # Rational + SCS-CN runoff, recharge
│   │   ├── weather.py          # Grid sampling + optional live weather
│   │   ├── rainfall_grid.py    # CMAP raster reader + bilinear sampler
│   │   ├── feasibility.py      # AHP structure recommendation engine
│   │   ├── mcda.py             # AHP weights, λmax, CI, CR
│   │   ├── cost_benefit.py     # Economic analysis
│   │   ├── text_shaper.py      # HarfBuzz shaping for ReportLab
│   │   └── pdf_report.py       # Multi-script PDF generation
│   ├── data/
│   │   ├── precip_climatology.bin   # 373 KB CMAP raster
│   │   └── fonts/                   # Noto Sans + Noto Sans Devanagari
│   ├── scripts/
│   │   └── build_rainfall_grid.py   # Reproducible raster builder
│   ├── tests/
│   │   ├── test_api.py         # End-to-end API tests
│   │   ├── test_hydrology.py   # Grid + runoff + recharge tests
│   │   └── test_pdf_text.py    # Shaping + PDF rendering tests
│   ├── requirements.txt
│   └── .env
│
└── frontend/                   # Next.js 14 App Router frontend
    ├── app/
    │   ├── page.tsx            # Landing page (hero, features, workflow)
    │   ├── assess/page.tsx     # 3-step assessment wizard + map picker
    │   ├── results/page.tsx    # Results dashboard with charts
    │   ├── ar/page.tsx         # 3D / AR visualisation
    │   └── about/page.tsx      # About the framework + references
    ├── components/
    │   ├── MapPicker.tsx       # Leaflet map pin + geocoding
    │   ├── ARViewer.tsx        # react-three-fiber scene
    │   ├── LanguageSwitcher.tsx
    │   ├── Navbar.tsx
    │   └── Footer.tsx
    ├── lib/
    │   ├── types.ts            # TypeScript interfaces
    │   ├── api.ts              # Axios API client
    │   ├── utils.ts            # Helper functions
    │   └── i18n/               # en / hi / mr dictionaries + provider
    ├── package.json
    └── .env.local
```

---

## 🔬 How It Works

### System Workflow

```
User Input → Weather Fetch → Hydrological Analysis → Feasibility Check → Report
```

1. **Data Input**: Name, location (lat/lng), roof details, site conditions
2. **Rainfall Lookup**: Bilinear sample of the CMAP 2.5° monthly climatology
3. **Runoff Calculation**: Rational/volumetric method (`V = C × R × A`), with the SCS Curve Number method computed alongside as a cross-check
4. **Recharge Analysis**: Soil infiltration rate × open area × rainy hours
5. **Feasibility & Recommendations**: Analytic Hierarchy Process over five criteria for 5 structure types
6. **Cost-Benefit**: Installation cost vs annual water savings, payback period
7. **AR Visualization**: react-three-fiber 3D model of the recommended system
8. **PDF Report**: Multi-script PDF (English / हिन्दी / मराठी) with all calculations, rankings and provenance

### Hydrological Methods

| Calculation | Method | Formula |
|---|---|---|
| Annual runoff | Rational / volumetric (CGWB, 2007) | `V = C × R × A` |
| Runoff cross-check | SCS Curve Number (USDA-NRCS TR-55) | `S = 25400/CN − 254`, `Q = (P − 0.2S)² / (P + 0.8S)` |
| Runoff coefficient | Roof material lookup | C = 0.30–0.95 |
| Curve number | Roof material lookup | CN = 75–98 |
| Recharge potential | Darcy/Infiltration | `Rg = Ks × A × T` |
| Tank sizing | Per capita demand | `People × 135L/day` |
| Payback period | Economic | `Cost / Net Annual Savings` |

Both runoff methods are always reported. Applied to *monthly* totals,
SCS-CN lands within roughly ±10% of the Rational method; that spread is
shown in the results and the PDF rather than hidden.

### Structure ranking: Analytic Hierarchy Process

Structures are ranked by AHP (T.L. Saaty, *The Analytic Hierarchy
Process*, McGraw-Hill, 1980) — a published, deterministic
multi-criteria decision method. It is **not machine learning**: there is
no training data, no fitted model and no learned parameters.

| Criterion | Weight |
|---|---|
| Harvestable yield | 41.7% |
| Annual rainfall | 26.3% |
| Soil infiltration | 16.0% |
| Open space | 9.8% |
| Groundwater depth | 6.2% |

Weights come from a stated pairwise comparison matrix
(`backend/services/mcda.py`) and are checked for internal consistency:
**CR = 0.015** against Saaty's 0.10 acceptability threshold. The matrix,
λmax, CI and CR are returned in the API response and printed in the PDF,
so a reviewer can audit or replace the judgements.

Each criterion is converted to a 0–1 utility before weighting, so
millimetres of rain are never added to square metres of space.
Physically impossible options (a percolation tank in 2 m²) are filtered
out before scoring rather than merely penalised.

### Recharge Structure Types

| Structure | Best For |
|---|---|
| Rooftop Storage Tank | All buildings (primary collection) |
| Recharge Pit | Sandy/gravel soil, depth > 5m, space > 9m² |
| Recharge Well | Deep aquifers (>15m), limited space |
| Percolation Tank | Large open spaces (>100m²) |
| Soak Pit / French Drain | Loamy soil, moderate depth |

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** — High-performance Python API
- **SQLAlchemy** + **aiosqlite** — Async SQLite database
- **ReportLab** — PDF layout, tables and vector graphics
- **HarfBuzz** (`uharfbuzz`) — complex-script shaping for Devanagari
- **fontTools** — glyph outlines → ReportLab vector paths
- **Noto Sans / Noto Sans Devanagari** (SIL OFL 1.1) — bundled in `data/fonts/`
- **httpx** — Async HTTP client for weather API
- **Pydantic v2** — Data validation

### Frontend
- **Next.js 14** (App Router) — React framework
- **Tailwind CSS** — Utility-first styling
- **Recharts** — Interactive charts
- **Framer Motion** — Animations
- **react-three-fiber + drei** — 3D visualisation (lazy-loaded on `/ar`)
- **@react-three/xr** — WebXR AR placement on supported Android devices
- **Leaflet + react-leaflet** — Map pin picker (OpenStreetMap, no API key)
- **react-hook-form + zod** — Form validation
- **Built-in i18n** — English / हिन्दी / मराठी

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/assess` | Run full hydrological assessment |
| `GET` | `/api/weather?lat=&lon=&annual_rainfall_override=` | Grid rainfall for coordinates (optional local total) |
| `GET` | `/api/assessment/{id}` | Fetch one stored assessment (powers shareable result links) |
| `GET` | `/api/report/{id}` | Download PDF report |
| `GET` | `/api/assessments` | List recent assessments |
| `POST` | `/api/init-db` | Manual table creation escape hatch |
| `GET` | `/api/health` | Health check |
| `GET` | `/docs` | Swagger UI (interactive API docs) |

`POST /api/init-db` and `GET /api/assessments` return personal data, so
when `ENVIRONMENT=production` they require an `X-Admin-Token` header
matching `ADMIN_TOKEN`. Without it, `/api/assessments` redacts the
`name` and `location` fields.

---

## 🧪 Running Tests

```bash
cd ..            # run from Project/, so `backend` is an importable package
python -m pytest -q
```

38 tests cover the CMAP grid sampler, both runoff methods, AHP
consistency, the API end to end, and Devanagari shaping (conjuncts,
matra reordering, reph, font fallback).

---

## 🧊 3D / AR Visualisation

The `/ar` page renders your recommended structure to **scale from your
own assessment data** (roof area, tank volume, pit depth, borewell
depth). It is lazy-loaded, so the rest of the site never downloads the
3D engine.

- **Desktop** — drag to rotate, scroll to zoom
- **Cutaway view** — makes the ground transparent so you can see the
  underground recharge pit / well and the standing water inside
- **Structure picker** — switch between every recommended structure
- **Mobile (Android Chrome)** — tap **Enter AR** to place the model on
  the floor in front of you (WebXR `immersive-ar`)

> The old A-Frame scene was removed: `<a-animation>` and `<a-grid>`
> were deleted in A-Frame 0.9.0, so every animation in it was dead.

---

## 🗺️ Map Pin Picker

Instead of typing coordinates, drop a pin on an OpenStreetMap map:

- Drag the marker (or right-click the map) to your rooftop
- Latitude / longitude are filled automatically
- The Location field auto-completes via Nominatim reverse geocoding
- Search for a place, or use your device's GPS
- A "enter coordinates manually" toggle keeps power users happy

No API key and no billing — tiles and geocoding come from
OpenStreetMap.

## 🌐 Multi-language

English, हिन्दी (Hindi) and मराठी (Marathi) are supported. Use the
globe icon in the navbar; the choice persists in `localStorage` and
sets `<html lang>` so Devanagari renders with Noto Sans Devanagari.

```text
frontend/lib/i18n/
├── en.ts   # source of truth, exports the TranslationKey type
├── hi.ts   # partial dictionary
├── mr.ts   # partial dictionary
└── index.tsx  # provider + useI18n() hook + enum labels
```

Any key missing from a translation falls back to English, so partial
coverage can never break the UI. Structure names and enum labels are
translated in the UI.

**The PDF prints Devanagari correctly too.** ReportLab cannot shape
Indic scripts — it would emit `पि` with the matra on the wrong side and
render `क्ष` as two separate glyphs. `services/text_shaper.py` shapes
every string with **HarfBuzz** (the engine Chrome and Firefox use) and
draws the resulting glyphs as vector outlines through fontTools, so
conjuncts, half-forms, the reph and reordered matras all come out right
in English, हिन्दी and मराठी. Latin runs still go through `drawString`,
so ordinary text stays copyable and searchable.

Two honest limits: Devanagari text in the PDF is drawn as outlines, so
it is **not selectable**, and characters no bundled font covers (arrows,
maths symbols) are substituted with ASCII equivalents rather than
silently rendered blank.

## ⚙️ Environment variables

See `backend/.env.example` and `frontend/.env.example`.

| Variable | Where | Purpose |
|---|---|---|
| `DATABASE_URL` | backend | SQLite locally, Postgres/Neon in production |
| `OPENWEATHER_API_KEY` | backend | `demo` skips live weather; rainfall always uses the grid |
| `CORS_ORIGINS` | backend | Comma-separated allowed browser origins |
| `ENVIRONMENT` | backend | `production` enables the maintenance auth gate |
| `ADMIN_TOKEN` | backend | Guards `/api/init-db` and `/api/assessments` |
| `NEXT_PUBLIC_API_URL` | frontend | Leave empty for the same-origin proxy |
| `API_PROXY_TARGET` | frontend | Where Next forwards `/api/*` (default `http://localhost:8000`) |

> ⚠️ **SQLite does not survive on serverless hosts.** Vercel (and any
> FaaS platform) gives each invocation a fresh filesystem, so stored
> assessments and PDF downloads will disappear between requests. Use
> Neon/Postgres via `DATABASE_URL` for a real deployment.

## 📝 License

For academic and research use. Cite as:

> Patil D., Desai S., Mahadik S., Agale K., Kshirsagar O., "Review of Hydrological Models and GIS Applications in Artificial Recharge and Rooftop Harvesting Assessment", ICICIS Conference 2026, ADYPU, Paper ID: 195.
