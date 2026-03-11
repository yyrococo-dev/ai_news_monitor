import os
import threading
import time
from typing import Optional
from deliver.telegram_deliver import TelegramDeliver

AI_NOTIFY_ON_LONG_RUN = os.environ.get('AI_NOTIFY_ON_LONG_RUN','0') == '1'
AI_NOTIFY_PROGRESS_SECONDS = int(os.environ.get('AI_NOTIFY_PROGRESS_SECONDS', '60'))


def _send_message(text: str, dry_run: bool = False):
    # respect global toggle
    if not AI_NOTIFY_ON_LONG_RUN:
        # log to stdout for visibility
        print('[notifier][mock]', text)
        return {'mock': True, 'text': text}
    td = TelegramDeliver()
    if dry_run or not td.token:
        print('[notifier][dry-run/send-suppressed]', text[:200])
        return {'mock': True, 'text': text}
    return td.deliver(text)


class notify_run:
    """Context manager to notify long-running tasks.

    Behavior (configurable by env):
    - If AI_NOTIFY_ON_LONG_RUN != '1' then messages are mocked (printed).
    - Waits AI_NOTIFY_PROGRESS_SECONDS; if still running sends one progress message.
    - Does not send start or completion messages by default (per user preference).
    """

    def __init__(self, name: str, run_id: Optional[str] = None, dry_run: bool = False):
        self.name = name
        self.run_id = run_id
        self.dry_run = dry_run
        self._timer = None
        self._sent_progress = False
        self._lock = threading.Lock()

    def _progress_send(self):
        text = f"(SUJI) 작업 진행중: {self.name} (run: {self.run_id}) — 실행 중 {AI_NOTIFY_PROGRESS_SECONDS}+초"
        try:
            _send_message(text, dry_run=self.dry_run)
            with self._lock:
                self._sent_progress = True
        except Exception as e:
            print('[notifier] failed to send progress message', e)

    def __enter__(self):
        # start timer thread
        self._timer = threading.Timer(AI_NOTIFY_PROGRESS_SECONDS, self._progress_send)
        self._timer.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        # cancel timer if still pending
        if self._timer:
            self._timer.cancel()
        # if progress was sent, optionally send completion (user said no)
        return False
