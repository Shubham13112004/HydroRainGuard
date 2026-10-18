"""
Cost-benefit analysis service.
All costs in Indian Rupees (INR).

Tariff note
-----------
`WATER_RATE_PER_KL` is a *blended avoided cost of water* for
urban India, not a municipal tariff:

* piped municipal supply is roughly Rs. 15/KL
* private tanker water is roughly Rs. 100-400/KL

A household that harvests rainwater avoids the marginal
(more expensive) litre first, so billing the whole harvest at
the municipal rate systematically understates the benefit and
produces absurd payback periods. Callers may override the rate
per request via `water_tariff_per_kl`.

Recharge is monetised at `RECHARGE_VALUE_FACTOR` x the tariff:
recharged groundwater is a real but indirect benefit (it is not
metered at the tap), so it is credited conservatively.
"""

from models.schemas import (
    AssessmentRequest,
    RunoffResult,
    RechargeResult,
    StructureRecommendation,
    CostBenefitAnalysis,
)

# Base installation costs per structure type (INR)
STRUCTURE_COSTS = {
    'Rooftop Storage Tank': 25000,
    'Recharge Pit': 15000,
    'Recharge Well / Borewell Recharge': 45000,
    'Percolation Tank': 80000,
    'Soak Pit / French Drain': 8000,
}

# Structures that collect water for direct use, as opposed to
# structures that only put water back into the aquifer.
STORAGE_STRUCTURES = {'Rooftop Storage Tank'}

# Blended avoided cost of water (see module docstring).
DEFAULT_WATER_RATE_PER_KL = 35.0

# Fraction of the water tariff used to value a kilolitre of
# groundwater recharge.
RECHARGE_VALUE_FACTOR = 0.5

# Plumbing / conveyance, Rs per metre of roof perimeter.
PLUMBING_RATE_PER_M = 500

# Annual operation & maintenance as a share of capital cost.
MAINTENANCE_RATE = 0.02

# Horizon used for the ROI figure, in years.
ROI_HORIZON_YEARS = 10


def _monthly_harvestable(runoff: RunoffResult) -> list[float]:
    """
    Split the annual first-flush loss across the twelve months
    in proportion to monthly runoff.

    `runoff.harvestable_volume` is the annual runoff *after*
    the first-flush deduction, while `runoff.monthly_runoff` is
    gross. Budgeting the loss monthly keeps the monthly savings
    series consistent with the annual figure -- previously the
    monthly series summed ~46% higher than the annual one.
    """
    gross_total = sum(runoff.monthly_runoff)

    if gross_total <= 0:
        return [0.0] * len(runoff.monthly_runoff)

    total_loss = max(
        0.0,
        runoff.annual_runoff_volume - runoff.harvestable_volume,
    )

    out = []
    for monthly in runoff.monthly_runoff:
        share = monthly / gross_total
        out.append(max(0.0, monthly - total_loss * share))

    return out


def calculate_cost_benefit(
    request: AssessmentRequest,
    runoff: RunoffResult,
    recharge: RechargeResult,
    structures: list[StructureRecommendation],
) -> CostBenefitAnalysis:

    rate = getattr(
        request,
        'water_tariff_per_kl',
        None,
    ) or DEFAULT_WATER_RATE_PER_KL

    # ------------------------------------------------------
    # CAPITAL COST
    # ------------------------------------------------------

    # Top 2 recommended structures.
    top_structures = structures[:2]

    storage_cost = sum(
        STRUCTURE_COSTS.get(s.structure_type, 20000)
        for s in top_structures
        if s.structure_type in STORAGE_STRUCTURES
    )

    recharge_cost = sum(
        STRUCTURE_COSTS.get(s.structure_type, 20000)
        for s in top_structures
        if s.structure_type not in STORAGE_STRUCTURES
    )

    # Plumbing / piping @ Rs 500 per metre of roof perimeter.
    perimeter_estimate = (request.roof_area ** 0.5) * 4
    plumbing_cost = perimeter_estimate * PLUMBING_RATE_PER_M

    total_cost = storage_cost + recharge_cost + plumbing_cost

    # ------------------------------------------------------
    # ANNUAL BENEFIT
    # ------------------------------------------------------

    monthly_harvestable = _monthly_harvestable(runoff)

    monthly_savings = [
        round((litres / 1000) * rate, 2)
        for litres in monthly_harvestable
    ]

    # Annual savings are the sum of the monthly series, so the
    # charts and the summary can never disagree.
    annual_savings_inr = round(sum(monthly_savings), 2)

    harvestable_kl = (
        sum(monthly_harvestable) / 1000
    )

    # Groundwater recharge, valued conservatively.
    annual_recharge_value_inr = round(
        (recharge.annual_recharge_potential / 1000)
        * rate
        * RECHARGE_VALUE_FACTOR,
        2,
    )

    annual_maintenance = total_cost * MAINTENANCE_RATE

    net_annual_savings = (
        annual_savings_inr
        + annual_recharge_value_inr
        - annual_maintenance
    )

    # ------------------------------------------------------
    # PAYBACK / ROI
    # ------------------------------------------------------

    # `None` means "never pays back". The old code returned the
    # sentinel 99.0, which the UI rendered as a real number.
    if net_annual_savings > 0:
        payback = round(total_cost / net_annual_savings, 1)
    else:
        payback = None

    total_savings_horizon = net_annual_savings * ROI_HORIZON_YEARS

    roi = (
        ((total_savings_horizon - total_cost) / total_cost) * 100
        if total_cost > 0
        else 0.0
    )

    return CostBenefitAnalysis(
        estimated_cost=round(total_cost, 2),
        storage_cost=round(storage_cost, 2),
        recharge_cost=round(recharge_cost, 2),
        plumbing_cost=round(plumbing_cost, 2),
        water_tariff_per_kl=round(rate, 2),
        annual_water_savings_liters=round(
            harvestable_kl * 1000, 2
        ),
        annual_savings_inr=annual_savings_inr,
        annual_recharge_value_inr=annual_recharge_value_inr,
        annual_maintenance_inr=round(annual_maintenance, 2),
        net_annual_savings_inr=round(net_annual_savings, 2),
        payback_period_years=payback,
        economically_viable=(
            payback is not None
            and payback <= ROI_HORIZON_YEARS
        ),
        roi_percentage=round(roi, 1),
        monthly_savings=monthly_savings,
    )
