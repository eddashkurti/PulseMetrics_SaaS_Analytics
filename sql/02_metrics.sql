-- Reusable business metrics. Run sql/00_load_data.sql first in the same DuckDB session.

CREATE OR REPLACE VIEW monthly_revenue AS
SELECT date_trunc('month', period_end)::DATE AS month,
       SUM(amount) FILTER (WHERE status IN ('paid', 'active')) AS revenue,
       COUNT(DISTINCT subscription_id) FILTER (WHERE status IN ('paid', 'active')) AS paying_subscriptions
FROM invoices GROUP BY 1 ORDER BY 1;

CREATE OR REPLACE VIEW organization_revenue AS
SELECT o.organization_id, o.org_name, o.industry, o.country, o.employee_band,
       p.tier, p.billing_interval,
       SUM(i.amount) FILTER (WHERE i.status IN ('paid', 'active')) AS lifetime_revenue,
       MAX(i.period_end)::DATE AS latest_invoice_date
FROM organizations o
LEFT JOIN subscriptions s ON s.organization_id = o.organization_id
LEFT JOIN plans p ON p.plan_id = s.plan_id
LEFT JOIN invoices i ON i.subscription_id = s.subscription_id
GROUP BY ALL;

CREATE OR REPLACE VIEW monthly_active_organizations AS
SELECT date_trunc('month', occurred_at)::DATE AS month,
       COUNT(DISTINCT organization_id) AS active_organizations,
       COUNT(*) AS total_events, SUM(quantity) AS total_quantity
FROM usage_events GROUP BY 1 ORDER BY 1;

CREATE OR REPLACE VIEW churn_summary AS
SELECT date_trunc('month', ended_on)::DATE AS churn_month,
       COUNT(*) AS churned_subscriptions,
       COUNT(DISTINCT organization_id) AS churned_organizations,
       SUM(seats) AS churned_seats, cancel_reason
FROM subscriptions WHERE ended_on IS NOT NULL
GROUP BY 1, cancel_reason ORDER BY 1, cancel_reason;

SELECT (SELECT COUNT(*) FROM organizations) AS organizations,
       (SELECT COUNT(*) FROM users) AS users,
       (SELECT COUNT(*) FROM subscriptions WHERE ended_on IS NULL) AS active_subscriptions,
       (SELECT COALESCE(SUM(amount), 0) FROM invoices WHERE status IN ('paid', 'active')) AS recognized_revenue,
       (SELECT COUNT(DISTINCT organization_id) FROM usage_events) AS active_organizations;
