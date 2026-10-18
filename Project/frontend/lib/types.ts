export type RoofType = 'RCC' | 'METAL' | 'TILE' | 'GREEN' | 'ASPHALT';
export type SoilType = 'SANDY' | 'LOAMY' | 'CLAY' | 'GRAVELLY' | 'SILTY';

export interface AssessmentRequest {
  name: string;
  location: string;
  latitude: number;
  longitude: number;
  num_people: number;
  roof_type: RoofType;
  roof_area: number;
  open_space_area: number;
  soil_type: SoilType;
  groundwater_depth: number;
  /** Rs per 1000 L. Optional; the backend defaults to 35. */
  water_tariff_per_kl?: number | null;
}

export interface RunoffResult {
  annual_runoff_volume: number;
  monthly_runoff: number[];
  runoff_coefficient: number;
  peak_runoff_rate: number;
  harvestable_volume: number;
}

export interface RechargeResult {
  annual_recharge_potential: number;
  groundwater_recharge_rate: number;
  infiltration_rate: number;
  aquifer_type: string;
  recharge_feasibility_score: number;
}

export interface StructureRecommendation {
  structure_type: string;
  suitability_score: number;
  description: string;
  dimensions: Record<string, string | number>;
  installation_notes: string;
}

export interface CostBenefitAnalysis {
  estimated_cost: number;
  /** Capital cost breakdown */
  storage_cost: number;
  recharge_cost: number;
  plumbing_cost: number;
  /** Tariff actually used, so the UI can state the assumption */
  water_tariff_per_kl: number;
  annual_water_savings_liters: number;
  annual_savings_inr: number;
  annual_recharge_value_inr: number;
  annual_maintenance_inr: number;
  net_annual_savings_inr: number;
  /** null == never pays back at the modelled tariff */
  payback_period_years: number | null;
  economically_viable: boolean;
  roi_percentage: number;
  monthly_savings: number[];
}

export interface WeatherData {
  location_name: string;
  annual_rainfall: number;
  monthly_rainfall: number[];
  avg_temperature: number;
  humidity: number;
  current_rainfall: number;
}

export interface HydroGeoInfo {
  aquifer_type: string;
  aquifer_depth: number;
  permeability: string;
  storage_coefficient: number;
  transmissivity: number;
  groundwater_quality: string;
  seasonal_fluctuation: number;
}

export interface AssessmentResponse {
  assessment_id: string;
  timestamp: string;
  request: AssessmentRequest;
  weather: WeatherData;
  runoff: RunoffResult;
  recharge: RechargeResult;
  recommended_structures: StructureRecommendation[];
  cost_benefit: CostBenefitAnalysis;
  hydrogeo_info: HydroGeoInfo;
}
