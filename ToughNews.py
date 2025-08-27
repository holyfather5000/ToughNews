import json
import os
import sys
from datetime import datetime
import feedparser

ARTICLES_FILE = "archive.json"

# List of RSS feeds
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
    # Odd / Weird feeds
    "https://www.odditycentral.com/feed",
    "https://www.huffpost.com/section/weird-news/feed",
]


def load_existing_articles():
    if os.path.exists(ARTICLES_FILE):
        with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ Warning: archive.json was corrupted. Starting fresh.")
                return []
    return []


def save_articles(articles):
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)


def fetch_new_articles():
    articles = []
    for feed_url in FEEDS:
        try:
            d = feedparser.parse(feed_url)

            if d.bozo:
                print(f"⚠️ Error parsing {feed_url}: {d.bozo_exception}")

            for entry in d.entries[:10]:  # grab top 10 per feed
                published = (
                    entry.get("published")
                    or entry.get("updated")
                    or datetime.utcnow().isoformat()
                )
                article = {
                    "title": entry.get("title", "No Title"),
                    "url": entry.get("link", ""),
                    "date": published,
                    "shown": False,  # default: hidden
                }
                articles.append(article)

        except Exception as e:
            print(f"❌ Failed fetching {feed_url}: {e}", file=sys.stderr)

    return articles


def main():
    existing = load_existing_articles()
    seen = {a["url"] for a in existing if "url" in a}
    merged = existing[:]

    new_articles = fetch_new_articles()
    added_count = 0

    for article in new_articles:
        if article["url"] and article["url"] not in seen:
            merged.append(article)
            seen.add(article["url"])
            added_count += 1

    save_articles(merged)
    print(f"✅ Added {added_count} new articles. Total now: {len(merged)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Script crashed: {e}", file=sys.stderr)
        sys.exit(1)
