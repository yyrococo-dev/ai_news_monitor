#!/usr/bin/env python3
from storage.schema import init_db
from collectors.rss_collector import RSSCollector
from aggregator.dedupe import normalize_url
import os

def main():
    init_db()
    # simple demo: fetch from example feeds
    feeds = os.environ.get('AI_NEWS_FEEDS','https://hnrss.org/frontpage').split(',')
    rc = RSSCollector(feeds=feeds)
    items = rc.fetch()
    print('fetched', len(items), 'items')
    # normalize urls
    for it in items[:5]:
        it['url_norm'] = normalize_url(it.get('url') or '')
        print(it['title'], it['url_norm'])

if __name__ == '__main__':
    main()
