"""Rebuild the local DuckDB database and curated analytics layer."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
db_path = ROOT / "pulsemetrics.duckdb"
con = duckdb.connect(str(db_path))
for script in ["00_load_data.sql", "03_analytics_model.sql", "04_retention_analysis.sql"]:
    con.execute((ROOT / "sql" / script).read_text())
    con.fetchall()
print(f"Built {db_path.name}")
print(con.execute("SELECT MAX(month) FROM fct_monthly_account_metrics").fetchone()[0])
