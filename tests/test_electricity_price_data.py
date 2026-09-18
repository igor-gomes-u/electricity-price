import pandas as pd
import pytest

from application.electricity_price_data import (
    extract_date_from_elpris_data,
    fetch_and_process_elpris_data,
)


@pytest.mark.parametrize(
    "invalid_data",
    [
        [],
        [{}],
        [{"time_start": None}],
        [{"time_start": 123}],
        [{"time_start": ""}],
        [{"time_start": "2023-11-05"}],
        [{"time_start": "invalid timestamp"}],
    ],
)
def test_extract_date_from_elpris_data_raises_on_invalid_data(invalid_data):
    with pytest.raises(ValueError):
        extract_date_from_elpris_data(invalid_data)


def test_fetch_and_process_elpris_data_success(monkeypatch):
    def _fake_get_elpris_data_from_api(_api_url):
        data = [
            {"time_start": "2023-11-05T00:00:00Z", "SEK_per_kWh": 0.1},
            {"time_start": "2023-11-05T01:00:00Z", "SEK_per_kWh": 0.2},
        ] + [{"time_start": f"2023-11-05T{hour:02d}:00:00Z", "SEK_per_kWh": 0.3} for hour in range(2, 24)]
        return "ok", data

    monkeypatch.setattr(
        "application.electricity_price_data.get_elpris_data_from_api",
        _fake_get_elpris_data_from_api,
    )

    current_prices, date, err = fetch_and_process_elpris_data(2023, 11, 5, "SE3")

    assert err is None
    assert date == "2023-11-05"
    assert isinstance(current_prices, pd.DataFrame)
    assert len(current_prices) == 24


def test_fetch_and_process_elpris_data_no_data_yet(monkeypatch):
    monkeypatch.setattr(
        "application.electricity_price_data.get_elpris_data_from_api",
        lambda _api_url: ("no_data_yet", None),
    )

    current_prices, date, err = fetch_and_process_elpris_data(2023, 11, 5, "SE3")

    assert current_prices is None
    assert date is None
    assert err == "no_data_yet"


def test_fetch_and_process_elpris_data_upstream_error(monkeypatch):
    monkeypatch.setattr(
        "application.electricity_price_data.get_elpris_data_from_api",
        lambda _api_url: ("upstream_error", None),
    )

    current_prices, date, err = fetch_and_process_elpris_data(2023, 11, 5, "SE3")

    assert current_prices is None
    assert date is None
    assert err == "upstream_error"
