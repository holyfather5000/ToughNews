import feedparser
from textblob import TextBlob
import time
import json
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
    
    "Odd News": "https://www.odditycentral.com/feed",
    "HuffPost Weird": "https://www.huffpost.com/section/weird-news/feed",
}

odd_feeds = {"Odd News", "HuffPost Weird"}

# Keywords
bad_keywords = [
    "earthquake", "war", "killed", "crash", "explosion", "riot", "terror",
    "bomb", "injury", "injuries", "injured", "fatal", "fatality", "emergency",
    "deadly", "attack", "violence", "warfare",
    "abduction", "assault", "homicide", "catastrophe", "evacuation",
    "public harm", "rigging", "forgery", "bribery",
    "scam", "crash", "collision", "oil company", "oil spill",
    "riot police", "death toll", "death", "deaths", "police clash",
    "fatalities", "hostage", "drought", "cyclone", "famine", "arson",
    "assassination", "crimes", "poison", "tragic", "tragedy", "explosions",
    "earthquakes", "shootings", "have died", "has died", "been killed",
    "deceased", "murder", "crisis", "disaster",
    "pandemic", "starvation", "disease", "outbreak", "terrorism", "hurricane",
    "tornado", "felony", "fire", "evacuation", "fatal", "injured", "hostage",
    "dictator", "scandal", "corruption", "pollution", "poverty", "fraud",
    "human trafficking", "racism", "rascist", "unemployment", "suicide", "North Korea",
]

exclude_keywords = [
    "film", "movie", "review", "trailer", "episode", "series",
    "plot", "music", "concert", "festival", "art", "exhibition",
    "author", "fiction"
]

ARCHIVE_FILE = "articles.json"

# -----------------------
# Helper Functions
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

def save_archive(articles):
    """Append new run to archive"""
    try:
        with open(ARCHIVE_FILE, "r") as f:
            archive = json.load(f)
    except FileNotFoundError:
        archive = []

    timestamp = datetime.now().isoformat()
    archive.append({"timestamp": timestamp, "articles": articles})

    with open(ARCHIVE_FILE, "w") as f:
        json.dump(archive, f, indent=2)

# -----------------------
# Main scraping routine
# -----------------------
def scrape_news():
    final_articles = []

    # Step 1: Strict bad news
    for source_name, feed_url in rss_feeds.items():
        if len(final_articles) >= 20:
            break
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

            if source_name in odd_feeds:
                if any(word in title_lower for word in bad_keywords):
                    final_articles.append({"source":source_name,"title":title,"link":link,"image":image_url,"polarity":polarity,"shown":True})
            else:
                if is_bad_news(title):
                    final_articles.append({"source":source_name,"title":title,"link":link,"image":image_url,"polarity":polarity,"shown":True})

    # Step 2: Fill with negative polarity if less than 20
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
                        final_articles.append({"source":source_name,"title":title,"link":link,"image":image_url,"polarity":polarity,"shown":True})

    # Step 3: Fill with odd feeds if still <20
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
                    final_articles.append({"source":source_name,"title":title,"link":link,"image":image_url,"polarity":0,"shown":True})

    # Step 4: Sort final 20 by newest published date
    final_articles_sorted = sorted(
        final_articles,
        key=lambda x: x.get('published_parsed', time.gmtime(0)) if 'published_parsed' in x else time.gmtime(0),
        reverse=True
    )
    # Step 5: Print exactly 20
    print(f"\n📰 Showing {len(final_articles_sorted[:20])} articles\n" + "-"*60)
    for art in final_articles_sorted[:20]:
        print(f"{art['source']}: {art['title']}")
        print(f"Link: {art['link']}")
        if art["image"]:
            print(f"Image: {art['image']}")
        print()

def save_for_website(articles):
    with open("articles.json", "w") as f:
        json.dump(articles, f, indent=2)

