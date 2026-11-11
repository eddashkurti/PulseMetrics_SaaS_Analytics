"""Fail-fast checks for source integrity and curated metric sanity."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
con = duckdb.connect()
for table in ["plans", "organizations", "users", "subscriptions", "invoices", "usage_events"]:
    path = (ROOT / "data" / f"{table}.parquet").as_posix()
    con.execute(f"CREATE OR REPLACE VIEW {table} AS SELECT * FROM read_parquet('{path}')")
con.execute((ROOT / "sql" / "03_analytics_model.sql").read_text())
con.fetchall()
con.execute((ROOT / "sql" / "04_retention_analysis.sql").read_text())
con.fetchall()

checks = {
    "duplicate organization IDs": "SELECT COUNT(*) - COUNT(DISTINCT organization_id) FROM organizations",
    "duplicate subscription IDs": "SELECT COUNT(*) - COUNT(DISTINCT subscription_id) FROM subscriptions",
    "duplicate invoice IDs": "SELECT COUNT(*) - COUNT(DISTINCT invoice_id) FROM invoices",
    "orphan subscriptions": "SELECT COUNT(*) FROM subscriptions s LEFT JOIN organizations o USING (organization_id) WHERE o.organization_id IS NULL",
    "orphan invoice subscriptions": "SELECT COUNT(*) FROM invoices i LEFT JOIN subscriptions s USING (subscription_id) WHERE s.subscription_id IS NULL",
    "invalid subscription dates": "SELECT COUNT(*) FROM subscriptions WHERE ended_on IS NOT NULL AND ended_on < started_on",
    "negative invoices": "SELECT COUNT(*) FROM invoices WHERE amount < 0",
    "negative MRR": "SELECT COUNT(*) FROM fct_monthly_account_metrics WHERE mrr < 0",
    "invalid retention rates": "SELECT COUNT(*) FROM cohort_retention WHERE retention_rate < 0 OR retention_rate > 100",
    "invalid health scores": "SELECT COUNT(*) FROM customer_health WHERE health_score < 0 OR health_score > 100",
}
failures = []
for name, sql in checks.items():
    value = con.execute(sql).fetchone()[0]
    print(f"{'PASS' if value == 0 else 'FAIL'} | {name}: {value}")
    if value:
        failures.append(name)
if failures:
    raise SystemExit("Quality checks failed: " + ", ".join(failures))
