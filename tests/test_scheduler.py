from unittest.mock import patch

from apscheduler.triggers.cron import CronTrigger

import backend.scheduler as sched_module
from backend.scheduler import check_tomorrow_rain

_WEATHER = {"rain": False, "temp_max": 25.0, "temp_min": 15.0, "pm10": 20.0, "pm2_5": 10.0}
_WEATHER_RAIN = {"rain": True, "temp_max": 18.0, "temp_min": 12.0, "pm10": 30.0, "pm2_5": 15.0}


# --- check_tomorrow_rain logic ---

@patch("backend.scheduler.send_daily_report")
@patch("backend.scheduler.get_tomorrow_weather")
def test_always_sends_report_regardless_of_rain(mock_weather, mock_report):
    mock_weather.return_value = _WEATHER
    check_tomorrow_rain()
    mock_report.assert_called_once_with(_WEATHER)


@patch("backend.scheduler.send_daily_report")
@patch("backend.scheduler.get_tomorrow_weather")
def test_sends_report_even_when_rain_expected(mock_weather, mock_report):
    mock_weather.return_value = _WEATHER_RAIN
    check_tomorrow_rain()
    mock_report.assert_called_once_with(_WEATHER_RAIN)


@patch("backend.scheduler.send_daily_report")
@patch("backend.scheduler.get_tomorrow_weather")
def test_weather_always_checked(mock_weather, mock_report):
    mock_weather.return_value = _WEATHER
    check_tomorrow_rain()
    mock_weather.assert_called_once()


# --- Job registration ---

def test_start_registers_daily_job_at_20_00():
    with (
        patch.object(sched_module.scheduler, "add_job") as mock_add_job,
        patch.object(sched_module.scheduler, "start"),
    ):
        sched_module.start()

        mock_add_job.assert_called_once()
        args, kwargs = mock_add_job.call_args

        assert args[0] is check_tomorrow_rain
        assert kwargs["id"] == "daily_weather_check"
        assert kwargs["replace_existing"] is True

        trigger: CronTrigger = kwargs["trigger"]
        assert isinstance(trigger, CronTrigger)
        fields = {f.name: f for f in trigger.fields}
        assert str(fields["hour"]) == "20"
        assert str(fields["minute"]) == "0"


def test_start_starts_scheduler():
    with (
        patch.object(sched_module.scheduler, "add_job"),
        patch.object(sched_module.scheduler, "start") as mock_start,
    ):
        sched_module.start()
        mock_start.assert_called_once()


def test_stop_shuts_down_scheduler():
    with patch.object(sched_module.scheduler, "shutdown") as mock_shutdown:
        sched_module.stop()
        mock_shutdown.assert_called_once()
