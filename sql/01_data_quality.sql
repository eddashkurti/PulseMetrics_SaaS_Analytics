SELECT 'plans' AS table_name, COUNT(*) AS row_count
FROM plans
UNION ALL
SELECT 'organizations', COUNT(*)
FROM organizations
UNION ALL
SELECT 'users', COUNT(*)
FROM users
UNION ALL
SELECT 'subscriptions', COUNT(*)
FROM subscriptions
UNION ALL
SELECT 'invoices', COUNT(*)
FROM invoices
UNION ALL
SELECT 'usage_events', COUNT(*)
FROM usage_events;

SELECT
    'plans' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT plan_id) AS unique_ids,
    COUNT(*) - COUNT(DISTINCT plan_id) AS duplicate_ids
FROM plans
UNION ALL
SELECT
    'organizations',
    COUNT(*),
    COUNT(DISTINCT organization_id),
    COUNT(*) - COUNT(DISTINCT organization_id)
FROM organizations
UNION ALL
SELECT
    'users',
    COUNT(*),
    COUNT(DISTINCT user_id),
    COUNT(*) - COUNT(DISTINCT user_id)
FROM users
UNION ALL
SELECT
    'subscriptions',
    COUNT(*),
    COUNT(DISTINCT subscription_id),
    COUNT(*) - COUNT(DISTINCT subscription_id)
FROM subscriptions
UNION ALL
SELECT
    'invoices',
    COUNT(*),
    COUNT(DISTINCT invoice_id),
    COUNT(*) - COUNT(DISTINCT invoice_id)
FROM invoices
UNION ALL
SELECT
    'usage_events',
    COUNT(*),
    COUNT(DISTINCT event_id),
    COUNT(*) - COUNT(DISTINCT event_id)
FROM usage_events;

SELECT
    SUM(CASE WHEN organization_id IS NULL THEN 1 ELSE 0 END) AS null_organization_id,
    SUM(CASE WHEN org_name IS NULL THEN 1 ELSE 0 END) AS null_org_name,
    SUM(CASE WHEN industry IS NULL THEN 1 ELSE 0 END) AS null_industry,
    SUM(CASE WHEN country IS NULL THEN 1 ELSE 0 END) AS null_country,
    SUM(CASE WHEN signed_up_on IS NULL THEN 1 ELSE 0 END) AS null_signed_up_on
FROM organizations;

SELECT
    SUM(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END) AS null_user_id,
    SUM(CASE WHEN organization_id IS NULL THEN 1 ELSE 0 END) AS null_organization_id,
    SUM(CASE WHEN email IS NULL THEN 1 ELSE 0 END) AS null_email,
    SUM(CASE WHEN role IS NULL THEN 1 ELSE 0 END) AS null_role,
    SUM(CASE WHEN joined_on IS NULL THEN 1 ELSE 0 END) AS null_joined_on
FROM users;

SELECT
    SUM(CASE WHEN subscription_id IS NULL THEN 1 ELSE 0 END) AS null_subscription_id,
    SUM(CASE WHEN organization_id IS NULL THEN 1 ELSE 0 END) AS null_organization_id,
    SUM(CASE WHEN plan_id IS NULL THEN 1 ELSE 0 END) AS null_plan_id,
    SUM(CASE WHEN started_on IS NULL THEN 1 ELSE 0 END) AS null_started_on,
    SUM(CASE WHEN seats IS NULL THEN 1 ELSE 0 END) AS null_seats
FROM subscriptions;

SELECT
    SUM(CASE WHEN invoice_id IS NULL THEN 1 ELSE 0 END) AS null_invoice_id,
    SUM(CASE WHEN subscription_id IS NULL THEN 1 ELSE 0 END) AS null_subscription_id,
    SUM(CASE WHEN issued_on IS NULL THEN 1 ELSE 0 END) AS null_issued_on,
    SUM(CASE WHEN period_start IS NULL THEN 1 ELSE 0 END) AS null_period_start,
    SUM(CASE WHEN period_end IS NULL THEN 1 ELSE 0 END) AS null_period_end,
    SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END) AS null_amount,
    SUM(CASE WHEN status IS NULL THEN 1 ELSE 0 END) AS null_status
