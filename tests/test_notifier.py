from unittest.mock import MagicMock, patch

import pytest

from backend.notifier import send_daily_report

_ENV = {
    "GMAIL_USER": "test@gmail.com",
    "GMAIL_APP_PASSWORD": "test_app_password",
    "NOTIFY_TO_EMAIL": "recipient@example.com",
}

_WEATHER_RAIN = {"rain": True, "temp_max": 20.0, "temp_min": 10.0, "pm10": 25.0, "pm2_5": 12.0}
_WEATHER_CLEAR = {"rain": False, "temp_max": 28.0, "temp_min": 18.0, "pm10": 15.0, "pm2_5": 8.0}


@pytest.fixture(autouse=True)
def env(monkeypatch):
    for k, v in _ENV.items():
        monkeypatch.setenv(k, v)


def _make_smtp_mock() -> MagicMock:
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)
    return mock_smtp


# --- SMTP connection and auth ---

@patch("backend.notifier.smtplib.SMTP")
def test_smtp_connects_to_gmail(mock_smtp_cls):
    mock_smtp_cls.return_value = _make_smtp_mock()
    send_daily_report(_WEATHER_RAIN)
    mock_smtp_cls.assert_called_once_with("smtp.gmail.com", 587)


@patch("backend.notifier.smtplib.SMTP")
def test_starttls_called(mock_smtp_cls):
    mock_smtp = _make_smtp_mock()
    mock_smtp_cls.return_value = mock_smtp
    send_daily_report(_WEATHER_RAIN)
    mock_smtp.starttls.assert_called_once()


@patch("backend.notifier.smtplib.SMTP")
def test_login_uses_credentials(mock_smtp_cls):
    mock_smtp = _make_smtp_mock()
    mock_smtp_cls.return_value = mock_smtp
    send_daily_report(_WEATHER_RAIN)
    mock_smtp.login.assert_called_once_with("test@gmail.com", "test_app_password")


# --- Email delivery ---

@patch("backend.notifier.smtplib.SMTP")
def test_sendmail_to_correct_recipient(mock_smtp_cls):
    mock_smtp = _make_smtp_mock()
    mock_smtp_cls.return_value = mock_smtp
    send_daily_report(_WEATHER_RAIN)
    args, _ = mock_smtp.sendmail.call_args
    assert args[0] == "test@gmail.com"
    assert args[1] == "recipient@example.com"


@patch("backend.notifier.smtplib.SMTP")
def test_subject_contains_rain_label_when_rain(mock_smtp_cls):
    import email
    from email.header import decode_header

    mock_smtp = _make_smtp_mock()
    mock_smtp_cls.return_value = mock_smtp
    send_daily_report(_WEATHER_RAIN)
    args, _ = mock_smtp.sendmail.call_args
    msg = email.message_from_string(args[2])
    raw_subject = msg["Subject"]
    decoded_parts = decode_header(raw_subject)
    subject = "".join(
        part.decode(enc or "utf-8") if isinstance(part, bytes) else part
        for part, enc in decoded_parts
    )
    assert "비 예보" in subject


@patch("backend.notifier.smtplib.SMTP")
def test_subject_no_rain_label_when_clear(mock_smtp_cls):
    import email
    from email.header import decode_header

    mock_smtp = _make_smtp_mock()
    mock_smtp_cls.return_value = mock_smtp
    send_daily_report(_WEATHER_CLEAR)
    args, _ = mock_smtp.sendmail.call_args
    msg = email.message_from_string(args[2])
    raw_subject = msg["Subject"]
    decoded_parts = decode_header(raw_subject)
    subject = "".join(
        part.decode(enc or "utf-8") if isinstance(part, bytes) else part
        for part, enc in decoded_parts
    )
    assert "비 예보" not in subject


@patch("backend.notifier.smtplib.SMTP")
def test_body_contains_weather_fields(mock_smtp_cls):
    import base64
    import email

    mock_smtp = _make_smtp_mock()
    mock_smtp_cls.return_value = mock_smtp
    send_daily_report(_WEATHER_RAIN)
    args, _ = mock_smtp.sendmail.call_args
    msg = email.message_from_string(args[2])
    payload = base64.b64decode(msg.get_payload()).decode("utf-8")
    assert "최고기온" in payload
    assert "최저기온" in payload
    assert "PM10" in payload or "미세먼지" in payload
    assert "PM2.5" in payload or "초미세먼지" in payload


# --- Logging ---

@patch("backend.notifier.smtplib.SMTP")
def test_prints_recipient_on_success(mock_smtp_cls, capsys):
    mock_smtp_cls.return_value = _make_smtp_mock()
    send_daily_report(_WEATHER_RAIN)
    assert "recipient@example.com" in capsys.readouterr().out
