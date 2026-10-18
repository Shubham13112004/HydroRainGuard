# 💧 HYDRO RAIN GUARD

> **Intelligent Rainwater Harvesting & Artificial Groundwater Recharge Assessment System**

An integrated decision-support framework combining **Hydrological Modelling + GIS + AI + AR** for sustainable water management.

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

## 🌦️ Optional: Real Weather Data

By default the app uses realistic **regional rainfall estimates** for India — no API key needed.

To enable **live weather data** from OpenWeatherMap:

1. Get a free API key at [openweathermap.org/api](https://openweathermap.org/api) (takes 2 minutes)
2. Edit `backend/.env`:
   ```
   OPENWEATHER_API_KEY=your_actual_key_here
   ```
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
│   │   ├── hydrology.py        # Runoff & recharge calculations
│   │   ├── weather.py          # OpenWeatherMap + regional fallback
│   │   ├── feasibility.py      # Structure recommendation engine
│   │   ├── cost_benefit.py     # Economic analysis
│   │   └── pdf_report.py       # ReportLab PDF generation
│   ├── tests/
│   │   └── test_hydrology.py   # Unit tests
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
2. **Weather Fetch**: OpenWeatherMap API or India regional estimates (IMD-based)
3. **Runoff Calculation**: Rational Method (Q = C × i × A) + monthly distribution
4. **Recharge Analysis**: Soil infiltration rate × open area × rainy hours
5. **Feasibility & Recommendations**: Multi-criteria scoring for 5 structure types
6. **Cost-Benefit**: Installation cost vs annual water savings, payback period
7. **AR Visualization**: A-Frame 3D model of the recommended system
8. **PDF Report**: Full ReportLab PDF with all calculations and recommendations

### Hydrological Methods

| Calculation | Method | Formula |
|---|---|---|
| Annual runoff | Rational Method | `V = C × R × A` |
| Runoff coefficient | Roof material lookup | C = 0.30–0.95 |
| Recharge potential | Darcy/Infiltration | `Rg = Ks × A × T` |
| Tank sizing | Per capita demand | `People × 135L/day` |
| Payback period | Economic | `Cost / Net Annual Savings` |

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
- **ReportLab** — PDF report generation
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
| `GET` | `/api/weather?lat=&lon=` | Preview rainfall for coordinates |
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

```powershell
cd backend
python -m pytest tests/ -v
```

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
translated in the UI; the API contract and PDF report stay English.

## ⚙️ Environment variables

See `backend/.env.example` and `frontend/.env.example`.

| Variable | Where | Purpose |
|---|---|---|
| `DATABASE_URL` | backend | SQLite locally, Postgres/Neon in production |
| `OPENWEATHER_API_KEY` | backend | `demo` uses the regional rainfall dataset |
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
