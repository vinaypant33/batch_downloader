"""The kinds of file the app can download, grouped the way the checkboxes are."""

from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

CATEGORIES = {
    "videos": (".mp4", ".webm", ".mov", ".mkv", ".avi"),
    "audio": (".mp3", ".wav", ".m4a", ".ogg", ".flac"),
    "images": (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"),
    "documents": (".pdf", ".docx", ".xlsx", ".pptx", ".csv", ".txt"),
    "archives": (".zip", ".rar", ".7z", ".tar", ".gz"),
}

LABELS = {
    "videos": "Videos (MP4…)",
    "audio": "Audio (MP3…)",
    "images": "Images (PNG, JPG…)",
    "documents": "Documents (PDF…)",
    "archives": "Archives (ZIP…)",
}


def extension_of(url):
    """'.pdf' for https://site/a/Report%20Final.PDF?x=1, '' when there is none."""
    path = unquote(urlparse(url).path)
    name = PurePosixPath(path).name.lower()
    if name.endswith(".tar.gz"):
        return ".gz"
    return PurePosixPath(name).suffix


def category_of(url):
    """The category a URL's file belongs to, or None if it is not a known file."""
    ext = extension_of(url)
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return None
