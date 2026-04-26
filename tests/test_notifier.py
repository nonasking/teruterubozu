from unittest.mock import MagicMock, patch

import pytest

from backend.notifier import send_rain_alert

_ENV = {
    "GMAIL_USER": "test@gmail.com",
    "GMAIL_APP_PASSWORD": "test_app_password",
    "NOTIFY_TO_EMAIL": "recipient@example.com",
}


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
    send_rain_alert()
    mock_smtp_cls.assert_called_once_with("smtp.gmail.com", 587)


@patch("backend.notifier.smtplib.SMTP")
def test_starttls_called(mock_smtp_cls):
    mock_smtp = _make_smtp_mock()
    mock_smtp_cls.return_value = mock_smtp
    send_rain_alert()
    mock_smtp.starttls.assert_called_once()


@patch("backend.notifier.smtplib.SMTP")
def test_login_uses_credentials(mock_smtp_cls):
    mock_smtp = _make_smtp_mock()
    mock_smtp_cls.return_value = mock_smtp
    send_rain_alert()
    mock_smtp.login.assert_called_once_with("test@gmail.com", "test_app_password")


# --- Email delivery ---

@patch("backend.notifier.smtplib.SMTP")
def test_sendmail_to_correct_recipient(mock_smtp_cls):
    mock_smtp = _make_smtp_mock()
    mock_smtp_cls.return_value = mock_smtp
    send_rain_alert()
    args, _ = mock_smtp.sendmail.call_args
    assert args[0] == "test@gmail.com"
    assert args[1] == "recipient@example.com"


@patch("backend.notifier.smtplib.SMTP")
def test_email_body_contains_rain_warning(mock_smtp_cls):
    import base64
    import email

    mock_smtp = _make_smtp_mock()
    mock_smtp_cls.return_value = mock_smtp
    send_rain_alert()
    args, _ = mock_smtp.sendmail.call_args
    raw_message = args[2]
    msg = email.message_from_string(raw_message)
    payload = base64.b64decode(msg.get_payload()).decode("utf-8")
    assert "비" in payload
    assert "우산" in payload


# --- Logging ---

@patch("backend.notifier.smtplib.SMTP")
def test_prints_recipient_on_success(mock_smtp_cls, capsys):
    mock_smtp_cls.return_value = _make_smtp_mock()
    send_rain_alert()
    assert "recipient@example.com" in capsys.readouterr().out