FROM invoices;

SELECT
    SUM(CASE WHEN event_id IS NULL THEN 1 ELSE 0 END) AS null_event_id,
    SUM(CASE WHEN organization_id IS NULL THEN 1 ELSE 0 END) AS null_organization_id,
    SUM(CASE WHEN occurred_at IS NULL THEN 1 ELSE 0 END) AS null_occurred_at,
    SUM(CASE WHEN event_type IS NULL THEN 1 ELSE 0 END) AS null_event_type,
    SUM(CASE WHEN quantity IS NULL THEN 1 ELSE 0 END) AS null_quantity
FROM usage_events;

SELECT *
FROM subscriptions
WHERE ended_on IS NOT NULL
  AND ended_on < started_on;

SELECT *
FROM subscriptions
WHERE seats <= 0;

SELECT *
FROM invoices
WHERE amount < 0;

SELECT *
FROM invoices
WHERE period_end < period_start
   OR issued_on > period_end;

SELECT *
FROM users
WHERE deactivated_on IS NOT NULL
  AND deactivated_on < joined_on;

SELECT s.*
FROM subscriptions s
LEFT JOIN organizations o
    ON s.organization_id = o.organization_id
WHERE o.organization_id IS NULL;

SELECT s.*
FROM subscriptions s
LEFT JOIN plans p
    ON s.plan_id = p.plan_id
WHERE p.plan_id IS NULL;

SELECT i.*
FROM invoices i
LEFT JOIN subscriptions s
    ON i.subscription_id = s.subscription_id
WHERE s.subscription_id IS NULL;

SELECT u.*
FROM users u
LEFT JOIN organizations o
    ON u.organization_id = o.organization_id
WHERE o.organization_id IS NULL;

SELECT ue.*
FROM usage_events ue
LEFT JOIN organizations o
    ON ue.organization_id = o.organization_id
WHERE o.organization_id IS NULL;

SELECT ue.*
FROM usage_events ue
LEFT JOIN users u
    ON ue.user_id = u.user_id
WHERE ue.user_id IS NOT NULL
  AND u.user_id IS NULL;

SELECT tier, COUNT(*) AS row_count
FROM plans
GROUP BY tier
ORDER BY row_count DESC;

SELECT billing_interval, COUNT(*) AS row_count
FROM plans
GROUP BY billing_interval
ORDER BY row_count DESC;

SELECT is_active, COUNT(*) AS row_count
FROM plans
GROUP BY is_active
ORDER BY row_count DESC;

SELECT industry, COUNT(*) AS row_count
FROM organizations
GROUP BY industry
ORDER BY row_count DESC;

SELECT country, COUNT(*) AS row_count
FROM organizations
GROUP BY country
ORDER BY row_count DESC;

SELECT employee_band, COUNT(*) AS row_count
FROM organizations
GROUP BY employee_band
ORDER BY row_count DESC;

SELECT acquisition_channel, COUNT(*) AS row_count
FROM organizations
GROUP BY acquisition_channel
ORDER BY row_count DESC;

SELECT role, COUNT(*) AS row_count
FROM users
GROUP BY role
ORDER BY row_count DESC;

SELECT status, COUNT(*) AS row_count
FROM invoices
GROUP BY status
ORDER BY row_count DESC;

SELECT cancel_reason, COUNT(*) AS row_count
FROM subscriptions
GROUP BY cancel_reason
ORDER BY row_count DESC;

SELECT event_type, COUNT(*) AS row_count
FROM usage_events
GROUP BY event_type
ORDER BY row_count DESC;

SELECT
    MIN(signed_up_on) AS earliest_signup,
    MAX(signed_up_on) AS latest_signup
FROM organizations;

SELECT
    MIN(started_on) AS earliest_subscription,
    MAX(started_on) AS latest_subscription,
    MIN(ended_on) AS earliest_end,
    MAX(ended_on) AS latest_end
FROM subscriptions;

SELECT
    MIN(issued_on) AS earliest_invoice,
    MAX(issued_on) AS latest_invoice
FROM invoices;

SELECT
    MIN(occurred_at) AS earliest_usage_event,
    MAX(occurred_at) AS latest_usage_event
FROM usage_events;