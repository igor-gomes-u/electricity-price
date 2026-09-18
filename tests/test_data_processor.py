import pandas as pd
import pytest

from application.electricity_price_data import fetch_and_process_elpris_data


def test_fetch_and_process_elpris_data_success(monkeypatch):
    def _fake_get_elpris_data_from_api(_api_url):
        data = [
            {"time_start": "2026-01-01T00:00:00+01:00", "SEK_per_kWh": 0.1},
            {"time_start": "2026-01-01T01:00:00+01:00", "SEK_per_kWh": 0.2},
        ] + [{"time_start": f"2026-01-01T{hour:02d}:00:00+01:00", "SEK_per_kWh": 0.3} for hour in range(2, 24)]
        return "ok", data

    monkeypatch.setattr(
        "application.electricity_price_data.get_elpris_data_from_api",
        _fake_get_elpris_data_from_api,
    )

    current_prices, date, err = fetch_and_process_elpris_data(2026, 1, 1, "SE3")

    assert err is None
    assert date == "2026-01-01"
    assert isinstance(current_prices, pd.DataFrame)
    assert len(current_prices) == 24


def test_fetch_and_process_elpris_data_no_data_yet(monkeypatch):
    monkeypatch.setattr(
        "application.electricity_price_data.get_elpris_data_from_api",
        lambda _api_url: ("no_data_yet", None),
    )

    current_prices, date, err = fetch_and_process_elpris_data(2025, 11, 3, "SE3")

    assert current_prices is None
    assert date is None
    assert err == "no_data_yet"


def test_fetch_and_process_elpris_data_upstream_error(monkeypatch):
    monkeypatch.setattr(
        "application.electricity_price_data.get_elpris_data_from_api",
        lambda _api_url: ("upstream_error", None),
    )

    current_prices, date, err = fetch_and_process_elpris_data(2025, 10, 7, "SE3")

    assert current_prices is None
    assert date is None
    assert err == "upstream_error"


def test_fetch_and_process_elpris_data_incomplete_payload_returns_upstream_error(monkeypatch):
    def _fake_get_elpris_data_from_api(_api_url):
        data = [
            {"time_start": "2026-01-01T00:00:00+01:00", "SEK_per_kWh": 0.1},
            {"time_start": "2026-01-01T01:00:00+01:00", "SEK_per_kWh": 0.2},
        ]
        return "ok", data

    monkeypatch.setattr(
        "application.electricity_price_data.get_elpris_data_from_api",
        _fake_get_elpris_data_from_api,
    )

    current_prices, date, err = fetch_and_process_elpris_data(2026, 1, 1, "SE3")

    assert current_prices is None
    assert date is None
    assert err == "upstream_error"


@pytest.mark.parametrize(
    "invalid_entry",
    [
        {"time_start": "2026-01-01T00:00:00+01:00"},
        {"SEK_per_kWh": 0.1},
        {"time_start": None, "SEK_per_kWh": 0.1},
        {"time_start": 123, "SEK_per_kWh": 0.1},
        {"time_start": "", "SEK_per_kWh": 0.1},
        {"time_start": "2026-01-01", "SEK_per_kWh": 0.1},
        {"time_start": "invalid timestamp", "SEK_per_kWh": 0.1},
        {
            "time_start": "2026-01-01T00:00:00+01:00",
            "SEK_per_kWh": "0.1",
        },
        {
            "time_start": "2026-01-01T00:00:00+01:00",
            "SEK_per_kWh": float("nan"),
        },
        {
            "time_start": "2026-01-01T00:00:00+01:00",
            "SEK_per_kWh": float("inf"),
        },
        {
            "time_start": "2026-01-01T00:00:00+01:00",
            "SEK_per_kWh": float("-inf"),
        },
    ],
)
def test_fetch_and_process_elpris_data_malformed_payload_returns_upstream_error(
    monkeypatch,
    invalid_entry,
):
    data = [
        {
            "time_start": f"2026-01-01T{hour:02d}:00:00+01:00",
            "SEK_per_kWh": 0.1,
        }
        for hour in range(24)
    ]
    data[0] = invalid_entry

    monkeypatch.setattr(
        "application.electricity_price_data.get_elpris_data_from_api",
        lambda _api_url: ("ok", data),
    )

    current_prices, date, err = fetch_and_process_elpris_data(
        2026,
        1,
        1,
        "SE3",
    )

    assert current_prices is None
    assert date is None
    assert err == "upstream_error"
