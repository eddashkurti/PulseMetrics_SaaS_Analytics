CREATE OR REPLACE TABLE plans AS
SELECT *
FROM read_parquet(
    'data/plans.parquet'
);


CREATE OR REPLACE TABLE organizations AS
SELECT *
FROM read_parquet(
    'data/organizations.parquet'
);


CREATE OR REPLACE TABLE users AS
SELECT *
FROM read_parquet(
    'data/users.parquet'
);


CREATE OR REPLACE TABLE subscriptions AS
SELECT *
FROM read_parquet(
    'data/subscriptions.parquet'
);


CREATE OR REPLACE TABLE invoices AS
SELECT *
FROM read_parquet(
    'data/invoices.parquet'
);


CREATE OR REPLACE TABLE usage_events AS
SELECT *
FROM read_parquet(
    'data/usage_events.parquet'
);


SHOW TABLES;
