# File content goes here

def get_weather(city_name):
    """Fetches weather data for a given city."""
    try:
        api_client = WeatherApiClient()
        weather_data = api_client.get_weather(city_name)
        return weather_data
    except Exception as e:
        print(f"Error fetching weather for {city_name}: {e}")
        return None


def main():
    """Main function to handle user input and display weather information."""
    import argparse
    parser = argparse.ArgumentParser(description="Fetch weather data for a city.")
    parser.add_argument("city_name", help="The name of the city to fetch weather data for.")
    args = parser.parse_args()
    weather_data = get_weather(args.city_name)
    if weather_data:
        print(f"Current weather in {args.city_name}:")
        print(f"Temperature: {weather_data.temperature}°C")
        print(f"Condition: {weather_data.condition}")
        print(f"Humidity: {weather_data.humidity}%")
    else:
        print("Failed to fetch weather data.")

if __name__ == "__main__":
    main()
    