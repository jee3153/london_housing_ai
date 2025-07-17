import hashlib
from pathlib import Path

READ_BYTES = "rb"


def file_sha256(path: Path, chunk_mb: int = 4) -> str:
    """
    Return SHA-256 checksum (hex string) of a local file.
    Reads the file in chunks so it works for GB-sized CSVs.
    """
    h = hashlib.sha256()
    with path.open(READ_BYTES) as f:
        for chunk in iter(lambda: f.read(chunk_mb * 1024**2), b""):
            h.update(chunk)
    return h.hexdigest()
