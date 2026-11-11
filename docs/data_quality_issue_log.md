# Data-quality issue log

## DQ-001 — Subscription end date precedes start date

- **Status:** Open; visible warning, not silently corrected
- **Count:** 23 source records
- **Check:** `subscriptions.ended_on < subscriptions.started_on`
- **Impact:** Can distort lifecycle duration and churn timing if interpreted without qualification.
- **Current treatment:** Raw Parquet is preserved. The quality script reports the issue. Curated model queries use explicit date logic and the README discloses the limitation.
- **Production remediation:** Confirm the source-system correction with the billing owner, backfill valid dates, and rerun historical retention and churn metrics.
- **Portfolio interpretation:** This is intentionally shown as a data-governance decision: preserve lineage, quantify the issue, disclose it, and prevent silent metric corruption.

All other current hard checks pass: duplicate keys, orphan relationships, negative invoices, negative MRR, invalid retention rates, and invalid health scores are zero.
