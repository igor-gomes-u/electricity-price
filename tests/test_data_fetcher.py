import requests

from application.data_fetcher import get_elpris_data_from_api


def test_get_elpris_data_from_api_success(monkeypatch):
    class _Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"key": "value"}

    monkeypatch.setattr(requests, "get", lambda _url, **_kwargs: _Response())

    status, data = get_elpris_data_from_api("https://example.test/api/data")
    assert status == "ok"
    assert data == {"key": "value"}


def test_get_elpris_data_from_api_invalid_json_returns_upstream_error(monkeypatch):
    class _Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            raise ValueError("Invalid JSON")

    monkeypatch.setattr(requests, "get", lambda _url, **_kwargs: _Response())

    status, data = get_elpris_data_from_api("https://example.test/api/data")

    assert status == "upstream_error"
    assert data is None


def test_get_elpris_data_from_api_404_returns_no_data_yet(monkeypatch):
    class _Response:
        status_code = 404

        def raise_for_status(self):
            raise requests.exceptions.HTTPError("Status code: 404", response=self)

        def json(self):
            return {"error": "Not Found"}

    monkeypatch.setattr(requests, "get", lambda _url, **_kwargs: _Response())

    status, data = get_elpris_data_from_api("https://example.test/api/data")
    assert status == "no_data_yet"
    assert data is None


def test_get_elpris_data_from_api_http_error_non_404_returns_upstream_error(monkeypatch):
    class _Response:
        status_code = 500

        def raise_for_status(self):
            raise requests.exceptions.HTTPError("Status code: 500", response=self)

        def json(self):
            return {"error": "Server Error"}

    monkeypatch.setattr(requests, "get", lambda _url, **_kwargs: _Response())

    status, data = get_elpris_data_from_api("https://example.test/api/data")
    assert status == "upstream_error"
    assert data is None


def test_get_elpris_data_from_api_request_exception(monkeypatch):
    monkeypatch.setattr(
        requests,
        "get",
        lambda _url, **_kwargs: (_ for _ in ()).throw(requests.exceptions.RequestException()),
    )

    status, data = get_elpris_data_from_api("https://example.test/api/data")
    assert status == "upstream_error"
    assert data is None
