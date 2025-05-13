# weather_client/main.py
import argparse
from weather_client.api_client import get_weather

def main():
    parser = argparse.ArgumentParser(description='Get current weather data for a city.')
    parser.add_argument('city_name', help='The name of the city')
    args = parser.parse_args()
    
    weather_data = get_weather(args.city_name)
    if weather_data:
        print(f"Weather in {args.city_name}:")
        print(f"Temperature: {weather_data['main']['temp']}°C")
        print(f"Description: {weather_data['weather'][0]['description']}")
        print(f"Humidity: {weather_data['main']['humidity']}%")
        print(f"Wind Speed: {weather_data['wind']['speed']} m/s")
    else:
        print(f"Could not retrieve weather data for {args.city_name}")

if __name__ == '__main__':
    main()
