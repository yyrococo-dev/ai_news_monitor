import os
from collectors.rss_collector import RSSCollector
from summarizer.local_fallback_summarizer import summarize_items
from deliver.telegram_deliver import TelegramDeliver
from aggregator.dedupe import normalize_url

# Integration test (dry run): fetch -> normalize/dedupe -> summarize(fallback) -> deliver (mock)

def mock_deliver(summary_text, items):
    print('--- MOCK DELIVER OUTPUT ---')
    print(summary_text[:1000])
    print('--- SOURCES ---')
    for it in items:
        print(it.get('title'), it.get('url'))


def run_integration_test():
    feeds = os.environ.get('AI_NEWS_FEEDS', 'https://hnrss.org/frontpage').split(',')
    rc = RSSCollector(feeds=feeds)
    items = rc.fetch()
    if not items:
        print('No items fetched; test cannot proceed.')
        return
    # normalize first 10 and dedupe by url
    seen = set()
    normalized = []
    for it in items[:10]:
        url = normalize_url(it.get('url') or '')
        if not url or url in seen:
            continue
        seen.add(url)
        it['url_norm'] = url
        normalized.append(it)
    summary = summarize_items(normalized)
    # use TelegramDeliver in dry-run mode (mock)
    mock_deliver(summary, normalized)

if __name__ == '__main__':
    run_integration_test()
