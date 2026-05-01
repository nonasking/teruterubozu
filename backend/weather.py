import os
from datetime import date, datetime, timedelta

import requests
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

_FORECAST_BASE = "https://api.openweathermap.org/data/2.5/forecast"
_AIR_POLLUTION_BASE = "https://api.openweathermap.org/data/2.5/air_pollution/forecast"


# --- Pydantic response schemas (validate only the fields we actually use) ---


class _ForecastWeather(BaseModel):
    id: int


class _ForecastMain(BaseModel):
    temp_max: float
    temp_min: float


class _ForecastEntry(BaseModel):
    dt_txt: str
    weather: list[_ForecastWeather]
    main: _ForecastMain


class ForecastResponse(BaseModel):
    list: list[_ForecastEntry]


class _AirComponents(BaseModel):
    pm10: float
    pm2_5: float


class _AirEntry(BaseModel):
    dt: int
    components: _AirComponents


class AirPollutionResponse(BaseModel):
    list: list[_AirEntry]


# --- Retry policy: retry on connection/timeout/5xx, fail-fast on 4xx ---


def _is_retryable(exc: BaseException) -> bool:
    """Retry on transient network errors and HTTP 5xx; do not retry on 4xx."""
    if isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        return True
    if isinstance(exc, requests.exceptions.HTTPError):
        response = exc.response
        if response is not None and 500 <= response.status_code < 600:
            return True
    return False


@retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)
def _get_with_retry(url: str, params: dict) -> requests.Response:
    """GET with exponential backoff on transient failures (connection/timeout/5xx)."""
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response


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

    Reliability:
        - Network/timeout/5xx failures are retried up to 3 times with exponential
          backoff (1s → 2s → 4s). 4xx responses fail fast (no retry).
        - Responses are validated against pydantic schemas; schema drift in the
          fields we depend on raises ``pydantic.ValidationError`` immediately.
    """
    api_key = os.environ["OPENWEATHER_API_KEY"]
    lat = os.environ["OPENWEATHER_LAT"]
    lon = os.environ["OPENWEATHER_LON"]

    tomorrow = date.today() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    # --- Forecast API: rain, temp_max, temp_min ---
    forecast_response = _get_with_retry(
        _FORECAST_BASE,
        params={
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric",
            "cnt": 16,  # covers next ~48 hours at 3-hour intervals
        },
    )
    forecast = ForecastResponse.model_validate(forecast_response.json())

    will_rain = False
    temp_max_values: list[float] = []
    temp_min_values: list[float] = []

    for entry in forecast.list:
        # entry.dt_txt format: "2025-04-13 09:00:00"
        if not entry.dt_txt.startswith(tomorrow_str):
            continue

        weather_ids = [w.id for w in entry.weather]
        # OpenWeather rain codes: 2xx (thunderstorm), 3xx (drizzle), 5xx (rain)
        if any(200 <= wid < 600 for wid in weather_ids):
            will_rain = True

        temp_max_values.append(entry.main.temp_max)
        temp_min_values.append(entry.main.temp_min)

    temp_max = max(temp_max_values) if temp_max_values else 0.0
    temp_min = min(temp_min_values) if temp_min_values else 0.0

    # --- Air Pollution API: pm10, pm2_5 ---
    air_response = _get_with_retry(
        _AIR_POLLUTION_BASE,
        params={
            "lat": lat,
            "lon": lon,
            "appid": api_key,
        },
    )
    air = AirPollutionResponse.model_validate(air_response.json())

    pm10_values: list[float] = []
    pm2_5_values: list[float] = []

    for item in air.list:
        item_date = datetime.utcfromtimestamp(item.dt).date()
        if item_date != tomorrow:
            continue
        pm10_values.append(item.components.pm10)
        pm2_5_values.append(item.components.pm2_5)

    pm10 = sum(pm10_values) / len(pm10_values) if pm10_values else 0.0
    pm2_5 = sum(pm2_5_values) / len(pm2_5_values) if pm2_5_values else 0.0

    return {
        "rain": will_rain,
        "temp_max": temp_max,
        "temp_min": temp_min,
        "pm10": pm10,
        "pm2_5": pm2_5,
    }
