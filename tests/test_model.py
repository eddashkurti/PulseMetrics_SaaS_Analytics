"""Small deterministic regression suite for the curated analytical model."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]


def connection():
    con = duckdb.connect()
    for table in ["plans", "organizations", "users", "subscriptions", "invoices", "usage_events"]:
        path = (ROOT / "data" / f"{table}.parquet").as_posix()
        con.execute(f"CREATE OR REPLACE VIEW {table} AS SELECT * FROM read_parquet('{path}')")
    con.execute((ROOT / "sql" / "03_analytics_model.sql").read_text())
    con.execute((ROOT / "sql" / "04_retention_analysis.sql").read_text())
    return con


def test_curated_views_exist():
    con = connection()
    names = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert {"dim_organizations", "dim_plans", "fct_monthly_account_metrics", "customer_health", "cohort_retention"} <= names


def test_health_scores_are_bounded():
    con = connection()
    assert con.execute("SELECT COUNT(*) FROM customer_health WHERE health_score NOT BETWEEN 0 AND 100").fetchone()[0] == 0


def test_retention_is_bounded():
    con = connection()
    assert con.execute("SELECT COUNT(*) FROM cohort_retention WHERE retention_rate NOT BETWEEN 0 AND 100").fetchone()[0] == 0


def test_revenue_is_non_negative():
    con = connection()
    assert con.execute("SELECT COUNT(*) FROM fct_monthly_account_metrics WHERE billed_revenue < 0 OR mrr < 0").fetchone()[0] == 0


if __name__ == "__main__":
    for name in ["test_curated_views_exist", "test_health_scores_are_bounded", "test_retention_is_bounded", "test_revenue_is_non_negative"]:
        globals()[name]()
    print("PASS | analytical model regression tests")
