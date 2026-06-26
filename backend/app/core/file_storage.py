"""Structured, safe file storage for uploaded bye-law documents.

Files are organized on disk as::

    <UPLOAD_DIR>/byelaws/<registration_no>/<year>/<uuid8>_<sanitized_name>.<ext>

Storing under the society registration number and year keeps a tidy, auditable
layout and avoids filename collisions across societies and versions (FR-02,
requirement: organized storage location).
"""
import re
import uuid
from datetime import datetime
from pathlib import Path

from app.config import settings

_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
_MAX_NAME_LEN = 120


def get_extension(filename: str) -> str:
    """Return the lowercase extension without a leading dot ('' if none)."""
    return Path(filename).suffix.lower().lstrip(".")


def sanitize_filename(filename: str) -> str:
    """Make a filename safe for the filesystem, preserving its extension."""
    name = Path(filename).name  # strip any directory components (path traversal guard)
    stem = Path(name).stem
    ext = get_extension(name)
    safe_stem = _SAFE_CHARS.sub("_", stem).strip("._-") or "document"
    safe_stem = safe_stem[:_MAX_NAME_LEN]
    return f"{safe_stem}.{ext}" if ext else safe_stem


def _sanitize_component(value: str) -> str:
    cleaned = _SAFE_CHARS.sub("_", value).strip("._-")
    return cleaned[:_MAX_NAME_LEN] or "unknown"


def build_target_path(registration_no: str, original_filename: str) -> Path:
    """Compute an absolute, collision-free destination path for an upload."""
    base = Path(settings.UPLOAD_DIR) / "byelaws"
    reg = _sanitize_component(registration_no)
    year = str(datetime.utcnow().year)
    unique = uuid.uuid4().hex[:8]
    stored_name = f"{unique}_{sanitize_filename(original_filename)}"
    return base / reg / year / stored_name


def save_bytes(target_path: Path, data: bytes) -> str:
    """Write bytes to ``target_path`` (creating parent dirs). Returns the absolute path."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "wb") as fh:
        fh.write(data)
    return str(target_path.resolve())


def delete_quietly(path: str | Path) -> None:
    """Best-effort deletion used to roll back a saved file when persistence fails."""
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        # Deliberately swallowed — this is cleanup, not a critical operation.
        pass
