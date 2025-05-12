# weather_parser.py

class WeatherParser:
    def display_weather(self, weather_data):
        try:
            print(f'Current Temperature: {weather_data["main"]["temp"]}°C')
            print(f'Condition: {weather_data["weather"][0]["description"]}')
            print('Forecast:')
            for i in range(3):
                print(f'  Day {i+1}: {weather_data['forecast']['list'][i]['weather'][0]["description"]} - {weather_data['forecast']['list'][i]['main']['temp']}°C')
        except KeyError as e:
            print(f'KeyError: {e}.  Data structure may have changed.')
        
