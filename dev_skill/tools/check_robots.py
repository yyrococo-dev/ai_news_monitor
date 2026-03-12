import requests
from urllib.parse import urljoin

def check_robots(base_url):
    try:
        if not base_url.endswith('/'):
            base_url = base_url + '/'
        robots_url = urljoin(base_url, 'robots.txt')
        r = requests.get(robots_url, timeout=5)
        if r.status_code != 200:
            return {'status':'no-robots','code':r.status_code}
        return {'status':'ok','content':r.text}
    except Exception as e:
        return {'status':'error','error':str(e)}

if __name__ == '__main__':
    import sys
    if len(sys.argv)<2:
        print('usage: python check_robots.py https://example.com')
    else:
        print(check_robots(sys.argv[1]))
