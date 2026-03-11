from github import Github
from tenacity import retry, stop_after_attempt, wait_exponential

class GithubWatcher:
    def __init__(self, token=None, repos=None):
        self.token = token
        self.repos = repos or []
        self.gh = Github(token) if token else None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _get_repo(self, repo_full):
        return self.gh.get_repo(repo_full)

    def fetch(self):
        items = []
        if not self.gh:
            return items
        for repo_full in self.repos:
            try:
                repo = self._get_repo(repo_full)
                releases = repo.get_releases()
                count = 0
                for r in releases:
                    items.append({
                        'title': r.title,
                        'url': r.html_url,
                        'published_at': r.published_at.isoformat() if r.published_at else None,
                        'snippet': (r.body or '')[:200]
                    })
                    count += 1
                    if count >= 5:
                        break
            except Exception:
                # skip problematic repo but continue others
                continue
        return items
