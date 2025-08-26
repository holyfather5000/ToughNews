import json
import os
from datetime import datetime

ARTICLES_FILE = "articles.json"

def load_existing_articles():
    """Load current articles.json if it exists."""
    if os.path.exists(ARTICLES_FILE):
        with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_articles(articles):
    """Save merged articles to articles.json."""
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

def fetch_new_articles():
    """
    Replace this with your logic that fetches or creates new articles.
    Right now it just returns an empty list to demonstrate.
    """
    return []

def main():
    existing = load_existing_articles()
    new = fetch_new_articles()

    if not new:
        print("⚠️ No new articles found. Keeping existing ones.")
        return

    # avoid duplicates by URL or title
    seen = {a["url"] for a in existing if "url" in a}
    merged = existing[:]

    for article in new:
        if article.get("url") not in seen:
            merged.append(article)
            seen.add(article.get("url"))

    save_articles(merged)
    print(f"✅ Articles updated. Total now: {len(merged)}")

if __name__ == "__main__":
    main()
