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
    │   ├── assess/page.tsx     # 3-step assessment wizard
    │   ├── results/page.tsx    # Results dashboard with charts
    │   ├── ar/page.tsx         # A-Frame AR/3D visualization
    │   └── about/page.tsx      # About the framework + references
    ├── lib/
    │   ├── types.ts            # TypeScript interfaces
    │   ├── api.ts              # Axios API client
    │   └── utils.ts            # Helper functions
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
- **A-Frame** — WebXR/AR 3D visualization
- **react-hook-form + zod** — Form validation

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/assess` | Run full hydrological assessment |
| `GET` | `/api/weather?lat=&lon=` | Preview weather for coordinates |
| `GET` | `/api/report/{id}` | Download PDF report |
| `GET` | `/api/assessments` | List recent assessments |
| `GET` | `/api/health` | Health check |
| `GET` | `/docs` | Swagger UI (interactive API docs) |

---

## 🧪 Running Tests

```powershell
cd backend
python -m pytest tests/ -v
```

---

## 📱 AR Visualization

- **Desktop**: Interactive 3D scene (A-Frame) — click and drag to rotate, scroll to zoom
- **Mobile (Android Chrome)**: WebXR AR mode — point camera at flat surface to place 3D model

---

## 📝 License

For academic and research use. Cite as:

> Patil D., Desai S., Mahadik S., Agale K., Kshirsagar O., "Review of Hydrological Models and GIS Applications in Artificial Recharge and Rooftop Harvesting Assessment", ICICIS Conference 2026, ADYPU, Paper ID: 195.
