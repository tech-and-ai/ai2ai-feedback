# File content goes here

import requests
import json

class WeatherApiClient:
    def __init__(self):
        self.api_key = "YOUR_API_KEY"  # Replace with your actual API key
        self.api_url = f"http://api.openweathermap.org/data/2.5/weather?q={}\&appid={}&units=metric" # Using OpenWeatherMap

    def get_weather(self, city_name):
        """Fetches weather data for a given city."""
        try:
            url = self.api_url.format(city_name, self.api_key)
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            return WeatherDataModel(data)
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None


class WeatherDataModel:
    def __init__(self, data):
        self.temperature = data.get("main\