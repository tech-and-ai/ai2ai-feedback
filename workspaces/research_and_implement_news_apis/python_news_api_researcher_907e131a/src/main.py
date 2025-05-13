# main.py
# This is the main script that orchestrates the news headline retrieval process.

import argparse
from src.news_api_client import fetch_news
from src.utils.api_config import API_KEY
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    parser = argparse.ArgumentParser(description='Fetch news headlines for a given topic.')
    parser.add_argument('topic', help='The news topic to search for.')
    args = parser.parse_args()

    headlines = fetch_news(args.topic, API_KEY)

    if headlines:
        print(f'News Headlines for "{args.topic}":')
        for headline in headlines:
            print(f'- {headline}')
    else:
        print(f'No news found for "{args.topic}".'
        )
