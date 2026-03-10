from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

def normalize_url(url):
    # remove query params that are tracking-like and sort
    p = urlparse(url)
    qs = dict(sorted(parse_qsl(p.query)))
    # drop common tracking params
    for k in list(qs.keys()):
        if k.startswith('utm_') or k in ('ref','fbclid'):
            qs.pop(k, None)
    newq = urlencode(qs)
    return urlunparse((p.scheme, p.netloc, p.path.rstrip('/'), '', newq, ''))
