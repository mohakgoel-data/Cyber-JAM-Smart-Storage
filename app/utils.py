import os
import re
import uuid
from .file_types import FILE_TYPE_MAP

def sanitize_filename(name: str) -> str:
    # Remove path traversal
    name = os.path.basename(name)

    # Replace spaces
    name = name.replace(" ", "_")

    # Remove unsafe characters
    name = re.sub(r"[^a-zA-Z0-9._-]", "", name)

    return name


def get_file_path(filename: str) -> str:
    # Clean the filename
    clean = sanitize_filename(filename)

    # Extract extension
    parts = clean.rsplit(".", 1)
    ext = parts[-1].lower() if len(parts) == 2 else ""

    # Pick correct directory
    folder = FILE_TYPE_MAP.get(ext, "others/")

    # Add unique prefix → avoids overwrite
    unique = uuid.uuid4().hex[:8]

    # Build final object path
    if ext:
        return f"{folder}{unique}_{clean}"
    else:
        # File without extension
        return f"{folder}{unique}_file"

