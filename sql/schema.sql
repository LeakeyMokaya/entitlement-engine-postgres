-- Entitlement Engine v2 (PostgreSQL). Synthetic data, illustrative rules.
-- Safe to re-run: it drops and recreates everything.

DROP VIEW  IF EXISTS impact_by_employee;
DROP VIEW  IF EXISTS valid_timesheets;
DROP TABLE IF EXISTS calc_results;
DROP TABLE IF EXISTS rejected_records;
DROP TABLE IF EXISTS raw_timesheets;
DROP TABLE IF EXISTS rule_sets;

CREATE TABLE rule_sets (
    version             TEXT PRIMARY KEY,
    ordinary_hours      NUMERIC NOT NULL,
    ot_band1_hours      NUMERIC NOT NULL,
    ot_band1_mult       NUMERIC NOT NULL,
    ot_band2_mult       NUMERIC NOT NULL,
    leave_accrual_rate  NUMERIC NOT NULL,
    status              TEXT NOT NULL
);

INSERT INTO rule_sets VALUES
 ('2026.1',          76, 8,  1.5, 2.0,  0.076923, 'current'),
 ('2026.2-proposed', 76, 8,  1.5, 2.25, 0.076923, 'proposed');

-- Raw data is loaded as-is (bad rows included) so nothing is silently lost.
CREATE TABLE raw_timesheets (
    employee_id   TEXT,
    hourly_rate   NUMERIC,
    hours_worked  NUMERIC
);

CREATE TABLE rejected_records (
    employee_id   TEXT,
    hourly_rate   NUMERIC,
    hours_worked  NUMERIC,
    reason        TEXT,
    rejected_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE calc_results (
    employee_id          TEXT NOT NULL,
    rules_version        TEXT NOT NULL REFERENCES rule_sets(version),
    ordinary_hours       NUMERIC,
    overtime_hours       NUMERIC,
    gross_pay            NUMERIC(12,2),
    leave_accrued_hours  NUMERIC(10,4),
    calculated_at        TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (employee_id, rules_version)
);

-- Same validation rule as v1: hours must be >= 0 and rate must be present.
CREATE VIEW valid_timesheets AS
SELECT * FROM raw_timesheets
WHERE hours_worked >= 0 AND hourly_rate IS NOT NULL;

-- Current rules vs proposed rules, one row per employee.
CREATE VIEW impact_by_employee AS
SELECT c.employee_id,
       c.gross_pay AS pay_current,
       p.gross_pay AS pay_proposed,
       p.gross_pay - c.gross_pay AS pay_change
FROM calc_results c
JOIN calc_results p ON p.employee_id = c.employee_id
WHERE c.rules_version = '2026.1' AND p.rules_version = '2026.2-proposed';
