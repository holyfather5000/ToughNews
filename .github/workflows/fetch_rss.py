import feedparser, json, os, time

# RSS feeds
feeds = [
    "https://rss.cbc.ca/lineup/topstories.xml",
    "https://www.theguardian.com/world/rss"
]

# Keywords to filter
keywords = ["AI", "Toronto", "Art", "Politics"]

articles_file = "articles.json"

# Load existing articles.json
if os.path.exists(articles_file):
    with open(articles_file, "r") as f:
        try:
            existing = json.load(f)
        except:
            existing = []
else:
    existing = []

existing_links = {a["link"] for a in existing}

new_articles = []

for url in feeds:
    d = feedparser.parse(url)
    for entry in d.entries:
        title = entry.title
        link = entry.link
        date = entry.get("published", "")

        if any(k.lower() in title.lower() for k in keywords):
            if link not in existing_links:
                new_articles.append({
                    "title": title,
                    "link": link,
                    "date": date,
                    "shown": False
                })

# Add new articles to front
all_articles = new_articles + existing

# Save back
with open(articles_file, "w") as f:
    json.dump(all_articles, f, indent=2)

print(f"Added {len(new_articles)} new articles")
