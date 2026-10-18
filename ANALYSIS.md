# HydroRainGuard — Technical Repository Analysis

**Repository:** [Shubham13112004/HydroRainGuard](https://github.com/Shubham13112004/HydroRainGuard)
**Analysed:** 2026-10-18 · branch `main` @ `50e457e`
**Scope:** full codebase (33 files, ~3,990 lines) — static review + executed verification

---

## 1. Executive Summary

| | |
|---|---|
| **What it is** | A full-stack rainwater-harvesting / groundwater-recharge assessment tool built as the reference implementation for conference paper ID 195 (ICICIS 2026, ADYPU). FastAPI backend + Next.js 14 App Router frontend, SQLite/Postgres persistence, ReportLab PDF export, A-Frame 3D view. |
| **Overall verdict** | **Impressive for its purpose, but not production- or demo-safe as committed.** The architecture is clean and the code is readable; however there is one **functional blocker that breaks the primary user journey on a fresh clone**, a **UI bug that makes the coordinate fields unusable**, a **cost model that reports "99 years" payback for the app's own default city**, and **unauthenticated endpoints exposing users' personal data**. |
| **Can a reviewer clone and run it?** | **No — not by following the README.** `POST /api/assess` returns HTTP 500 on a fresh database. See §4.1. |
| **Can it be deployed as-is?** | **No.** SQLite on serverless is ephemeral, the CORS allowlist appears to point at a different hostname than the deployed frontend, and the API base URL defaults to `http://localhost:8000`. See §4.2, §6. |
| **Biggest academic risk** | The landing page and About page claim **GIS/Remote Sensing**, **AI/ML**, and **SCS-CN** capability that the code does not implement. See §7. |

### Top 5 things to fix first

1. **Create DB tables on startup** — every assessment currently 500s on a fresh clone. (§4.1)
2. **Hoist `InputField`/`SelectField` out of `AssessPage`** — typing in Latitude/Longitude drops focus after every keystroke. (§4.3)
3. **Fix the cost-benefit model** — the default Pune scenario yields *99 years* payback and −113% ROI. (§4.4)
4. **Lock down or remove `/api/assessments`, `/api/init-db`, `/api/report/{id}`** — no auth, serve other users' names/locations/coordinates. (§6)
5. **Reconcile the marketing claims with the code** before reviewers read the paper. (§7)

---

## 2. Repository Facts

| Attribute | Value |
|---|---|
| Created | 2026-09-22 |
| Last push | 2026-10-18 |
| Commits on `main` | **1** (`50e457e` "Update page.tsx", 2026-09-23) |
| Branches | `main` only |
| Contributors | 1 |
| Stars / Forks / Watchers | 0 / 0 / 0 |
| Open issues / PRs | 0 / 0 |
| CI/CD | **none** (no GitHub Actions, no workflows, no test-on-PR) |
| License | **none** (README says "for academic and research use" — legally this is all-rights-reserved) |
| Description | empty |
| Homepage | `https://hydro-rain-guard.vercel.app` |
| Language split | TypeScript 79 KB · Python 48.5 KB · Batchfile 2.2 KB · CSS 1.3 KB · JS 0.3 KB |

**Everything was landed in a single squashed commit.** There is no history to bisect, no review trail, and no record of how any of the constants were derived — which is a real problem for a repository attached to a research paper, where provenance of coefficients matters.

**Missing files you would expect in any committed project:**

- `.gitignore` ← **highest risk**: `node_modules/`, `.next/`, `__pycache__/`, `*.db`, and the `.env` / `.env.local` files the README instructs you to create are all untracked-but-not-ignored. One `git add -A` commits your OpenWeatherMap key and your SQLite database.
- `package-lock.json` — no reproducible frontend install
- `.env.example` (backend and frontend)
- `pytest.ini` / `conftest.py` — tests only import correctly if run from `backend/` (see §5)
- `LICENSE`
- Any CI workflow

---

## 3. Architecture — what's genuinely good

The bones are sound. Credit where it's due:

- **Clean layering.** `main.py` (routing) → `services/` (pure functions) → `models/` (Pydantic + SQLAlchemy). Hydrology, weather, feasibility, cost-benefit, and PDF are properly separated, and each service is a small, readable, unit-testable module.
- **Contracts are shared and consistent.** `models/schemas.py` and `frontend/lib/types.ts` mirror each other field-for-field. I checked all 10 response types — they match. This is better than most student projects.
- **The wizard is defensively built.** Someone clearly hit the classic "pressing Next submits the form" bug and fixed it deliberately: there is no wrapping `<form>`, every button is `type="button"`, `handleNext` only validates the current step, and `onSubmit` has a `if (step !== 2) return` guard. The code comments explain *why*. Good instinct.
- **A serious deployment attempt was made.** `database.py` rewrites `postgres://` → `postgresql+asyncpg://`, strips `sslmode`/`channel_binding` from Neon URLs and moves SSL into `connect_args`. Someone debugged a real Neon connection. DB init was deliberately moved off the startup path for Vercel.
- **Graceful degradation.** Weather falls back to a regional table if the API key is `demo` or the call fails, so the app never hard-fails on missing config.
- **Frontend builds clean.** `next build` compiles with **zero** TypeScript and zero ESLint errors under `strict: true`; all 6 routes prerender static.
- **The PDF generator is genuinely polished** — styled tables, A4 layout, executive summary, per-structure breakdown. 8.4 KB of real, correct output.

---

## 4. Defects Found (verified by execution)

### 4.1 🔴 BLOCKER — `/api/assess` returns HTTP 500 on a fresh clone

**Severity: Critical · verified by running the API**

`main.py` never calls `init_db()`. Every route handler uses `Depends(get_db)` and writes to `assessments`, but nothing creates the table. There is an `POST /api/init-db` endpoint that does it — **but the README never mentions it**, and the setup scripts don't call it.

Actual output from a clean working directory, following the README exactly:

```
$ uvicorn main:app --reload --port 8000
$ POST /api/assess  { ...valid payload... }

HTTP 500
{"detail": "Assessment failed: (sqlite3.OperationalError) no such table: assessments
 [SQL: INSERT INTO assessments (id, timestamp, name, location, ...) VALUES (?, ?, ...)]"}
```

After `POST /api/init-db`, the identical request returns **200** with a complete, correct payload — so the pipeline itself is fine. **A reviewer following your README will hit a 500 on their first click and conclude the project is broken.**

**Fix** — add a lifespan handler (and keep `/api/init-db` as a manual escape hatch):

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(..., lifespan=lifespan)
```

Also add `/api/init-db` to the README quick-start.

---

### 4.2 🟠 HIGH — the DB layer cannot work on the deployed backend

**Severity: High · deployment**

`config.py` defaults to `sqlite+aiosqlite:///./hydro_rain_guard.db`. On Vercel (or any serverless/FaaS host) the filesystem is ephemeral and each invocation may get a fresh container. Consequences:

- `POST /api/assess` writes to a DB that vanishes → `GET /api/report/{id}` returns **404** for a report the user just generated.
- `GET /api/assessments` returns an empty or partial list.
- Even on a warm container, concurrent invocations don't share SQLite state.

The Neon/Postgres path is already written — it just isn't the default and isn't documented. **Fix:** require `DATABASE_URL` in production, fail fast at startup if it's missing, and document the Neon setup. Also note: **SQLite + `init_db()` in a lifespan handler is not concurrency-safe** — add a guard or `check_same_thread=False`.

---

### 4.3 🟠 HIGH — typing in Latitude/Longitude loses focus after every keystroke

**Severity: High · verified by execution**

`app/assess/page.tsx` declares `InputField` and `SelectField` **inside** `AssessPage`. React sees a brand-new component *type* on every render, so it unmounts and remounts the entire input subtree. Combined with `watch('latitude')` / `watch('longitude')` — which re-renders `AssessPage` on **every keystroke in those two fields** — the DOM node is destroyed and recreated after each character.

I reproduced this with React 18 + jsdom using the exact structure from the file:

```
same DOM node after re-render?   false
input was focused before?        true
still focused after re-render?   false
```

So the two fields the UI explicitly instructs the user to fill with high-precision decimals (`18.5204`) are the two that can't be typed into.

**Fix (two lines):** move `InputField` and `SelectField` to module scope, and drop the `watch` subscription — `lat`/`lon` are used **only** inside `handleFetchWeather` (lines 185–186 → 280–281), so `getValues()` at click time is the correct tool:

```tsx
const { getValues } = useForm<FormData>({ ... });
// ...
const { latitude: lat, longitude: lon } = getValues();
```

This also removes 2 re-renders per keystroke.

---

### 4.4 🟠 HIGH — the cost model says the flagship scenario never pays back

**Severity: High · correctness of the paper's central economic claim**

I ran the engine across five scenarios. The default Pune case (100 m², RCC, 4 people — the wizard's own pre-filled values) is the worst possible advertisement for the tool:

| Scenario | Rain (mm) | Harvest (KL/yr) | Cost (₹) | Gross ₹/yr | Maint ₹/yr | Net ₹/yr | **Payback** | **10-yr ROI** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Pune 100 m² / 4 p** | 700 | 43.0 | 90,000 | 645 | 1,800 | **−1,155** | **99.0 yr** | **−112.8 %** |
| Pune 300 m² / 10 p | 700 | 129.0 | 104,641 | 1,935 | 2,093 | **−158** | **99.0 yr** | −101.5 % |
| Mumbai 500 m² / 20 p | 2,300 | 935.0 | 84,721 | 14,025 | 1,694 | 12,331 | 6.9 yr | +45.5 % |
| Kerala 200 m² / 6 p | 3,000 | 500.0 | 68,284 | 7,500 | 1,366 | 6,134 | 11.1 yr | −10.2 % |
| Delhi 1000 m² / 50 p | 780 | 502.0 | 133,246 | 7,530 | 2,665 | 4,865 | 27.4 yr | −63.5 % |

Three distinct problems:

**(a) The measurement unit is wrong.** `99.0` is a *sentinel* for "never", but it's typed as a plain float and rendered as `99 yrs` in the UI and `99.0 Years` in the PDF. It isn't clamped, flagged, or explained.

**(b) Costs are charged for structures that generate no credited savings.** `calculate_cost_benefit` sums the **top 2** structures — typically `Rooftop Storage Tank` (₹25,000) **+ `Recharge Well` (₹45,000)** — but `annual_savings_inr` is derived *only* from `runoff.harvestable_volume`, i.e. the rooftop tank. The recharge well's benefit (groundwater recharge, borewell yield, avoided tanker costs) is never monetised, yet its full capital and maintenance cost is charged. That single asymmetry drives the Pune result. Either monetise recharge or cost the structures separately.

**(c) The tariff is implausibly low.** ₹15/KL (₹0.015/L) is far below the marginal cost of water in water-stressed Indian cities, where households pay tanker rates orders of magnitude higher. This is the single most sensitive parameter and it is a bare module-level constant (`WATER_RATE_PER_KL = 15`) with no citation and no UI exposure.

Also note the landing page advertises **"5-7yr — Typical payback period"** while the model returns 99 years for the default city.

**Fix:** separate storage economics from recharge economics; make the tariff a documented, user-adjustable, region-sensitive parameter (with a citation); and return `payback_period_years: null` (rendering "Not economically viable") instead of the `99.0` sentinel.

---

### 4.5 🟠 HIGH — annual and monthly savings disagree by 46%

**Severity: High · the numbers in the PDF and charts contradict each other**

`cost_benefit.py` computes the two figures from different bases:

- `annual_water_savings_liters` / `annual_savings_inr` ← **harvestable** volume (gross runoff **minus** first-flush loss)
- `monthly_savings[]` ← **gross** `runoff.monthly_runoff[i]`, with **no** first-flush deduction

Measured on the default Pune case:

```
annual_savings_inr   = ₹645
sum(monthly_savings) = ₹945      ← 46.5% higher
annual_water_savings_liters = 43,000 L
sum(monthly_runoff)          = 63,000 L
```

The 1.465× ratio is exactly `63,000 / 43,000` and appears in **every** scenario I ran (Mumbai: ₹15,525 vs ₹14,025; Delhi: ₹10,530 vs ₹7,530). Both figures are printed in the same PDF — the monthly table's `ANNUAL` row (₹945-equivalent basis) disagrees with the Executive Summary ("₹645"). The monthly area chart on the Results tab is likewise inflated.

**Fix:** apply the first-flush deduction per-month before converting to savings, then derive the annual figure as `sum(monthly_savings)` so they reconcile by construction.

---

### 4.6 🟡 MEDIUM — AR page is a static 1990s-era A-Frame scene, not AR

The `ar/` route is the paper's headline differentiator, but:

- **`<a-animation>` was removed in A-Frame 0.9.0** and doesn't exist in the 1.5.0 build you load. There are **7** of them in the scene (tank rotation, pit pulse, water particles, water level). **Every animation in the scene is silently dead.** They must be rewritten as the `animation="property: …; to: …; loop: true"` component.
- **`<a-grid>` was also removed** — the ground grid renders as nothing.
- **There is no WebXR hit-test.** No `webxr="optionalFeatures: hit-test"`, no `ar-hit-test` component, no reticle. The page tells mobile users to "point your camera at a flat surface to place the 3D model" — that interaction is not implemented. A-Frame enters its default VR-mode presentation, not AR.
- The scene is **hardcoded** and ignores the user's assessment entirely. `data`, `selected`, `structures3D` and `topStructure` are all read/declared but `setSelected` is never called and `structures3D` is never rendered — the "Here is *your* system" story isn't wired up.
- `dangerouslySetInnerHTML` with a 90-line inline HTML string bypasses React entirely and is unmaintainable.
- `layout.tsx` loads A-Frame with `strategy="beforeInteractive"` on **every route** — the landing page, About, the wizard all download a ~1 MB 3D engine they never use. Move it into `ar/page.tsx` with `afterInteractive`.

### 4.7 🟡 MEDIUM — rainfall data is a 10-row hardcoded table with global gaps

`weather.py` maps coordinates to annual rainfall via 10 bounding boxes. Problems:

- **Non-Indian coordinates get Indian monsoon data.** The catch-all box is `lat 0–90, lon 60–100`, so e.g. New York (40.7, −74) fails every box and falls through to the *initial default* of **1100 mm with an Indian monthly distribution** — then is labelled with a raw coordinate string. The form accepts −90…90 / −180…180, so this is reachable by any user.
- **Boxes overlap and order decides.** Pune (18.0–19.5, 73.0–74.5) and Mumbai (19.0–20.0, 72.7–73.5) intersect over lat 19.0–19.5 / lon 73.0–73.5; Pune silently wins because it's listed first. Undocumented, order-dependent behaviour.
- **Coverage outside 9 metros is a single flat 1100 mm** for the whole subcontinent — wrong by ~4× in Rajasthan and ~10× in Meghalaya.
- **The API key barely changes anything.** Even with a valid OpenWeatherMap key, `_fetch_from_openweather` overwrites `annual_rainfall` and `monthly_rainfall` from the same hardcoded regional table (`regional = _get_regional_estimate(...)`). The key only buys you `location_name`, `avg_temperature`, `humidity`, and `current_rainfall`. The "Real-time Weather / live rainfall data" claim is misleading.
- `current_rainfall = rain['1h'] * 24` extrapolates one hour to a full day.

**Fix:** use a real gridded climatology (IMD 0.25° gridded rainfall, or CHIRPS/WorldClim), store it as a raster or a proper lookup file, and fail loudly for out-of-coverage coordinates rather than defaulting to 1100 mm.

### 4.8 🟡 MEDIUM — dead code and unused assets

| Item | Location | Note |
|---|---|---|
| `ROOF_CN_VALUES` | `services/hydrology.py:20` | Defined, **never referenced**. The SCS-CN method it belongs to is not implemented. |
| `listAssessments()` | `lib/api.ts:33` | Exported, never imported. |
| `structures3D`, `topStructure` | `app/ar/page.tsx:16,47` | Declared, never rendered. |
| `setSelected` | `app/ar/page.tsx:9` | Never called. |
| `params` (from `useSearchParams`) | `app/results/page.tsx:39` | Never used — the `?id=` the assess page navigates to is ignored. |
| `frontend_url` | `config.py:12` | Set, never read. |
| `python-multipart` | `requirements.txt:11` | Pinned dependency for an app with **zero** form/File/UploadFile endpoints — and pinned to a vulnerable version (§6). |
| `components/**` in Tailwind `content` | `tailwind.config.ts` | Directory doesn't exist. |

### 4.9 🟡 MEDIUM — results are trapped in `localStorage`

`assess` writes to `localStorage['hydro_result']` and both `results` and `ar` read from it. Consequences: the `?id=` in the URL is decorative (§4.8); a shared or bookmarked `/results?id=X` link **redirects to `/assess`** for anyone else; results are gone in another browser or in incognito; and nothing invalidates a stale blob from an older schema version.

**Fix:** have `/results?id=` re-fetch from `GET /api/assessments/{id}` (or a dedicated `GET /api/assessment/{id}`), falling back to `localStorage`. This also makes the PDF download reliable once the DB is persistent (§4.2).

### 4.10 🟢 LOW — cosmetic / correctness nits

- **PDF timestamps are mislabelled.** `pdf_report.py` renders `datetime.now().strftime('%d %B %Y, %H:%M IST')` but `datetime.now()` returns **server-local** time — UTC on Vercel. The report says "IST" and is off by 5:30. Use `zoneinfo.ZoneInfo("Asia/Kolkata")`.
- **Emoji in the PDF title.** `'💧 HYDRO RAIN GUARD'` is rendered in Helvetica, which has no such glyph — it will come out as a tofu box. Use `<font name="DejaVuSans">` or drop it.
- **`transmissivity` is not transmissivity.** `main.py` sets it to `SOIL_INFILTRATION_RATES[soil] * 10` and the UI labels it `m²/day`. Real transmissivity is `K × saturated thickness`; the ×10 is an undocumented fudge factor. Presenting a fabricated number with physical units in a research report is a real liability.
- **`seasonal_fluctuation = annual_rainfall / 500 * 2`** — another undocumented heuristic presented as a measurement (metres).
- **Peak runoff is crude:** `(peak_month_mm / (30 × 24)) × 3` — a monthly mean annualised to an hourly rate, then tripled. It's an approximation; label it as such or derive intensity from a real IDF curve.
- **First flush assumes exactly 100 rain events/year**, everywhere — identical for Kerala (3,000 mm) and Delhi (780 mm). Should scale with rainy-day counts.
- **`a-text` line breaks won't render.** The source writes `value="Storage\\nTank"`, which lands in the DOM as a literal backslash-n; A-Frame's text component doesn't interpret it.
- **`asyncpg` is the only unpinned requirement** — the one dependency where an unpinned major bump is most likely to break you.
- **`results/page.tsx` is 403 lines** with five inline tab bodies and duplicated key/value rendering. Extract a `<StatRow>` and per-tab components; it's the only file in the repo that's genuinely hard to read.
- **No error boundary or empty-state handling.** The only failure UX is `alert('Failed to download. Make sure the backend is running.')` — misleading when the real cause is the ephemeral SQLite DB.

---

## 5. Testing & Quality Infrastructure

**Current state: 4 tests, all passing, all in one file.**

```
tests/test_hydrology.py::test_pune_rcc_100m2_runoff      PASSED
tests/test_hydrology.py::test_green_roof_lower_runoff    PASSED
tests/test_hydrology.py::test_recharge_feasibility_score PASSED
tests/test_hydrology.py::test_monthly_runoff_sums_to_annual PASSED
=========== 4 passed, 1 warning in 0.14s ===========
```

Good news: they're real behavioural tests (not smoke tests), they exercise the Pune/RCC path end-to-end, and they pass. The suite is a reasonable seed.

Gaps:

- **Coverage is confined to `hydrology.py`.** Zero tests for `feasibility`, `cost_benefit`, `weather`, `pdf_report`, or any API route. **§4.1 (the 500 on fresh DB) would have been caught by a single `TestClient` test of `/api/assess`.** So would §4.5 — one assertion that `sum(monthly_savings) ≈ annual_savings_inr`.
- **`pytest` isn't in `requirements.txt`**, so `pip install -r requirements.txt && pytest` fails.
- **There's no `conftest.py` or `pytest.ini`.** The tests import `models.schemas`, which only resolves when CWD is `backend/`. `pytest` from the repo root fails with `ModuleNotFoundError`.
- **`pydantic_settings` emits a deprecation warning** on `class Config` — will break on Pydantic v3. Switch to `ConfigDict`.
- **No linting/formatting in CI** (no ruff, black, eslint config beyond `eslint-config-next`, no pre-commit).
- **No CI at all** — nothing runs on push. For a repo backing a paper submission, a green badge matters.

**Recommended next tests (high value, low effort):**
1. `TestClient` POST `/api/assess` on a fresh in-memory DB → asserts 200 (catches §4.1)
2. `abs(sum(monthly_savings) - annual_savings_inr) < 1` → catches §4.5
3. Payback is positive for a high-rainfall site → catches §4.4
4. `weather.py`: assert non-Indian coordinates do **not** return 1100 mm → catches §4.7
5. `/api/assess` end-to-end → `generate_pdf_report` returns valid `%PDF` bytes

---

## 6. Security

| # | Issue | Severity | Detail |
|---|---|---|---|
| 1 | **Unauthenticated PII exposure** | **High** | `GET /api/assessments` requires no auth and returns `name`, `location`, `latitude`, `longitude` for the 20 most recent submissions. Full name + precise home coordinates of real users, publicly readable. |
| 2 | **Unauthenticated `/api/init-db`** | **High** | Anyone can POST it. At best a nuisance; at worst it forces schema creation against your production Postgres and can lock/error the pool. |
| 3 | **Insecure direct object reference** | Medium | `GET /api/report/{id}` has no ownership check. The ID is `uuid4()[:8]` → 16⁸ ≈ 4.3 × 10⁹ space. Not trivially enumerable, but combined with #1 (which hands out IDs) any ID leaks the full report: name, address text, coordinates. |
| 4 | **`full_response_json` stored in plaintext** | Medium | Every assessment persists the complete response — name, location, coordinates — as a `Text` column. No encryption, no retention policy, no deletion path. |
| 5 | **Vulnerable pinned dependency** | Medium | `python-multipart==0.0.9` is affected by **CVE-2024-53981** (DoS via deformed multipart boundary, CVSS 7.5, fixed in 0.0.18). The dependency is **entirely unnecessary** — the app has no form/File endpoints. **Delete it.** |
| 6 | **Vulnerable transitive dependency** | Medium | `fastapi==0.111.0` resolves `starlette==0.37.2`, affected by **CVE-2024-47874** (unbounded multipart buffering → DoS, fixed in 0.40.0). Requires bumping FastAPI. *(Practical risk is low — no endpoint declares `Form`/`File`, so the parser isn't invoked — but patch it anyway.)* |
| 7 | **Critical frontend advisory** | **High** | `next@14.2.3` — `npm audit` reports **1 critical + 1 high**, including unauthenticated RCE and SSRF advisories; patched in the 14.2.x line. `npm audit fix` wants `next@14.2.35`. |
| 8 | **High frontend advisory** | High | Transitive `postcss` ≤ 8.5.22 — XSS in CSS stringify output + arbitrary `.map` file read via `sourceMappingURL`. |
| 9 | **No rate limiting** | Low | `/api/assess` is unauthenticated and does PDF generation; trivially abused for resource exhaustion. |
| 10 | **Overly broad exception detail** | Low | Handlers return `str(e)` in `detail`, which can leak internals. Return a correlation ID; log the exception server-side. |

**Also verify** (I could not reach the deployment from this sandbox): `main.py` allows CORS from `https://hydro-rain-guard-mhus.vercel.app`, but the repository homepage is `https://hydro-rain-guard.vercel.app`. **If the deployed frontend lives at the latter, every browser API call is blocked by CORS.** The allowlist is also hardcoded, so no Vercel preview deployment will ever work. Move it to an env var (`CORS_ORIGINS`) and include the real production origin.

---

## 7. Research-Claim vs. Implementation Gap ⚠️

**This is the section I would most want the authors to read before submitting.** The landing page, README, and About page make three capability claims the code does not support. A reviewer who reads the source will find them, and they undermine the paper rather than support it.

| Claim (from `page.tsx` / README / `about/page.tsx`) | Reality in code |
|---|---|
| **"GIS & Remote Sensing"**, "Location-aware analysis using real coordinates" | No GIS library anywhere — no `geopandas`, `shapely`, `rasterio`, `folium`, `pyproj`. No raster or vector data. Latitude/longitude is used for **one thing**: a lookup into a 10-entry `if/elif` bounding-box table in `weather.py`. That's a coordinate lookup, not GIS, and nothing is remotely sensed. |
| **"AI Recommendations"**, "AI-powered structure recommendations", team member credited to "AI/ML Recommendation Engine" | `feasibility.py` is a **rule-based expert system**: 5 hardcoded `base_score` values (85/70/80/65/60) with ±10–25 point adjustments for soil, depth, space, and rainfall. No training data, no model artefact, no inference, no learning. It's a defensible and reasonable design — it just isn't AI. |
| **"Rational Method & SCS-CN based runoff estimation"**, `hydrology.py` docstring: "SCS Curve Number method" | Only the **Rational Method** (`V = C × R × A`) is implemented. `ROOF_CN_VALUES` is defined at line 20 and **never used anywhere in the codebase**. SCS-CN is dead code. |

Two of these are one-line fixes to the *wording*; the third is an honest reframing:

- Say **"rule-based multi-criteria decision scoring"** instead of "AI". It's accurate, and multi-criteria decision analysis (MCDA) is a legitimate, citable method — arguably more appropriate for a civil-engineering paper than an unvalidated ML model.
- Either **implement SCS-CN** (you have the CN table already — `S = 25400/CN − 254`, `Q = (P − 0.2S)² / (P + 0.8S)`, and comparing the two methods would make a genuinely interesting result for the paper) or **remove the claim**.
- Either drop "GIS" or add one real GIS feature. A cheap, honest win: serve the IMD/CHIRPS gridded rainfall raster and do a server-side point lookup — which simultaneously fixes §4.7.

The About page's 13-entry reference list is a genuine strength — CGWB's *Manual on Artificial Recharge of Groundwater*, BIS IS 15797, and current 2025 literature. **Cite those sources inline as comments next to the constants they justify** (`ROOF_RUNOFF_COEFFICIENTS`, `SOIL_INFILTRATION_RATES`, `WATER_RATE_PER_KL`, the 120-days × 8-hours recharge window, `base_score` values). Right now the magic numbers are unsourced, which is the first thing a reviewer will ask about — and it also documents *why* Pune's payback is 99 years.

---

## 8. Prioritized Remediation Plan

### Phase 1 — make it demo-safe (≈ 1 hour)
1. Add the `lifespan` handler calling `init_db()` → **fixes the 500** (§4.1)
2. Hoist `InputField`/`SelectField` to module scope; swap `watch()` → `getValues()` (§4.3)
3. Add `.gitignore` (`node_modules/`, `.next/`, `__pycache__/`, `*.db`, `.env*`) **before anything else**
4. Add `pytest` to `requirements.txt`; add `conftest.py`/`pytest.ini` so tests run from the repo root (§5)
5. Fix the CORS origin against the real deployment URL; move origins to env (§6)

### Phase 2 — make the numbers defensible (≈ half a day)
6. Reconcile monthly vs. annual savings; derive annual from the sum (§4.5)
7. Split storage vs. recharge economics; return `null` payback (not `99.0`) when infeasible; expose the water tariff as a cited, adjustable parameter (§4.4)
8. Add the 5 regression tests in §5 — especially the `/api/assess` 200 and the savings-reconciliation assertions
9. Replace the A-Frame `<a-animation>`/`<a-grid>` markup with the `animation` component; add `webxr="optionalFeatures: hit-test"`; move the A-Frame `<Script>` from `layout.tsx` into `ar/page.tsx` (§4.6)

### Phase 3 — make it production- and submission-ready (≈ 1–2 days)
10. Require `DATABASE_URL` (Neon/Postgres) in production; fail fast; document (§4.2)
11. Auth-gate `/api/assessments`, `/api/init-db`, `/api/report/{id}`; or delete the history endpoint (§6)
12. Bump `next` → 14.2.x patched, `fastapi` → ≥0.115 (starlette ≥0.40), **delete `python-multipart`** (§6)
13. Add GitHub Actions: `pytest` + `next build` + `npm audit` on every PR
14. Replace the rainfall table with a real gridded dataset; error on out-of-coverage coordinates (§4.7); this also grounds the GIS claim (§7)
15. Reword the AI/GIS/SCS-CN claims to match the implementation (§7)
16. Add `LICENSE`, `package-lock.json`, `.env.example` (§2)

---

## 9. Closing Assessment

This is **good student engineering with an unfinished finish**. The architecture is sound, the separation of concerns is real, the TypeScript/Pydantic contracts actually line up, the PDF output is genuinely professional, and someone clearly debugged Neon connections and the "Next button submits the form" bug the hard way. The foundation is better than most projects at this stage.

What's missing is verification: **no CI, 4 tests, and one commit.** Every defect in §4.1–§4.5 — the 500 on a fresh clone, the self-contradicting savings figures, the 99-year payback for the app's own default city — would have been caught by the modest test suite described in §5. The gap isn't ability; it's that nothing was ever set up to check.

The other theme is **claims outrunning implementation** (§7). The three capability statements on the landing page are the project's public face, and all three are contradicted by the source. For a repository published alongside a conference paper, that's the highest-leverage thing to fix — and the fixes are mostly wording plus one real GIS feature that you'd want anyway.

**My recommendation: do Phase 1 today** (it's about an hour and turns "broken on clone" into "works"), **Phase 2 before you demo to anyone**, and **Phase 3 before the paper submission.**

---

*Analysis method: full static read of all 33 files; backend executed under Python 3.11.2 with pinned dependencies (`pytest` 4/4 pass; API exercised via `TestClient` against a fresh SQLite DB; cost model run across 5 scenarios); frontend `next build` compiled clean under `strict` TypeScript; nested-component remount behaviour reproduced with React 18 + jsdom; dependency advisories from `npm audit` and NVD/GHSA. All findings marked "verified" were reproduced in this environment. No repository files were modified.*
