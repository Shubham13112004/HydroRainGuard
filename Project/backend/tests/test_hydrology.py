import math
import pytest

from models.schemas import AssessmentRequest, RoofType, SoilType, WeatherData
from services.hydrology import calculate_runoff, calculate_recharge, scs_cn_runoff_mm
from services.rainfall_grid import sample, scale_to_annual, is_available


def make_request(**kwargs):
    defaults = dict(
        name='Test', location='Pune', latitude=18.5, longitude=73.8,
        num_people=4, roof_type='RCC', roof_area=100.0,
        open_space_area=50.0, soil_type='SANDY', groundwater_depth=15.0
    )
    defaults.update(kwargs)
    return AssessmentRequest(**defaults)


def make_weather(lat=18.5, lon=73.8, annual_override=700.0):
    """IMD Pune station annual (700 mm) with the grid's monthly shape."""
    g = scale_to_annual(sample(lat, lon), annual_override)
    return WeatherData(
        location_name="Test site",
        annual_rainfall=round(g.annual_mm, 1),
        monthly_rainfall=[round(v, 1) for v in g.monthly_mm],
        avg_temperature=25.0,
        humidity=60.0,
        current_rainfall=0.0,
        rainfall_source=g.source,
        rainfall_method=g.describe(),
        grid_cell=f"{g.cell_lat:.2f}, {g.cell_lon:.2f}",
        grid_resolution_deg=g.resolution_deg,
        climatology_period=g.period,
        rainfall_is_grid_estimate=False,
        rainfall_is_live=False,
    )


# ---------------------------------------------------------------- rainfall grid

@pytest.mark.skipif(not is_available(), reason="climatology grid not built")
def test_grid_is_installed_and_real():
    s = sample(18.5204, 73.8567)
    assert s.source
    assert len(s.monthly_mm) == 12
    assert s.annual_mm > 0
    assert s.valid_years == 30
    assert abs(sum(s.monthly_mm) - s.annual_mm) < 1.0


@pytest.mark.skipif(not is_available(), reason="climatology grid not built")
def test_grid_is_global_not_india_specific():
    """New York must NOT get an Indian monsoon profile."""
    ny = sample(40.7128, -74.006)
    assert 700 < ny.annual_mm < 1400            # NY is ~1200 mm
    peak = max(ny.monthly_mm)
    trough = min(ny.monthly_mm)
    assert peak / trough < 3.0                  # no monsoon peak

    pune = sample(18.5204, 73.8567)
    assert max(pune.monthly_mm) / max(min(pune.monthly_mm), 0.01) > 50


@pytest.mark.skipif(not is_available(), reason="climatology grid not built")
def test_grid_interpolates_between_cells():
    a = sample(18.75, 73.75)          # exactly a cell centre
    b = sample(19.5, 74.0)            # between centres
    assert a.cell_lat == 18.75 and a.cell_lon == 73.75
    assert isinstance(b.interpolated, bool)
    assert a.annual_mm != b.annual_mm


@pytest.mark.skipif(not is_available(), reason="climatology grid not built")
def test_grid_handles_dateline_and_poles():
    for lat, lon in [(0, 180), (0, -180), (89.9, 10), (-89.9, -170)]:
        s = sample(lat, lon)
        assert s.annual_mm >= 0
        assert math.isfinite(s.annual_mm)


@pytest.mark.skipif(not is_available(), reason="climatology grid not built")
def test_scale_to_annual_preserves_shape():
    s = sample(18.5204, 73.8567)
    scaled = scale_to_annual(s, 700.0)
    assert abs(scaled.annual_mm - 700.0) < 1.0
    assert scaled.monthly_mm[6] == max(scaled.monthly_mm)   # July peak kept
    assert abs(sum(scaled.monthly_mm) - 700.0) < 1.0


# ------------------------------------------------------------------------ runoff

def test_pune_rcc_100m2_runoff():
    req = make_request()
    weather = make_weather()
    runoff = calculate_runoff(req, weather)
    # 700mm, C=0.9, A=100 => ~63,000 liters gross
    assert 55000 < runoff.annual_runoff_volume < 70000
    assert runoff.runoff_coefficient == 0.90
    assert len(runoff.monthly_runoff) == 12
    assert runoff.harvestable_volume < runoff.annual_runoff_volume


def test_green_roof_lower_runoff():
    weather = make_weather()
    runoff_green = calculate_runoff(make_request(roof_type='GREEN'), weather)
    runoff_rcc = calculate_runoff(make_request(roof_type='RCC'), weather)
    assert runoff_green.annual_runoff_volume < runoff_rcc.annual_runoff_volume


def test_monthly_runoff_sums_to_annual():
    weather = make_weather()
    runoff = calculate_runoff(make_request(), weather)
    monthly_sum = sum(runoff.monthly_runoff)
    assert abs(monthly_sum - runoff.annual_runoff_volume) < 1.0  # within 1 liter


# ------------------------------------------------------------------------ SCS-CN

def test_scs_cn_basics():
    # Below the initial abstraction, no runoff at all.
    assert scs_cn_runoff_mm(0.0, 98) == 0.0
    # 1 mm of runoff over 1 m2 is exactly 1 litre; check the algebra.
    S = 25400 / 98 - 254
    Ia = 0.2 * S
    assert scs_cn_runoff_mm(100.0, 98) == pytest.approx(
        (100 - Ia) ** 2 / (100 - Ia + S), rel=1e-9)
    # Impervious roofs run off almost everything; green roofs much less.
    assert scs_cn_runoff_mm(100.0, 98) > scs_cn_runoff_mm(100.0, 75)
    # Monotonic in rainfall.
    assert scs_cn_runoff_mm(50, 95) < scs_cn_runoff_mm(100, 95)


def test_scs_cn_reported_alongside_rational():
    weather = make_weather()
    r = calculate_runoff(make_request(), weather)
    assert r.runoff_method == "rational"
    assert r.curve_number == 98
    assert r.scs_cn_annual_runoff > 0
    assert len(r.scs_cn_monthly_runoff) == 12
    # Both methods should land in the same ballpark (within 40%).
    assert abs(r.scs_cn_vs_rational_pct) < 40


def test_runoff_method_selection():
    weather = make_weather()
    rat = calculate_runoff(make_request(runoff_method="rational"), weather)
    scs = calculate_runoff(make_request(runoff_method="scs_cn"), weather)
    assert rat.annual_runoff_volume != scs.annual_runoff_volume
    assert scs.runoff_method == "scs_cn"
    assert abs(scs.annual_runoff_volume - rat.scs_cn_annual_runoff) < 1.0


# ---------------------------------------------------------------------- recharge

def test_recharge_feasibility_score():
    weather = make_weather()
    sandy = calculate_recharge(
        make_request(soil_type='SANDY', groundwater_depth=25.0, open_space_area=200.0),
        weather)
    clay = calculate_recharge(
        make_request(soil_type='CLAY', groundwater_depth=3.0, open_space_area=5.0),
        weather)
    assert sandy.recharge_feasibility_score > clay.recharge_feasibility_score
