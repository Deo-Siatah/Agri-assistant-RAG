import requests

def get_weather(latitude, longitude):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&current=temperature_2m,relative_humidity_2m,weather_code,precipitation,wind_speed_10m"
    )

    response = requests.get(url)
    response.raise_for_status()
    return response.json()