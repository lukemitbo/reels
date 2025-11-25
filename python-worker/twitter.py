import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
load_dotenv()
url = "https://api.twitterapi.io/twitter/tweet/advanced_search"
API_KEY = os.getenv("TWITTERAPIIO_API_KEY")
HEADERS = {
  'X-API-KEY': API_KEY,
  'Content-Type': 'application/json'
}
def get_tweets(query: str) -> list[str]:
    cursor = None
    tweets = []
    for i in range(3):
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        query_url = f"{url}?query={query} since:{yesterday}PST lang:en&queryType=Top"
        if cursor:
            query_url += f"&cursor={cursor}"
        response = requests.request("GET", query_url, headers=HEADERS)
        tweets.extend([tweet["text"][:300] for tweet in response.json()["tweets"]])
        cursor = response.json()["next_cursor"]
    return tweets

if __name__ == "__main__":
    tweets = get_tweets("ai news")
    print(tweets)