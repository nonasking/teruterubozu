import os
from datetime import date, timedelta

import requests

_API_BASE = "https://api.openweathermap.org/data/2.5/forecast"


def get_tomorrow_weather() -> bool:
    """Return True if rain is forecast at any point tomorrow, False otherwise.

    Required environment variables:
        OPENWEATHER_API_KEY  – OpenWeather API key
        OPENWEATHER_LAT      – Latitude of the target location
        OPENWEATHER_LON      – Longitude of the target location
    """
    api_key = os.environ["OPENWEATHER_API_KEY"]
    lat = os.environ["OPENWEATHER_LAT"]
    lon = os.environ["OPENWEATHER_LON"]

    response = requests.get(
        _API_BASE,
        params={
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric",
            "cnt": 16,  # covers next ~48 hours at 3-hour intervals
        },
        timeout=10,
    )
    response.raise_for_status()

    tomorrow = date.today() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    for entry in response.json()["list"]:
        # entry["dt_txt"] format: "2025-04-13 09:00:00"
        if not entry["dt_txt"].startswith(tomorrow_str):
            continue

        weather_ids = [w["id"] for w in entry["weather"]]
        # OpenWeather rain codes: 2xx (thunderstorm), 3xx (drizzle), 5xx (rain)
        if any(200 <= wid < 600 for wid in weather_ids):
            return True

    return False
