# PulseMetrics metric validation report

Generated from the versioned Parquet inputs and curated DuckDB SQL model.

**Invoice coverage:** 2023-02-12 through 2026-12-30

| Metric | Value |
|---|---:|
| Organizations | 3,000 |
| Users | 26,000 |
| Subscriptions | 4,200 |
| Invoices | 46,000 |
| Usage events | 180,000 |
| Recognized revenue | $30,079,838 |
| Active accounts | 2,010 |
| Churned subscriptions | 2,190 |
| Retention rows | 1,097 |
| At-risk accounts | 2,992 |
| Invalid subscription dates | 23 |

## Interpretation

- Hard analytical invariants pass in `scripts/run_quality_checks.py`.
- Invalid subscription dates are disclosed as a source warning rather than silently rewritten.
- Health scores are prioritization signals based on recency, active users, product events, and MRR.
