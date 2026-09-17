import logging
import socket
import time

from flask import Flask, Response, g, render_template, request, url_for
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from application.date_utils import get_default_form_field_values, get_min_max_allowed_dates, validate_date
from application.electricity_price_data import fetch_and_process_elpris_data
from application.electricity_price_visualization import create_chart, create_pandas_table
from application.menu_options import menu_options
from application.user_input import get_user_input

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

HTTP_REQUESTS = Counter(
    "app_http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "http_status"],
)

HTTP_LATENCY = Histogram(
    "app_request_latency_seconds",
    "HTTP request latency (seconds)",
    ["endpoint"],
)

UPSTREAM_REQUESTS = Counter(
    "app_upstream_requests_total",
    "Total number of upstream requests (result)",
    ["result"],
)


@app.before_request
def _metrics_start_timer():
    g._start_time = time.perf_counter()


@app.after_request
def _metrics_record(response):
    try:
        elapsed = time.perf_counter() - getattr(g, "_start_time", time.perf_counter())
        endpoint = request.endpoint or "unknown"
        HTTP_LATENCY.labels(endpoint=endpoint).observe(elapsed)
        HTTP_REQUESTS.labels(method=request.method, endpoint=endpoint, http_status=response.status_code).inc()
    except Exception:
        logger.exception("Failed to record metrics")
    return response


@app.get("/healthz")
def healthz():
    return "ok", 200


@app.get("/readyz")
def readyz():
    try:
        with socket.create_connection(("www.elprisetjustnu.se", 443), timeout=1):
            return "ready", 200
    except OSError:
        return "not ready", 503


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.get("/")
def index():
    min_date, next_day = get_min_max_allowed_dates()
    year, month, day, price_class = get_default_form_field_values()
    return render_template(
        "index.html",
        year=year,
        month=month,
        day=day,
        price_class=price_class,
        menu_options=menu_options,
        min_date=min_date,
        next_day=next_day,
    )


@app.post("/calculate")
def calculate_prices():
    try:
        year, month, day, price_class = get_user_input()
    except ValueError as exc:
        return (
            render_template(
                "message.html",
                title="Invalid price area",
                message=str(exc),
                severity="danger",
                back_url=url_for("index"),
            ),
            422,
        )

    validation_error = validate_date(year, month, day)
    if validation_error:
        message, status = validation_error
        return (
            render_template(
                "message.html",
                title="Invalid date",
                message=message,
                severity="danger",
                back_url=url_for("index"),
            ),
            status,
        )

    current_prices, date, err = fetch_and_process_elpris_data(
        year,
        month,
        day,
        price_class,
    )

    upstream_result = "ok" if err is None else err
    UPSTREAM_REQUESTS.labels(result=upstream_result).inc()

    if err == "no_data_yet":
        return (
            render_template(
                "message.html",
                title="Electricity price data not available yet",
                message=(
                    "Electricity price data for the next day becomes available after 13:00. Please try again later."
                ),
                severity="warning",
                back_url=url_for("index"),
            ),
            503,
        )

    if err == "upstream_error":
        return (
            render_template(
                "message.html",
                title="Temporary error",
                message="Could not fetch electricity price data at the moment. Please try again later.",
                severity="danger",
                back_url=url_for("index"),
            ),
            502,
        )

    prices = current_prices["Corresponding price (kr/kWh)"]
    stats = {
        "avg": round(prices.mean(), 3),
        "min": round(prices.min(), 3),
        "max": round(prices.max(), 3),
        "min_time": current_prices.loc[prices.idxmin(), "Time of day (hh:mm)"],
        "max_time": current_prices.loc[prices.idxmax(), "Time of day (hh:mm)"],
    }

    return render_template(
        "result.html",
        date=date,
        price_class=price_class,
        current_prices=current_prices,
        error_message=None,
        pandas_table=create_pandas_table(current_prices),
        chart_html=create_chart(current_prices, date, price_class),
        stats=stats,
    )


@app.errorhandler(404)
def handle_not_found_error(_error):
    return (
        render_template(
            "message.html",
            title="Page not found",
            message="The page you are trying to access does not exist.",
            severity="warning",
            back_url=url_for("index"),
        ),
        404,
    )


@app.errorhandler(413)
def handle_request_entity_too_large(_error):
    return (
        render_template(
            "message.html",
            title="Request too large",
            message="The submitted request exceeds the allowed size.",
            severity="danger",
            back_url=url_for("index"),
        ),
        413,
    )


@app.errorhandler(500)
def handle_internal_server_error(error):
    details = str(error) if app.debug else None
    return (
        render_template(
            "message.html",
            title="Internal server error",
            message="An unexpected error occurred. Please try again later.",
            details=details,
            severity="danger",
            back_url=url_for("index"),
        ),
        500,
    )


if __name__ == "__main__":
    app.run()
