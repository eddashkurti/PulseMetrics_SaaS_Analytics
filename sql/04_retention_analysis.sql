-- Cohort retention views. Run after 00_load_data.sql and 03_analytics_model.sql.

CREATE OR REPLACE VIEW customer_cohorts AS
SELECT organization_id, date_trunc('month', signed_up_on)::DATE AS cohort_month,
       industry, country, employee_band, acquisition_channel
FROM dim_organizations;

CREATE OR REPLACE VIEW cohort_retention AS
WITH cohort_sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_accounts
    FROM customer_cohorts GROUP BY 1
), active_months AS (
    SELECT DISTINCT m.organization_id, c.cohort_month,
           date_diff('month', c.cohort_month, m.month) AS month_number
    FROM fct_monthly_account_metrics m
    JOIN customer_cohorts c USING (organization_id)
    WHERE m.mrr > 0
), retained AS (
    SELECT cohort_month, month_number, COUNT(*) AS retained_accounts
    FROM active_months WHERE month_number >= 0 GROUP BY 1, 2
)
SELECT r.cohort_month, r.month_number, s.cohort_accounts,
       r.retained_accounts,
       ROUND(100.0 * r.retained_accounts / NULLIF(s.cohort_accounts, 0), 1) AS retention_rate
FROM retained r JOIN cohort_sizes s USING (cohort_month)
ORDER BY 1, 2;

CREATE OR REPLACE VIEW segment_retention AS
WITH cohort AS (
    SELECT c.industry, c.acquisition_channel, c.organization_id,
           MAX(m.month) AS last_active_month
    FROM customer_cohorts c JOIN fct_monthly_account_metrics m USING (organization_id)
    WHERE m.mrr > 0 GROUP BY 1, 2, 3
)
SELECT cohort.industry, cohort.acquisition_channel, COUNT(*) AS active_accounts,
       ROUND(AVG(date_diff('month', date_trunc('month', o.signed_up_on), last_active_month)), 1) AS avg_active_months
FROM cohort JOIN organizations o USING (organization_id)
GROUP BY 1, 2 ORDER BY active_accounts DESC;
