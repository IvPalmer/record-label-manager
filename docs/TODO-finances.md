## Finances module - next steps

This checklist captures the remaining work to finish the finances integration (ingest → normalize → payouts) inside Record Label Manager.

### 1) Dependencies and setup
- [ ] Add data-processing deps to backend/requirements.txt: `openpyxl`, `chardet`, `python-dateutil`, `pycountry`, `Babel`, `requests`, `polars`.
- [ ] `pip install -r backend/requirements.txt` in the RLM backend venv.

### 2) Data sources
- [ ] Move source files into this repo under:
  - `finance/sources/tropical-twista/{bandcamp,distribution}/...`
- [ ] Commit `.gitignore` entries for large binary files if needed.

### 3) Canonicalization pipeline (reuse existing code)
- [ ] Copy `finance_pipeline/` package from label-manager-finance repo to `finance/pipeline/` here (same structure), or add it as a git submodule.
- [ ] Verify ingest CLI runs in this repo:
  ```bash
  PYTHONPATH="$REPO_ROOT" python -m finance_pipeline.cli.ingest --label tropical-twista --path finance/sources/tropical-twista
  ```
- [ ] Confirm canonical partition outputs under `finance/sources/tropical-twista/{bandcamp,distribution}/canonical/...` and `meta.json` lineage.

### 4) Django finances app
- [ ] Run migrations for `backend/finances` models.
  ```bash
  cd backend
  python manage.py makemigrations finances
  python manage.py migrate
  ```
- [ ] Seed reference data: `Platform`, `Store`, `Country`, `DataSource` (simple fixtures or admin).

### 5) Normalization to DB
- [ ] Implement `backend/finances/management/commands/finances_ingest.py` that wraps the canonicalization (calls pipeline ingest and registers `SourceFile`).
- [ ] Implement `finances_normalize` command:
  - Read canonical CSVs
  - Map provider/shop/country → `Platform`/`Store`/`Country`
  - Parse amounts; compute `row_hash` and dedupe per `SourceFile`
  - Link `Release`/`Track` (ISRC/UPC/EAN/label_order_nr; fallback to fuzzy title/artist)
  - Insert `RevenueEvent` (and `CostEvent` when present)
  - FX conversion to EUR using `FxRate`

### 6) Payouts
- [ ] Implement `finances_payout --label <id> --period YYYY-Q#`:
  - Load `RevenueEvent`s in period
  - Apply `Contract`/`ContractParty` rates (basis: gross/net/platform_net)
  - Apply `RecoupmentAccount` balances
  - Write `PayoutRun` + `PayoutLine`s
- [ ] Add admin list and CSV export for payout runs.

### 7) Reporting & API
- [ ] Add read-only endpoints for distribution summary and bandcamp quarterly breakdown.
- [ ] CLI/endpoint to export artist statements (CSV/PDF).

### 8) Multi-label standardization
- [ ] Prepare to ingest DSRPTV by adding its sources under `finance/sources/dsrptv/...` and reusing the same commands.
- [ ] Ensure all core facts reference `label_id` and are platform/vendor-neutral (already modeled).

### 9) Cleanup
- [ ] After validation, deprecate the separate label-manager-finance repo; keep the `finance_pipeline` code inside this repo.

### Notes
- Canonicalization rules: prefer detailed statements; corrections only if substantive; auto-pick Sales/Royalty/Detail sheets from XLSX.
- Amounts are stored both in original currency and in base EUR with `FxRate` lineage.
- Idempotency is guaranteed via `(source_file, row_hash)` across imports.


