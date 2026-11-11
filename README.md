# PulseMetrics SaaS Analytics

An end-to-end B2B SaaS analytics project for revenue growth, churn, retention, customer segmentation, and product usage. Source data is stored as Parquet, the analytical layer uses DuckDB SQL, and the implemented interactive dashboard uses Streamlit. The curated SQL views are also structured for a Power BI semantic model.

## Repository layout

- `data/` — source Parquet files.
- `sql/00_load_data.sql` — loads Parquet into DuckDB tables.
- `sql/01_data_quality.sql` — uniqueness, null, referential-integrity, and range checks.
- `sql/02_metrics.sql` — reusable revenue, activity, churn, and KPI views.
- `sql/03_analytics_model.sql` — curated subscription-month, account-metric, revenue-bridge, and customer-health model.
- `sql/04_retention_analysis.sql` — cohort retention and segment-retention views.
- `dashboard/app.py` — interactive Streamlit dashboard.
- `docs/metric_definitions.md` — metric definitions and analytical assumptions.
- `reports/` — reserved for exported analysis and dashboard documentation.
- `powerbi/` — Power BI model guidance and future `.pbix`/`.pbit` artifacts.

## Quick start

Install [DuckDB](https://duckdb.org/docs/installation/) and run from the repository root:

```text
duckdb pulsemetrics.duckdb -c ".read sql/00_load_data.sql"
duckdb pulsemetrics.duckdb -c ".read sql/01_data_quality.sql"
duckdb pulsemetrics.duckdb -c ".read sql/02_metrics.sql"
duckdb pulsemetrics.duckdb -c ".read sql/03_analytics_model.sql"
duckdb pulsemetrics.duckdb -c ".read sql/04_retention_analysis.sql"
```

Or rebuild and validate the complete model with Python:

```text
py -3.13 scripts/build_model.py
py -3.13 scripts/run_quality_checks.py
```

The SQL uses repository-relative paths and works after cloning on Windows, macOS, or Linux. The generated `pulsemetrics.duckdb` database and WAL files are ignored by Git.

## Metrics

`sql/02_metrics.sql` creates `monthly_revenue`, `organization_revenue`, `monthly_active_organizations`, and `churn_summary` views, followed by a compact KPI query for dashboard cards or CSV export.

Launch the interactive dashboard with:

```text
py -3.13 -m pip install -r requirements.txt
py -3.13 -m streamlit run dashboard/app.py
```

The dashboard includes executive KPIs, revenue mix, churn reasons, product adoption, cohort retention, account portfolio analysis, and an explainable customer-health queue. The `sql/03_analytics_model.sql` and `sql/04_retention_analysis.sql` views provide the clean source layer for Power BI if a `.pbix` report is added later.

GitHub Actions runs Python compilation and the data-quality suite on every push and pull request.

## Data quality

Run the data-quality script before using the metrics. It checks duplicate IDs, required fields, invalid date ranges, negative invoice amounts, and orphaned foreign keys. Queries that return rows identify records requiring investigation; all other checks should return zero violations.

## Reproducibility

No generated database, WAL file, notebook checkpoint, or raw staging files are committed. Rebuild the local database from the versioned Parquet inputs and SQL scripts whenever needed.
