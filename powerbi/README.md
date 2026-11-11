# Power BI handoff

The repository currently ships the interactive dashboard as Streamlit; no Power BI Desktop file is committed yet. The curated DuckDB views are designed to be consumed by Power BI:

- `dim_organizations`
- `dim_plans`
- `fct_subscription_months`
- `fct_monthly_account_metrics`
- `customer_health`
- `revenue_bridge`
- `cohort_retention`
- `segment_retention`

For a Power BI implementation, load these views as the semantic layer, relate organizations and plans through their keys, and use the definitions in `docs/metric_definitions.md` as the measure specification. The Streamlit dashboard remains the runnable local experience until a `.pbix` or `.pbit` artifact is created.
