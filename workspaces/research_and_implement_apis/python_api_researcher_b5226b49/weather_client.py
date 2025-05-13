# weather_client.py
# This file contains the main Weather Client implementation
import requests
import json

class WeatherClient:
    def __init__(self, city_name):
        self.city_name = city_name
        self.api_key = 'YOUR_OPENWEATHERMAP_API_KEY'
        # Replace 'YOUR_OPENWEATHERMAP_API_KEY' with your actual API key.  Get one at https://openweathermap.org/

    def get_weather_data(self):
        """Fetches current weather data from OpenWeatherMap."""
        url = f'http://api.openweathermap.org/data/2.5/weather?q={self.city_name}&appid={self.api_key}&units=metric'
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            return None

    def display_weather(self):
        """Displays the weather data in a user-friendly format."""
        weather_data = self.get_weather_data()
        if weather_data:
            print(f"Weather in {self.city_name}:")
            print(f"Temperature: {weather_data['main']['temp']}°C")
            print(f"Humidity: {weather_data['main']['humidity']}%")
            print(f"Description: {weather_data['weather'][0]['description']}")
            print(f"Wind Speed: {weather_data['wind']['speed']} m/s")
        else:
            print("Could not retrieve weather data.")


if __name__ == '__main__':
    city = input("Enter city name: ")
    client = WeatherClient(city)
    client.display_weather()"""

