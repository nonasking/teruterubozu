import os
import smtplib
from email.mime.multipart import MIMEMultipart
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


def _grade_color(grade: str) -> str:
    """Return badge background color for a given air-quality grade."""
    return {
        "좋음": "#388e3c",
        "보통": "#f9a825",
        "나쁨": "#e65100",
        "매우나쁨": "#b71c1c",
    }[grade]


def _badge(grade: str) -> str:
    """Render an inline severity badge as an HTML span."""
    color = _grade_color(grade)
    return (
        f'<span style="background:{color};color:#fff;'
        f'padding:2px 8px;border-radius:10px;font-size:12px;">{grade}</span>'
    )


def _build_html(
    weather: dict,
    subject: str,
    pm10_grade: str,
    pm2_5_grade: str,
) -> str:
    """Build the HTML body for the daily weather report email.

    Args:
        weather: dict with keys rain, temp_max, temp_min, pm10, pm2_5
        subject: full email subject (used as header title, includes emoji)
        pm10_grade: Korean grade for PM10
        pm2_5_grade: Korean grade for PM2.5

    Returns:
        Complete HTML document as a string. All CSS is inline for Gmail
        compatibility.
    """
    rain_label = "있음" if weather["rain"] else "없음"

    label_style = (
        "padding:10px 4px;color:#555;font-size:14px;"
        "border-bottom:1px solid #eee;"
    )
    value_style = (
        "padding:10px 4px;color:#222;font-size:14px;text-align:right;"
        "border-bottom:1px solid #eee;"
    )
    last_label_style = "padding:10px 4px;color:#555;font-size:14px;"
    last_value_style = (
        "padding:10px 4px;color:#222;font-size:14px;text-align:right;"
    )

    pm10_badge = _badge(pm10_grade)
    pm2_5_badge = _badge(pm2_5_grade)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>{subject}</title>
</head>
<body style="margin:0;padding:24px 12px;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;">
  <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="max-width:480px;width:100%;margin:0 auto;border-collapse:collapse;">
    <tr>
      <td style="background:#1a237e;color:#ffffff;padding:20px 24px;border-radius:8px 8px 0 0;text-align:center;font-size:18px;font-weight:600;">
        {subject}
      </td>
    </tr>
    <tr>
      <td style="background:#ffffff;padding:16px 24px;border-radius:0 0 8px 8px;">
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="border-collapse:collapse;">
          <tr>
            <td style="{label_style}">비 예보</td>
            <td style="{value_style}">{rain_label}</td>
          </tr>
          <tr>
            <td style="{label_style}">최고기온</td>
            <td style="{value_style}">{weather['temp_max']:.1f}°C</td>
          </tr>
          <tr>
            <td style="{label_style}">최저기온</td>
            <td style="{value_style}">{weather['temp_min']:.1f}°C</td>
          </tr>
          <tr>
            <td style="{label_style}">PM10</td>
            <td style="{value_style}">{weather['pm10']:.1f} μg/m³ &nbsp;{pm10_badge}</td>
          </tr>
          <tr>
            <td style="{last_label_style}">PM2.5</td>
            <td style="{last_value_style}">{weather['pm2_5']:.1f} μg/m³ &nbsp;{pm2_5_badge}</td>
          </tr>
        </table>
      </td>
    </tr>
    <tr>
      <td style="padding:12px 4px;text-align:center;color:#999;font-size:11px;">
        teruterubozu · 자동 발송
      </td>
    </tr>
  </table>
</body>
</html>"""


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

    html_body = _build_html(weather, subject, pm10_grade, pm2_5_grade)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(gmail_user, gmail_app_password)
        smtp.sendmail(gmail_user, to_email, msg.as_string())

    print(f"[notifier] Email sent to {to_email}")
