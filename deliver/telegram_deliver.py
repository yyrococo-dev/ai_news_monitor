import os
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from ..utils.html_utils import html_to_text

class TelegramDeliver:
    def __init__(self, token=None, chat_id=None, max_chunk=3500):
        self.token = token or os.environ.get('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.environ.get('TELEGRAM_ADMIN_ID')
        self.api = f'https://api.telegram.org/bot{self.token}/sendMessage' if self.token else None
        self.max_chunk = max_chunk

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _send(self, text):
        if not self.token or not self.chat_id:
            raise RuntimeError('Missing telegram creds')
        payload = {'chat_id': self.chat_id, 'text': text}
        r = requests.post(self.api, data=payload, timeout=10)
        r.raise_for_status()
        return r.json()

    def _split_text(self, text):
        # split on paragraph/newline boundaries where possible
        if len(text) <= self.max_chunk:
            return [text]
        parts = []
        paragraphs = text.split('\n\n')
        cur = ''
        for p in paragraphs:
            if len(cur) + len(p) + 2 <= self.max_chunk:
                cur = (cur + '\n\n' + p).strip() if cur else p
            else:
                if cur:
                    parts.append(cur)
                # if single paragraph too long, split by sentences
                if len(p) > self.max_chunk:
                    # naive sentence split
                    sentences = p.split('. ')
                    cur2 = ''
                    for s in sentences:
                        s = s.strip()
                        if not s:
                            continue
                        if len(cur2) + len(s) + 2 <= self.max_chunk:
                            cur2 = (cur2 + '. ' + s).strip() if cur2 else s
                        else:
                            parts.append(cur2 + '.')
                            cur2 = s
                    if cur2:
                        parts.append(cur2 + '.')
                    cur = ''
                else:
                    cur = p
        if cur:
            parts.append(cur)
        return parts

    def deliver(self, summary_text, items=None, html=False, dry_run=False):
        # Convert HTML to plain text if requested
        text = html_to_text(summary_text) if html else summary_text
        # If dry run, return chunks without sending
        chunks = self._split_text(text)
        if dry_run:
            return [{'mock': True, 'text': c[:200]} for c in chunks]
        results = []
        for c in chunks:
            results.append(self._send(c))
        return results
