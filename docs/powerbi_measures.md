# Power BI measure specification

These measures are designed for a future Power BI semantic model over the curated views.

```DAX
Recognized Revenue = SUM ( fct_monthly_account_metrics[billed_revenue] )

Contracted MRR = SUM ( fct_monthly_account_metrics[mrr] )

ARR = [Contracted MRR] * 12

Active Accounts =
CALCULATE (
    DISTINCTCOUNT ( fct_monthly_account_metrics[organization_id] ),
    fct_monthly_account_metrics[mrr] > 0
)

Product Events = SUM ( fct_monthly_account_metrics[product_events] )

Active Users = SUM ( fct_monthly_account_metrics[active_users] )

Average Revenue per Account = DIVIDE ( [Recognized Revenue], [Active Accounts] )
```

Retention and churn measures should use a dedicated date table and the cohort fields from `cohort_retention`. Do not calculate MRR from invoice totals; invoices and contracted MRR are intentionally separate concepts.
