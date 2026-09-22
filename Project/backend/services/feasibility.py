"""
Feasibility service — recommends appropriate recharge structures
based on site conditions using a multi-criteria scoring approach.
"""
from models.schemas import AssessmentRequest, WeatherData, RunoffResult, RechargeResult, StructureRecommendation

STRUCTURES = [
    {
        'name': 'Rooftop Storage Tank',
        'always_include': True,
        'base_score': 85,
        'description': 'A dedicated storage tank collects and stores harvested rooftop runoff for direct use in toilets, gardening, and non-potable purposes. Most cost-effective first step for any building.',
        'installation_notes': 'Install at ground level or underground. Connect to rooftop downpipes via first-flush diverter. Include overflow pipe to recharge pit.',
    },
    {
        'name': 'Recharge Pit',
        'min_open_space': 9,  # m²
        'preferred_soil': ['SANDY', 'GRAVELLY', 'LOAMY'],
        'min_depth': 5,
        'base_score': 70,
        'description': 'A recharge pit (1.5m × 1.5m × 2m) filled with gravel and sand filters allows harvested water to percolate directly into the groundwater table. Highly effective for shallow aquifers.',
        'installation_notes': 'Excavate 2m deep, fill with 0.5m gravel at bottom, 1m stone/brick, 0.5m sand. Install inlet pipe from tank overflow. Provide removable top cover for cleaning.',
    },
    {
        'name': 'Recharge Well / Borewell Recharge',
        'min_open_space': 4,
        'preferred_soil': ['ALL'],
        'min_depth': 15,
        'base_score': 80,
        'description': 'A dedicated recharge well (200–300mm diameter, 10–30m deep) channels treated rooftop runoff directly into deeper aquifers. Ideal where surface soil has low permeability but deep aquifers are present.',
        'installation_notes': 'Drill 200–300mm bore to aquifer depth. Install casing with perforations. Connect via first-flush diverter → settling tank → filter media → well. Annual cleaning required.',
    },
    {
        'name': 'Percolation Tank',
        'min_open_space': 100,
        'preferred_soil': ['SANDY', 'GRAVELLY', 'LOAMY'],
        'min_depth': 3,
        'max_depth': 25,
        'base_score': 65,
        'description': 'A large open-surface impoundment (percolation tank) captures runoff from rooftops and open spaces, allowing slow percolation over a large area. Best for large plots and community use.',
        'installation_notes': 'Suitable for land area >100m². Depth 1.5–3m. Provide inlet, spillway, and de-silting arrangement. Plant grass on bunds to prevent erosion.',
    },
    {
        'name': 'Soak Pit / French Drain',
        'min_open_space': 6,
        'preferred_soil': ['LOAMY', 'SILTY', 'SANDY'],
        'min_depth': 3,
        'max_depth': 20,
        'base_score': 60,
        'description': 'A soak pit (1m diameter, 1.5–2m deep) filled with gravel provides a simple low-cost solution for small rooftop areas, distributing water slowly into surrounding soil.',
        'installation_notes': 'Dig 1m diameter × 1.5m depth. Line sides with dry-brick or perforated concrete rings. Fill with 40mm stone aggregate. Cover with perforated slab.',
    },
]

def get_recommendations(request: AssessmentRequest, weather: WeatherData, runoff: RunoffResult, recharge: RechargeResult) -> list[StructureRecommendation]:
    results = []
    for s in STRUCTURES:
        score = s['base_score']
        # Check minimum open space
        if 'min_open_space' in s and request.open_space_area < s['min_open_space']:
            if not s.get('always_include'):
                continue
        # Check soil suitability
        if 'preferred_soil' in s and s['preferred_soil'] != ['ALL']:
            if request.soil_type not in s['preferred_soil']:
                score -= 25
        # Check depth
        if 'min_depth' in s and request.groundwater_depth < s['min_depth']:
            if not s.get('always_include'):
                score -= 20
        if 'max_depth' in s and request.groundwater_depth > s['max_depth']:
            score -= 15
        # Boost if rainfall is high
        if weather.annual_rainfall > 1200:
            score += 10
        elif weather.annual_rainfall < 600:
            score -= 10
        
        score = max(0, min(100, score))
        
        # Calculate dimensions
        dims = _calculate_dimensions(s['name'], request, runoff)
        
        results.append(StructureRecommendation(
            structure_type=s['name'],
            suitability_score=round(score, 1),
            description=s['description'],
            dimensions=dims,
            installation_notes=s['installation_notes']
        ))
    
    # Sort by suitability score
    results.sort(key=lambda x: x.suitability_score, reverse=True)
    return results

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
