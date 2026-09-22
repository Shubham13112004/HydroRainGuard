"""
Cost-benefit analysis service.
All costs in Indian Rupees (INR).
Water rate: Rs. 15 per 1000 liters (municipal supply average India 2024)
"""
from models.schemas import AssessmentRequest, RunoffResult, RechargeResult, StructureRecommendation, CostBenefitAnalysis

# Base installation costs per structure type (INR)
STRUCTURE_COSTS = {
    'Rooftop Storage Tank': 25000,
    'Recharge Pit': 15000,
    'Recharge Well / Borewell Recharge': 45000,
    'Percolation Tank': 80000,
    'Soak Pit / French Drain': 8000,
}

WATER_RATE_PER_KL = 15  # Rs. per 1000 liters (1 KL)

def calculate_cost_benefit(
    request: AssessmentRequest,
    runoff: RunoffResult,
    recharge: RechargeResult,
    structures: list[StructureRecommendation]
) -> CostBenefitAnalysis:
    # Total installation cost for top 2 recommended structures
    top_structures = structures[:2]
    total_cost = sum(
        STRUCTURE_COSTS.get(s.structure_type, 20000)
        for s in top_structures
    )
    # Add plumbing/piping @ Rs 500/m of roof area perimeter
    perimeter_estimate = (request.roof_area ** 0.5) * 4
    plumbing_cost = perimeter_estimate * 500
    total_cost += plumbing_cost
    
    # Annual water savings
    harvestable_kl = runoff.harvestable_volume / 1000
    annual_savings_inr = harvestable_kl * WATER_RATE_PER_KL
    
    # Maintenance cost (2% of installation/year)
    annual_maintenance = total_cost * 0.02
    net_annual_savings = annual_savings_inr - annual_maintenance
    
    # Payback period
    if net_annual_savings > 0:
        payback = total_cost / net_annual_savings
    else:
        payback = 99.0
    
    # ROI over 10 years
    total_savings_10yr = net_annual_savings * 10
    roi = ((total_savings_10yr - total_cost) / total_cost) * 100 if total_cost > 0 else 0
    
    # Monthly savings
    monthly_savings = []
    for monthly_run_L in runoff.monthly_runoff:
        monthly_kl = monthly_run_L / 1000
        monthly_save = monthly_kl * WATER_RATE_PER_KL
        monthly_savings.append(round(monthly_save, 2))
    
    return CostBenefitAnalysis(
        estimated_cost=round(total_cost, 2),
        annual_water_savings_liters=runoff.harvestable_volume,
        annual_savings_inr=round(annual_savings_inr, 2),
        payback_period_years=round(payback, 1),
        roi_percentage=round(roi, 1),
        monthly_savings=monthly_savings
    )
