# File content goes here

from weather_app.api_client import WeatherApiClient
from unittest.mock import patch
import pytest

@patch('weather_app.api_client.requests.get')
def test_get_weather_success(mock_get):
    # Mock the response from the API call
    mock_response = {
        "json": {
            "coord": {"lon": -0.12574, "lat": 51.5074}, "weather": [{\"id": 803, "main": "clouds\