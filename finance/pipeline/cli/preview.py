import argparse
from pathlib import Path
import polars as pl


def summarize_distribution(canonical_root: Path) -> pl.DataFrame:
    rows = []
    for csv_path in canonical_root.rglob("royalty.csv"):
        try:
            year = csv_path.parent.parent.name
            quarter = csv_path.parent.name
            df = pl.read_csv(csv_path, ignore_errors=True, truncate_ragged_lines=True)
            # Detect schema: Zebralution vs Labelworx
            cols = set(df.columns)
            # Zebralution style
            if {"Revenue-EUR", "Rev.less Publ.EUR"}.intersection(cols):
                revenue_col = next((c for c in ["Revenue-EUR", "Revenue_EUR", "Revenue EUR"] if c in cols), None)
                net_col = next((c for c in ["Rev.less Publ.EUR", "Rev_less_Publ_EUR", "Rev less Publ EUR"] if c in cols), None)
                sales_col = "Sales" if "Sales" in cols else None
                def to_f(col: str) -> pl.Series:
                    return (
                        df[col]
                        .cast(str)
                        .str.replace(" ", "")
                        .str.replace(",", ".")
                        .cast(pl.Float64, strict=False)
                    )
                revenue = float(to_f(revenue_col).sum()) if revenue_col else 0.0
                net = float(to_f(net_col).sum()) if net_col else revenue
                sales = int(df[sales_col].cast(pl.Int64, strict=False).sum()) if sales_col else 0
            # Labelworx style (Value, Royalty, Qty)
            elif {"Royalty", "Value"}.issubset(cols) or "Royalty" in cols:
                def to_flex(col: str) -> float:
                    if col not in cols:
                        return 0.0
                    return float(
                        df[col]
                        .cast(str)
                        .str.replace(" ", "")
                        .str.replace(",", "")
                        .str.replace("€", "")
                        .str.replace("$", "")
                        .cast(pl.Float64, strict=False)
                        .sum()
                        or 0.0
                    )
                revenue = to_flex("Value")
                net = to_flex("Royalty") or revenue
                sales = int(df["Qty"].cast(pl.Int64, strict=False).sum()) if "Qty" in cols else 0
            else:
                # Unknown schema; skip
                continue
            rows.append({"year": year, "quarter": quarter, "revenue_eur": revenue, "net_after_publ_eur": net, "sales": sales})
        except Exception:
            continue
    if not rows:
        return pl.DataFrame({"year": [], "quarter": [], "revenue_eur": [], "net_after_publ_eur": [], "sales": []})
    out = pl.from_dicts(rows).sort(["year", "quarter"]).with_columns([
        pl.col("revenue_eur").fill_null(0.0),
        pl.col("net_after_publ_eur").fill_null(0.0),
        pl.col("sales").fill_null(0),
    ])
    return out


def summarize_bandcamp(bandcamp_canonical: Path) -> pl.DataFrame:
    if not bandcamp_canonical.exists():
        return pl.DataFrame({"total_net_amount": []})
    df = pl.read_csv(
        bandcamp_canonical,
        ignore_errors=True,
        truncate_ragged_lines=True,
    )
    # Normalize column names to handle NUL chars or whitespace issues
    norm = {c: c.replace("\x00", "").strip().lower() for c in df.columns}
    colname = None
    for original, lowered in norm.items():
        if lowered in ("amount you received", "amount_you_received", "net amount", "net_amount"):
            colname = original
            break
    if not colname:
        return pl.DataFrame({"total_net_amount": []})
    total = (
        df[colname]
        .cast(str)
        .str.replace("$", "")
        .str.replace("€", "")
        .str.replace(",", "")
        .cast(pl.Float64, strict=False)
        .sum()
    )
    return pl.DataFrame({"total_net_amount": [float(total) if total is not None else 0.0]})


