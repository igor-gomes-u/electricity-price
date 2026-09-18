import math

import pandas as pd
import plotly.graph_objects as go


def create_pandas_dataframe(elpris_data: list[dict]) -> pd.DataFrame:
    if not isinstance(elpris_data, list) or len(elpris_data) < 24:
        raise ValueError("Expected at least 24 hourly entries from the upstream API")

    current_prices = []

    for hour, entry in enumerate(elpris_data[:24]):
        if not isinstance(entry, dict):
            raise ValueError("Each hourly entry must be an object")

        if "SEK_per_kWh" not in entry:
            raise ValueError("Each hourly entry must contain SEK_per_kWh")

        price = entry["SEK_per_kWh"]

        if isinstance(price, bool) or not isinstance(price, (int, float)):
            raise ValueError("SEK_per_kWh must be numeric")

        if isinstance(price, float) and not math.isfinite(price):
            raise ValueError("SEK_per_kWh must be finite")

        current_prices.append((hour, price))

    return pd.DataFrame(
        {
            "Time of day (hh:mm)": [f"{hour:02d}:00" for hour, _ in current_prices],
            "Corresponding price (kr/kWh)": [price for _, price in current_prices],
        }
    )


def create_pandas_table(current_prices: pd.DataFrame) -> str:
    return current_prices.to_html(
        classes="table table-bordered table-striped",
        justify="left",
        index=False,
        escape=True,
    )


def create_chart(current_prices: pd.DataFrame, date: str, price_class: str) -> str:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=current_prices["Time of day (hh:mm)"],
            y=current_prices["Corresponding price (kr/kWh)"],
            mode="lines",
        )
    )

    fig.update_layout(
        title=f"Date: {date}<br>Price area: {price_class}",
        xaxis_title="Time of day (hh:mm)",
        yaxis_title="Corresponding price (kr/kWh)",
    )

    return fig.to_html(full_html=False)
