from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import uuid
import json
import io
import logging
from datetime import datetime

from database import get_db, init_db
from config import settings
from models.schemas import (
    AssessmentRequest,
    AssessmentResponse,
    HydroGeoInfo,
)
from models.db_models import Assessment

from services.weather import get_weather_data
from services.hydrology import calculate_runoff, calculate_recharge
from services.feasibility import get_recommendations, get_mcda_info
from services.cost_benefit import calculate_cost_benefit
from services.pdf_report import generate_pdf_report


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger("hydro_rain_guard")


# ============================================================
# DATABASE STARTUP
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Create database tables on startup.

    Without this, POST /api/assess fails with
    `no such table: assessments` on a fresh clone.
    """
    try:
        await init_db()
        logger.info("Database initialised")
    except Exception as exc:  # pragma: no cover
        # Do not crash the process: the health endpoint still
        # has to answer so the platform can report the failure.
        logger.error("Database init failed: %s", exc)

    yield


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="HYDRO RAIN GUARD API",
    description=(
        "Intelligent Rainwater Harvesting and "
        "Groundwater Recharge Assessment System"
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MAINTENANCE AUTH
# ============================================================

def _authorised(admin_token: str | None) -> bool:
    """
    Maintenance endpoints are open in development so the
    documented local workflow keeps working, and require
    `X-Admin-Token` (or `?token=`) in production.
    """
    if not settings.is_production:
        return True

    expected = settings.admin_token
    if not expected:
        return False

    return admin_token == expected


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():
    return {
        "message": "HYDRO RAIN GUARD API v1.0",
        "status": "running",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================
# WEATHER PREVIEW
# ============================================================

@app.get("/api/weather")
async def weather_preview(
    lat: float,
    lon: float,
    annual_rainfall_override: float | None = None,
    location_name: str | None = None,
):
    """
    Rainfall climatology for the supplied coordinates.

    `annual_rainfall_override` (mm/yr) replaces the grid's annual total
    while keeping its monthly distribution -- use a local station value
    (e.g. IMD) where you have one, because the grid cell is ~278 km
    across and cannot resolve orographic gradients such as the Western
    Ghats.
    """

    try:
        weather = await get_weather_data(
            lat, lon,
            annual_rainfall_override=annual_rainfall_override,
            location_name=location_name,
        )
        return weather

    except Exception as e:
        print(f"Weather API error: {type(e).__name__}: {e}")

        raise HTTPException(
            status_code=500,
            detail=f"Weather service failed: {str(e)}",
        )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

@app.post("/api/init-db")
async def initialize_database(
    x_admin_token: str | None = Header(default=None),
):
    """
    Initialize database tables manually.

    Tables are also created automatically on application
    startup (see `lifespan`). This endpoint remains as a
    manual escape hatch for serverless platforms where the
    filesystem is ephemeral.

    In production it requires the `X-Admin-Token` header to
    match `settings.admin_token`.
    """

    if not _authorised(x_admin_token):
        raise HTTPException(
            status_code=403,
            detail="Not authorised",
        )

    try:
        await init_db(force=True)

        return {
            "status": "success",
            "message": "Database initialized successfully",
        }

    except Exception as e:
        print(f"Database initialization error: {type(e).__name__}: {e}")

        raise HTTPException(
            status_code=500,
            detail=f"Database initialization failed: {str(e)}",
        )


# ============================================================
# MAIN ASSESSMENT
# ============================================================

@app.post("/api/assess", response_model=AssessmentResponse)
async def assess(
    request: AssessmentRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Main assessment endpoint.

    Pipeline:
    1. Weather
    2. Hydrology
    3. Recharge
    4. Feasibility
    5. Cost-benefit
    6. Hydrogeological information
    7. Database persistence
    """

    try:

        # ----------------------------------------------------
        # STEP 1: WEATHER
        # ----------------------------------------------------

        weather = await get_weather_data(
            request.latitude,
            request.longitude,
            annual_rainfall_override=request.annual_rainfall_override,
            location_name=request.location_name,
        )

        # ----------------------------------------------------
        # STEP 2: HYDROLOGICAL CALCULATIONS
        # ----------------------------------------------------

        runoff = calculate_runoff(
            request,
            weather,
        )

        recharge = calculate_recharge(
            request,
            weather,
        )

        # ----------------------------------------------------
        # STEP 3: RECOMMENDATIONS
        # ----------------------------------------------------

        structures = get_recommendations(
            request,
            weather,
            runoff,
            recharge,
        )

        # ----------------------------------------------------
        # STEP 4: COST-BENEFIT
        # ----------------------------------------------------

        cost_benefit = calculate_cost_benefit(
            request,
            runoff,
            recharge,
            structures,
        )

        # ----------------------------------------------------
        # STEP 5: HYDROGEOLOGICAL INFORMATION
        # ----------------------------------------------------

        from services.hydrology import SOIL_INFILTRATION_RATES

        soil_perm_map = {
            "SANDY": "High (20-30 mm/hr)",
            "GRAVELLY": "Very High (25-50 mm/hr)",
            "LOAMY": "Moderate (10-15 mm/hr)",
            "SILTY": "Moderate-Low (5-10 mm/hr)",
            "CLAY": "Low (1-5 mm/hr)",
        }

        storage_coeff_map = {
            "SANDY": 0.25,
            "GRAVELLY": 0.30,
            "LOAMY": 0.15,
            "SILTY": 0.10,
            "CLAY": 0.05,
        }

        hydrogeo = HydroGeoInfo(
            aquifer_type=recharge.aquifer_type,
            aquifer_depth=request.groundwater_depth,

            permeability=soil_perm_map.get(
                request.soil_type,
                "Moderate",
            ),

            storage_coefficient=storage_coeff_map.get(
                request.soil_type,
                0.15,
            ),

            transmissivity=(
                SOIL_INFILTRATION_RATES.get(
                    request.soil_type,
                    10,
                ) * 10
            ),

            groundwater_quality=(
                "Potable - requires testing"
                if request.groundwater_depth > 10
                else "Shallow - may need treatment"
            ),

            seasonal_fluctuation=round(
                weather.annual_rainfall / 500 * 2,
                1,
            ),
        )

        # ----------------------------------------------------
        # STEP 6: ASSESSMENT ID
        # ----------------------------------------------------

        assessment_id = str(uuid.uuid4())[:8].upper()

        timestamp = datetime.now().isoformat()

        # ----------------------------------------------------
        # STEP 7: RESPONSE
        # ----------------------------------------------------

        response = AssessmentResponse(
            assessment_id=assessment_id,
            timestamp=timestamp,
            request=request,
            weather=weather,
            runoff=runoff,
            recharge=recharge,
            recommended_structures=structures,
            cost_benefit=cost_benefit,
            hydrogeo_info=hydrogeo,
            mcda=get_mcda_info(),
        )

        # ----------------------------------------------------
        # STEP 8: DATABASE
        # ----------------------------------------------------

        db_assessment = Assessment(
            id=assessment_id,
            timestamp=timestamp,

            name=request.name,
            location=request.location,

            latitude=request.latitude,
            longitude=request.longitude,

            roof_type=request.roof_type,
            roof_area=request.roof_area,

            soil_type=request.soil_type,
            groundwater_depth=request.groundwater_depth,

            num_people=request.num_people,
            open_space_area=request.open_space_area,

            annual_runoff_volume=runoff.annual_runoff_volume,

            annual_recharge_potential=(
                recharge.annual_recharge_potential
            ),

            recommended_structure=(
                structures[0].structure_type
                if structures
                else "N/A"
            ),

            estimated_cost=cost_benefit.estimated_cost,

            payback_period=(
                cost_benefit.payback_period_years
            ),

            full_response_json=response.model_dump_json(),
        )

        db.add(db_assessment)

        await db.commit()

        return response

    except HTTPException:
        raise

    except Exception as e:

        print(
            f"Assessment error: "
            f"{type(e).__name__}: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Assessment failed: {str(e)}",
        )