def summarize_bandcamp_quarterly(bandcamp_canonical: Path) -> pl.DataFrame:
    if not bandcamp_canonical.exists():
        return pl.DataFrame({"year": [], "quarter": [], "currency": [], "net_amount": []})
    df = pl.read_csv(
        bandcamp_canonical,
        ignore_errors=True,
        truncate_ragged_lines=True,
    )
    # Normalize headers (strip NULs, lower case)
    norm = {c: c.replace("\x00", "").strip().lower() for c in df.columns}
    # Resolve important columns
    date_col = next((orig for orig, low in norm.items() if low == "date"), None)
    currency_col = next((orig for orig, low in norm.items() if low == "currency"), None)
    amount_col = None
    for orig, low in norm.items():
        if low in ("amount you received", "amount_you_received", "net amount", "net_amount"):
            amount_col = orig
            break
    if not (date_col and currency_col and amount_col):
        return pl.DataFrame({"year": [], "quarter": [], "currency": [], "net_amount": []})
    cleaned = (
        df.rename({date_col: "date", currency_col: "currency", amount_col: "amount"})
        .with_columns([
            pl.col("amount")
            .cast(str)
            .str.replace("$", "")
            .str.replace("€", "")
            .str.replace(",", "")
            .cast(pl.Float64, strict=False)
            .alias("amount"),
            pl.col("date").cast(str).str.replace("\x00", "").str.replace("^\\s+|\\s+$", "").alias("date_clean"),
        ])
        .with_columns([
            pl.col("date_clean").str.replace(r"\s+.*$", "").alias("date_only"),
        ])
        .with_columns([
            pl.col("date_only").str.split("/").list.get(0).cast(pl.Int64).alias("month"),
            pl.col("date_only").str.split("/").list.get(2).cast(pl.Int64).alias("year_raw"),
        ])
        .with_columns([
            pl.when(pl.col("year_raw") < 100)
              .then(pl.col("year_raw") + 2000)
              .otherwise(pl.col("year_raw"))
              .cast(pl.Int64)
              .alias("year"),
            ((pl.col("month") - 1) // 3 + 1).cast(pl.Int64).alias("quarter"),
        ])
        .drop_nulls(["year", "quarter"])
    )
    out = (
        cleaned
        .group_by(["year", "quarter", "currency"], maintain_order=True)
        .agg(pl.sum("amount").alias("net_amount"))
        .sort(["year", "quarter", "currency"]) 
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview canonical summaries")
    parser.add_argument("--label", default="tropical-twista")
    parser.add_argument("--path", required=True, help="Path to label sources root")
    args = parser.parse_args()
    root = Path(args.path)
    dist_canon = root / "distribution" / "canonical"
    bc_canon = root / "bandcamp" / "canonical" / "bandcamp_all.csv"
    dist = summarize_distribution(dist_canon)
    bc = summarize_bandcamp(bc_canon)
    bc_q = summarize_bandcamp_quarterly(bc_canon)
    print("Distribution summary (EUR):")
    if dist.height:
        print(dist)
    else:
        print("No distribution canonical data found")
    print("\nBandcamp total net (original currency sums, naive):")
    if bc.height:
        print(bc)
    else:
        print("No bandcamp canonical data found")
    print("\nBandcamp quarterly net by currency:")
    if bc_q.height:
        print(bc_q)
    else:
        print("No bandcamp quarterly breakdown found")
    preview_dir = root.parent.parent / "finance" / "pipeline" / "storage" / "warehouse" / "preview"
    preview_dir.mkdir(parents=True, exist_ok=True)
    dist.write_csv(preview_dir / f"{args.label}_distribution_summary.csv")
    bc.write_csv(preview_dir / f"{args.label}_bandcamp_total.csv")
    bc_q.write_csv(preview_dir / f"{args.label}_bandcamp_quarterly.csv")
    print(f"\nWrote CSV previews to {preview_dir}")


if __name__ == "__main__":
    main()


