import re

import pandas as pd
import pytest

from application.app import app


@pytest.fixture
def client():
    return app.test_client()


def test_healthz_ok(client, get_text):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert get_text(r) == "ok"


def test_readyz_ok(client, get_text, monkeypatch):
    class _Conn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("application.app.socket.create_connection", lambda *_a, **_kw: _Conn())

    r = client.get("/readyz")
    assert r.status_code == 200
    assert get_text(r) == "ready"


def test_metrics_exposes_custom_metrics(client, get_text):
    assert client.get("/").status_code == 200

    r = client.get("/metrics")
    assert r.status_code == 200

    text = get_text(r)
    assert "app_http_requests_total" in text
    assert "app_request_latency_seconds" in text

    m = re.search(r"app_http_requests_total\{.*\}\s+(\d+(\.\d+)?)", text)
    assert m is not None


def test_metrics_latency_has_healthz_label(client, get_text):
    client.get("/healthz")

    r = client.get("/metrics")
    assert r.status_code == 200
    text = get_text(r)

    assert (
        re.search(
            r'app_request_latency_seconds_(count|sum)\{endpoint="healthz"\}',
            text,
        )
        is not None
    )


def test_metrics_enabled_by_default_when_unset(client, get_text, monkeypatch):
    monkeypatch.delenv("METRICS_ENABLED", raising=False)

    r = client.get("/metrics")
    assert r.status_code == 200
    assert r.mimetype == "text/plain"


def test_metrics_enabled_explicit_true(client, get_text, monkeypatch):
    monkeypatch.setenv("METRICS_ENABLED", "true")

    r = client.get("/metrics")
    assert r.status_code == 200


def test_metrics_disabled_returns_404(client, get_text, monkeypatch):
    monkeypatch.setenv("METRICS_ENABLED", "false")

    r = client.get("/metrics")
    assert r.status_code == 404

    text = get_text(r)
    assert "Page not found" in text
    assert "Traceback" not in text


def test_metrics_disabled_is_case_insensitive(client, monkeypatch):
    monkeypatch.setenv("METRICS_ENABLED", "FALSE")

    r = client.get("/metrics")
    assert r.status_code == 404


def test_metrics_disabled_does_not_expose_prometheus_output(client, get_text, monkeypatch):
    monkeypatch.setenv("METRICS_ENABLED", "false")

    r = client.get("/metrics")
    text = get_text(r)

    assert "app_http_requests_total" not in text


def test_metrics_exposes_upstream_requests_total(client, get_text, monkeypatch):
    def _fake_fetch_and_process_elpris_data(year, month, day, price_class):
        df = pd.DataFrame(
            {
                "Time of day (hh:mm)": ["00:00"],
                "Corresponding price (kr/kWh)": [0.1],
            }
        )
        return df, "2022-11-01", None

    monkeypatch.setattr(
        "application.app.fetch_and_process_elpris_data",
        _fake_fetch_and_process_elpris_data,
    )

    r = client.post(
        "/calculate",
        data={"year": "2022", "month": "11", "day": "1", "price_class": "SE3"},
    )
    assert r.status_code == 200

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    text = get_text(metrics)

    assert "app_upstream_requests_total" in text
    assert re.search(r'app_upstream_requests_total\{result="ok"\}\s+\d+(\.\d+)?', text) is not None
