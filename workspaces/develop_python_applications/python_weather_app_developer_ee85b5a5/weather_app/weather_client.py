# weather_client.py
import requests
import os

class WeatherClient:
    def __init__(self):
        self.api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
        if not self.api_key:
            raise ValueError('OPENWEATHERMAP_API_KEY environment variable not set.')

    def get_weather(self, city):
        base_url = 'http://api.openweathermap.org/data/2.5/weather?'
        url = base_url + 'q=' + city + '&appid=' + self.api_key + '&units=metric'
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print(f'Error fetching weather data: {e}')\            return None
        except Exception as e:
            print(f'An unexpected error occurred: {e}')\            return None
        
