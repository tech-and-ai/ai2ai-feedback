# test_news_client.py
import unittest
from news_client import fetch_headlines

class TestNewsClient(unittest.TestCase):

    def test_fetch_headlines_success(self):
        # Mock API key and topic
        api_key = "YOUR_NEWSAPI_API_KEY" # Replace with a valid API key for testing
        topic = "technology"
        # Call the function
        headlines = fetch_headlines(topic, api_key)

        # Assert that the return value is a list
        self.assertIsInstance(headlines, list)
        # Assert that the list is not empty
        self.assertIsNotNone(headlines)

    def test_fetch_headlines_error_api_request(self):
        # Mock an API request error
        api_key = "YOUR_NEWSAPI_API_KEY" # Replace with a valid API key for testing
        topic = "technology"
        # Mock the requests.get() call to raise an exception
        with self.assertRaises(requests.exceptions.RequestException):
            fetch_headlines(topic, api_key)

if __name__ == '__main__':
    unittest.main()