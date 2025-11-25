import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

SEARCH_URL = "https://google.serper.dev/search"
NEWS_URL = "https://google.serper.dev/news"
API_KEY = os.getenv("SERPERDEV_API_KEY")

HEADERS = {
  'X-API-KEY': API_KEY,
  'Content-Type': 'application/json'
}
def get_news(query: str, time_frame):
    payload = json.dumps({
        "q": query,
        "tbs": f"qdr:{time_frame}"
    })
    response = requests.request("POST", NEWS_URL, data=payload, headers=HEADERS)
    return response.json()

def get_news_title_and_snippet(query: str, time_frame: str) -> list[tuple[str, str]]:
    results = get_news(query, time_frame)
    return [(result['title'], result['snippet']) for result in results['news']]

def get_search_results(query: str, time_frame: str) -> list[tuple[str, str]]:
    payload = json.dumps({
        "q": query,
        "tbs": f"qdr:{time_frame}"
    })
    response = requests.request("POST", SEARCH_URL, data=payload, headers=HEADERS)
    return response.json()

def get_search_result_links(query: str, time_frame: str) -> list[str]:
    results = get_search_results(query, time_frame)
    return [result['link'] for result in results['organic']]

if __name__ == "__main__":
    # ml_research = get_news_title_and_snippet("ml research", "w")
    # ai_tech = get_news_title_and_snippet("ai tech", "d")
    # print(ml_research)
    # print(ai_tech)

    search_links = get_search_result_links("ai news", "w")
    print(search_links)