# weather_client/tests/test_api_client.py
import unittest
from weather_client.api_client import get_weather

class TestApiClient(unittest.TestCase):

    def test_get_weather_success(self):
        # Replace with a valid API key for testing
        data = {
            'coord': {'lon': -37.8136, 'lat': -6.174056'},
            'weather': [{
                'id': 803, 
                'main': 'clouds',
                'description': 'broken clouds',
                'icon': '03d'
            }],
            'base': 'sensors',
            'main': {
                'temp': 28.37,
                'feels_like': 27.38,
                'temp_min': 27.74,
                'temp_max': 28.74,
                'pressure': 1016,
                'sea_level': 1016,
                'humidity': 73
            },
            'visibility': 1000,
            'wind': {
                'speed': 4.86,
                'deg': 113.38
            },
            'clouds': {
                'all': 40
            },
            'dt': 1678886400,
            'sys': {
                'type': 2,
                'id': 2074050,
                'country': 'US',
                'sunrise': 1678875446,
                'sunset': 1678899631
            },
            'name': 'London',
            'id': 2643708,
            'cod': 200
        }
        )
        result = get_weather('London')
        self.assertEqual(result, data)

    def test_get_weather_failure(self):
        # Simulate a failure (e.g., invalid API key or network error)
        result = get_weather('NonExistentCity')
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()