# ============================================================
# FETCH ONE ASSESSMENT
# ============================================================

@app.get("/api/assessment/{assessment_id}")
async def get_assessment(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Return a previously stored assessment.

    Lets /results?id=<assessment_id> rehydrate on another
    device or after a reload, instead of depending on
    localStorage alone.
    """

    try:

        result = await db.execute(
            select(Assessment).where(
                Assessment.id == assessment_id
            )
        )

        db_item = result.scalar_one_or_none()

        if not db_item:
            raise HTTPException(
                status_code=404,
                detail="Assessment not found",
            )

        return json.loads(db_item.full_response_json)

    except HTTPException:
        raise

    except Exception as e:

        logger.exception("Fetch assessment failed")

        raise HTTPException(
            status_code=500,
            detail="Could not load assessment",
        )


# ============================================================
# PDF REPORT
# ============================================================

@app.get("/api/report/{assessment_id}")
async def download_report(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate and download a PDF report.
    """

    try:

        result = await db.execute(
            select(Assessment).where(
                Assessment.id == assessment_id
            )
        )

        db_item = result.scalar_one_or_none()

        if not db_item:
            raise HTTPException(
                status_code=404,
                detail="Assessment not found",
            )

        response_data = json.loads(
            db_item.full_response_json
        )

        assessment = AssessmentResponse(
            **response_data
        )

        pdf_bytes = generate_pdf_report(
            assessment
        )

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    "attachment; "
                    f"filename=HYDRO_RAIN_GUARD_"
                    f"{assessment_id}.pdf"
                )
            },
        )

    except HTTPException:
        raise

    except Exception as e:

        print(
            f"PDF report error: "
            f"{type(e).__name__}: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}",
        )


# ============================================================
# ASSESSMENT HISTORY
# ============================================================

@app.get("/api/assessments")
async def list_assessments(
    db: AsyncSession = Depends(get_db),
    x_admin_token: str | None = Header(default=None),
):
    """
    Return the latest 20 assessments.

    These records contain personal data (name, location and
    precise coordinates), so in production this endpoint
    requires `X-Admin-Token`. Without it, records are
    returned with the identifying fields redacted.
    """

    authorised = _authorised(x_admin_token)

    try:

        result = await db.execute(
            select(Assessment)
            .order_by(
                Assessment.timestamp.desc()
            )
            .limit(20)
        )

        items = result.scalars().all()

        out = []
        for i in items:
            record = {
                "id": i.id,
                "name": i.name,
                "location": i.location,
                "timestamp": i.timestamp,
                "roof_area": i.roof_area,
                "annual_runoff_volume": (
                    i.annual_runoff_volume
                ),
                "recommended_structure": (
                    i.recommended_structure
                ),
                "estimated_cost": (
                    i.estimated_cost
                ),
            }

            if not authorised:
                # Hide personally identifying information
                record["name"] = "—"
                record["location"] = "—"

            out.append(record)

        return out

    except Exception as e:

        print(
            f"Assessment history error: "
            f"{type(e).__name__}: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Could not load assessments: {str(e)}",
        )
