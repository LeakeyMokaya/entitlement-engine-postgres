import pandas as pd
from sqlalchemy import text
from db import get_engine

df = pd.read_csv("data/employees.csv")
engine = get_engine()

with engine.begin() as conn:
    conn.execute(text("TRUNCATE raw_timesheets"))
    df.to_sql("raw_timesheets", conn, if_exists="append", index=False)
    n = conn.execute(text("SELECT COUNT(*) FROM raw_timesheets")).scalar()
    versions = conn.execute(text("SELECT version FROM rule_sets ORDER BY version")).scalars().all()

print(f"Loaded {n} rows into raw_timesheets")
print(f"Rule versions available: {versions}")
