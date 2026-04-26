import os
from datetime import date, datetime, timedelta

import requests

_FORECAST_BASE = "https://api.openweathermap.org/data/2.5/forecast"
_AIR_POLLUTION_BASE = "https://api.openweathermap.org/data/2.5/air_pollution/forecast"


def get_tomorrow_weather() -> dict:
    """Return a weather summary dict for tomorrow.

    Returns:
        {
            "rain": bool,       # True if rain is forecast at any point tomorrow
            "temp_max": float,  # Maximum temperature (Celsius)
            "temp_min": float,  # Minimum temperature (Celsius)
            "pm10": float,      # Average PM10 (μg/m³), 0.0 if no data
            "pm2_5": float,     # Average PM2.5 (μg/m³), 0.0 if no data
        }

    Required environment variables:
        OPENWEATHER_API_KEY  – OpenWeather API key
        OPENWEATHER_LAT      – Latitude of the target location
        OPENWEATHER_LON      – Longitude of the target location
    """
    api_key = os.environ["OPENWEATHER_API_KEY"]
    lat = os.environ["OPENWEATHER_LAT"]
    lon = os.environ["OPENWEATHER_LON"]

    tomorrow = date.today() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    # --- Forecast API: rain, temp_max, temp_min ---
    forecast_response = requests.get(
        _FORECAST_BASE,
        params={
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric",
            "cnt": 16,  # covers next ~48 hours at 3-hour intervals
        },
        timeout=10,
    )
    forecast_response.raise_for_status()

    will_rain = False
    temp_max_values: list[float] = []
    temp_min_values: list[float] = []

    for entry in forecast_response.json()["list"]:
        # entry["dt_txt"] format: "2025-04-13 09:00:00"
        if not entry["dt_txt"].startswith(tomorrow_str):
            continue

        weather_ids = [w["id"] for w in entry["weather"]]
        # OpenWeather rain codes: 2xx (thunderstorm), 3xx (drizzle), 5xx (rain)
        if any(200 <= wid < 600 for wid in weather_ids):
            will_rain = True

        temp_max_values.append(entry["main"]["temp_max"])
        temp_min_values.append(entry["main"]["temp_min"])

    temp_max = max(temp_max_values) if temp_max_values else 0.0
    temp_min = min(temp_min_values) if temp_min_values else 0.0

    # --- Air Pollution API: pm10, pm2_5 ---
    air_response = requests.get(
        _AIR_POLLUTION_BASE,
        params={
            "lat": lat,
            "lon": lon,
            "appid": api_key,
        },
        timeout=10,
    )
    air_response.raise_for_status()

    pm10_values: list[float] = []
    pm2_5_values: list[float] = []

    for item in air_response.json()["list"]:
        item_date = datetime.utcfromtimestamp(item["dt"]).date()
        if item_date != tomorrow:
            continue
        pm10_values.append(item["components"]["pm10"])
        pm2_5_values.append(item["components"]["pm2_5"])

    pm10 = sum(pm10_values) / len(pm10_values) if pm10_values else 0.0
    pm2_5 = sum(pm2_5_values) / len(pm2_5_values) if pm2_5_values else 0.0

    return {
        "rain": will_rain,
        "temp_max": temp_max,
        "temp_min": temp_min,
        "pm10": pm10,
        "pm2_5": pm2_5,
    }
