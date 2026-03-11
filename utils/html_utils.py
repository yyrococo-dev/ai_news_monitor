from html import unescape
import re

def html_to_text(html: str) -> str:
    if not html:
        return ''
    # Remove script/style
    html = re.sub(r'(?is)<(script|style).*?>.*?(</\1>)', '', html)
    # Replace links: <a href="url">text</a> -> text (url)
    html = re.sub(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', lambda m: f"{m.group(2)} ({m.group(1)})", html, flags=re.IGNORECASE)
    # Remove all tags
    text = re.sub(r'<[^>]+>', '', html)
    # Unescape HTML entities
    text = unescape(text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text
