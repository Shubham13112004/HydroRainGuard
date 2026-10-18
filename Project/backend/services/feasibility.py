"""
Feasibility service — recommends recharge / storage structures for a
site using Analytic Hierarchy Process (AHP) multi-criteria decision
analysis.

Each candidate structure is scored on five criteria (see
services/mcda.py for the weight derivation and consistency test).
Every criterion is converted to a 0-1 suitability utility first, so
millimetres of rain are never added to square metres of open space.

Hard physical constraints (a percolation tank cannot be built in
2 m2) are applied as filters before scoring, not as score penalties.
"""
from models.schemas import (
    AssessmentRequest, WeatherData, RunoffResult, RechargeResult,
    StructureRecommendation, CriterionScore, MCDAInfo,
)
from services.mcda import (
    CRITERIA, build_pairwise_matrix, ahp_weights, clamp01, ramp, trapezoid,
)

# ------------------------------------------------------------------
# Structure catalogue
# ------------------------------------------------------------------
#
# For each structure:
#   min_harvestable_l  -- annual litres below which the structure is
#                         oversized for this catchment (CGWB sizing
#                         practice). 0 == no volume requirement.
#   min_open_space     -- m2 of clear ground physically needed.
#   rain_band          -- (low, high) mm/yr ramp for the rainfall
#                         criterion.
#   infiltration_band  -- (low, high) mm/hr ramp, or None when the
#                         structure is indifferent to soil infiltration.
#   depth_band         -- (a, b, c, d) trapezoid on groundwater depth
#                         in m, or None when indifferent.

STRUCTURES = [
    {
        'name': 'Rooftop Storage Tank',
        'always_include': True,
        'min_harvestable_l': 0,
        'min_open_space': 0,
        'rain_band': (150, 900),
        'infiltration_band': None,
        'depth_band': None,
        'description': 'A dedicated storage tank collects and stores harvested rooftop runoff for direct use in toilets, gardening, and non-potable purposes. Most cost-effective first step for any building.',
        'installation_notes': 'Install at ground level or underground. Connect to rooftop downpipes via first-flush diverter. Include overflow pipe to recharge pit.',
    },
    {
        'name': 'Recharge Pit',
        'min_harvestable_l': 20000,
        'min_open_space': 9,  # m²
        'rain_band': (400, 1400),
        'infiltration_band': (5, 40),
        'depth_band': (1, 4, 15, 30),
        'description': 'A recharge pit (1.5m × 1.5m × 2m) filled with gravel and sand filters allows harvested water to percolate directly into the groundwater table. Highly effective for shallow aquifers.',
        'installation_notes': 'Excavate 2m deep, fill with 0.5m gravel at bottom, 1m stone/brick, 0.5m sand. Install inlet pipe from tank overflow. Provide removable top cover for cleaning.',
    },
    {
        'name': 'Recharge Well / Borewell Recharge',
        'min_harvestable_l': 60000,
        'min_open_space': 4,
        'rain_band': (400, 1400),
        # Its whole purpose is to bypass low-permeability surface soil,
        # so it is deliberately indifferent to infiltration.
        'infiltration_band': None,
        'depth_band': (5, 15, 45, 90),
        'description': 'A dedicated recharge well (200–300mm diameter, 10–30m deep) channels treated rooftop runoff directly into deeper aquifers. Ideal where surface soil has low permeability but deep aquifers are present.',
        'installation_notes': 'Drill 200–300mm bore to aquifer depth. Install casing with perforations. Connect via first-flush diverter → settling tank → filter media → well. Annual cleaning required.',
    },
    {
        'name': 'Percolation Tank',
        'min_harvestable_l': 200000,
        'min_open_space': 100,
        'rain_band': (500, 1500),
        'infiltration_band': (10, 40),
        'depth_band': (1, 3, 25, 45),
        'description': 'A large open-surface impoundment (percolation tank) captures runoff from rooftops and open spaces, allowing slow percolation over a large area. Best for large plots and community use.',
        'installation_notes': 'Suitable for land area >100m². Depth 1.5–3m. Provide inlet, spillway, and de-silting arrangement. Plant grass on bunds to prevent erosion.',
    },
    {
        'name': 'Soak Pit / French Drain',
        'min_harvestable_l': 10000,
        'min_open_space': 6,
        'rain_band': (300, 1200),
        'infiltration_band': (5, 40),
        'depth_band': (1, 3, 20, 40),
        'description': 'A soak pit (1m diameter, 1.5–2m deep) filled with gravel provides a simple low-cost solution for small rooftop areas, distributing water slowly into surrounding soil.',
        'installation_notes': 'Dig 1m diameter × 1.5m depth. Line sides with dry-brick or perforated concrete rings. Fill with 40mm stone aggregate. Cover with perforated slab.',
    },
]

# Below this fraction of a structure's space requirement the structure
# is physically impossible, not merely unsuitable -- filter it out
# rather than scoring it low.
SPACE_HARD_LIMIT = 0.6

_AHP = ahp_weights(build_pairwise_matrix())
WEIGHTS = _AHP["weights"]


