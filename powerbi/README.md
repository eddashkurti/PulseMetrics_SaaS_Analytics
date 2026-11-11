# Power BI handoff

The repository ships the interactive dashboard as Streamlit and the completed Power BI report as `pulsemetrics.pbix`. The curated DuckDB views are designed to be consumed by Power BI:

- `dim_organizations`
- `dim_plans`
- `fct_subscription_months`
- `fct_monthly_account_metrics`
- `customer_health`
- `revenue_bridge`
- `cohort_retention`
- `segment_retention`

The report uses these views as its analytical source layer, relates organizations and plans through their keys, and follows the definitions in `docs/metric_definitions.md` as the measure specification. The Streamlit dashboard remains the reproducible local experience, while `pulsemetrics.pbix` is the Power BI presentation deliverable.
