from unittest.mock import patch

import pytest
from apscheduler.triggers.cron import CronTrigger

from backend.scheduler import check_tomorrow_rain
import backend.scheduler as sched_module


# --- check_tomorrow_rain logic ---

@patch("backend.scheduler.send_rain_alert")
@patch("backend.scheduler.get_tomorrow_weather")
def test_sends_sms_when_rain_expected(mock_weather, mock_alert):
    mock_weather.return_value = True
    check_tomorrow_rain()
    mock_alert.assert_called_once()


@patch("backend.scheduler.send_rain_alert")
@patch("backend.scheduler.get_tomorrow_weather")
def test_no_sms_when_no_rain(mock_weather, mock_alert):
    mock_weather.return_value = False
    check_tomorrow_rain()
    mock_alert.assert_not_called()


@patch("backend.scheduler.send_rain_alert")
@patch("backend.scheduler.get_tomorrow_weather")
def test_weather_always_checked(mock_weather, mock_alert):
    mock_weather.return_value = False
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
