#!/usr/bin/env python3
import argparse
import logging
import os

from dotenv import load_dotenv
load_dotenv()

from storage.schema import init_db
from collectors.rss_collector import RSSCollector
from aggregator.dedupe import normalize_url
from summarizer import llm_client
from summarizer import batch_requestor

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--use-llm', action='store_true', help='Use LLM summarizer when key is present')
    parser.add_argument('--dry-run', action='store_true', help='Do not send messages, just simulate')
    args = parser.parse_args()

    init_db()
    # ensure OpenClaw official sources are seeded (idempotent)
    from storage.schema import seed_sources
    seed_sources()

    feeds = os.environ.get('AI_NEWS_FEEDS','https://hnrss.org/frontpage').split(',')
    rc = RSSCollector(feeds=feeds)
    items = rc.fetch()
    # also fetch web sources (docs/blog/github pages)
    try:
        from collectors.web_collector import WebCollector
        wc = WebCollector()
        web_items = wc.fetch()
        print('web fetched', len(web_items), 'items')
        items.extend(web_items)
    except Exception:
        print('web collector load failed')
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

    # Rank and choose top-K important items for full LLM summarization
    from summarizer.ranker import rank_items
    TOP_K = int(os.environ.get('AI_SUMMARY_TOP_K','5'))

    ranked = rank_items(normalized, top_k=TOP_K)
    print('Selected top items:')
    for it, sc in ranked:
        print(' -', (it.get('title') or '')[:120], 'score=', sc)

    # Before summarizing, insert new items into sent_items (PENDING) and filter since_last_run
    import sqlite3, time
    DB = os.path.join(os.path.expanduser('~'),'dev','ai_news_monitor','storage.db')
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    new_top_items = []
    for it in [it for it, sc in ranked]:
        url = it.get('url')
        cur.execute('SELECT 1 FROM sent_items WHERE url=? LIMIT 1', (url,))
        if cur.fetchone():
            # already seen, skip inserting but keep for potential summarization
            new_top_items.append(it)
            continue
        # insert as PENDING
        now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        try:
            cur.execute('INSERT INTO sent_items (source,url,title,summary,published_at,fetched_at,status) VALUES (?,?,?,?,?,?,?)', (
                it.get('source') or it.get('feed') or '', url, it.get('title') or '', it.get('snippet') or '', it.get('published_at') or '', now, 'PENDING'
            ))
            conn.commit()
            new_top_items.append(it)
        except Exception:
            conn.rollback()
            new_top_items.append(it)
    conn.close()

    top_items = new_top_items

    from core.notifier import notify_run
    with notify_run(name='summarize-top-k'):
        if args.use_llm:
            logger.info('--use-llm flag set: using Gemini API for summarization')
            summary_text = llm_client.summarize_batch(top_items, prompt_name='summarize.daily')
        else:
            logger.info('--use-llm not set: using local fallback summarizer')
            from summarizer.local_fallback_summarizer import summarize_items
            summary_text = summarize_items(top_items)

    # For rest, produce a short headlines list
    others = [it for it in normalized if it not in top_items]
    headlines = '\n'.join(['- ' + (it.get('title') or '') + ' (' + (it.get('url') or '') + ')' for it in others[:20]])

    # Produce a compact Korean summary: one-paragraph per item
    def make_compact_summary(top_items, summary_text):
        parts = []
        parts.append('오늘의 핵심 뉴스 (요약은 한국어):')
        # assume summary_text contains per-item paragraphs in order; if not, we include brief snippet
        for idx, it in enumerate(top_items, start=1):
            title = (it.get('title') or '').strip()
            url = it.get('url') or ''
            # try to extract per-item paragraph from summary_text by splitting paragraphs
            para = ''
            try:
                paras = [p.strip() for p in summary_text.split('\n') if p.strip()]
                if len(paras) >= idx:
                    para = paras[idx-1]
            except Exception:
                para = ''
            if not para:
                para = (it.get('snippet') or '')[:200]
            parts.append(f"{idx}) {title} — {para} 링크: {url}")
        # add short other headlines list
        if headlines:
            parts.append('\n기타 헤드라인:')
            parts.append(headlines)
        return '\n\n'.join(parts)

    final_summary = make_compact_summary(top_items, summary_text)

    if args.dry_run:
        print('DRY RUN SUMMARY:\n')
        print(final_summary[:4000])
    else:
        # send via Telegram deliverer if creds present
        from deliver.telegram_deliver import TelegramDeliver
        td = TelegramDeliver()
        if not td.token:
            print('No TELEGRAM_BOT_TOKEN found in environment; skipping send')
            return
        # sanitize HTML in summaries
        results = td.deliver(final_summary, items=normalized, html=False, dry_run=False)
        print('Delivered, results count:', len(results))

if __name__ == '__main__':
    main()
