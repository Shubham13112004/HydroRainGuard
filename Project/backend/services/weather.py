"""
Weather service - fetches real rainfall data from OpenWeatherMap.
Falls back to realistic India-region estimates if API key is 'demo' or call fails.
"""
import httpx
from models.schemas import WeatherData
from config import settings

# Monthly rainfall distribution factors by climate zone (for fallback)
# India average monthly rainfall pattern (fraction of annual)
INDIA_MONTHLY_PATTERN = [0.01, 0.01, 0.02, 0.02, 0.04, 0.18, 0.26, 0.22, 0.12, 0.06, 0.04, 0.02]

# Regional annual rainfall estimates (mm) by lat/lon bounding boxes
# (lat_min, lat_max, lon_min, lon_max, annual_mm, region_name)
REGIONAL_RAINFALL = [
    (18.0, 19.5, 73.0, 74.5, 700, "Pune Region"),
    (19.0, 20.0, 72.7, 73.5, 2300, "Mumbai Region"),
    (12.8, 13.2, 77.4, 77.8, 970, "Bangalore Region"),
    (13.0, 14.0, 80.0, 80.5, 1400, "Chennai Region"),
    (22.4, 23.0, 72.8, 73.2, 900, "Ahmedabad Region"),
    (28.4, 28.8, 76.8, 77.5, 780, "Delhi Region"),
    (22.4, 22.8, 88.2, 88.6, 1600, "Kolkata Region"),
    (17.2, 17.6, 78.3, 78.7, 820, "Hyderabad Region"),
    (8.0, 12.0, 76.0, 78.0, 3000, "Kerala Region"),
    (0.0, 90.0, 60.0, 100.0, 1100, "India Average"),  # fallback
]

async def get_weather_data(lat: float, lon: float) -> WeatherData:
    """
    Fetch weather data for given coordinates.
    Uses OpenWeatherMap if API key is available, otherwise uses regional estimates.
    """
    if settings.openweather_api_key and settings.openweather_api_key != 'demo':
        try:
            return await _fetch_from_openweather(lat, lon)
        except Exception:
            pass
    return _get_regional_estimate(lat, lon)

async def _fetch_from_openweather(lat: float, lon: float) -> WeatherData:
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={settings.openweather_api_key}&units=metric"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    
    location_name = data.get('name', f"{lat:.2f},{lon:.2f}")
    current_rainfall = data.get('rain', {}).get('1h', 0.0) * 24  # convert to daily
    temp = data['main']['temp']
    humidity = data['main']['humidity']
    
    # Get regional annual estimate since OWM free tier doesn't give annual data
    regional = _get_regional_estimate(lat, lon)
    annual_rainfall = regional.annual_rainfall
    monthly_rainfall = regional.monthly_rainfall
    
    return WeatherData(
        location_name=location_name,
        annual_rainfall=annual_rainfall,
        monthly_rainfall=monthly_rainfall,
        avg_temperature=temp,
        humidity=humidity,
        current_rainfall=current_rainfall
    )

def _get_regional_estimate(lat: float, lon: float) -> WeatherData:
    annual_mm = 1100
    region_name = f"{lat:.2f}°N, {lon:.2f}°E"
    for lat_min, lat_max, lon_min, lon_max, rain, name in REGIONAL_RAINFALL:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            annual_mm = rain
            region_name = name
            break
    
    monthly = [annual_mm * f for f in INDIA_MONTHLY_PATTERN]
    
    return WeatherData(
        location_name=region_name,
        annual_rainfall=annual_mm,
        monthly_rainfall=monthly,
        avg_temperature=27.0,
        humidity=65.0,
        current_rainfall=0.0
    )
