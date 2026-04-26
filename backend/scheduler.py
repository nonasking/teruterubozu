from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.notifier import send_rain_alert
from backend.weather import get_tomorrow_weather

scheduler = AsyncIOScheduler()


def check_tomorrow_rain() -> None:
    will_rain = get_tomorrow_weather()
    print(f"[scheduler] tomorrow rain forecast: {will_rain}")
    if will_rain:
        send_rain_alert()


def start() -> None:
    scheduler.add_job(
        check_tomorrow_rain,
        trigger=CronTrigger(hour=20, minute=0),
        id="daily_weather_check",
        replace_existing=True,
    )
    scheduler.start()


def stop() -> None:
    scheduler.shutdown()
