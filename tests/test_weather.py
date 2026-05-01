from datetime import date, datetime, timedelta
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


def _tomorrow_dt() -> int:
    """Unix timestamp for tomorrow noon UTC."""
    tomorrow = date.today() + timedelta(days=1)
    return int(datetime(tomorrow.year, tomorrow.month, tomorrow.day, 12, 0, 0).timestamp())


def _forecast_entry(date_str: str, weather_id: int, temp_max: float = 20.0, temp_min: float = 10.0) -> dict:
    return {
        "dt_txt": f"{date_str} 12:00:00",
        "weather": [{"id": weather_id}],
        "main": {"temp_max": temp_max, "temp_min": temp_min},
    }


def _air_entry(dt: int, pm10: float = 25.0, pm2_5: float = 12.0) -> dict:
    return {"dt": dt, "components": {"pm10": pm10, "pm2_5": pm2_5}}


def _mock_forecast_response(entries: list) -> MagicMock:
    m = MagicMock()
    m.json.return_value = {"list": entries}
    return m


def _mock_air_response(items: list) -> MagicMock:
    m = MagicMock()
    m.json.return_value = {"list": items}
    return m


def _make_get_side_effect(forecast_entries: list, air_items: list):
    """Return a side_effect function that serves forecast first, air pollution second."""
    forecast_mock = _mock_forecast_response(forecast_entries)
    air_mock = _mock_air_response(air_items)
    return [forecast_mock, air_mock]


# --- Return type ---

@patch("backend.weather.requests.get")
def test_returns_dict_with_expected_keys(mock_get):
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(_tomorrow(), 800)],
        [_air_entry(_tomorrow_dt())],
    )
    result = get_tomorrow_weather()
    assert isinstance(result, dict)
    assert set(result.keys()) == {"rain", "temp_max", "temp_min", "pm10", "pm2_5"}


# --- Rain detection ---

@patch("backend.weather.requests.get")
def test_rain_5xx_sets_rain_true(mock_get):
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(_tomorrow(), 501)],
        [_air_entry(_tomorrow_dt())],
    )
    assert get_tomorrow_weather()["rain"] is True


@patch("backend.weather.requests.get")
def test_drizzle_3xx_sets_rain_true(mock_get):
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(_tomorrow(), 300)],
        [_air_entry(_tomorrow_dt())],
    )
    assert get_tomorrow_weather()["rain"] is True


@patch("backend.weather.requests.get")
def test_thunderstorm_2xx_sets_rain_true(mock_get):
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(_tomorrow(), 200)],
        [_air_entry(_tomorrow_dt())],
    )
    assert get_tomorrow_weather()["rain"] is True


@patch("backend.weather.requests.get")
def test_clear_sky_sets_rain_false(mock_get):
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(_tomorrow(), 800)],
        [_air_entry(_tomorrow_dt())],
    )
    assert get_tomorrow_weather()["rain"] is False


# --- Boundary conditions on weather ID ---

@patch("backend.weather.requests.get")
def test_weather_id_boundary_200_rain_true(mock_get):
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(_tomorrow(), 200)],
        [_air_entry(_tomorrow_dt())],
    )
    assert get_tomorrow_weather()["rain"] is True


@patch("backend.weather.requests.get")
def test_weather_id_boundary_599_rain_true(mock_get):
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(_tomorrow(), 599)],
        [_air_entry(_tomorrow_dt())],
    )
    assert get_tomorrow_weather()["rain"] is True


@patch("backend.weather.requests.get")
def test_weather_id_199_rain_false(mock_get):
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(_tomorrow(), 199)],
        [_air_entry(_tomorrow_dt())],
    )
    assert get_tomorrow_weather()["rain"] is False


@patch("backend.weather.requests.get")
def test_weather_id_600_rain_false(mock_get):
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(_tomorrow(), 600)],
        [_air_entry(_tomorrow_dt())],
    )
    assert get_tomorrow_weather()["rain"] is False


# --- Date filtering ---

@patch("backend.weather.requests.get")
def test_no_tomorrow_entries_rain_false(mock_get):
    today = date.today().strftime("%Y-%m-%d")
    day_after = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(today, 501), _forecast_entry(day_after, 501)],
        [_air_entry(_tomorrow_dt())],
    )
    assert get_tomorrow_weather()["rain"] is False


@patch("backend.weather.requests.get")
def test_rain_only_on_day_after_rain_false(mock_get):
    day_after = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(day_after, 501)],
        [_air_entry(_tomorrow_dt())],
    )
    assert get_tomorrow_weather()["rain"] is False


@patch("backend.weather.requests.get")
def test_multiple_tomorrow_entries_all_clear_rain_false(mock_get):
    mock_get.side_effect = _make_get_side_effect(
        [
            _forecast_entry(_tomorrow(), 800),
            _forecast_entry(_tomorrow(), 801),
            _forecast_entry(_tomorrow(), 802),
        ],
        [_air_entry(_tomorrow_dt())],
    )
    assert get_tomorrow_weather()["rain"] is False


