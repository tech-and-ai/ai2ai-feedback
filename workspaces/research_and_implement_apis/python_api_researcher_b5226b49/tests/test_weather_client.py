# tests/test_weather_client.py

import unittest
from weather_client import WeatherClient

class TestWeatherClient(unittest.TestCase):

    def test_get_weather_success(self):
        # Mock API response for successful retrieval
        mock_response = {
            'cod': '200',
            'message': 'OK',
            'main': {
                'temp': 25.5,
                'feels_like': 23.2,
                'temp_min': 22.1,
                'temp_max': 26.3
            },
            'weather': [{
                'id': 803,
                'main': 'Clear',
                'description': 'clear sky',
                'icon': '01d'
            }],
            'clouds': {
                'all': 0
            },
            'visibility': 1000,
            'wind': {
                'speed': 5.1,
                'deg': 16.0,
                'gust': 6.1
            },
            'rain': {
                'onehr': 0.0,
                'threehr': 0.0,
                'sixhr': 0.0,
                'twentyfourhr': 0.0
            },
            'snow': {
                'onehr': 0.0,
                'threehr': 0.0,
                'sixhr': 0.0,
                'twentyfourhr': 0.0
            },
            'dt': 1678886400,
            'id': 28920,
            'name': 'London',
            'sys': {
                'country': 'GB',
                'sunrise': 1678872800,
                'sunset': 1678898400
            },
            'timezone': 0,
            'visibility': 1000,
            'lat': 51.5074,
            'lon': 0.1278
        }
        client = WeatherClient("London")
        weather_data = client.get_weather_data()
        self.assertEqual(weather_data, client.get_weather_data())

    def test_get_weather_error(self):
        # Mock API error response
        client = WeatherClient("InvalidCity")
        weather_data = client.get_weather_data()
        self.assertIsNone(weather_data)

if __name__ == '__main__':
    unittest.main()
