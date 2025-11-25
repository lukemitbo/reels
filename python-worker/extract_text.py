import requests
from bs4 import BeautifulSoup
import trafilatura

UA = "Mozilla/5.0 (compatible; AIReelsBot/1.0; +https://example.com/bot)"

def extract_from_html(html: str) -> str:
    # Primary: trafilatura (handles boilerplate well)
    text = trafilatura.extract(html, include_comments=False) or ""
    if len(text) >= 800:
        return text

    # Fallback: simple BeautifulSoup text extraction
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    return text

def fetch_and_extract(url: str, timeout: int = 12) -> str:
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
        resp.raise_for_status()
        return extract_from_html(resp.text)[:20000]
    except Exception:
        return ""