# --- Temperature aggregation ---

@patch("backend.weather.requests.get")
def test_temp_max_is_maximum_of_tomorrow_entries(mock_get):
    mock_get.side_effect = _make_get_side_effect(
        [
            _forecast_entry(_tomorrow(), 800, temp_max=22.0, temp_min=10.0),
            _forecast_entry(_tomorrow(), 800, temp_max=30.0, temp_min=15.0),
            _forecast_entry(_tomorrow(), 800, temp_max=25.0, temp_min=12.0),
        ],
        [_air_entry(_tomorrow_dt())],
    )
    result = get_tomorrow_weather()
    assert result["temp_max"] == pytest.approx(30.0)


@patch("backend.weather.requests.get")
def test_temp_min_is_minimum_of_tomorrow_entries(mock_get):
    mock_get.side_effect = _make_get_side_effect(
        [
            _forecast_entry(_tomorrow(), 800, temp_max=22.0, temp_min=10.0),
            _forecast_entry(_tomorrow(), 800, temp_max=30.0, temp_min=15.0),
            _forecast_entry(_tomorrow(), 800, temp_max=25.0, temp_min=8.0),
        ],
        [_air_entry(_tomorrow_dt())],
    )
    result = get_tomorrow_weather()
    assert result["temp_min"] == pytest.approx(8.0)


@patch("backend.weather.requests.get")
def test_temp_defaults_to_zero_when_no_tomorrow_entries(mock_get):
    today = date.today().strftime("%Y-%m-%d")
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(today, 800, temp_max=30.0, temp_min=10.0)],
        [_air_entry(_tomorrow_dt())],
    )
    result = get_tomorrow_weather()
    assert result["temp_max"] == pytest.approx(0.0)
    assert result["temp_min"] == pytest.approx(0.0)


# --- PM aggregation ---

@patch("backend.weather.requests.get")
def test_pm_values_are_averaged_over_tomorrow_entries(mock_get):
    tomorrow_dt1 = _tomorrow_dt()
    tomorrow_dt2 = _tomorrow_dt() + 3600
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(_tomorrow(), 800)],
        [
            _air_entry(tomorrow_dt1, pm10=20.0, pm2_5=10.0),
            _air_entry(tomorrow_dt2, pm10=40.0, pm2_5=30.0),
        ],
    )
    result = get_tomorrow_weather()
    assert result["pm10"] == pytest.approx(30.0)
    assert result["pm2_5"] == pytest.approx(20.0)


@patch("backend.weather.requests.get")
def test_pm_defaults_to_zero_when_no_tomorrow_air_entries(mock_get):
    # Provide an air entry for today (not tomorrow) to trigger the no-data path
    today_dt = int(datetime(date.today().year, date.today().month, date.today().day, 12, 0, 0).timestamp())
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(_tomorrow(), 800)],
        [_air_entry(today_dt, pm10=50.0, pm2_5=25.0)],
    )
    result = get_tomorrow_weather()
    assert result["pm10"] == pytest.approx(0.0)
    assert result["pm2_5"] == pytest.approx(0.0)


# --- API call correctness ---

@patch("backend.weather.requests.get")
def test_forecast_api_called_with_correct_params(mock_get):
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(_tomorrow(), 800)],
        [_air_entry(_tomorrow_dt())],
    )
    get_tomorrow_weather()
    first_call_args, first_call_kwargs = mock_get.call_args_list[0]
    params = first_call_kwargs["params"]
    assert params["appid"] == "test_key"
    assert params["lat"] == "37.5"
    assert params["lon"] == "126.9"
    assert params["cnt"] == 16
    assert first_call_kwargs["timeout"] == 10


@patch("backend.weather.requests.get")
def test_air_pollution_api_called_with_correct_params(mock_get):
    mock_get.side_effect = _make_get_side_effect(
        [_forecast_entry(_tomorrow(), 800)],
        [_air_entry(_tomorrow_dt())],
    )
    get_tomorrow_weather()
    second_call_args, second_call_kwargs = mock_get.call_args_list[1]
    params = second_call_kwargs["params"]
    assert params["appid"] == "test_key"
    assert params["lat"] == "37.5"
    assert params["lon"] == "126.9"
    assert second_call_kwargs["timeout"] == 10


@patch("backend.weather.requests.get")
def test_raise_for_status_called_for_both_apis(mock_get):
    forecast_mock = _mock_forecast_response([_forecast_entry(_tomorrow(), 800)])
    air_mock = _mock_air_response([_air_entry(_tomorrow_dt())])
    mock_get.side_effect = [forecast_mock, air_mock]
    get_tomorrow_weather()
    forecast_mock.raise_for_status.assert_called_once()
    air_mock.raise_for_status.assert_called_once()
