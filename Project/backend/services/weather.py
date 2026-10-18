"""
Weather / rainfall service.

Rainfall comes from the gridded CMAP climatology in
`services/rainfall_grid.py` -- a real, global, public-domain raster --
rather than a hand-written lookup table.

OpenWeatherMap (when a real key is configured) supplies *current*
conditions: temperature, humidity and recent rain. It has never been
able to supply annual rainfall, so it never did more than decorate the
response with a station name.
"""

import httpx

from models.schemas import WeatherData
from config import settings

from services.rainfall_grid import (
    sample,
    scale_to_annual,
    is_available,
)


async def get_weather_data(
    lat: float,
    lon: float,
    annual_rainfall_override: float | None = None,
    location_name: str | None = None,
) -> WeatherData:
    """
    Build the rainfall / weather block for a coordinate.

    `annual_rainfall_override` lets a user substitute a locally known
    annual total (e.g. from IMD) while keeping the grid's monthly
    distribution -- see rainfall_grid.scale_to_annual().
    """

    if not is_available():
        raise RuntimeError(
            "Rainfall climatology grid is not installed. Run "
            "scripts/build_rainfall_grid.py"
        )

    grid = sample(lat, lon)

    if annual_rainfall_override and annual_rainfall_override > 0:
        grid = scale_to_annual(grid, float(annual_rainfall_override))

    fallback_name = (
        location_name
        or f"{lat:.4f}°{'N' if lat >= 0 else 'S'}, "
        f"{abs(lon):.4f}°{'E' if lon >= 0 else 'W'}"
    )

    # Defaults used when no live API key is configured.
    temp = 27.0
    humidity = 65.0
    current_rainfall = 0.0
    name = fallback_name
    live = False

    if settings.openweather_api_key and settings.openweather_api_key != "demo":
        try:
            live_data = await _fetch_from_openweather(lat, lon)
            name = live_data.get("name") or fallback_name
            temp = live_data.get("temp", temp)
            humidity = live_data.get("humidity", humidity)
            current_rainfall = live_data.get("current_rainfall", 0.0)
            live = True
        except Exception:
            # Live weather is a nicety; the climatology always stands.
            pass

    return WeatherData(
        location_name=name,
        annual_rainfall=round(grid.annual_mm, 1),
        monthly_rainfall=[round(v, 1) for v in grid.monthly_mm],
        avg_temperature=temp,
        humidity=humidity,
        current_rainfall=current_rainfall,
        # --- provenance ---
        rainfall_source=grid.source,
        rainfall_method=grid.describe(),
        grid_cell=f"{grid.cell_lat:.2f}°, {grid.cell_lon:.2f}°",
        grid_resolution_deg=grid.resolution_deg,
        climatology_period=grid.period,
        rainfall_is_grid_estimate=not grid.scaled_to_override,
        rainfall_is_live=live,
    )


async def _fetch_from_openweather(lat: float, lon: float) -> dict:
    """Current conditions only. Annual rainfall comes from the grid."""

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}"
        f"&appid={settings.openweather_api_key}&units=metric"
    )

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    return {
        "name": data.get("name"),
        "temp": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        # Rain over the last hour, extrapolated to a day. Indicative only.
        "current_rainfall": data.get("rain", {}).get("1h", 0.0) * 24,
    }
