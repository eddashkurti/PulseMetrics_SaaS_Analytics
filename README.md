# PulseMetrics SaaS Analytics

An end-to-end B2B SaaS analytics project for revenue growth, churn, retention, customer segmentation, and product usage. Source data is stored as Parquet and the analysis layer uses DuckDB SQL, so it runs locally without a server.

## Repository layout

- `data/` — source Parquet files.
- `sql/00_load_data.sql` — loads Parquet into DuckDB tables.
- `sql/01_data_quality.sql` — uniqueness, null, referential-integrity, and range checks.
- `sql/02_metrics.sql` — reusable revenue, activity, churn, and KPI views.
- `reports/` and `powerbi/` — reserved for report and dashboard artifacts.

## Quick start

Install [DuckDB](https://duckdb.org/docs/installation/) and run from the repository root:

```text
duckdb pulsemetrics.duckdb -c ".read sql/00_load_data.sql"
duckdb pulsemetrics.duckdb -c ".read sql/01_data_quality.sql"
duckdb pulsemetrics.duckdb -c ".read sql/02_metrics.sql"
```

The SQL uses repository-relative paths and works after cloning on Windows, macOS, or Linux. The generated `pulsemetrics.duckdb` database and WAL files are ignored by Git.

## Metrics

`sql/02_metrics.sql` creates `monthly_revenue`, `organization_revenue`, `monthly_active_organizations`, and `churn_summary` views, followed by a compact KPI query for dashboard cards or CSV export.

## Data quality

Run the data-quality script before using the metrics. It checks duplicate IDs, required fields, invalid date ranges, negative invoice amounts, and orphaned foreign keys. Queries that return rows identify records requiring investigation; all other checks should return zero violations.

## Reproducibility

No generated database, WAL file, notebook checkpoint, or raw staging files are committed. Rebuild the local database from the versioned Parquet inputs and SQL scripts whenever needed.
