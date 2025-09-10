import csv
from pathlib import Path
from typing import Dict, Iterable


def parse_semicolon_csv(path: Path) -> Iterable[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            yield row