def get_mcda_info() -> MCDAInfo:
    """Expose the AHP audit trail so the UI and PDF can show it."""
    return MCDAInfo(
        method="Analytic Hierarchy Process (Saaty, 1980) — geometric "
               "mean weights, consistency-checked",
        criteria=list(CRITERIA),
        weights={k: round(v, 4) for k, v in WEIGHTS.items()},
        pairwise_matrix=[[round(v, 4) for v in row]
                         for row in build_pairwise_matrix()],
        lambda_max=_AHP["lambda_max"],
        consistency_index=_AHP["consistency_index"],
        consistency_ratio=_AHP["consistency_ratio"],
        consistent=_AHP["consistent"],
    )


def get_recommendations(
    request: AssessmentRequest,
    weather: WeatherData,
    runoff: RunoffResult,
    recharge: RechargeResult,
) -> list[StructureRecommendation]:
    results = []

    for s in STRUCTURES:
        # --- hard physical constraint: footprint -------------------
        min_space = s.get('min_open_space', 0)
        if min_space and request.open_space_area < SPACE_HARD_LIMIT * min_space:
            if not s.get('always_include'):
                continue

        raw, norm = _criterion_values(s, request, weather, runoff, recharge)

        # Weighted sum of the 0-1 utilities -> 0..1
        score = sum(WEIGHTS[c] * norm[c] for c in CRITERIA)

        results.append(StructureRecommendation(
            structure_type=s['name'],
            suitability_score=round(clamp01(score) * 100.0, 1),
            description=s['description'],
            dimensions=_calculate_dimensions(s['name'], request, runoff),
            installation_notes=s['installation_notes'],
            criteria=[
                CriterionScore(
                    name=c,
                    raw=round(raw[c], 3),
                    normalised=round(norm[c], 3),
                    weight=round(WEIGHTS[c], 4),
                )
                for c in CRITERIA
            ],
        ))

    results.sort(key=lambda x: x.suitability_score, reverse=True)
    return results


def _criterion_values(s, request, weather, runoff, recharge):
    """
    Return (raw, normalised) dicts for the five AHP criteria.
    `raw` is in the criterion's own physical unit, so the report can
    explain the number; `normalised` is the 0-1 utility used for
    scoring.
    """
    yield_l = runoff.harvestable_volume
    rain = weather.annual_rainfall
    infil = recharge.infiltration_rate
    space = request.open_space_area
    depth = request.groundwater_depth

    raw = {
        "harvestable_yield": yield_l,
        "annual_rainfall": rain,
        "soil_infiltration": infil,
        "open_space": space,
        "groundwater_depth": depth,
    }

    # 1. Yield vs. the volume this structure is sized for.
    min_yield = s.get('min_harvestable_l', 0)
    if min_yield:
        # 0 at 40% of requirement, 1 at 150% of requirement.
        u_yield = clamp01((yield_l - 0.4 * min_yield) / (1.1 * min_yield))
    else:
        u_yield = 1.0

    # 2. Rainfall.
    lo, hi = s['rain_band']
    u_rain = ramp(rain, lo, hi)

    # 3. Soil infiltration (recharge structures only).
    band = s.get('infiltration_band')
    u_infil = ramp(infil, *band) if band else 1.0

    # 4. Open space vs. footprint requirement.
    min_space = s.get('min_open_space', 0)
    u_space = ramp(space, 0.5 * min_space, 1.5 * min_space) if min_space else 1.0

    # 5. Groundwater depth window.
    db = s.get('depth_band')
    u_depth = trapezoid(depth, *db) if db else 1.0

    norm = {
        "harvestable_yield": u_yield,
        "annual_rainfall": u_rain,
        "soil_infiltration": u_infil,
        "open_space": u_space,
        "groundwater_depth": u_depth,
    }
    return raw, norm


def _calculate_dimensions(structure: str, request: AssessmentRequest, runoff: RunoffResult) -> dict:
    monthly_peak = max(runoff.monthly_runoff) / 1000  # m³
    if structure == 'Rooftop Storage Tank':
        # Size for peak month storage + 30 days demand
        demand_30d = request.num_people * 0.135 * 30  # m³
        vol = max(monthly_peak * 0.5, demand_30d)
        return {'volume_m3': round(vol, 1), 'diameter_m': round((4*vol/(3.14*2))**0.5, 2), 'depth_m': 2.0, 'material': 'RCC/PVC'}
    elif structure == 'Recharge Pit':
        return {'length_m': 1.5, 'width_m': 1.5, 'depth_m': 2.0, 'filter_layers': '0.5m gravel + 1.0m stone + 0.5m sand'}
    elif structure == 'Recharge Well / Borewell Recharge':
        return {'diameter_mm': 250, 'depth_m': max(request.groundwater_depth + 5, 20), 'casing_type': 'MS perforated pipe'}
    elif structure == 'Percolation Tank':
        area = min(request.open_space_area * 0.3, 200)
        return {'surface_area_m2': round(area, 1), 'depth_m': 2.5, 'storage_volume_m3': round(area * 2.5 * 0.6, 1)}
    elif structure == 'Soak Pit / French Drain':
        return {'diameter_m': 1.0, 'depth_m': 1.5, 'fill_material': '40mm stone aggregate'}
    return {}
