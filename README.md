# Entitlement Engine (PostgreSQL)

A config-driven pay and leave entitlement engine built in Python and PostgreSQL. It calculates fortnightly gross pay and leave accrual from timesheet data, rejects invalid records with a recorded reason, and tests the impact of a proposed rule change before it is applied.

> **All data is synthetic and all rules are illustrative.** This is a learning project. It does not use real employee data and does not represent any real award or agreement.

## What it does

1. **Generates** 500 synthetic timesheet records (3 deliberately invalid).
2. **Loads** them untouched into PostgreSQL (`raw_timesheets`), so no bad row is silently lost.
3. **Validates** with a SQL view: hours must be 0 or more and the hourly rate must be present. Invalid rows go to `rejected_records` with a reason.
4. **Calculates** pay and leave for every valid employee under **two rule versions at once** (`2026.1` current, `2026.2-proposed`), using one set-based SQL statement.
5. **Reconciles** the SQL results against an independent Python calculator (within 1 cent).
6. **Reports the impact** of the proposed rules per employee and in total.

## Results (synthetic data)

| Check | Result |
|---|---|
| Records loaded | 500 |
| Records rejected (with reason) | 3 |
| Employees calculated, per rule version | 497 |
| SQL vs Python reconciliation | PASS for both versions (max difference 1 cent, from rounding) |
| Proposed rule change | second overtime band 2.0x to 2.25x |
| Employees affected | 69 of 497 (13.9%) |
| Total change per fortnight | +$3,098.49 |
| Average change (affected only) | +$44.91 |
| Largest single change | +$177.47 |

![Impact histogram](reports/impact_histogram.png)

## Project structure

| File | Purpose |
|---|---|
| `rules.yaml` | Rules used by the Python calculator (version 1) |
| `calculator.py` | Pure-Python pay and leave calculation |
| `generate_data.py` | Creates the synthetic timesheet data |
| `sql/schema.sql` | Tables, rule versions and views in PostgreSQL |
| `db.py` | Database connection (reads `DATABASE_URL` from `.env`) |
| `load_data.py` | Loads the CSV into `raw_timesheets` |
| `run_v2.py` | Rejects invalid rows and calculates pay under every rule version |
| `reconcile.py` | Compares SQL results with the Python calculator |
| `impact_report.py` | Rule-change impact summary, CSV and chart |
| `test_calculator.py`, `test_sql_results.py` | pytest tests |
| `run_pipeline.py`, `analysis.ipynb` | Version 1 (SQLite) pipeline and notebook |

## How to run it

Requires Python 3.10+ and PostgreSQL.

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
pip install -r requirements.txt
```

1. In PostgreSQL create a database called `entitlement`.
2. Create a `.env` file in the project folder (it is git-ignored, never commit it):
   ```
   DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/entitlement
   ```
3. Run:
   ```bash
   psql -U postgres -h localhost -d entitlement -f sql/schema.sql
   python generate_data.py
   python load_data.py
   python run_v2.py
   python reconcile.py
   python impact_report.py
   pytest
   ```

## Design decisions

- **Rules live in a table, not in code.** Adding a rule version is one `INSERT`, and every version is calculated side by side.
- **Raw data is never modified.** Rejections are recorded in their own table with a reason, which gives an audit trail.
- **Two implementations that must agree.** The SQL calculation is checked against a separate Python implementation. A mismatch fails the reconciliation.

## Limitations

- Synthetic data and simplified, illustrative rules: no penalty rates, allowances, tax or superannuation.
- Single fortnightly pay period; no employment history or back-pay.
- SQL rounds half-up and Python rounds half-to-even, so results can differ by up to 1 cent.
