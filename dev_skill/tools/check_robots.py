"""
check_robots.py — robots.txt 검사 유틸리티 (ai-legal 지원)

주요 기능:
  - check_robots(base_url): robots.txt 원문을 가져와 상태 반환
  - is_allowed(base_url, path, user_agent): 특정 경로 크롤링 허용 여부 반환
"""

import requests
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser


def check_robots(base_url: str) -> dict:
    """robots.txt를 가져와 상태와 원문을 반환합니다.

    Returns:
        {'status': 'ok', 'content': str} |
        {'status': 'no-robots', 'code': int} |
        {'status': 'error', 'error': str}
    """
    try:
        if not base_url.endswith('/'):
            base_url = base_url + '/'
        robots_url = urljoin(base_url, 'robots.txt')
        r = requests.get(robots_url, timeout=5)
        if r.status_code != 200:
            return {'status': 'no-robots', 'code': r.status_code}
        return {'status': 'ok', 'content': r.text}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def is_allowed(base_url: str, path: str, user_agent: str = '*') -> bool:
    """해당 URL 경로에 대한 크롤링 허용 여부를 반환합니다.

    표준 robots.txt 규칙(RobotFileParser)을 사용하여 파싱합니다.

    Args:
        base_url: 사이트 루트 URL (예: 'https://example.com')
        path: 검사할 경로 (예: '/articles/')
        user_agent: 검사할 User-Agent 문자열 (기본값: '*')

    Returns:
        True이면 수집 허용, False이면 금지
    """
    if not base_url.endswith('/'):
        base_url = base_url + '/'
    robots_url = urljoin(base_url, 'robots.txt')
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception:
        # robots.txt를 읽을 수 없으면 허용으로 간주 (표준 관례)
        return True
    return rp.can_fetch(user_agent, urljoin(base_url, path))


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('usage: python check_robots.py <base_url> [path] [user_agent]')
        print('  example: python check_robots.py https://example.com /articles/')
    else:
        url = sys.argv[1]
        path = sys.argv[2] if len(sys.argv) > 2 else '/'
        ua = sys.argv[3] if len(sys.argv) > 3 else '*'
        print('robots.txt 상태:', check_robots(url))
        print(f'is_allowed({path!r}, user_agent={ua!r}):', is_allowed(url, path, ua))
