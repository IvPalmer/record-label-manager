from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    repo_root: Path = Path(__file__).resolve().parents[2]
    sources_root: Path = repo_root / "finance" / "sources"
    archive_root: Path = repo_root / "finance" / "archive"
    storage_root: Path = repo_root / "finance" / "pipeline" / "storage"
    warehouse_root: Path = storage_root / "warehouse"
    logs_root: Path = storage_root / "logs"


PATHS = Paths()




