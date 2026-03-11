import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Minimal Gemini/OpenAI stub wrapper. If GEMINI_API_KEY is present, caller should implement
# actual API call. Otherwise fallback to local summarizer.

def summarize_batch(items: List[Dict], prompt_name: str = 'summarize.daily') -> str:
    """Summarize a batch of items.
    If GEMINI_API_KEY (or GOOGLE_GENERATIVE_AI_API_KEY) is present, call the real API (not implemented here).
    Otherwise use the local fallback summarizer.
    Returns the summary text.
    """
    key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_GENERATIVE_AI_API_KEY')
    from summarizer.local_fallback_summarizer import summarize_items

    if not key:
        logger.info('No GEMINI key found, using fallback summarizer')
        return summarize_items(items)

    # Real API path (stub) — implement actual call when key is available
    logger.info('GEMINI key found, calling external API (stub)')
    # Placeholder: return fallback for now and log that real implementation is needed
    # Future: implement google.genai client call here
    return summarize_items(items)
