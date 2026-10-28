import sys
import pandas as pd
from calculator import calculate_pay
from db import get_engine

engine = get_engine()
rules_df = pd.read_sql("SELECT * FROM rule_sets", engine)
valid = pd.read_sql("SELECT * FROM valid_timesheets", engine)
sql_res = pd.read_sql("SELECT * FROM calc_results", engine)

all_pass = True
for _, r in rules_df.iterrows():
    rules = {
        "version": r.version,
        "ordinary_hours_per_fortnight": float(r.ordinary_hours),
        "overtime": {"band1_hours": float(r.ot_band1_hours),
                     "band1_multiplier": float(r.ot_band1_mult),
                     "band2_multiplier": float(r.ot_band2_mult)},
        "leave_accrual_rate": float(r.leave_accrual_rate),
    }
    py = valid.apply(
        lambda t: calculate_pay(float(t.hours_worked), float(t.hourly_rate), rules),
        axis=1, result_type="expand")
    py.insert(0, "employee_id", valid.employee_id.values)
    sql_v = sql_res[sql_res.rules_version == r.version]
    m = py.merge(sql_v, on="employee_id", suffixes=("_py", "_sql"))
    pay_diff = round((m.gross_pay_py - m.gross_pay_sql.astype(float)).abs().max(), 4)
    leave_diff = round((m.leave_accrued_hours_py - m.leave_accrued_hours_sql.astype(float)).abs().max(), 6)
    ok = len(m) == len(valid) == len(sql_v) and pay_diff <= 0.01 and leave_diff <= 0.0001
    all_pass &= ok
    print(f"{'PASS' if ok else 'FAIL'}: rules {r.version} - {len(m)} employees compared, "
          f"max pay difference ${pay_diff:.4f}, max leave difference {leave_diff:.6f} hrs")

sys.exit(0 if all_pass else 1)
