import feedparser
import logging

logger = logging.getLogger(__name__)

class RSSCollector:
    def __init__(self, feeds=None):
        self.feeds = feeds or []

    def fetch(self):
        items = []
        for url in self.feeds:
            try:
                d = feedparser.parse(url)
                if d.bozo:
                    logger.warning('feed parse error for %s: %s', url, getattr(d, 'bozo_exception', ''))
                for entry in d.entries[:10]:
                    items.append({
                        'title': entry.get('title'),
                        'url': entry.get('link'),
                        'published_at': entry.get('published'),
                        'snippet': entry.get('summary') if 'summary' in entry else ''
                    })
            except Exception as e:
                logger.exception('error fetching feed %s: %s', url, e)
        return items
