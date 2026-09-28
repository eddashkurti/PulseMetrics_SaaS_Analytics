CREATE OR REPLACE TABLE plans AS
SELECT *
FROM read_parquet(
    'C:/Users/GNTC/Desktop/l/PulseMetrics_SaaS_Analytics/data/plans.parquet'
);


CREATE OR REPLACE TABLE organizations AS
SELECT *
FROM read_parquet(
    'C:/Users/GNTC/Desktop/l/PulseMetrics_SaaS_Analytics/data/organizations.parquet'
);


CREATE OR REPLACE TABLE users AS
SELECT *
FROM read_parquet(
    'C:/Users/GNTC/Desktop/l/PulseMetrics_SaaS_Analytics/data/users.parquet'
);


CREATE OR REPLACE TABLE subscriptions AS
SELECT *
FROM read_parquet(
    'C:/Users/GNTC/Desktop/l/PulseMetrics_SaaS_Analytics/data/subscriptions.parquet'
);


CREATE OR REPLACE TABLE invoices AS
SELECT *
FROM read_parquet(
    'C:/Users/GNTC/Desktop/l/PulseMetrics_SaaS_Analytics/data/invoices.parquet'
);


CREATE OR REPLACE TABLE usage_events AS
SELECT *
FROM read_parquet(
    'C:/Users/GNTC/Desktop/l/PulseMetrics_SaaS_Analytics/data/usage_events.parquet'
);


SHOW TABLES;