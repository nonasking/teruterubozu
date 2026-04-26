from backend.weather import get_tomorrow_weather
from backend.notifier import send_rain_alert

rain = get_tomorrow_weather()
print(f"[run] 내일 비 예보: {rain}")
if rain:
    send_rain_alert()
