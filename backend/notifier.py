import os
import smtplib
from email.mime.text import MIMEText


def _grade(value: float, thresholds: list[int]) -> str:
    """Return Korean air-quality grade for a particulate-matter value.

    Args:
        value: measured concentration (μg/m³)
        thresholds: [보통 경계, 나쁨 경계, 매우나쁨 경계]
            e.g. PM10 → [31, 81, 151], PM2.5 → [16, 36, 76]

    Returns:
        "좋음" / "보통" / "나쁨" / "매우나쁨"
    """
    moderate, unhealthy, very_unhealthy = thresholds
    if value < moderate:
        return "좋음"
    if value < unhealthy:
        return "보통"
    if value < very_unhealthy:
        return "나쁨"
    return "매우나쁨"


def send_daily_report(weather: dict) -> None:
    """Send a daily weather report email regardless of rain forecast.

    Args:
        weather: dict returned by get_tomorrow_weather(), containing:
            rain (bool), temp_max (float), temp_min (float),
            pm10 (float), pm2_5 (float)

    Required environment variables:
        GMAIL_USER          – Gmail address used to send the email
        GMAIL_APP_PASSWORD  – Gmail App Password
        NOTIFY_TO_EMAIL     – Recipient email address
    """
    gmail_user = os.environ["GMAIL_USER"]
    gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]
    to_email = os.environ["NOTIFY_TO_EMAIL"]

    if weather["rain"]:
        subject = "☔ 내일 날씨 알림 - 비 예보"
    else:
        subject = "☀️ 내일 날씨 알림"

    rain_label = "있음" if weather["rain"] else "없음"
    pm10_grade = _grade(weather["pm10"], [31, 81, 151])
    pm2_5_grade = _grade(weather["pm2_5"], [16, 36, 76])
    body = (
        "[내일 날씨 요약]\n"
        f"🌧 비 예보: {rain_label}\n"
        f"🌡 최고기온: {weather['temp_max']:.1f}°C\n"
        f"🌡 최저기온: {weather['temp_min']:.1f}°C\n"
        f"😷 미세먼지(PM10): {weather['pm10']:.1f} μg/m³ ({pm10_grade})\n"
        f"😷 초미세먼지(PM2.5): {weather['pm2_5']:.1f} μg/m³ ({pm2_5_grade})"
    )

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = to_email

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(gmail_user, gmail_app_password)
        smtp.sendmail(gmail_user, to_email, msg.as_string())

    print(f"[notifier] Email sent to {to_email}")
