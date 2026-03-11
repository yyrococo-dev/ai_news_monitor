import os
import logging
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# helper to create a Jira issue if JIRA credentials are present
def _create_jira_issue(title: str, body: str):
    import requests
    jira_host = os.environ.get('JIRA_HOST')
    jira_email = os.environ.get('JIRA_EMAIL')
    jira_token = os.environ.get('JIRA_API_TOKEN')
    jira_project = os.environ.get('JIRA_PROJECT_KEY','KAN')
    if not (jira_host and jira_email and jira_token):
        # fallback: log to local file
        p = os.path.expanduser('~/.openclaw/logs/jira_fallbacks.log')
        with open(p,'a') as f:
            f.write(f"TITLE: {title}\n{body}\n---\n")
        logger.info('Jira creds not present; wrote fallback note to %s', p)
        return False
    url = jira_host.rstrip('/') + '/rest/api/3/issue'
    headers = {'Content-Type':'application/json'}
    auth = (jira_email, jira_token)
    payload = {
        'fields':{
            'project':{'key': jira_project},
            'summary': title,
            'description': body,
            'issuetype':{'name':'Task'}
        }
    }
    resp = requests.post(url, json=payload, headers=headers, auth=auth, timeout=10)
    if resp.status_code in (200,201):
        logger.info('Created Jira issue %s', resp.json().get('key'))
        return True
    else:
        logger.warning('Failed to create Jira issue: %s %s', resp.status_code, resp.text)
        return False


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _call_gemini_api(items: List[Dict], prompt_name: str) -> str:
    """Call Google Gemini/Generative AI if client is available.
    Attempts to use `google.generativeai` if installed; otherwise raises.
    The prompt requests a Korean summary for the provided items.
    """
    key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_GENERATIVE_AI_API_KEY')
    if not key:
        raise RuntimeError('No GEMINI key')

    # try google.generativeai client
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        # build prompt text
        prompt_lines = ['다음 기사들을 한국어로 간결하게 요약해 주세요. 각 기사는 번호를 붙여 한 문단(2-3문장)으로 요약하고, 마지막에 출처 링크를 넣어주세요.\n']
        for i, it in enumerate(items, start=1):
            title = it.get('title') or ''
            snippet = it.get('snippet') or ''
            url = it.get('url') or ''
            prompt_lines.append(f"{i}. 제목: {title}\n요약 참고: {snippet}\n링크: {url}\n")
        prompt = '\n'.join(prompt_lines)
        # call text generation
        response = genai.predict(model='gpt-4o-mini', input=prompt)
        # response may have 'content' or 'candidates'
        if hasattr(response, 'text'):
            return response.text
        if isinstance(response, dict):
            return response.get('candidates', [{}])[0].get('content','')
        return str(response)
    except Exception as e:
        logger.exception('Gemini client call failed: %s', e)
        raise


def summarize_batch(items: List[Dict], prompt_name: str = 'summarize.daily') -> str:
    """Summarize a batch of items.
    If GEMINI_API_KEY (or GOOGLE_GENERATIVE_AI_API_KEY) is present, call the real API.
    On failures (network/quota), fall back to local summarizer and create a Jira note if creds present.
    Returns the summary text (Korean when using Gemini).
    """
    key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_GENERATIVE_AI_API_KEY')
    from summarizer.local_fallback_summarizer import summarize_items

    if not key:
        logger.info('No GEMINI key found, using fallback summarizer')
        return summarize_items(items)

    # Try external API with retries; on failure, fallback to local
    try:
        logger.info('GEMINI key found, attempting external API')
        result = _call_gemini_api(items, prompt_name=prompt_name)
        return result
    except Exception as e:
        logger.exception('External LLM call failed, falling back to local summarizer: %s', e)
        summary = summarize_items(items)
        # create jira issue to report failure
        title = f'(SUJI) LLM summarization failed: {str(e)[:100]}'
        body = f'LLM summarization attempted and failed with error:\n{str(e)}\n\nFalling back to local summarizer. Items count: {len(items)}'
        try:
            _create_jira_issue(title, body)
        except Exception:
            logger.exception('Failed to create jira fallback issue')
        return summary
