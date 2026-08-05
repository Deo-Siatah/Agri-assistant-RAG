"""
Weather service — calls Open-Meteo's forecast API.

Includes one automatic retry for transient 5xx errors, since Open-Meteo
occasionally returns brief 502/503/504 blips that succeed on a second try.
"""

import time

import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_SECONDS = 10
RETRY_DELAY_SECONDS = 1.5


class WeatherServiceError(Exception):
    """Raised when the weather API fails after retrying."""


def get_weather(latitude: float, longitude: float) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,weather_code,precipitation,wind_speed_10m",
    }

    last_error: Exception | None = None

    for attempt in range(2):  # one initial attempt + one retry
        try:
            response = requests.get(OPEN_METEO_URL, params=params, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            last_error = exc
            if status in (502, 503, 504) and attempt == 0:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            raise WeatherServiceError(f"Open-Meteo request failed: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            last_error = exc
            if attempt == 0:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            raise WeatherServiceError(f"Open-Meteo request failed: {exc}") from exc

    raise WeatherServiceError(f"Open-Meteo request failed after retry: {last_error}")