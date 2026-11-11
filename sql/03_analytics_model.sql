-- Curated analytical layer. Run after 00_load_data.sql.
-- Grain is documented in the view names so downstream dashboard queries stay explicit.

CREATE OR REPLACE VIEW dim_organizations AS
SELECT organization_id, org_name, industry, country, employee_band,
       signed_up_on, acquisition_channel
FROM organizations;

CREATE OR REPLACE VIEW dim_plans AS
SELECT plan_id, plan_name, tier, monthly_price, seat_price,
       billing_interval, is_active
FROM plans;

CREATE OR REPLACE VIEW fct_subscription_months AS
WITH as_of AS (
    SELECT date_trunc('month', GREATEST(
        (SELECT MAX(period_end) FROM invoices),
        (SELECT MAX(occurred_at)::DATE FROM usage_events),
        (SELECT MAX(started_on) FROM subscriptions),
        (SELECT MAX(ended_on) FROM subscriptions)
    ))::DATE AS as_of_month
), calendar AS (
    SELECT month::DATE AS month
    FROM generate_series(
        date_trunc('month', (SELECT MIN(started_on) FROM subscriptions)),
        (SELECT as_of_month FROM as_of),
        INTERVAL '1 month'
    ) AS x(month)
)
SELECT s.subscription_id, s.organization_id, s.plan_id, c.month,
       s.seats,
       p.monthly_price + (p.seat_price * s.seats) AS contracted_mrr,
       CASE WHEN c.month >= date_trunc('month', s.started_on)
              AND (s.ended_on IS NULL OR c.month <= date_trunc('month', s.ended_on))
            THEN TRUE ELSE FALSE END AS is_active
FROM subscriptions s
JOIN dim_plans p USING (plan_id)
CROSS JOIN calendar c
WHERE c.month >= date_trunc('month', s.started_on)
  AND (s.ended_on IS NULL OR c.month <= date_trunc('month', s.ended_on));

CREATE OR REPLACE VIEW fct_monthly_account_metrics AS
WITH active AS (
    SELECT month, organization_id, SUM(contracted_mrr) AS mrr,
           SUM(seats) AS seats, COUNT(DISTINCT subscription_id) AS subscriptions
    FROM fct_subscription_months
    WHERE is_active GROUP BY 1, 2
), usage AS (
    SELECT date_trunc('month', occurred_at)::DATE AS month, organization_id,
           COUNT(*) AS product_events, COUNT(DISTINCT user_id) AS active_users,
           SUM(quantity) AS usage_quantity, MAX(occurred_at)::DATE AS last_activity
    FROM usage_events GROUP BY 1, 2
), invoice_status AS (
    SELECT s.organization_id, date_trunc('month', i.period_end)::DATE AS month,
           SUM(i.amount) FILTER (WHERE i.status IN ('paid', 'active')) AS billed_revenue,
           COUNT(*) FILTER (WHERE i.status IN ('paid', 'active')) AS successful_invoices
    FROM invoices i JOIN subscriptions s USING (subscription_id)
    GROUP BY 1, 2
)
SELECT COALESCE(a.month, u.month, inv.month) AS month,
       COALESCE(a.organization_id, u.organization_id, inv.organization_id) AS organization_id,
       COALESCE(a.mrr, 0) AS mrr, COALESCE(a.seats, 0) AS seats,
       COALESCE(a.subscriptions, 0) AS subscriptions,
       COALESCE(u.product_events, 0) AS product_events,
       COALESCE(u.active_users, 0) AS active_users,
       COALESCE(u.usage_quantity, 0) AS usage_quantity,
       u.last_activity, COALESCE(inv.billed_revenue, 0) AS billed_revenue,
       COALESCE(inv.successful_invoices, 0) AS successful_invoices
FROM active a
FULL OUTER JOIN usage u USING (month, organization_id)
FULL OUTER JOIN invoice_status inv USING (month, organization_id);

CREATE OR REPLACE VIEW customer_health AS
WITH latest AS (
    SELECT organization_id, MAX(month) AS latest_month
    FROM fct_monthly_account_metrics GROUP BY 1
), as_of AS (
    SELECT MAX(month) AS as_of_month FROM fct_monthly_account_metrics
), scored AS (
    SELECT o.organization_id, o.org_name, o.industry, o.country, o.employee_band,
           o.acquisition_channel, m.mrr, m.seats, m.active_users, m.product_events,
           m.last_activity, COALESCE(m.billed_revenue, 0) AS billed_revenue,
           CASE WHEN m.last_activity >= a.as_of_month - INTERVAL '30 days' THEN 30
                WHEN m.last_activity >= a.as_of_month - INTERVAL '60 days' THEN 15 ELSE 0 END
           + CASE WHEN m.active_users >= 5 THEN 25 WHEN m.active_users >= 2 THEN 15 ELSE 5 END
           + CASE WHEN m.product_events >= 20 THEN 25 WHEN m.product_events >= 5 THEN 15 ELSE 5 END
           + CASE WHEN m.mrr > 0 THEN 20 ELSE 0 END AS health_score
    FROM dim_organizations o JOIN latest l USING (organization_id) CROSS JOIN as_of a
    JOIN fct_monthly_account_metrics m
      ON m.organization_id = l.organization_id AND m.month = l.latest_month
)
SELECT *, CASE WHEN health_score >= 75 THEN 'Healthy'
               WHEN health_score >= 45 THEN 'Monitor' ELSE 'At risk' END AS health_segment
FROM scored;

CREATE OR REPLACE VIEW revenue_bridge AS
WITH monthly AS (
    SELECT month, SUM(mrr) AS ending_mrr
    FROM fct_monthly_account_metrics GROUP BY 1
), changes AS (
    SELECT month, ending_mrr,
           ending_mrr - LAG(ending_mrr) OVER (ORDER BY month) AS net_mrr_change
    FROM monthly
)
SELECT month, ending_mrr, COALESCE(net_mrr_change, 0) AS net_mrr_change,
       ending_mrr * 12 AS arr
FROM changes ORDER BY month;
