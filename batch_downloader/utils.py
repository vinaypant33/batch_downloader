"""Small helpers shared across the package."""

import datetime as dt


def human_size(num_bytes):
    """1536 -> '1.5 KB'. None -> '?'."""
    if num_bytes is None:
        return "?"
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"  # pragma: no cover


def now_iso():
    """Current local time as 'YYYY-MM-DD HH:MM:SS'."""
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def shorten(text, width=60):
    """Shorten long text in the middle: 'https://site/very.../file.pdf'.

    Uses plain dots so it prints correctly in every Windows console.
    """
    if len(text) <= width:
        return text
    keep = (width - 3) // 2
    return text[:keep] + "..." + text[-(width - 3 - keep):]
