# news_client.py
import requests
import json

def fetch_headlines(topic, api_key):
    """Fetches news headlines for a given topic from NewsAPI.org.

    Args:
        topic (str): The topic to search for news headlines.
        api_key (str): Your NewsAPI.org API key.

    Returns:
        list: A list of news headlines, or None if an error occurred.
    """
    url = f'https://newsapi.org/v2/top-headlines?q={topic}&apiKey={api_key}'
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        headlines = [item['title'] for item in data['articles']]
        return headlines
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None
    except (KeyError, TypeError) as e:
        print(f"Error parsing API response: {e}")
        return None

if __name__ == '__main__':
    # Example Usage
    api_key = "YOUR_NEWSAPI_API_KEY"  # Replace with your actual API key
    topic = "technology"
    headlines = fetch_headlines(topic, api_key)
    if headlines:
        print(f"News Headlines for '{topic}':")
        for headline in headlines:
            print(f"- {headline}")
    else:
        print("Failed to fetch headlines.")