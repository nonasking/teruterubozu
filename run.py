from backend.notifier import send_daily_report
from backend.weather import get_tomorrow_weather

weather = get_tomorrow_weather()
print(f"[run] 내일 비 예보: {weather['rain']}, 최고: {weather['temp_max']:.1f}°C, 최저: {weather['temp_min']:.1f}°C, PM10: {weather['pm10']:.1f}, PM2.5: {weather['pm2_5']:.1f}")
send_daily_report(weather)
