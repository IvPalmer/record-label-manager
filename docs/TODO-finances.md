## Finances module - next steps

This checklist captures the remaining work to finish the finances integration (ingest → normalize → payouts) inside Record Label Manager.

### 1) Dependencies and setup
- [x] Add data-processing deps to `backend/requirements.txt` (`openpyxl`, `chardet`, `python-dateutil`, `pycountry`, `Babel`, `requests`, `polars`).
- [x] Install requirements inside `backend/venv` (`pip install -r backend/requirements.txt`).

### 2) Data sources
- [x] Move source files into this repo under:
  - `finance/sources/tropical-twista/{bandcamp,distribution}/...`
- [x] Add `.gitignore` rules as needed (current tree keeps large statements outside version control).

### 3) Canonicalization pipeline (reuse existing code)
- [x] Copy `finance_pipeline/` package from label-manager-finance repo to `finance/pipeline/` here (same structure), or add it as a git submodule.
- [x] Verify ingest CLI runs in this repo:
  ```bash
  PYTHONPATH="$REPO_ROOT" python -m finance_pipeline.cli.ingest --label tropical-twista --path finance/sources/tropical-twista
  ```
- [x] Confirm canonical partition outputs under `finance/sources/tropical-twista/{bandcamp,distribution}/canonical/...` and `meta.json` lineage.

### 4) Django finances app
- [x] Run migrations for `backend/finances` models (latest migration `0004_delete_dwartist...` applied).
- [ ] Seed reference data: `Platform`, `Store`, `Country`, `DataSource` (double-check fixtures remain current after the latest cleanup).

### 5) Normalization to DB
- [x] Implement `backend/finances/management/commands/finances_ingest.py` that wraps the canonicalization (calls pipeline ingest and registers `SourceFile`).
- [x] Implement `finances_normalize` command:
  - Reads canonical CSVs
  - Maps provider/shop/country → `Platform`/`Store`/`Country`
  - Parses amounts, computes `row_hash`, dedupes per `SourceFile`
  - Links releases/tracks where metadata exists
  - Inserts `RevenueEvent`/`CostEvent`
  - Performs FX conversion to base currency

### 6) Payouts
- [x] Implement `finances_payout --label <id> --period YYYY-Q#` (command available, preview mode supported).
- [x] Add admin list and CSV export for payout runs.

### 7) Reporting & API
- [x] Add read-only endpoints for revenue KPIs, platform pie chart, monthly overview (see `RevenueAnalysisViewSet`).
- [ ] CLI/endpoint to export artist statements (CSV/PDF).

### 8) Multi-label standardization
- [ ] Prepare to ingest DSRPTV by adding its sources under `finance/sources/dsrptv/...` and reusing the same commands.
- [ ] Double-check all core facts reference `label_id` (current models support it, but ETL needs second-label smoke tests).

### 9) Cleanup
- [ ] After validation, deprecate the separate label-manager-finance repo; keep the `finance_pipeline` code inside this repo.

### 10) New follow-ups after latest run
- [ ] Capture regression tests for `finances_ingest`, `finances_normalize`, and `finances_payout` (smoke + fixtures).
- [ ] Wire the frontend analytics fetches to configurable base URLs (currently hard-coded to `http://127.0.0.1:8000`).
- [ ] Review finance admin UX to ensure datasets/analytics in docs match live figures after future imports.

### Notes
- Canonicalization rules: prefer detailed statements; corrections only if substantive; auto-pick Sales/Royalty/Detail sheets from XLSX.
- Amounts are stored both in original currency and in base EUR with `FxRate` lineage.
- Idempotency is guaranteed via `(source_file, row_hash)` across imports.

