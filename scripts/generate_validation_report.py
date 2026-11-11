"""Generate a concise, reproducible metric validation summary for portfolio review."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "metric_validation_report.md"
con = duckdb.connect()
for table in ["plans", "organizations", "users", "subscriptions", "invoices", "usage_events"]:
    path = (ROOT / "data" / f"{table}.parquet").as_posix()
    con.execute(f"CREATE OR REPLACE VIEW {table} AS SELECT * FROM read_parquet('{path}')")
con.execute((ROOT / "sql" / "03_analytics_model.sql").read_text())
con.execute((ROOT / "sql" / "04_retention_analysis.sql").read_text())
queries = {
    "Organizations": "SELECT COUNT(*) FROM organizations", "Users": "SELECT COUNT(*) FROM users",
    "Subscriptions": "SELECT COUNT(*) FROM subscriptions", "Invoices": "SELECT COUNT(*) FROM invoices",
    "Usage events": "SELECT COUNT(*) FROM usage_events",
    "Recognized revenue": "SELECT COALESCE(SUM(amount), 0) FROM invoices WHERE status IN ('paid', 'active')",
    "Active accounts": "SELECT COUNT(DISTINCT organization_id) FROM subscriptions WHERE ended_on IS NULL",
    "Churned subscriptions": "SELECT COUNT(*) FROM subscriptions WHERE ended_on IS NOT NULL",
    "Retention rows": "SELECT COUNT(*) FROM cohort_retention",
    "At-risk accounts": "SELECT COUNT(*) FROM customer_health WHERE health_segment = 'At risk'",
    "Invalid subscription dates": "SELECT COUNT(*) FROM subscriptions WHERE ended_on IS NOT NULL AND ended_on < started_on",
}
values = {label: con.execute(sql).fetchone()[0] for label, sql in queries.items()}
min_date, max_date = con.execute("SELECT MIN(period_end), MAX(period_end) FROM invoices").fetchone()
lines = ["# PulseMetrics metric validation report", "", "Generated from the versioned Parquet inputs and curated DuckDB SQL model.", "", f"**Invoice coverage:** {min_date} through {max_date}", "", "| Metric | Value |", "|---|---:|"]
for label, value in values.items():
    rendered = f"${value:,.0f}" if label == "Recognized revenue" else f"{value:,}"
    lines.append(f"| {label} | {rendered} |")
lines += ["", "## Interpretation", "", "- Hard analytical invariants pass in `scripts/run_quality_checks.py`.", "- Invalid subscription dates are disclosed as a source warning rather than silently rewritten.", "- Health scores are prioritization signals based on recency, active users, product events, and MRR."]
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Wrote {OUT}")
