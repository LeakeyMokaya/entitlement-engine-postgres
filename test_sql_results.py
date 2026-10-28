"""Checks on the PostgreSQL results. Run the pipeline first:
python load_data.py ; python run_v2.py
These tests are skipped automatically if the database is not reachable."""
import pandas as pd
import pytest
from sqlalchemy.exc import OperationalError

from calculator import calculate_pay
from db import get_engine


@pytest.fixture(scope="module")
def engine():
    try:
        eng = get_engine()
        with eng.connect():
            pass
    except (OperationalError, KeyError):
        pytest.skip("PostgreSQL not reachable - check .env and that the service is running")
    return eng


def test_every_raw_row_is_either_calculated_or_rejected(engine):
    raw = pd.read_sql("SELECT COUNT(*) n FROM raw_timesheets", engine).n[0]
    rejected = pd.read_sql("SELECT COUNT(*) n FROM rejected_records", engine).n[0]
    calculated = pd.read_sql(
        "SELECT COUNT(*) n FROM calc_results WHERE rules_version = '2026.1'", engine).n[0]
    assert raw == rejected + calculated


def test_each_rule_version_calculates_the_same_employees(engine):
    counts = pd.read_sql(
        "SELECT rules_version, COUNT(*) n FROM calc_results GROUP BY 1", engine)
    assert counts.n.nunique() == 1
    assert len(counts) == 2


def test_rejected_records_have_a_reason_and_are_actually_invalid(engine):
    rej = pd.read_sql("SELECT * FROM rejected_records", engine)
    assert rej.reason.notna().all()
    invalid = (rej.hours_worked < 0) | rej.hourly_rate.isna() | rej.hours_worked.isna()
    assert invalid.all()


def test_no_negative_pay_or_leave(engine):
    res = pd.read_sql("SELECT * FROM calc_results", engine)
    assert (res.gross_pay.astype(float) >= 0).all()
    assert (res.leave_accrued_hours.astype(float) >= 0).all()


def test_sql_matches_python_calculator_within_one_cent(engine):
    rules_df = pd.read_sql("SELECT * FROM rule_sets", engine)
    valid = pd.read_sql("SELECT * FROM valid_timesheets", engine)
    sql_res = pd.read_sql("SELECT * FROM calc_results", engine)
    for _, r in rules_df.iterrows():
        rules = {
            "version": r.version,
            "ordinary_hours_per_fortnight": float(r.ordinary_hours),
            "overtime": {"band1_hours": float(r.ot_band1_hours),
                         "band1_multiplier": float(r.ot_band1_mult),
                         "band2_multiplier": float(r.ot_band2_mult)},
            "leave_accrual_rate": float(r.leave_accrual_rate),
        }
        sql_v = sql_res[sql_res.rules_version == r.version].set_index("employee_id")
        for t in valid.itertuples():
            expected = calculate_pay(float(t.hours_worked), float(t.hourly_rate), rules)
            assert abs(expected["gross_pay"] - float(sql_v.loc[t.employee_id, "gross_pay"])) <= 0.0101


def test_proposed_rules_never_reduce_pay(engine):
    """The proposed change only raises the second overtime multiplier."""
    impact = pd.read_sql("SELECT pay_change FROM impact_by_employee", engine)
    assert (impact.pay_change.astype(float) >= -0.0101).all()
