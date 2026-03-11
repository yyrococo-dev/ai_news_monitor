import requests
import logging
from typing import List
from pathlib import Path
import re

logger = logging.getLogger(__name__)

# try to import bs4 but fall back to simple regex parsing if unavailable
try:
    from bs4 import BeautifulSoup
    HAVE_BS4 = True
except Exception:
    HAVE_BS4 = False

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
                content = resp.content
                title = url
                desc = ''
                if HAVE_BS4:
                    soup = BeautifulSoup(content, 'html.parser')
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
                else:
                    text = content.decode('utf-8', errors='ignore')
                    m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', text, re.IGNORECASE)
                    if m:
                        title = m.group(1)
                    else:
                        m2 = re.search(r'<title[^>]*>(.*?)</title>', text, re.IGNORECASE|re.DOTALL)
                        if m2:
                            title = re.sub('\s+',' ', m2.group(1)).strip()
                    m3 = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']', text, re.IGNORECASE)
                    if m3:
                        desc = m3.group(1)
                    else:
                        m4 = re.search(r'<p[^>]*>(.*?)</p>', text, re.IGNORECASE|re.DOTALL)
                        if m4:
                            desc = re.sub('<[^>]+>','',m4.group(1)).strip()

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
