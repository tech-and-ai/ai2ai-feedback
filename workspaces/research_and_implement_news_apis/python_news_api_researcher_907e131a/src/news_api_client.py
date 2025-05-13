# news_api_client.py
# This module handles communication with the News API.
# It makes requests, parses the response, and handles errors.

def fetch_news(topic, api_key):
    """Fetches news headlines for a given topic from the News API.

    Args:
        topic (str): The news topic to search for.
        api_key (str): Your News API key.

    Returns:
        list: A list of news headlines.
    """
    try:
        url = f'https://newsapi.org/v2/top-headlines?q={topic}&pageSize=5&apiKey={api_key}'
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        headlines = [item['title'] for item in data['articles']]
        return headlines
    except requests.exceptions.RequestException as e:
        logging.error(f'Request error: {e}')
        return []
    except KeyError as e:
        logging.error(f'Key error in JSON response: {e}')
        return []
    except Exception as e:
        logging.error(f'An unexpected error occurred: {e}')
        return []
