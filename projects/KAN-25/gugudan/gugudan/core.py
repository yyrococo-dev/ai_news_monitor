from typing import List


def generate_dan(dan: int) -> List[str]:
    """Generate lines for a single multiplication table 'dan'.

    Returns a list of strings: e.g. ['1 x 1 = 1', ... '1 x 9 = 9']
    """
    return [f"{dan} x {i} = {dan * i}" for i in range(1, 10)]


def build_full_output(max_dan: int = 2) -> str:
    """Build full output for 1..max_dan, with a blank line between dans."""
    parts = []
    for d in range(1, max_dan + 1):
        parts.extend(generate_dan(d))
        if d != max_dan:
            parts.append("")
    return "\n".join(parts) + "\n"
