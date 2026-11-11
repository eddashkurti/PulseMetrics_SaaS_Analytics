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

## Report review checklist

- Executive scorecard: revenue, active accounts, churned subscriptions, active organizations, and seats.
- Revenue analysis: monthly trajectory and plan-tier mix.
- Retention analysis: churn reasons and signup-cohort retention.
- Adoption analysis: active organizations by product event.
- Customer success: health segmentation and account-priority queue.
- Drill-through: organization-level revenue, usage, subscription, and health context.

To refresh the model, rebuild the local DuckDB database from the Parquet inputs, confirm the quality checks pass, and refresh the Power BI source queries. The `.pbix` file is versioned for portfolio review; it is not a substitute for the reproducible SQL and Python model.

Power BI Desktop is required to open, refresh, or edit the `.pbix`. GitHub Actions cannot execute Power BI Desktop, so automated validation covers the shared Parquet/SQL/Python source layer and the metric validation report; visual refresh remains a documented desktop step.
