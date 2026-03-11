from typing import List, Dict, Tuple
import os
import sqlite3
from datetime import datetime, timedelta

# Config via env
TOP_K = int(os.environ.get('AI_SUMMARY_TOP_K','5'))
RECENCY_WINDOW_HOURS = int(os.environ.get('AI_SUMMARY_RECENCY_HOURS','48'))

# Keywords to boost (OpenClaw priority already handled via source priorities)
KEYWORDS = [k.strip().lower() for k in os.environ.get('AI_KEYWORDS','openclaw,open claw,claw').split(',') if k.strip()]


def _source_priority(identifier: str) -> float:
    # simple heuristic: if contains 'openclaw' boost
    if not identifier:
        return 0.0
    return 1.0 if 'openclaw' in identifier.lower() else 0.0


def _recency_score(published_at: str) -> float:
    try:
        # try common formats
        dt = datetime.fromisoformat(published_at)
    except Exception:
        try:
            dt = datetime.strptime(published_at, '%a, %d %b %Y %H:%M:%S %z')
        except Exception:
            return 0.0
    now = datetime.utcnow()
    # normalize: within RECENCY_WINDOW_HOURS -> 1.0, else decays
    delta = now - dt.replace(tzinfo=None)
    hours = delta.total_seconds()/3600
    if hours <= 0:
        return 1.0
    if hours > RECENCY_WINDOW_HOURS:
        return 0.0
    return max(0.0, 1.0 - (hours/RECENCY_WINDOW_HOURS))


def _keyword_match_score(text: str) -> float:
    if not text:
        return 0.0
    t = text.lower()
    for kw in KEYWORDS:
        if kw and kw in t:
            return 1.0
    return 0.0


def _novelty_score(url: str) -> float:
    # if url exists in sent_items -> 0 else 1
    try:
        DB = os.path.join(os.path.expanduser('~'),'dev','ai_news_monitor','storage.db')
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM sent_items WHERE url=? LIMIT 1', (url,))
        r = cur.fetchone()
        conn.close()
        return 0.0 if r else 1.0
    except Exception:
        return 1.0


def score_item(item: Dict) -> float:
    # weights
    w_source = 3.0
    w_keyword = 4.5  # increased weight to prioritize AI/coding keywords
    w_novel = 2.0
    w_recency = 1.5
    w_pop = 1.0

    source_score = _source_priority(item.get('source') or item.get('feed') or '')
    keyword = _keyword_match_score((item.get('title') or '') + ' ' + (item.get('snippet') or ''))
    novel = _novelty_score(item.get('url') or '')
    recency = _recency_score(item.get('published_at') or '')
    # popularity unknown in many feeds; attempt to use 'points' or 'comments'
    pop = 0.0
    try:
        points = int(item.get('points') or 0)
        comments = int(item.get('comments') or 0)
        pop = min(1.0, (points + comments) / 100.0)
    except Exception:
        pop = 0.0

    score = (w_source*source_score + w_keyword*keyword + w_novel*novel + w_recency*recency + w_pop*pop)
    return score


def rank_items(items: List[Dict], top_k: int = None) -> List[Tuple[Dict,float]]:
    if top_k is None:
        top_k = TOP_K
    scored = []
    for it in items:
        s = score_item(it)
        scored.append((it, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    # apply diversity: avoid more than 2 items from same domain in top_k
    selected = []
    domain_count = {}
    ai_related = []
    non_ai = []
    for it, sc in scored:
        # classify as ai-related via keyword match
        kscore = _keyword_match_score((it.get('title') or '') + ' ' + (it.get('snippet') or ''))
        if kscore > 0:
            ai_related.append((it, sc))
        else:
            non_ai.append((it, sc))

    # ensure at least min_ai items (env AI_MIN_AI_IN_TOP, default 3)
    min_ai = int(os.environ.get('AI_MIN_AI_IN_TOP','3'))
    # pick ai items first with diversity
    def pick_from_list(source_list, limit, selected, domain_count):
        for it, sc in source_list:
            if len(selected) >= limit:
                break
            domain = ''
            try:
                from urllib.parse import urlparse
                domain = urlparse(it.get('url') or '').netloc
            except Exception:
                domain = ''
            if domain:
                cnt = domain_count.get(domain,0)
                if cnt >= 2:
                    continue
                domain_count[domain] = cnt+1
            selected.append((it, sc))
        return selected

    selected = pick_from_list(ai_related, top_k, selected, domain_count)
    if len(selected) < min_ai:
        # if not enough ai items found, try filling with top ai_related ignoring diversity
        for it, sc in ai_related:
            if (it, sc) in selected:
                continue
            selected.append((it, sc))
            if len(selected) >= min_ai:
                break

    # fill remaining slots with non-ai items respecting diversity
    if len(selected) < top_k:
        selected = pick_from_list(non_ai, top_k, selected, domain_count)

    # if still short, fill from scored list
    if len(selected) < top_k:
        for it, sc in scored:
            if (it, sc) in selected:
                continue
            selected.append((it, sc))
            if len(selected) >= top_k:
                break
    return selected
