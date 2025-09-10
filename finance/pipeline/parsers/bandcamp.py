import csv
from pathlib import Path
from typing import Dict, Iterable


EXPECTED_HEADERS = [
    "date",
    "paid to",
    "item type",
    "item name",
    "artist",
    "currency",
    "item price",
    "quantity",
    "discount code",
    "sub total",
    "additional fan contribution",
    "tax rate",
    "seller tax",
    "marketplace tax",
    "shipping",
    "ship from country name",
    "transaction fee",
    "fee type",
    "item total",
    "amount you received",
]


def parse_bandcamp_csv(path: Path) -> Iterable[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row




