import json
import os
from datetime import datetime
import feedparser

ARTICLES_FILE = "articles.json"

FEEDS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://feedx.net/rss/ap.xml",
    "https://www.euronews.com/rss",
    "https://time.com/feed/",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://www.cbc.ca/webfeed/rss/rss-topstories",
    "https://globalnews.ca/feed/",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.npr.org/rss/rss.php?id=1001",
    "https://reliefweb.int/updates/rss.xml",
    "https://www.odditycentral.com/feed",
    "https://www.huffpost.com/section/weird-news/feed",
]

def load_existing_articles():
    if os.path.exists(ARTICLES_FILE):
        with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_articles(articles):
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

def fetch_new_articles():
    articles = []
    for feed_url in FEEDS:
        d = feedparser.parse(feed_url)
        for entry in d.entries[:20]:  # get top 20 instead of 10
            article = {
                "title": entry.get("title", "No Title"),
                "url": entry.get("link", ""),
                "date": (
                    entry.get("published")
                    or entry.get("updated")
                    or datetime.utcnow().isoformat()
                ),
                "shown": False,  # default hidden
            }
            articles.append(article)
    return articles

def main():
    existing = load_existing_articles()
    seen_urls = {a["url"] for a in existing if "url" in a}

    new_articles = fetch_new_articles()
    added_count = 0

    for article in new_articles:
        if article["url"] and article["url"] not in seen_urls:
            existing.append(article)
            seen_urls.add(article["url"])
            added_count += 1

    # sort newest first
    existing.sort(key=lambda x: x.get("date", ""), reverse=True)

    save_articles(existing)
    print(f"✅ Added {added_count} new articles. Total now: {len(existing)}")

if __name__ == "__main__":
    main()
