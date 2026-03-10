import feedparser

class RSSCollector:
    def __init__(self, feeds=None):
        self.feeds = feeds or []

    def fetch(self):
        items = []
        for url in self.feeds:
            d = feedparser.parse(url)
            for entry in d.entries[:10]:
                items.append({
                    'title': entry.get('title'),
                    'url': entry.get('link'),
                    'published_at': entry.get('published'),
                    'snippet': entry.get('summary') if 'summary' in entry else ''
                })
        return items
