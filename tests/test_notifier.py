from unittest.mock import MagicMock, patch

import pytest

from backend.notifier import send_rain_alert

_ENV = {
    "TWILIO_ACCOUNT_SID": "ACtest123",
    "TWILIO_AUTH_TOKEN": "auth_token_test",
    "TWILIO_FROM_NUMBER": "+10000000000",
    "TWILIO_TO_NUMBER": "+821000000000",
}


@pytest.fixture(autouse=True)
def env(monkeypatch):
    for k, v in _ENV.items():
        monkeypatch.setenv(k, v)


def _setup_mock_client(mock_client_cls: MagicMock, sid: str = "SM_TEST") -> MagicMock:
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.sid = sid
    mock_client.messages.create.return_value = mock_message
    return mock_client


# --- Twilio client initialization ---

@patch("backend.notifier.Client")
def test_client_initialized_with_credentials(mock_client_cls):
    _setup_mock_client(mock_client_cls)
    send_rain_alert()
    mock_client_cls.assert_called_once_with("ACtest123", "auth_token_test")


# --- Message creation ---

@patch("backend.notifier.Client")
def test_message_sent_to_correct_number(mock_client_cls):
    mock_client = _setup_mock_client(mock_client_cls)
    send_rain_alert()
    mock_client.messages.create.assert_called_once_with(
        body="☔ 내일 비가 올 예정입니다. 우산을 챙기세요!",
        from_="+10000000000",
        to="+821000000000",
    )


@patch("backend.notifier.Client")
def test_message_body_contains_rain_warning(mock_client_cls):
    mock_client = _setup_mock_client(mock_client_cls)
    send_rain_alert()
    _, kwargs = mock_client.messages.create.call_args
    assert "비" in kwargs["body"]
    assert "우산" in kwargs["body"]


# --- Logging ---

@patch("backend.notifier.Client")
def test_prints_message_sid(mock_client_cls, capsys):
    _setup_mock_client(mock_client_cls, sid="SM_UNIQUE_SID")
    send_rain_alert()
    assert "SM_UNIQUE_SID" in capsys.readouterr().out
