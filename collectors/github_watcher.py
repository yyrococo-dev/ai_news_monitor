from github import Github

class GithubWatcher:
    def __init__(self, token=None, repos=None):
        self.token = token
        self.repos = repos or []
        self.gh = Github(token) if token else None

    def fetch(self):
        items = []
        if not self.gh:
            return items
        for repo_full in self.repos:
            try:
                repo = self.gh.get_repo(repo_full)
                releases = repo.get_releases()[:5]
                for r in releases:
                    items.append({
                        'title': r.title,
                        'url': r.html_url,
                        'published_at': r.published_at.isoformat() if r.published_at else None,
                        'snippet': r.body[:200] if r.body else ''
                    })
            except Exception:
                continue
        return items
