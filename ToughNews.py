import feedparser
from textblob import TextBlob
import time
import json
import os
from datetime import datetime

# -----------------------
# Configuration
# -----------------------
rss_feeds = {
    "BBC News": "https://feeds.bbci.co.uk/news/rss.xml",
    "AP News": "https://feedx.net/rss/ap.xml",
    "Euronews": "https://www.euronews.com/rss",
    "Time": "https://time.com/feed/",
    "NY Times": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "CBC": "https://www.cbc.ca/webfeed/rss/rss-topstories",
    "Global News": "https://globalnews.ca/feed/",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "NPR News": "https://www.npr.org/rss/rss.php?id=1001",
    "ReliefWeb": "https://reliefweb.int/updates/rss.xml",
    # Odd / Weird feeds
    "Odd News": "https://www.odditycentral.com/feed",
    "HuffPost Weird": "https://www.huffpost.com/section/weird-news/feed",
}

odd_feeds = {"Odd News", "HuffPost Weird"}

bad_keywords = [
    "earthquake","war","killed","crash","explosion","riot","terror","bomb",
    "injury","injuries","injured","fatal","fatality","emergency","deadly",
    "attack","violence","warfare","abduction","assault","homicide","catastrophe",
    "evacuation","public harm","misinformation","rigging","forgery","bribery",
    "scam","collision","oil company","oil spill","death toll","deaths",
    "police clash","fatalities","hostage","drought","cyclone","famine","arson",
    "assassination","crimes","poison","tragic","tragedy","explosions",
    "earthquakes","shootings","have died","has died","been killed","deceased",
    "murder","crisis","disaster","pandemic","starvation","disease","outbreak",
    "terrorism","hurricane","tornado","felony","fire","dictator","scandal",
    "corruption","pollution","poverty","fraud","human trafficking","racism",
    "unemployment","suicide","North Korea",
]

exclude_keywords = [
    "film","movie","review","trailer","episode","series",
    "plot","music","concert","festival","art","exhibition",
    "author","fiction"
]

ARTICLES_FILE = "articles.json"
ARCHIVE_FILE = "archive.json"

# -----------------------
# Helper functions
# -----------------------
def is_bad_news(title):
    title_lower = title.lower()
    keyword_match = any(word in title_lower for word in bad_keywords)
    exclude_match = any(word in title_lower for word in exclude_keywords)
    polarity = TextBlob(title).sentiment.polarity
    sentiment_bad = polarity < -0.2
    return (keyword_match or sentiment_bad) and not exclude_match

def get_image(entry):
    if "media_content" in entry and len(entry.media_content) > 0:
        return entry.media_content[0].get("url")
    if "enclosures" in entry and len(entry.enclosures) > 0:
        return entry.enclosures[0].get("href")
    if "links" in entry:
        for link in entry.links:
            if link.get("rel") == "enclosure" and "image" in link.get("type",""):
                return link.get("href")
    if "summary" in entry and "img" in entry.summary:
        import re
        match = re.search(r'<img[^>]+src="([^">]+)"', entry.summary)
        if match:
            return match.group(1)
    return None

def load_existing_articles():
    if os.path.exists(ARTICLES_FILE):
        try:
            with open(ARTICLES_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_articles(final_articles):
    # Merge with existing so admin-approved ones aren’t lost
    existing = load_existing_articles()
    existing_titles = {a["title"] for a in existing}

    merged = existing + [a for a in final_articles if a["title"] not in existing_titles]

    # save merged list
    with open(ARTICLES_FILE, "w") as f:
        json.dump(merged, f, indent=2)

    # append snapshot to archive
    try:
        with open(ARCHIVE_FILE, "r") as f:
            archive = json.load(f)
    except FileNotFoundError:
        archive = []

    timestamp = datetime.now().isoformat()
    archive.append({"timestamp": timestamp, "articles": merged})

    with open(ARCHIVE_FILE, "w") as f:
        json.dump(archive, f, indent=2)

    print(f"Saved {len(merged)} merged articles to {ARTICLES_FILE} and archived snapshot in {ARCHIVE_FILE}.")

# -----------------------
# Main scraping routine
# -----------------------
def scrape_news():
    final_articles = []

    # Step 1: Strict bad news
    for source_name, feed_url in rss_feeds.items():
        feed = feedparser.parse(feed_url, request_headers={'User-Agent':'Mozilla/5.0'})
        entries_sorted = sorted(
            feed.entries,
            key=lambda x: x.get('published_parsed', time.gmtime(0)),
            reverse=True
        )
        for entry in entries_sorted:
            if len(final_articles) >= 20:
                break
            title = entry.get("title","")
            link = entry.get("link","")
            image_url = get_image(entry)
            title_lower = title.lower()

            if source_name in odd_feeds:
                if any(word in title_lower for word in bad_keywords):
                    final_articles.append({"source":source_name,"title":title,"link":link,"image":image_url,"shown":True})
            else:
                if is_bad_news(title):
                    final_articles.append({"source":source_name,"title":title,"link":link,"image":image_url,"shown":True})

    # Step 2: Fill with negative polarity if <20
    if len(final_articles) < 20:
        for source_name, feed_url in rss_feeds.items():
            feed = feedparser.parse(feed_url, request_headers={'User-Agent':'Mozilla/5.0'})
            entries_sorted = sorted(
                feed.entries,
                key=lambda x: x.get('published_parsed', time.gmtime(0)),
                reverse=True
            )
            for entry in entries_sorted:
                if len(final_articles) >= 20:
                    break
                title = entry.get("title","")
                link = entry.get("link","")
                image_url = get_image(entry)
                title_lower = title.lower()
                polarity = TextBlob(title).sentiment.polarity

                if polarity < 0 and not any(word in title_lower for word in exclude_keywords):
                    if not any(a["title"]==title for a in final_articles):
                        final_articles.append({"source":source_name,"title":title,"link":link,"image":image_url,"shown":True})

    # Step 3: Fill remaining with odd feeds
    if len(final_articles) < 20:
        for source_name in odd_feeds:
            feed_url = rss_feeds.get(source_name)
            feed = feedparser.parse(feed_url, request_headers={'User-Agent':'Mozilla/5.0'})
            entries_sorted = sorted(
                feed.entries,
                key=lambda x: x.get('published_parsed', time.gmtime(0)),
                reverse=True
            )
            for entry in entries_sorted:
                if len(final_articles) >= 20:
                    break
                title = entry.get("title","")
                link = entry.get("link","")
                image_url = get_image(entry)
                if not any(a["title"]==title for a in final_articles):
                    final_articles.append({"source":source_name,"title":title,"link":link,"image":image_url,"shown":True})

    # Step 4: Sort scraped batch by recency
    final_articles_sorted = sorted(
        final_articles,
        key=lambda x: x.get('published_parsed', time.gmtime(0)) if 'published_parsed' in x else time.gmtime(0),
        reverse=True
    )[:20]

    save_articles(final_articles_sorted)

if __name__ == "__main__":
    scrape_news()
