import pandas as pd
import pytest

from application.app import app, handle_internal_server_error, handle_rate_limit_error


@pytest.fixture
def client():
    return app.test_client()


def test_home_page_method_get(client, get_text):
    response = client.get("/")
    assert response.status_code == 200
    assert "Electricity Price" in get_text(response)


def test_home_page_method_post(client, get_text):
    response = client.post("/")
    assert response.status_code == 405
    assert "Method Not Allowed" in get_text(response)


def test_invalid_date_calculation(client, get_text):
    response = client.post(
        "/calculate",
        data={"year": "2022", "month": "10", "day": "31", "price_class": "SE1"},
    )
    assert response.status_code == 422
    assert "Invalid date" in get_text(response)


def test_invalid_price_class_calculation(client, get_text):
    response = client.post(
        "/calculate",
        data={"year": "2022", "month": "11", "day": "1", "price_class": "SE9"},
    )
    assert response.status_code == 422
    text = get_text(response)
    assert "Invalid price area" in text


def test_malformed_date_input_calculation(client, get_text):
    response = client.post(
        "/calculate",
        data={"year": "abc", "month": "11", "day": "1", "price_class": "SE1"},
    )

    assert response.status_code == 422
    text = get_text(response)
    assert "Invalid price area" in text
    assert "Invalid date input." in text


def test_calculate_success_renders_result(client, monkeypatch, get_text):
    def _fake_fetch_and_process_elpris_data(year, month, day, price_class):
        df = pd.DataFrame(
            {
                "Time of day (hh:mm)": ["00:00", "01:00"],
                "Corresponding price (kr/kWh)": [0.1, 0.2],
            }
        )
        return df, "2022-11-01", None

    monkeypatch.setattr(
        "application.app.fetch_and_process_elpris_data",
        _fake_fetch_and_process_elpris_data,
    )

    response = client.post(
        "/calculate",
        data={"year": "2022", "month": "11", "day": "1", "price_class": "SE3"},
    )

    assert response.status_code == 200
    assert "Electricity Prices" in get_text(response)


def test_calculate_returns_no_data_yet_message(client, monkeypatch, get_text):
    def _fake_fetch_and_process_elpris_data(year, month, day, price_class):
        return None, None, "no_data_yet"

    monkeypatch.setattr(
        "application.app.fetch_and_process_elpris_data",
        _fake_fetch_and_process_elpris_data,
    )

    response = client.post(
        "/calculate",
        data={"year": "2022", "month": "11", "day": "1", "price_class": "SE3"},
    )

    assert response.status_code == 503
    text = get_text(response)
    assert "after 13:00" in text
    assert "Electricity price data not available yet" in text


def test_calculate_returns_upstream_error_message(client, monkeypatch, get_text):
    def _fake_fetch_and_process_elpris_data(year, month, day, price_class):
        return None, None, "upstream_error"

    monkeypatch.setattr(
        "application.app.fetch_and_process_elpris_data",
        _fake_fetch_and_process_elpris_data,
    )

    response = client.post(
        "/calculate",
        data={"year": "2022", "month": "11", "day": "1", "price_class": "SE3"},
    )

    assert response.status_code == 502
    text = get_text(response)
    assert "Temporary error" in text
    assert "Could not fetch electricity price data" in text


def test_invalid_endpoint(client, get_text):
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert "Page not found" in get_text(response) or "The page you are trying to access does not exist" in get_text(
        response
    )


def test_404_handler_returns_message(client, get_text):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert "The page you are trying to access does not exist." in get_text(response)


def test_internal_server_error(client):
    with app.test_request_context("/"):
        response, status = handle_internal_server_error(RuntimeError("boom"))

    assert status == 500
    assert "Internal server error" in response


def test_rate_limit_handler_returns_message():
    with app.test_request_context("/calculate"):
        response, status = handle_rate_limit_error(None)

    assert status == 429
    assert "Too many requests" in response
    assert "Please wait a moment and try again." in response


def test_calculate_rejects_oversized_request_before_upstream(client, monkeypatch, get_text):
    def _unexpected_upstream_call(*_args, **_kwargs):
        pytest.fail("The upstream service must not be called for an oversized request.")

    monkeypatch.setattr(
        "application.app.fetch_and_process_elpris_data",
        _unexpected_upstream_call,
    )

    response = client.post(
        "/calculate",
        data={
            "year": "2022",
            "month": "11",
            "day": "1",
            "price_class": "SE3",
            "padding": "x" * (16 * 1024),
        },
    )

    assert response.status_code == 413

    text = get_text(response)
    assert "Request too large" in text
    assert "The submitted request exceeds the allowed size." in text
    assert "Traceback" not in text
