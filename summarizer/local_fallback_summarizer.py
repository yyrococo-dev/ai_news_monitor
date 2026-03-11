def summarize_items(items):
    """Simple fallback summarizer: join titles and first 2 sentences of snippets."""
    parts = []
    for it in items:
        title = it.get('title') or ''
        snippet = it.get('snippet') or ''
        # naive sentence split
        sentences = snippet.split('. ')
        lead = '. '.join(sentences[:2]).strip()
        if lead and not lead.endswith('.'):
            lead += '.'
        parts.append(f"- {title}\n  {lead}")
    return "\n\n".join(parts)
