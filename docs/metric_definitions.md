# PulseMetrics metric definitions

These definitions are intentionally explicit so every dashboard number can be challenged and reproduced.

| Metric | Definition | Grain |
| --- | --- | --- |
| Recognized revenue | Sum of invoice amounts whose status is `paid` or `active`, filtered by invoice period end | Invoice month |
| Contracted MRR | Plan monthly price plus seat price multiplied by subscription seats | Active subscription-month |
| ARR | Ending MRR multiplied by 12 | Month |
| Active account | Organization with at least one subscription that is active in the selected period | Organization-period |
| Logo churn | Subscriptions with a non-null end date in the selected period | Subscription month |
| Product adoption | Distinct organizations producing at least one usage event | Organization-month |
| Retention rate | Active organizations in a cohort month divided by the original cohort size | Cohort-age month |
| Customer health | Explainable score from usage recency, active users, product events, and current MRR | Latest organization snapshot |

## Important assumptions

- Invoice revenue is treated as recognized for dashboard purposes only when status is `paid` or `active`.
- Contracted MRR is modeled from plan price and seats; it is separate from invoice revenue.
- A customer is considered active when their subscription month overlaps the calendar month.
- Health scoring is directional and designed for prioritization, not as a statistically calibrated churn probability.
- The source data has no acquisition-cost, support-ticket, or contract-discount fields, so CAC, payback, and true NRR are not inferred.
