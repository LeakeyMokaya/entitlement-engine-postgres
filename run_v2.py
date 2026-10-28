from sqlalchemy import text
from db import get_engine

engine = get_engine()

REJECT_SQL = """
INSERT INTO rejected_records (employee_id, hourly_rate, hours_worked, reason)
SELECT employee_id, hourly_rate, hours_worked,
       CASE WHEN hourly_rate IS NULL THEN 'missing hourly rate'
            WHEN hours_worked IS NULL THEN 'missing hours'
            ELSE 'negative hours' END
FROM raw_timesheets
WHERE NOT (hours_worked >= 0 AND hourly_rate IS NOT NULL);
"""

CALC_SQL = """
INSERT INTO calc_results
    (employee_id, rules_version, ordinary_hours, overtime_hours, gross_pay, leave_accrued_hours)
SELECT employee_id, version, ordinary, overtime,
       ROUND(ordinary * hourly_rate
             + band1 * hourly_rate * ot_band1_mult
             + (overtime - band1) * hourly_rate * ot_band2_mult, 2),
       ROUND(ordinary * leave_accrual_rate, 4)
FROM (
    SELECT t.employee_id, t.hourly_rate, r.version, r.ot_band1_mult,
           r.ot_band2_mult, r.leave_accrual_rate,
           LEAST(t.hours_worked, r.ordinary_hours)               AS ordinary,
           GREATEST(t.hours_worked - r.ordinary_hours, 0)        AS overtime,
           LEAST(GREATEST(t.hours_worked - r.ordinary_hours, 0),
                 r.ot_band1_hours)                               AS band1
    FROM valid_timesheets t
    CROSS JOIN rule_sets r
) x;
"""

with engine.begin() as conn:
    conn.execute(text("TRUNCATE calc_results, rejected_records"))
    conn.execute(text(REJECT_SQL))
    conn.execute(text(CALC_SQL))
    rejected = conn.execute(text("SELECT COUNT(*) FROM rejected_records")).scalar()
    rows = conn.execute(text(
        "SELECT rules_version, COUNT(*) FROM calc_results GROUP BY 1 ORDER BY 1")).all()

print(f"Rejected: {rejected}")
for version, n in rows:
    print(f"Calculated {n} employees under rules {version}")
