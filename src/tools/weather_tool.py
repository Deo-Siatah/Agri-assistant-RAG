from src.services.weather_service import get_weather

class WeatherTool:

    def run(self, latitude, longitude):
        data = get_weather(latitude, longitude)
        current = data["current"]

        return {
            "temperature": current["temperature_2m"],
            "humidity": current["relative_humidity_2m"],
            "weather_code": current.get("weather_code"),  # Safe access
            "precipitation": current.get("precipitation", 0),  # Default to 0 if missing
            "wind_speed": current.get("wind_speed_10m", 0)  # Default to 0 if missing
        }