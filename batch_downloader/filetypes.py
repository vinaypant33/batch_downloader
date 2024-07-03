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
