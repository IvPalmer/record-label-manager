import argparse
import re
from pathlib import Path
from typing import Optional

from finance.pipeline.config import PATHS
from finance.pipeline.etl.ingest import build_canonical_distribution
from finance.pipeline.io.converters import normalize_delimiter_and_decimal, xlsx_to_csv
from finance.pipeline.io.registry import SourceFileMeta, compute_sha256, write_meta_json


def _infer_period_from_name(name: str) -> Optional[tuple[str, str]]:
    # Accept patterns like 2022-Q4, 2022_Q4, 2022Q4
    m = re.search(r"(20\d{2})[-_\s]?Q\s*([1-4])", name, flags=re.IGNORECASE)
    if m:
        return m.group(1), f"Q{m.group(2)}"
    # Accept patterns like Q4 2022 or Q4-2022
    m2 = re.search(r"Q\s*([1-4])[-_\s]?(20\d{2})", name, flags=re.IGNORECASE)
    if m2:
        return m2.group(2), f"Q{m2.group(1)}"
    return None


def ingest_distribution(label_root: Path) -> None:
    src_root = label_root / "distribution"
    canon_root = label_root / "distribution" / "canonical"

    # Convert xlsx → csv helpers first
    for xlsx in src_root.rglob("*.xlsx"):
        period = _infer_period_from_name(xlsx.as_posix())
        if not period:
            continue
        tmp_csv = xlsx.with_suffix("").with_name(xlsx.stem + "__converted.csv")
        try:
            xlsx_to_csv(xlsx, tmp_csv)
        except Exception:
            continue

    # Collect candidates per (year, quarter, statement_type)
    groups: dict[tuple[str, str, str], list[Path]] = {}
    info: dict[Path, dict] = {}
    for path in src_root.rglob("*.csv"):
        if "canonical" in path.parts:
            continue
        name_lower = path.name.lower()
        is_converted = path.name.endswith("__converted.csv")
        stype: Optional[str]
        if is_converted or "_rs_" in name_lower or "royalty" in path.as_posix().lower():
            stype = "royalty"
        elif "_tk_" in name_lower or "encoding" in path.as_posix().lower() or "tk cost" in path.as_posix().lower():
            stype = "encoding"
        else:
            continue
        period = _infer_period_from_name(path.as_posix())
        if not period:
            continue
        year, q = period
        key = (year, q, stype)
        groups.setdefault(key, []).append(path)
        info[path] = {
            "is_converted": is_converted,
            "name_lower": name_lower,
            "size": path.stat().st_size if path.exists() else 0,
        }

    # Choose the best candidate per group: prefer corrections/corrigido; else largest file; else converted
    def score(p: Path) -> tuple[int, int, int]:
        meta = info[p]
        # Prefer corrections only if they look like detailed statements (not tiny summaries)
        is_corr = ("correction" in meta["name_lower"] or "corrigido" in meta["name_lower"]) and meta["size"] > 10_000
        s1 = 1 if is_corr else 0
        s2 = meta["size"]
        s3 = 1 if meta["is_converted"] else 0
        return (s1, s2, s3)

    for (year, q, stype), paths in groups.items():
        chosen = sorted(paths, key=score, reverse=True)[0]
        chosen_meta = info[chosen]
        out = build_canonical_distribution(
            chosen,
            canon_root,
            year,
            q,
            stype,
            delimiter_in="," if chosen_meta["is_converted"] else ";",
            decimal_comma_to_dot=False if chosen_meta["is_converted"] else True,
        )
        sha = compute_sha256(chosen)
        meta = SourceFileMeta(
            path=str(chosen.resolve().relative_to(PATHS.repo_root)),
            sha256=sha,
            bytes=chosen.stat().st_size,
            mtime=chosen.stat().st_mtime,
            source="distribution",
            statement_type=stype,
            period=f"{year}-{q}",
            correction_of=("supersedes") if ("correction" in chosen_meta["name_lower"] or "corrigido" in chosen_meta["name_lower"]) else None,
        )
        write_meta_json(out.parent, meta)


def ingest_bandcamp(label_root: Path) -> None:
    bc_dir = label_root / "bandcamp"
    raw = next((p for p in bc_dir.glob("*.csv")), None)
    if not raw:
        return
    out = bc_dir / "canonical" / "bandcamp_all.csv"
    normalize_delimiter_and_decimal(raw, out, delimiter_in=",", delimiter_out=",", decimal_comma_to_dot=False)
    sha = compute_sha256(raw)
    meta = SourceFileMeta(
        path=str(raw.resolve().relative_to(PATHS.repo_root)),
        sha256=sha,
        bytes=raw.stat().st_size,
        mtime=raw.stat().st_mtime,
        source="bandcamp",
        statement_type="bandcamp",
        period="all",
    )
    write_meta_json(out.parent, meta)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest sources -> canonical for a label")
    parser.add_argument("--label", default="tropical-twista")
    parser.add_argument(
        "--path", default=str(PATHS.sources_root / "tropical-twista"), help="Path to label sources"
    )
    args = parser.parse_args()
    root = Path(args.path)
    ingest_distribution(root)
    ingest_bandcamp(root)
    print(f"Ingest completed for {root}")


if __name__ == "__main__":
    main()


