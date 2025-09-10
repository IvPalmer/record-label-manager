from pathlib import Path
from typing import Optional

from finance.pipeline.io.converters import normalize_delimiter_and_decimal


def build_canonical_distribution(
    src_csv: Path,
    dest_dir: Path,
    period_year: str,
    period_q: str,
    statement_type: str = "royalty",
    delimiter_in: str = ";",
    decimal_comma_to_dot: bool = True,
) -> Path:
    dest_dir = dest_dir / period_year / period_q
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / ("royalty.csv" if statement_type == "royalty" else "encoding.csv")
    normalize_delimiter_and_decimal(
        src_csv, out, delimiter_in=delimiter_in, delimiter_out=",", decimal_comma_to_dot=decimal_comma_to_dot
    )
    return out


