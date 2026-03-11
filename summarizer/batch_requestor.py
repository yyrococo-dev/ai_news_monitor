from typing import List, Dict

# Simple batcher by item count. For production replace with token-based batching.

def chunk_items(items: List[Dict], max_items: int = 20) -> List[List[Dict]]:
    chunks = []
    for i in range(0, len(items), max_items):
        chunks.append(items[i:i+max_items])
    return chunks
