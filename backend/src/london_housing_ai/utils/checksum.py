import hashlib
from pathlib import Path
from datetime import datetime, timezone

READ_BYTES = "rb"
ONE_MiB = 1024**2


def file_sha256(path: Path, chunk_mb: int = 4) -> str:
    """
    Return SHA-256 checksum (hex string) of a local file.
    Reads the file in chunks so it works for GB-sized CSVs.
    """
    h = hashlib.sha256()
    with path.open(READ_BYTES) as f:
        # 4Mib is big enough to be efficient yet small enough not to bloat RAM
        for chunk in iter(lambda: f.read(chunk_mb * ONE_MiB), b""):
            h.update(chunk)
    return h.hexdigest()


def unique_filename_from_sha256(
    prefix: str, checksum: str, extension: str = "json"
) -> str:
    return f"{prefix}_{checksum[:16]}_{datetime.now(timezone.utc)}.{extension}"
