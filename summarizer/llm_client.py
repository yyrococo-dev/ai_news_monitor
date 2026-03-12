import os
import logging
import yaml
from pathlib import Path
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Default model — can override via GEMINI_MODEL env var
DEFAULT_MODEL = 'gemini-2.5-flash'


# --- Prompt loader ---

def _load_prompt(prompt_name: str) -> dict:
    """Load a prompt template from prompts/<prompt_name>.yaml."""
    prompt_dir = Path(__file__).resolve().parent.parent / 'prompts'
    prompt_file = prompt_dir / f'{prompt_name}.yaml'
    if prompt_file.exists():
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data or {}
        except Exception as e:
            logger.warning('Failed to load prompt file %s: %s', prompt_file, e)
    return {}


def _build_prompt(items: List[Dict], prompt_name: str) -> str:
    """Combine prompt template with item list to produce a full prompt string."""
    tpl = _load_prompt(prompt_name)
    system_msg = tpl.get('system', '').strip()
    user_msg = tpl.get('user', '').strip()

    lines = []
    if system_msg:
        lines.append(system_msg)
    if user_msg:
        lines.append(user_msg)

    lines.append(
        '\n다음 기사들을 한국어로 간결하게 요약해 주세요. '
        '각 기사는 번호를 붙여 한 문단(2-3문장)으로 요약하고, 마지막에 출처 링크를 넣어주세요.\n'
    )
    for i, it in enumerate(items, start=1):
        title = it.get('title') or ''
        snippet = it.get('snippet') or ''
        url = it.get('url') or ''
        lines.append(f"{i}. 제목: {title}\n   요약 참고: {snippet}\n   링크: {url}\n")

    return '\n'.join(lines)


# --- Gemini API call ---

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call_gemini_api(items: List[Dict], prompt_name: str) -> str:
    """Call Google Gemini API using the new google-genai SDK.

    Uses gemini-2.0-flash by default (free tier available).
    Raises on failure so tenacity can retry.
    """
    key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_GENERATIVE_AI_API_KEY')
    if not key:
        raise RuntimeError('GEMINI_API_KEY not set in environment')

    try:
        from google import genai
    except ImportError:
        raise RuntimeError(
            'google-genai package not installed. Run: pip install google-genai'
        )

    client = genai.Client(api_key=key)
    model_name = os.environ.get('GEMINI_MODEL', DEFAULT_MODEL)
    prompt = _build_prompt(items, prompt_name)

    logger.info('Calling Gemini API (model=%s, items=%d)', model_name, len(items))
    response = client.models.generate_content(model=model_name, contents=prompt)

    text = getattr(response, 'text', None)
    if text:
        return text

    # Fallback: traverse candidates
    try:
        return response.candidates[0].content.parts[0].text
    except (AttributeError, IndexError):
        pass

    raise RuntimeError(f'Unexpected Gemini response format: {response}')


# --- Public interface ---

def summarize_batch(items: List[Dict], prompt_name: str = 'summarize.daily') -> str:
    """Summarize a batch of news items using Gemini API.

    If GEMINI_API_KEY is present, calls the Gemini API (with up to 2 retries).
    On all failures, falls back to local rule-based summarizer.

    Args:
        items: list of dicts with keys title, url, snippet.
        prompt_name: name of the prompt template file (without .yaml).

    Returns:
        Summary text string (Korean when using Gemini).
    """
    from summarizer.local_fallback_summarizer import summarize_items

    key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_GENERATIVE_AI_API_KEY')
    if not key:
        logger.info('GEMINI_API_KEY not set — using local fallback summarizer')
        return summarize_items(items)

    try:
        logger.info('GEMINI_API_KEY found — calling Gemini API (%d items)', len(items))
        result = _call_gemini_api(items, prompt_name=prompt_name)
        logger.info('Gemini API call succeeded')
        return result
    except Exception as e:
        logger.exception('Gemini API call failed, falling back to local summarizer: %s', e)
        return summarize_items(items)
