"""Profile all source Parquet tables and print a compact data dictionary."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = duckdb.connect()
tables = ["plans", "organizations", "users", "subscriptions", "invoices", "usage_events"]

for table in tables:
    path = (ROOT / "data" / f"{table}.parquet").as_posix()
    relation = f"read_parquet('{path}')"
    count = DB.execute(f"SELECT count(*) FROM {relation}").fetchone()[0]
    print(f"## {table} ({count:,} rows)")
    for name, dtype, *_ in DB.execute(f"DESCRIBE SELECT * FROM {relation}").fetchall():
        print(f"- `{name}`: {dtype}")
    print()
