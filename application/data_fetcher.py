import logging

import requests

logger = logging.getLogger(__name__)


def get_elpris_data_from_api(api_url, timeout=5):
    try:
        response = requests.get(api_url, timeout=timeout)
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as exc:
            logger.warning("Upstream returned invalid JSON: %s", exc)
            return "upstream_error", None

        return "ok", data

    except requests.exceptions.HTTPError as exc:
        status_code = getattr(exc.response, "status_code", None)

        if status_code == 404:
            return "no_data_yet", None

        logger.warning("Upstream HTTP error: %s", exc)
        return "upstream_error", None

    except requests.exceptions.RequestException as exc:
        logger.warning("Upstream request failed: %s", exc)
        return "upstream_error", None
