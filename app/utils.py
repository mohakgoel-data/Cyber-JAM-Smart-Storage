import os
import re
import uuid
from .file_types import FILE_TYPE_MAP

def sanitize_filename(name: str) -> str:
    name = os.path.basename(name)

    name = name.replace(" ", "_")

    name = re.sub(r"[^a-zA-Z0-9._-]", "", name)

    return name


def get_file_path(filename: str) -> str:

    clean = sanitize_filename(filename)

    parts = clean.rsplit(".", 1)
    ext = parts[-1].lower() if len(parts) == 2 else ""

    folder = FILE_TYPE_MAP.get(ext, "others/")

    unique = uuid.uuid4().hex[:8]

    if ext:
        return f"{folder}{unique}_{clean}"
    else:
        return f"{folder}{unique}_file"

