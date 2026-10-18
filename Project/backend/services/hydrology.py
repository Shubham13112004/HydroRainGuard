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

# SCS Curve Numbers per roof type (USDA-NRCS TR-55 / NEH-4 Ch.10).
# A roof is effectively an impervious urban surface: CN 95-98 for hard
# roofs, with green roofs behaving like good-condition open space.
ROOF_CN_VALUES = {
    'RCC': 98,
    'METAL': 97,
    'TILE': 95,
    'GREEN': 75,
    'ASPHALT': 96,
}

# Initial abstraction ratio, Ia = LAMBDA * S. 0.2 is the conventional
# TR-55 value; the literature notes 0.05 is often better for urban
# catchments, so it is named rather than hard-coded.
SCS_LAMBDA = 0.2

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

def scs_cn_runoff_mm(daily_or_monthly_mm: float, cn: float) -> float:
    """
    SCS Curve Number runoff depth, USDA-NRCS TR-55 (eq. 2-4).

        S  = 25400 / CN - 254        (mm of potential retention)
        Ia = lambda * S              (initial abstraction)
        Q  = (P - Ia)^2 / (P - Ia + S)   for P > Ia, else 0

    Note: 1 mm of runoff over 1 m2 is exactly 1 litre, so the depth in
    mm equals litres per square metre of catchment.
    """
    if cn <= 0 or cn > 100:
        return 0.0
    S = 25400.0 / cn - 254.0
    if S < 0:
        S = 0.0
    Ia = SCS_LAMBDA * S
    P = daily_or_monthly_mm
    if P <= Ia:
        return 0.0
    return (P - Ia) ** 2 / (P - Ia + S)


def calculate_runoff(request: AssessmentRequest, weather: WeatherData) -> RunoffResult:
    C = ROOF_RUNOFF_COEFFICIENTS[request.roof_type]
    CN = ROOF_CN_VALUES[request.roof_type]
    A = request.roof_area  # m²
    annual_R = weather.annual_rainfall / 1000  # convert mm to meters

    # --- Method 1: Rational / volumetric method (CGWB, 2007) --------
    annual_runoff_m3 = C * annual_R * A
    annual_runoff_liters = annual_runoff_m3 * 1000

    monthly_runoff = []
    for monthly_mm in weather.monthly_rainfall:
        monthly_m = monthly_mm / 1000
        monthly_vol_liters = C * monthly_m * A * 1000
        monthly_runoff.append(round(monthly_vol_liters, 2))

    # --- Method 2: SCS Curve Number (USDA-NRCS TR-55) ---------------
    # Reported alongside the Rational result as a cross-check. Applying
    # CN to monthly (rather than daily) totals is an approximation: it
    # under-counts runoff from intense storms and over-counts it from
    # long drizzle, which is why both numbers are shown.
    monthly_cn = [scs_cn_runoff_mm(mm, CN) * A for mm in weather.monthly_rainfall]
    cn_annual = sum(monthly_cn)

    # First flush loss: 2mm per rain event (assume ~100 rain events/year)
    first_flush_loss = FIRST_FLUSH_MM / 1000 * A * 1000 * 100  # liters

    # The request picks which of the two methods drives costing.
    method = (request.runoff_method or "rational").lower()
    if method == "scs_cn":
        primary_annual = cn_annual
        primary_monthly = monthly_cn
    else:
        method = "rational"
        primary_annual = annual_runoff_liters
        primary_monthly = monthly_runoff

    harvestable = max(0, primary_annual - first_flush_loss)

    if annual_runoff_liters > 0:
        cn_vs_rational = (cn_annual - annual_runoff_liters) / annual_runoff_liters * 100
    else:
        cn_vs_rational = 0.0
    
    # Peak runoff rate using rational formula Q = C*i*A
    # i = peak intensity = 3× average intensity in peak monsoon month
    peak_month_mm = max(weather.monthly_rainfall)
    peak_intensity_mm_hr = (peak_month_mm / (30 * 24)) * 3  # mm/hr
    peak_intensity_m_hr = peak_intensity_mm_hr / 1000
    peak_Q_m3_hr = C * peak_intensity_m_hr * A
    
    return RunoffResult(
        annual_runoff_volume=round(primary_annual, 2),
        monthly_runoff=[round(v, 2) for v in primary_monthly],
        runoff_coefficient=C,
        peak_runoff_rate=round(peak_Q_m3_hr, 4),
        harvestable_volume=round(harvestable, 2),
        runoff_method=method,
        curve_number=CN,
        scs_cn_annual_runoff=round(cn_annual, 2),
        scs_cn_monthly_runoff=[round(v, 2) for v in monthly_cn],
        scs_cn_vs_rational_pct=round(cn_vs_rational, 1),
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
