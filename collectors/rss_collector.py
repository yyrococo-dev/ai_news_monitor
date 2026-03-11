import feedparser
import logging

logger = logging.getLogger(__name__)

class RSSCollector:
    def __init__(self, feeds=None):
        # feeds can be provided OR pulled from storage.sources table
        self.feeds = feeds or []

    def _load_seeded_sources(self):
        # read sources table and return list of identifiers (urls) with OpenClaw sources first
        try:
            import sqlite3
            from pathlib import Path
            DB = Path.home() / 'dev' / 'ai_news_monitor' / 'storage.db'
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute("SELECT identifier FROM sources ORDER BY CASE WHEN identifier LIKE '%openclaw%' THEN 0 ELSE 1 END, id")
            rows = cur.fetchall()
            conn.close()
            return [r[0] for r in rows]
        except Exception:
            logger.exception('failed to load seeded sources from DB')
            return []

    def fetch(self):
        items = []
        # combine provided feeds with seeded sources (seeded prioritized)
        seeded = self._load_seeded_sources()
        feed_list = seeded + [f for f in self.feeds if f not in seeded]
        for url in feed_list:
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
