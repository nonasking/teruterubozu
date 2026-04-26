import os
import smtplib
from email.mime.text import MIMEText


def send_rain_alert() -> None:
    """Send an email alert when rain is expected tomorrow."""
    gmail_user = os.environ["GMAIL_USER"]
    gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]
    to_email = os.environ["NOTIFY_TO_EMAIL"]

    subject = "☔ 내일 비 예보 - 우산을 챙기세요!"
    body = "내일 비가 올 예정입니다. 우산을 챙기세요!"

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
