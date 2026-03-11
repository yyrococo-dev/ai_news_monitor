from typing import List, Dict

# Token-based batcher. Estimates tokens by character count (rough heuristic)
# Default: target ~3000 tokens per batch (adjustable)

def estimate_tokens(text: str) -> int:
    # rough heuristic: 4 chars ~ 1 token
    return max(1, int(len(text) / 4))

def item_tokens(item: Dict) -> int:
    # estimate tokens for a single item (title + snippet)
    title = item.get('title','') or ''
    snippet = item.get('snippet','') or ''
    return estimate_tokens(title) + estimate_tokens(snippet)


def chunk_items_by_tokens(items: List[Dict], target_tokens: int = 3000) -> List[List[Dict]]:
    chunks: List[List[Dict]] = []
    cur: List[Dict] = []
    cur_tokens = 0
    for it in items:
        t = item_tokens(it)
        # if single item exceeds target, still include it alone
        if cur_tokens + t > target_tokens and cur:
            chunks.append(cur)
            cur = [it]
            cur_tokens = t
        else:
            cur.append(it)
            cur_tokens += t
    if cur:
        chunks.append(cur)
    return chunks

# Backwards-compatible alias
def chunk_items(items: List[Dict], max_items: int = 20, use_token: bool = False, target_tokens: int = 3000) -> List[List[Dict]]:
    if use_token:
        return chunk_items_by_tokens(items, target_tokens=target_tokens)
    # legacy behaviour
    chunks = []
    for i in range(0, len(items), max_items):
        chunks.append(items[i:i+max_items])
    return chunks
