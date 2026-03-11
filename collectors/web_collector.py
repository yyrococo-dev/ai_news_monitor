import requests
from bs4 import BeautifulSoup
import logging
from typing import List
from pathlib import Path

logger = logging.getLogger(__name__)

class WebCollector:
    def __init__(self, sources=None, timeout=8):
        self.timeout = timeout
        self.sources = sources or []

    def fetch(self) -> List[dict]:
        items = []
        # if sources not provided, load from DB sources where type=='web'
        if not self.sources:
            try:
                import sqlite3
                DB = Path.home() / 'dev' / 'ai_news_monitor' / 'storage.db'
                conn = sqlite3.connect(DB)
                cur = conn.cursor()
                cur.execute("SELECT identifier FROM sources WHERE type='web'")
                rows = cur.fetchall()
                conn.close()
                self.sources = [r[0] for r in rows]
            except Exception:
                logger.exception('failed to load web sources from DB')
                self.sources = []

        for url in self.sources:
            try:
                resp = requests.get(url, timeout=self.timeout)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.content, 'html.parser')
                title = None
                desc = None
                # try Open Graph
                og_title = soup.find('meta', property='og:title')
                if og_title and og_title.get('content'):
                    title = og_title.get('content')
                og_desc = soup.find('meta', property='og:description')
                if og_desc and og_desc.get('content'):
                    desc = og_desc.get('content')
                if not title:
                    t = soup.find('title')
                    title = t.get_text().strip() if t else url
                if not desc:
                    p = soup.find('p')
                    desc = p.get_text().strip() if p else ''

                # create single item representing site latest content
                items.append({
                    'title': title,
                    'url': url,
                    'published_at': '',
                    'snippet': desc,
                    'source': url
                })
            except Exception:
                logger.exception('error scraping web source %s', url)
        return items
