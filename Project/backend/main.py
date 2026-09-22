from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid, json, io
from datetime import datetime

from database import get_db, init_db, engine
from models.schemas import (
    AssessmentRequest, AssessmentResponse, WeatherData,
    HydroGeoInfo
)
from models.db_models import Assessment, Base
from services.weather import get_weather_data
from services.hydrology import calculate_runoff, calculate_recharge
from services.feasibility import get_recommendations
from services.cost_benefit import calculate_cost_benefit
from services.pdf_report import generate_pdf_report
from config import settings
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title='HYDRO RAIN GUARD API',
    description='Intelligent Rainwater Harvesting and Groundwater Recharge Assessment System',
    version='1.0.0'
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://hydro-rain-guard-mhus.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event('startup')
async def startup():
    await init_db()

@app.get('/')
async def root():
    return {'message': 'HYDRO RAIN GUARD API v1.0', 'status': 'running'}

@app.post('/api/assess', response_model=AssessmentResponse)
async def assess(request: AssessmentRequest, db: AsyncSession = Depends(get_db)):
    """Main assessment endpoint. Runs the complete hydrological analysis pipeline."""
    # Step 1: Fetch weather data
    weather = await get_weather_data(request.latitude, request.longitude)
    
    # Step 2: Hydrological calculations
    runoff = calculate_runoff(request, weather)
    recharge = calculate_recharge(request, weather)
    
    # Step 3: Feasibility & recommendations
    structures = get_recommendations(request, weather, runoff, recharge)
    
    # Step 4: Cost-benefit analysis
    cost_benefit = calculate_cost_benefit(request, runoff, recharge, structures)
    
    # Step 5: Hydrogeological info
    from services.hydrology import SOIL_INFILTRATION_RATES
    soil_perm_map = {
        'SANDY': 'High (20-30 mm/hr)',
        'GRAVELLY': 'Very High (25-50 mm/hr)',
        'LOAMY': 'Moderate (10-15 mm/hr)',
        'SILTY': 'Moderate-Low (5-10 mm/hr)',
        'CLAY': 'Low (1-5 mm/hr)',
    }
    storage_coeff_map = {'SANDY': 0.25, 'GRAVELLY': 0.30, 'LOAMY': 0.15, 'SILTY': 0.10, 'CLAY': 0.05}
    hydrogeo = HydroGeoInfo(
        aquifer_type=recharge.aquifer_type,
        aquifer_depth=request.groundwater_depth,
        permeability=soil_perm_map.get(request.soil_type, 'Moderate'),
        storage_coefficient=storage_coeff_map.get(request.soil_type, 0.15),
        transmissivity=SOIL_INFILTRATION_RATES.get(request.soil_type, 10) * 10,
        groundwater_quality='Potable - requires testing' if request.groundwater_depth > 10 else 'Shallow - may need treatment',
        seasonal_fluctuation=round(weather.annual_rainfall / 500 * 2, 1)
    )
    
    assessment_id = str(uuid.uuid4())[:8].upper()
    timestamp = datetime.now().isoformat()
    
    response = AssessmentResponse(
        assessment_id=assessment_id,
        timestamp=timestamp,
        request=request,
        weather=weather,
        runoff=runoff,
        recharge=recharge,
        recommended_structures=structures,
        cost_benefit=cost_benefit,
        hydrogeo_info=hydrogeo
    )
    
    # Persist to DB
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
        annual_recharge_potential=recharge.annual_recharge_potential,
        recommended_structure=structures[0].structure_type if structures else 'N/A',
        estimated_cost=cost_benefit.estimated_cost,
        payback_period=cost_benefit.payback_period_years,
        full_response_json=response.model_dump_json()
    )
    db.add(db_assessment)
    await db.commit()
    
    return response

@app.get('/api/report/{assessment_id}')
async def download_report(assessment_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and download a PDF report for a given assessment."""
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    db_item = result.scalar_one_or_none()
    if not db_item:
        raise HTTPException(status_code=404, detail='Assessment not found')
    
    response_data = json.loads(db_item.full_response_json)
    assessment = AssessmentResponse(**response_data)
    pdf_bytes = generate_pdf_report(assessment)
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=HYDRO_RAIN_GUARD_{assessment_id}.pdf'}
    )

@app.get('/api/assessments')
async def list_assessments(db: AsyncSession = Depends(get_db)):
    """List recent assessments (last 20)."""
    result = await db.execute(select(Assessment).order_by(Assessment.timestamp.desc()).limit(20))
    items = result.scalars().all()
    return [{
        'id': i.id,
        'name': i.name,
        'location': i.location,
        'timestamp': i.timestamp,
        'roof_area': i.roof_area,
        'annual_runoff_volume': i.annual_runoff_volume,
        'recommended_structure': i.recommended_structure,
        'estimated_cost': i.estimated_cost,
    } for i in items]

@app.get('/api/weather')
async def weather_preview(lat: float, lon: float):
    """Preview weather data for a location."""
    weather = await get_weather_data(lat, lon)
    return weather

@app.get('/api/health')
async def health():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
