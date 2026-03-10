import os
from pathlib import Path
import requests

class TelegramDeliver:
    def __init__(self, token=None, chat_id=None):
        self.token = token or os.environ.get('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.environ.get('TELEGRAM_ADMIN_ID')
        self.api = f'https://api.telegram.org/bot{self.token}/sendMessage'

    def _send(self, text):
        if not self.token or not self.chat_id:
            raise RuntimeError('Missing telegram creds')
        payload = {'chat_id': self.chat_id, 'text': text}
        r = requests.post(self.api, data=payload, timeout=10)
        r.raise_for_status()
        return r.json()

    def deliver(self, summary_text, items=None):
        # naive truncation
        max_len = 4000
        text = summary_text
        if len(text) > max_len:
            text = text[:max_len-3] + '...'
        return self._send(text)
