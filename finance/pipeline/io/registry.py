import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class SourceFileMeta:
    path: str
    sha256: str
    bytes: int
    mtime: float
    source: str
    statement_type: Optional[str] = None
    period: Optional[str] = None
    correction_of: Optional[str] = None
    registered_at: str = datetime.utcnow().isoformat(timespec="seconds") + "Z"


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_meta_json(output_dir: Path, meta: SourceFileMeta) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "meta.json"
    if target.exists():
        # merge append
        try:
            existing = json.loads(target.read_text())
            if not isinstance(existing, list):
                existing = [existing]
        except Exception:
            existing = []
    else:
        existing = []
    existing.append(asdict(meta))
    target.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    return target




