"""
Weather tool — function-based, matching the pattern used elsewhere
(soil_tool, csv_tool). Entry point expected by src/agents/llm_router.py
is get_weather_summary(latitude, longitude).
"""

from src.services.weather_service import get_weather


def get_weather_summary(latitude: float, longitude: float) -> dict:
    data = get_weather(latitude, longitude)
    current = data["current"]

    return {
        "temperature": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "weather_code": current.get("weather_code"),
        "precipitation": current.get("precipitation", 0),
        "wind_speed": current.get("wind_speed_10m", 0),
    }