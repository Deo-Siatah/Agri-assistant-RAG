import requests

response = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={
        "latitude": -1.2921,
        "longitude": 36.8219,
        "current": "temperature_2m,relative_humidity_2m,weather_code"
    }
)

print(response.json())  # See what keys are actually returned