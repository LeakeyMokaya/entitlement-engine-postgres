import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from db import get_engine

os.makedirs("reports", exist_ok=True)
df = pd.read_sql("SELECT * FROM impact_by_employee ORDER BY employee_id", get_engine())
for c in ["pay_current", "pay_proposed", "pay_change"]:
    df[c] = df[c].astype(float)

affected = df[df.pay_change != 0]
print("RULE CHANGE IMPACT (SYNTHETIC DATA): 2026.1 -> 2026.2-proposed")
print(f"Employees compared:   {len(df)}")
print(f"Employees affected:   {len(affected)} ({len(affected)/len(df):.1%})")
print(f"Total fortnightly pay, current:  ${df.pay_current.sum():,.2f}")
print(f"Total fortnightly pay, proposed: ${df.pay_proposed.sum():,.2f}")
print(f"Total change per fortnight:      ${df.pay_change.sum():,.2f}")
if len(affected):
    print(f"Average change (affected only):  ${affected.pay_change.mean():,.2f}")
    print(f"Largest single change:           ${affected.pay_change.max():,.2f}")

df.to_csv("reports/impact_by_employee_SYNTHETIC.csv", index=False)

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.hist(affected.pay_change, bins=20)
ax.set_xlabel("Change in fortnightly gross pay ($)")
ax.set_ylabel("Employees")
ax.set_title("Impact of proposed overtime rules (synthetic data)")
fig.tight_layout()
fig.savefig("reports/impact_histogram.png", dpi=150)
print("Saved reports/impact_by_employee_SYNTHETIC.csv and reports/impact_histogram.png")
