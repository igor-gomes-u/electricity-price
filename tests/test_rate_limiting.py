import pandas as pd
import pytest

from application.app import app

VALID_FORM_DATA = {
    "year": "2022",
    "month": "11",
    "day": "1",
    "price_class": "SE3",
}


@pytest.fixture
def client():
    return app.test_client()


def _fake_fetch_and_process_elpris_data(year, month, day, price_class):
    return (
        pd.DataFrame(
            {
                "Time of day (hh:mm)": ["00:00", "01:00"],
                "Corresponding price (kr/kWh)": [0.1, 0.2],
            }
        ),
        "2022-11-01",
        None,
    )


def test_calculate_allows_requests_within_rate_limit(client, monkeypatch):
    monkeypatch.setattr(
        "application.app.fetch_and_process_elpris_data",
        _fake_fetch_and_process_elpris_data,
    )

    for _ in range(10):
        response = client.post(
            "/calculate",
            data=VALID_FORM_DATA,
            environ_base={"REMOTE_ADDR": "192.0.2.10"},
        )

        assert response.status_code == 200


def test_calculate_returns_429_after_rate_limit_is_exceeded(client, monkeypatch):
    monkeypatch.setattr(
        "application.app.fetch_and_process_elpris_data",
        _fake_fetch_and_process_elpris_data,
    )

    for _ in range(10):
        response = client.post(
            "/calculate",
            data=VALID_FORM_DATA,
            environ_base={"REMOTE_ADDR": "192.0.2.11"},
        )

        assert response.status_code == 200

    response = client.post(
        "/calculate",
        data=VALID_FORM_DATA,
        environ_base={"REMOTE_ADDR": "192.0.2.11"},
    )

    assert response.status_code == 429


def test_rate_limit_response_contains_safe_message(client, monkeypatch):
    monkeypatch.setattr(
        "application.app.fetch_and_process_elpris_data",
        _fake_fetch_and_process_elpris_data,
    )

    for _ in range(10):
        client.post(
            "/calculate",
            data=VALID_FORM_DATA,
            environ_base={"REMOTE_ADDR": "192.0.2.12"},
        )

    response = client.post(
        "/calculate",
        data=VALID_FORM_DATA,
        environ_base={"REMOTE_ADDR": "192.0.2.12"},
    )

    text = response.get_data(as_text=True)

    assert response.status_code == 429
    assert "Too many requests" in text
    assert "Please wait a moment and try again." in text
    assert "Traceback" not in text


def test_health_endpoint_is_not_rate_limited(client):
    for _ in range(12):
        response = client.get(
            "/healthz",
            environ_base={"REMOTE_ADDR": "192.0.2.13"},
        )

        assert response.status_code == 200
        assert response.get_data(as_text=True) == "ok"


def test_forwarded_for_header_does_not_bypass_rate_limit(client, monkeypatch):
    monkeypatch.setattr(
        "application.app.fetch_and_process_elpris_data",
        _fake_fetch_and_process_elpris_data,
    )

    for request_number in range(10):
        response = client.post(
            "/calculate",
            data=VALID_FORM_DATA,
            headers={
                "X-Forwarded-For": f"198.51.100.{request_number + 1}",
            },
            environ_base={"REMOTE_ADDR": "192.0.2.14"},
        )

        assert response.status_code == 200

    response = client.post(
        "/calculate",
        data=VALID_FORM_DATA,
        headers={"X-Forwarded-For": "203.0.113.99"},
        environ_base={"REMOTE_ADDR": "192.0.2.14"},
    )

    assert response.status_code == 429
