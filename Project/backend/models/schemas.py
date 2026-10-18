from enum import Enum
from pydantic import BaseModel

class RoofType(str, Enum):
    RCC = 'RCC'
    METAL = 'METAL'
    TILE = 'TILE'
    GREEN = 'GREEN'
    ASPHALT = 'ASPHALT'

class SoilType(str, Enum):
    SANDY = 'SANDY'
    LOAMY = 'LOAMY'
    CLAY = 'CLAY'
    GRAVELLY = 'GRAVELLY'
    SILTY = 'SILTY'

class AssessmentRequest(BaseModel):
    # Basic Info
    name: str
    location: str
    latitude: float
    longitude: float
    num_people: int
    # Roof Details  
    roof_type: RoofType
    roof_area: float  # m²
    # Site Condition
    open_space_area: float  # m²
    soil_type: SoilType
    groundwater_depth: float  # meters
    # Economics override (Rs per 1000 L). Optional.
    water_tariff_per_kl: float | None = None

class RunoffResult(BaseModel):
    annual_runoff_volume: float  # liters
    monthly_runoff: list[float]  # 12 months
    runoff_coefficient: float
    peak_runoff_rate: float  # m³/hr
    harvestable_volume: float  # liters after first flush loss

class RechargeResult(BaseModel):
    annual_recharge_potential: float  # liters
    groundwater_recharge_rate: float  # liters/day
    infiltration_rate: float  # mm/hr
    aquifer_type: str
    recharge_feasibility_score: float  # 0-100

class StructureRecommendation(BaseModel):
    structure_type: str
    suitability_score: float
    description: str
    dimensions: dict
    installation_notes: str

class CostBenefitAnalysis(BaseModel):
    estimated_cost: float  # INR
    # Capital cost breakdown
    storage_cost: float = 0.0
    recharge_cost: float = 0.0
    plumbing_cost: float = 0.0
    # Tariff actually used, so reports can state the assumption
    water_tariff_per_kl: float = 0.0
    # Benefits
    annual_water_savings_liters: float
    annual_savings_inr: float
    annual_recharge_value_inr: float = 0.0
    annual_maintenance_inr: float = 0.0
    net_annual_savings_inr: float = 0.0
    # None == never pays back at the modelled tariff
    payback_period_years: float | None = None
    # True when the system pays back inside the ROI horizon
    economically_viable: bool = False
    roi_percentage: float
    monthly_savings: list[float]

class WeatherData(BaseModel):
    location_name: str
    annual_rainfall: float  # mm
    monthly_rainfall: list[float]  # 12 months mm
    avg_temperature: float
    humidity: float
    current_rainfall: float

class HydroGeoInfo(BaseModel):
    aquifer_type: str
    aquifer_depth: float
    permeability: str
    storage_coefficient: float
    transmissivity: float
    groundwater_quality: str
    seasonal_fluctuation: float

class AssessmentResponse(BaseModel):
    assessment_id: str
    timestamp: str
    request: AssessmentRequest
    weather: WeatherData
    runoff: RunoffResult
    recharge: RechargeResult
    recommended_structures: list[StructureRecommendation]
    cost_benefit: CostBenefitAnalysis
    hydrogeo_info: HydroGeoInfo
