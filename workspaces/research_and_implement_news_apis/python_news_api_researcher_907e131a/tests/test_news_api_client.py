# test_news_api_client.py
# This module contains unit tests for the news_api_client.py module.

import unittest
from src.news_api_client import fetch_news
from src.utils.api_config import API_KEY

class TestNewsApiClient(unittest.TestCase):

    def test_fetch_news_success(self):
        # Mock API response
        mock_response = {
            'articles': [{
                'title': 'Test Headline'
            }] 
        }
        # Simulate fetching news
        headlines = fetch_news('test_topic', API_KEY)
        self.assertEqual(len(headlines), 1)
        self.assertEqual(headlines[0], 'Test Headline')

    def test_fetch_news_no_results(self):
        headlines = fetch_news('nonexistent_topic', API_KEY)
        self.assertEqual(len(headlines), 0)

    def test_fetch_news_error(self):
        # Mock an error response
        mock_response = {
            'error': 'Invalid API key'
        }

        with self.assertRaises(Exception):
            fetch_news('error_topic', API_KEY)
