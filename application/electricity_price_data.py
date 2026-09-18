from datetime import datetime

from application.data_fetcher import get_elpris_data_from_api
from application.electricity_price_visualization import create_pandas_dataframe


def _build_api_url(year: int, month: int, day: int, price_class: str) -> str:
    return f"https://www.elprisetjustnu.se/api/v1/prices/{year}/{month:02d}-{day:02d}_{price_class}.json"


def extract_date_from_elpris_data(elpris_data: list[dict]) -> str:
    try:
        time_start = elpris_data[0]["time_start"]
    except (IndexError, KeyError, TypeError) as exc:
        raise ValueError("The first hourly entry must contain time_start") from exc

    if not isinstance(time_start, str) or not time_start.strip():
        raise ValueError("time_start must be a non-empty string")

    time_start = time_start.strip()

    if "T" not in time_start:
        raise ValueError("time_start must contain a date and time")

    try:
        timestamp = datetime.fromisoformat(time_start.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("time_start must be a valid ISO timestamp") from exc

    return timestamp.date().isoformat()


def fetch_and_process_elpris_data(year: int, month: int, day: int, price_class: str):
    api_url = _build_api_url(year, month, day, price_class)
    status, elpris_data = get_elpris_data_from_api(api_url)

    if status != "ok":
        return None, None, status

    try:
        current_prices = create_pandas_dataframe(elpris_data)
        date = extract_date_from_elpris_data(elpris_data)
    except ValueError:
        return None, None, "upstream_error"

    return current_prices, date, None
