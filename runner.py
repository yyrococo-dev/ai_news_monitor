#!/usr/bin/env python3
import argparse
from storage.schema import init_db
from collectors.rss_collector import RSSCollector
from aggregator.dedupe import normalize_url
import os

from summarizer import llm_client
from summarizer import batch_requestor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--use-llm', action='store_true', help='Use LLM summarizer when key is present')
    parser.add_argument('--dry-run', action='store_true', help='Do not send messages, just simulate')
    args = parser.parse_args()

    init_db()
    feeds = os.environ.get('AI_NEWS_FEEDS','https://hnrss.org/frontpage').split(',')
    rc = RSSCollector(feeds=feeds)
    items = rc.fetch()
    print('fetched', len(items), 'items')

    # normalize urls
    normalized = []
    seen = set()
    for it in items:
        url = normalize_url(it.get('url') or '')
        if not url or url in seen:
            continue
        seen.add(url)
        it['url_norm'] = url
        normalized.append(it)

    if not normalized:
        print('no items to summarize')
        return

    # batching - prefer token-based batching
    use_token = True
    chunks = batch_requestor.chunk_items(normalized, use_token=use_token, target_tokens=3000)
    summaries = []
    for i, chunk in enumerate(chunks):
        print(f'Processing chunk {i+1}/{len(chunks)} with {len(chunk)} items')
        s = llm_client.summarize_batch(chunk, prompt_name='summarize.daily')
        summaries.append(s)

    final_summary = '\n\n---\n\n'.join(summaries)

    if args.dry_run:
        print('DRY RUN SUMMARY:\n')
        print(final_summary[:2000])
    else:
        # TODO: send via Telegram deliverer
        from deliver.telegram_deliver import TelegramDeliver
        td = TelegramDeliver()
        td.deliver(final_summary[:8000], items=normalized)

if __name__ == '__main__':
    main()
