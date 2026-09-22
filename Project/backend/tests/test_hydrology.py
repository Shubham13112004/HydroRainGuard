import pytest
from models.schemas import AssessmentRequest, RoofType, SoilType
from services.hydrology import calculate_runoff, calculate_recharge
from services.weather import _get_regional_estimate

def make_request(**kwargs):
    defaults = dict(
        name='Test', location='Pune', latitude=18.5, longitude=73.8,
        num_people=4, roof_type='RCC', roof_area=100.0,
        open_space_area=50.0, soil_type='SANDY', groundwater_depth=15.0
    )
    defaults.update(kwargs)
    return AssessmentRequest(**defaults)

def test_pune_rcc_100m2_runoff():
    req = make_request()
    weather = _get_regional_estimate(18.5, 73.8)
    runoff = calculate_runoff(req, weather)
    # Pune 700mm, C=0.9, A=100 => ~63,000 liters
    assert 50000 < runoff.annual_runoff_volume < 100000
    assert runoff.runoff_coefficient == 0.90
    assert len(runoff.monthly_runoff) == 12
    assert runoff.harvestable_volume < runoff.annual_runoff_volume

def test_green_roof_lower_runoff():
    req_green = make_request(roof_type='GREEN')
    req_rcc = make_request(roof_type='RCC')
    weather = _get_regional_estimate(18.5, 73.8)
    runoff_green = calculate_runoff(req_green, weather)
    runoff_rcc = calculate_runoff(req_rcc, weather)
    assert runoff_green.annual_runoff_volume < runoff_rcc.annual_runoff_volume

def test_recharge_feasibility_score():
    req_sandy = make_request(soil_type='SANDY', groundwater_depth=25.0, open_space_area=200.0)
    req_clay = make_request(soil_type='CLAY', groundwater_depth=3.0, open_space_area=5.0)
    weather = _get_regional_estimate(18.5, 73.8)
    recharge_sandy = calculate_recharge(req_sandy, weather)
    recharge_clay = calculate_recharge(req_clay, weather)
    assert recharge_sandy.recharge_feasibility_score > recharge_clay.recharge_feasibility_score

def test_monthly_runoff_sums_to_annual():
    req = make_request()
    weather = _get_regional_estimate(18.5, 73.8)
    runoff = calculate_runoff(req, weather)
    monthly_sum = sum(runoff.monthly_runoff)
    assert abs(monthly_sum - runoff.annual_runoff_volume) < 1.0  # within 1 liter
