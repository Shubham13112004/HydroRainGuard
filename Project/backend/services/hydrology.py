"""
Hydrology service implementing:
- Rational Method for runoff estimation  
- SCS Curve Number method
- Rooftop harvesting volume calculation
- Groundwater recharge potential
"""
from models.schemas import AssessmentRequest, WeatherData, RunoffResult, RechargeResult

# Runoff coefficients per roof type (Rational Method)
ROOF_RUNOFF_COEFFICIENTS = {
    'RCC': 0.90,
    'METAL': 0.85,
    'TILE': 0.75,
    'GREEN': 0.30,
    'ASPHALT': 0.80,
}

# SCS-CN values per roof type
ROOF_CN_VALUES = {
    'RCC': 98,
    'METAL': 97,
    'TILE': 95,
    'GREEN': 75,
    'ASPHALT': 96,
}

# Soil infiltration rates (mm/hr)
SOIL_INFILTRATION_RATES = {
    'SANDY': 25.0,
    'GRAVELLY': 30.0,
    'LOAMY': 12.5,
    'SILTY': 6.5,
    'CLAY': 2.5,
}

# First flush losses (mm of rainfall to discard)
FIRST_FLUSH_MM = 2.0

def calculate_runoff(request: AssessmentRequest, weather: WeatherData) -> RunoffResult:
    C = ROOF_RUNOFF_COEFFICIENTS[request.roof_type]
    A = request.roof_area  # m²
    annual_R = weather.annual_rainfall / 1000  # convert mm to meters
    
    # Annual runoff volume (m³) = C × R × A
    annual_runoff_m3 = C * annual_R * A
    annual_runoff_liters = annual_runoff_m3 * 1000
    
    # Monthly runoff
    monthly_runoff = []
    for monthly_mm in weather.monthly_rainfall:
        monthly_m = monthly_mm / 1000
        monthly_vol_liters = C * monthly_m * A * 1000
        monthly_runoff.append(round(monthly_vol_liters, 2))
    
    # First flush loss: 2mm per rain event (assume ~100 rain events/year)
    first_flush_loss = FIRST_FLUSH_MM / 1000 * A * 1000 * 100  # liters
    harvestable = max(0, annual_runoff_liters - first_flush_loss)
    
    # Peak runoff rate using rational formula Q = C*i*A
    # i = peak intensity = 3× average intensity in peak monsoon month
    peak_month_mm = max(weather.monthly_rainfall)
    peak_intensity_mm_hr = (peak_month_mm / (30 * 24)) * 3  # mm/hr
    peak_intensity_m_hr = peak_intensity_mm_hr / 1000
    peak_Q_m3_hr = C * peak_intensity_m_hr * A
    
    return RunoffResult(
        annual_runoff_volume=round(annual_runoff_liters, 2),
        monthly_runoff=monthly_runoff,
        runoff_coefficient=C,
        peak_runoff_rate=round(peak_Q_m3_hr, 4),
        harvestable_volume=round(harvestable, 2)
    )

def calculate_recharge(request: AssessmentRequest, weather: WeatherData) -> RechargeResult:
    ks = SOIL_INFILTRATION_RATES[request.soil_type]  # mm/hr
    open_area = request.open_space_area  # m²
    depth = request.groundwater_depth  # m
    
    # Annual infiltration potential
    # Assume recharge possible during 120 rainy days at 8hrs/day
    rainy_days = 120
    hours_per_day = 8
    infiltration_vol_m3 = (ks / 1000) * open_area * rainy_days * hours_per_day
    infiltration_liters = infiltration_vol_m3 * 1000
    
    # Cap at annual rainfall × open area (can't infiltrate more than rainfall)
    max_possible = (weather.annual_rainfall / 1000) * open_area * 1000
    annual_recharge = min(infiltration_liters, max_possible * 0.7)  # 70% efficiency
    
    daily_recharge = annual_recharge / 365
    
    # Feasibility score (0-100)
    score = 0
    if depth > 20: score += 30
    elif depth > 10: score += 20
    elif depth > 5: score += 10
    
    if request.soil_type in ['SANDY', 'GRAVELLY']: score += 35
    elif request.soil_type == 'LOAMY': score += 20
    elif request.soil_type == 'SILTY': score += 10
    
    if open_area > 200: score += 20
    elif open_area > 50: score += 15
    elif open_area > 20: score += 10
    
    if weather.annual_rainfall > 1500: score += 15
    elif weather.annual_rainfall > 700: score += 10
    else: score += 5
    
    # Aquifer type based on depth and soil
    if depth < 10:
        aquifer_type = "Phreatic (Unconfined) Aquifer"
    elif depth < 30:
        aquifer_type = "Semi-Confined Aquifer"
    else:
        aquifer_type = "Confined Artesian Aquifer"
    
    return RechargeResult(
        annual_recharge_potential=round(annual_recharge, 2),
        groundwater_recharge_rate=round(daily_recharge, 2),
        infiltration_rate=ks,
        aquifer_type=aquifer_type,
        recharge_feasibility_score=min(100, score)
    )
