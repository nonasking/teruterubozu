from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from backend.weather import get_tomorrow_weather

_ENV = {
    "OPENWEATHER_API_KEY": "test_key",
    "OPENWEATHER_LAT": "37.5",
    "OPENWEATHER_LON": "126.9",
}


@pytest.fixture(autouse=True)
def env(monkeypatch):
    for k, v in _ENV.items():
        monkeypatch.setenv(k, v)


def _tomorrow() -> str:
    return (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")


def _entry(date_str: str, weather_id: int) -> dict:
    return {"dt_txt": f"{date_str} 12:00:00", "weather": [{"id": weather_id}]}


def _mock_response(entries: list) -> MagicMock:
    m = MagicMock()
    m.json.return_value = {"list": entries}
    return m


# --- Rain detection ---

@patch("backend.weather.requests.get")
def test_rain_5xx_returns_true(mock_get):
    mock_get.return_value = _mock_response([_entry(_tomorrow(), 501)])
    assert get_tomorrow_weather() is True


@patch("backend.weather.requests.get")
def test_drizzle_3xx_returns_true(mock_get):
    mock_get.return_value = _mock_response([_entry(_tomorrow(), 300)])
    assert get_tomorrow_weather() is True


@patch("backend.weather.requests.get")
def test_thunderstorm_2xx_returns_true(mock_get):
    mock_get.return_value = _mock_response([_entry(_tomorrow(), 200)])
    assert get_tomorrow_weather() is True


@patch("backend.weather.requests.get")
def test_clear_sky_returns_false(mock_get):
    mock_get.return_value = _mock_response([_entry(_tomorrow(), 800)])
    assert get_tomorrow_weather() is False


# --- Boundary conditions on weather ID ---

@patch("backend.weather.requests.get")
def test_weather_id_boundary_200_returns_true(mock_get):
    mock_get.return_value = _mock_response([_entry(_tomorrow(), 200)])
    assert get_tomorrow_weather() is True


@patch("backend.weather.requests.get")
def test_weather_id_boundary_599_returns_true(mock_get):
    mock_get.return_value = _mock_response([_entry(_tomorrow(), 599)])
    assert get_tomorrow_weather() is True


@patch("backend.weather.requests.get")
def test_weather_id_199_returns_false(mock_get):
    mock_get.return_value = _mock_response([_entry(_tomorrow(), 199)])
    assert get_tomorrow_weather() is False


@patch("backend.weather.requests.get")
def test_weather_id_600_returns_false(mock_get):
    mock_get.return_value = _mock_response([_entry(_tomorrow(), 600)])
    assert get_tomorrow_weather() is False


# --- Date filtering ---

@patch("backend.weather.requests.get")
def test_no_tomorrow_entries_returns_false(mock_get):
    today = date.today().strftime("%Y-%m-%d")
    day_after = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
    mock_get.return_value = _mock_response([
        _entry(today, 501),
        _entry(day_after, 501),
    ])
    assert get_tomorrow_weather() is False


@patch("backend.weather.requests.get")
def test_rain_only_on_day_after_returns_false(mock_get):
    day_after = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
    mock_get.return_value = _mock_response([_entry(day_after, 501)])
    assert get_tomorrow_weather() is False


@patch("backend.weather.requests.get")
def test_first_rainy_entry_short_circuits(mock_get):
    """Rain found in first tomorrow entry → True without checking the rest."""
    mock_get.return_value = _mock_response([
        _entry(_tomorrow(), 501),
        _entry(_tomorrow(), 800),
    ])
    assert get_tomorrow_weather() is True


@patch("backend.weather.requests.get")
def test_multiple_tomorrow_entries_all_clear_returns_false(mock_get):
    mock_get.return_value = _mock_response([
        _entry(_tomorrow(), 800),
        _entry(_tomorrow(), 801),
        _entry(_tomorrow(), 802),
    ])
    assert get_tomorrow_weather() is False


# --- API call correctness ---

@patch("backend.weather.requests.get")
def test_api_called_with_correct_params(mock_get):
    mock_get.return_value = _mock_response([])
    get_tomorrow_weather()
    _, kwargs = mock_get.call_args
    params = kwargs["params"]
    assert params["appid"] == "test_key"
    assert params["lat"] == "37.5"
    assert params["lon"] == "126.9"
    assert params["cnt"] == 16
    assert kwargs["timeout"] == 10


@patch("backend.weather.requests.get")
def test_raise_for_status_called(mock_get):
    mock_get.return_value = _mock_response([])
    get_tomorrow_weather()
    mock_get.return_value.raise_for_status.assert_called_once()
