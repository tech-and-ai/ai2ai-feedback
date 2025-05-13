# weather_client/api_client.py
import requests
import json

def get_weather(city_name):
    """Fetches current weather data for a given city from OpenWeatherMap.

    Args:
        city_name (str): The name of the city.

    Returns:
        dict: A dictionary containing the weather data, or None if an error occurred.
    """
    base_url = 'http://api.openweathermap.org/data/2.5/weather'
    params = {
        'q': city_name,
        'appid': 'YOUR_API_KEY',  # Replace with your API key
        'units': 'metric'
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return None
