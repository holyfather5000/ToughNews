import json
import os
from datetime import datetime
import feedparser

ARTICLES_FILE = "articles.json"

# List of RSS feeds
FEEDS = [
    "https://rss.cbc.ca/lineup/topstories.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.reutersagency.com/feed/?best-topics=world&post_type=best",
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
        for entry in d.entries[:10]:  # grab top 10 per feed
            article = {
                "title": entry.get("title", "No Title"),
                "url": entry.get("link", ""),
                "date": entry.get("published", datetime.utcnow().isoformat()),
                "shown": False  # default: hidden
            }
            articles.append(article)
    return articles

def main():
    existing = load_existing_articles()
    seen = {a["url"] for a in existing if "url" in a}
    merged = existing[:]

    new_articles = fetch_new_articles()
    added_count = 0

    for article in new_articles:
        if article["url"] not in seen:
            merged.append(article)
            seen.add(article["url"])
            added_count += 1

    save_articles(merged)
    print(f"✅ Added {added_count} new articles. Total now: {len(merged)}")

if __name__ == "__main__":
    main()
