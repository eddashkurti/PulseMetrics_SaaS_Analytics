"""PulseMetrics executive and revenue-operations dashboard."""
from pathlib import Path
from threading import Lock
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DB_LOCK = Lock()
st.set_page_config(page_title="PulseMetrics | SaaS Intelligence", page_icon="◈", layout="wide")

st.markdown("""
<style>
div[data-testid="stMetric"] { background:#111827; border:1px solid #263449; padding:16px; border-radius:12px; }
div[data-testid="stMetricLabel"] { color:#9ca3af; }
.block-container { padding-top:2rem; }
h1 { letter-spacing:-.04em; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_connection():
    con = duckdb.connect()
    with DB_LOCK:
        for table in ["plans", "organizations", "users", "subscriptions", "invoices", "usage_events"]:
            path = (ROOT / "data" / f"{table}.parquet").as_posix()
            con.execute(f"CREATE OR REPLACE VIEW {table} AS SELECT * FROM read_parquet('{path}')")
        model_path = ROOT / "sql" / "03_analytics_model.sql"
        con.execute(model_path.read_text())
        retention_path = ROOT / "sql" / "04_retention_analysis.sql"
        con.execute(retention_path.read_text())
    return con

con = get_connection()

@st.cache_data
def bounds():
    with DB_LOCK:
        return con.execute("SELECT min(period_start), max(period_end) FROM invoices").fetchone()

@st.cache_data
def options():
    with DB_LOCK:
        industries = con.execute("SELECT DISTINCT industry FROM organizations ORDER BY 1").df()["industry"].tolist()
        tiers = con.execute("SELECT DISTINCT tier FROM plans ORDER BY 1").df()["tier"].tolist()
    return industries, tiers

min_date, max_date = bounds()
industries, tiers = options()

st.title("PulseMetrics")
st.caption("SaaS intelligence workspace · revenue, retention, customer health, and product adoption")

with st.sidebar:
    st.header("Analysis controls")
    start = st.date_input("Period start", min_date, min_value=min_date, max_value=max_date)
    end = st.date_input("Period end", max_date, min_value=min_date, max_value=max_date)
    selected_industries = st.multiselect("Industry", industries)
    selected_tiers = st.multiselect("Plan tier", tiers)
    if start > end:
        st.error("Period start must precede period end.")
        st.stop()

industry_sql = "" if not selected_industries else " AND o.industry IN (" + ",".join("?" for _ in selected_industries) + ")"
tier_sql = "" if not selected_tiers else " AND p.tier IN (" + ",".join("?" for _ in selected_tiers) + ")"
params = [start, end, *selected_industries, *selected_tiers]

def query(sql, values=params):
    with DB_LOCK:
        return con.execute(sql, values).df()

scope = f"""
WITH scoped_orgs AS (
    SELECT DISTINCT o.organization_id
    FROM organizations o
    LEFT JOIN subscriptions s ON s.organization_id=o.organization_id
    LEFT JOIN plans p ON p.plan_id=s.plan_id
    WHERE 1=1 {industry_sql} {tier_sql}
)
"""

kpi = query(scope + """
SELECT
 (SELECT COALESCE(SUM(i.amount),0) FROM invoices i JOIN subscriptions s USING(subscription_id)
  WHERE i.period_end BETWEEN ? AND ? AND i.status IN ('paid','active') AND s.organization_id IN (SELECT organization_id FROM scoped_orgs)) AS revenue,
 (SELECT COUNT(DISTINCT s.organization_id) FROM subscriptions s WHERE s.ended_on IS NULL AND s.organization_id IN (SELECT organization_id FROM scoped_orgs)) AS active_accounts,
 (SELECT COUNT(*) FROM subscriptions s WHERE s.ended_on BETWEEN ? AND ? AND s.organization_id IN (SELECT organization_id FROM scoped_orgs)) AS churned_subscriptions,
 (SELECT COUNT(DISTINCT ue.organization_id) FROM usage_events ue WHERE ue.occurred_at::DATE BETWEEN ? AND ? AND ue.organization_id IN (SELECT organization_id FROM scoped_orgs)) AS active_organizations,
 (SELECT COALESCE(SUM(s.seats),0) FROM subscriptions s WHERE s.ended_on IS NULL AND s.organization_id IN (SELECT organization_id FROM scoped_orgs)) AS active_seats
""", [*selected_industries, *selected_tiers, start, end, start, end, start, end])

revenue = float(kpi.iloc[0].revenue or 0)
st.subheader("Executive scorecard")
cols = st.columns(5)
cols[0].metric("Recognized revenue", f"${revenue:,.0f}", help="Paid and active invoices in the selected period")
cols[1].metric("Active accounts", f"{int(kpi.iloc[0].active_accounts):,}")
cols[2].metric("Churned subscriptions", f"{int(kpi.iloc[0].churned_subscriptions):,}")
cols[3].metric("Active organizations", f"{int(kpi.iloc[0].active_organizations):,}")
cols[4].metric("Subscribed seats", f"{int(kpi.iloc[0].active_seats):,}")

left, right = st.columns([1.4, 1])
with left:
    st.subheader("Revenue trajectory")
    revenue_df = query(scope + """
      SELECT date_trunc('month', i.period_end)::DATE AS month,
             SUM(i.amount) FILTER (WHERE i.status IN ('paid','active')) AS revenue,
             COUNT(DISTINCT s.organization_id) FILTER (WHERE i.status IN ('paid','active')) AS accounts
      FROM invoices i JOIN subscriptions s USING(subscription_id)
      WHERE i.period_end BETWEEN ? AND ? AND s.organization_id IN (SELECT organization_id FROM scoped_orgs)
      GROUP BY 1 ORDER BY 1
    """, [*selected_industries, *selected_tiers, start, end])
    fig = go.Figure()
    fig.add_trace(go.Bar(x=revenue_df.month, y=revenue_df.revenue, name="Revenue", marker_color="#60a5fa"))
    fig.add_trace(go.Scatter(x=revenue_df.month, y=revenue_df.accounts, name="Paying accounts", yaxis="y2", line=dict(color="#fbbf24", width=3)))
    fig.update_layout(template="plotly_dark", height=340, margin=dict(l=0,r=0,t=10,b=0), yaxis_title="Revenue", yaxis2=dict(title="Accounts", overlaying="y", side="right"), legend=dict(orientation="h"))
    st.plotly_chart(fig, width="stretch")
with right:
    st.subheader("Revenue mix")
    mix = query(scope + """
      SELECT COALESCE(p.tier,'Unknown') AS tier, SUM(i.amount) AS revenue
      FROM invoices i JOIN subscriptions s USING(subscription_id) LEFT JOIN plans p USING(plan_id)
      WHERE i.period_end BETWEEN ? AND ? AND i.status IN ('paid','active') AND s.organization_id IN (SELECT organization_id FROM scoped_orgs)
      GROUP BY 1 ORDER BY 2 DESC
    """, [*selected_industries, *selected_tiers, start, end])
    fig = px.pie(mix, names="tier", values="revenue", hole=.62, color_discrete_sequence=["#60a5fa","#a78bfa","#34d399","#fbbf24"])
    fig.update_layout(template="plotly_dark", height=340, margin=dict(l=0,r=0,t=10,b=0), showlegend=True)
    st.plotly_chart(fig, width="stretch")

st.subheader("Retention and customer health")
left, right = st.columns(2)
with left:
    churn = query(scope + """
      SELECT date_trunc('month', ended_on)::DATE AS month, cancel_reason, COUNT(*) AS subscriptions
      FROM subscriptions s WHERE ended_on BETWEEN ? AND ? AND organization_id IN (SELECT organization_id FROM scoped_orgs)
      GROUP BY 1,2 ORDER BY 1
    """, [*selected_industries, *selected_tiers, start, end])
    fig = px.bar(churn, x="month", y="subscriptions", color="cancel_reason", barmode="stack", title="Churn by cancellation reason")
    fig.update_layout(template="plotly_dark", height=330, margin=dict(l=0,r=0,t=40,b=0), legend_title="")
    st.plotly_chart(fig, width="stretch")

st.subheader("Signup cohort retention")
cohort = query(scope + """
, cohort_sizes AS (
    SELECT date_trunc('month', o.signed_up_on)::DATE AS cohort_month,
           COUNT(DISTINCT o.organization_id) AS cohort_accounts
    FROM organizations o
    WHERE o.organization_id IN (SELECT organization_id FROM scoped_orgs)
    GROUP BY 1
), active_months AS (
    SELECT DISTINCT m.organization_id, date_trunc('month', o.signed_up_on)::DATE AS cohort_month,
           date_diff('month', date_trunc('month', o.signed_up_on), m.month) AS month_number
    FROM fct_monthly_account_metrics m
    JOIN organizations o USING (organization_id)
    WHERE m.mrr > 0 AND m.month BETWEEN date_trunc('month', ?) AND date_trunc('month', ?)
      AND m.organization_id IN (SELECT organization_id FROM scoped_orgs)
), retained AS (
    SELECT cohort_month, month_number, COUNT(*) AS retained_accounts
    FROM active_months WHERE month_number BETWEEN 0 AND 12 GROUP BY 1, 2
)
SELECT r.cohort_month, r.month_number,
       ROUND(100.0 * r.retained_accounts / NULLIF(s.cohort_accounts, 0), 1) AS retention_rate
FROM retained r JOIN cohort_sizes s USING (cohort_month)
ORDER BY 1, 2
""", [*selected_industries, *selected_tiers, start, end])
if not cohort.empty:
    cohort_pivot = cohort.pivot(index="cohort_month", columns="month_number", values="retention_rate")
    cohort_pivot.columns = [f"M{int(x)}" for x in cohort_pivot.columns]
    fig = go.Figure(go.Heatmap(z=cohort_pivot.values, x=cohort_pivot.columns,
                               y=[str(x)[:7] for x in cohort_pivot.index],
                               colorscale=[[0, "#172033"], [.5, "#2563eb"], [1, "#34d399"]],
                               text=cohort_pivot.round(1).astype(str).values,
                               texttemplate="%{text}%", colorbar_title="Retention %"))
    fig.update_layout(template="plotly_dark", height=420, margin=dict(l=0,r=0,t=10,b=0),
                      xaxis_title="Months since signup", yaxis_title="Signup cohort")
    st.plotly_chart(fig, width="stretch")
with right:
    adoption = query(scope + """
      SELECT date_trunc('month', occurred_at)::DATE AS month, event_type,
             COUNT(DISTINCT organization_id) AS organizations, SUM(quantity) AS quantity
      FROM usage_events ue WHERE occurred_at::DATE BETWEEN ? AND ? AND organization_id IN (SELECT organization_id FROM scoped_orgs)
      GROUP BY 1,2 ORDER BY 1
    """, [*selected_industries, *selected_tiers, start, end])
    fig = px.line(adoption, x="month", y="organizations", color="event_type", markers=True, title="Product adoption: organizations active by event")
    fig.update_layout(template="plotly_dark", height=330, margin=dict(l=0,r=0,t=40,b=0), legend_title="")
    st.plotly_chart(fig, width="stretch")

st.subheader("Account portfolio")
portfolio = query(scope + """
, invoice_agg AS (
  SELECT s.organization_id, SUM(i.amount) AS revenue
  FROM invoices i JOIN subscriptions s USING(subscription_id)
  WHERE i.period_end BETWEEN ? AND ? AND i.status IN ('paid','active') GROUP BY 1
), subscription_agg AS (
  SELECT organization_id, SUM(seats) AS seats, MAX(plan_id) AS plan_id
  FROM subscriptions WHERE ended_on IS NULL GROUP BY 1
), usage_agg AS (
  SELECT organization_id, COUNT(*) AS product_events, MAX(occurred_at)::DATE AS last_activity
  FROM usage_events GROUP BY 1
)
SELECT o.org_name AS account, o.industry, o.country, o.employee_band,
       o.organization_id,
       COALESCE(p.tier,'No plan') AS tier, COALESCE(ia.revenue,0) AS revenue,
       COALESCE(sa.seats,0) AS seats, COALESCE(ua.product_events,0) AS product_events,
       ua.last_activity
FROM organizations o JOIN scoped_orgs so USING(organization_id)
LEFT JOIN subscription_agg sa USING(organization_id)
LEFT JOIN plans p ON p.plan_id=sa.plan_id
LEFT JOIN invoice_agg ia USING(organization_id)
LEFT JOIN usage_agg ua USING(organization_id)
ORDER BY revenue DESC
""", [*selected_industries, *selected_tiers, start, end])
st.dataframe(portfolio, width="stretch", hide_index=True, column_config={"revenue": st.column_config.NumberColumn(format="$%d")})

st.subheader("Customer health queue")
st.caption("Health scores are as-of the latest available source month; industry, plan-tier, and portfolio filters still scope the account queue.")
health = query(scope + """
SELECT organization_id, org_name AS account, industry, health_score,
       health_segment, mrr, active_users, product_events, last_activity
FROM customer_health
WHERE organization_id IN (SELECT organization_id FROM scoped_orgs)
ORDER BY health_score ASC, mrr DESC
""", [*selected_industries, *selected_tiers])
health_left, health_right = st.columns([1, 2])
with health_left:
    health_mix = health.groupby("health_segment", as_index=False).size().rename(columns={"size": "accounts"})
    fig = px.pie(health_mix, names="health_segment", values="accounts", hole=.65,
                 color="health_segment", color_discrete_map={"Healthy":"#34d399", "Monitor":"#fbbf24", "At risk":"#f87171"})
    fig.update_layout(template="plotly_dark", height=300, margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig, width="stretch")
with health_right:
    st.caption("Health score is explainable: recency, active users, product events, and current MRR.")
    st.dataframe(health.head(25), width="stretch", hide_index=True,
                 column_config={"health_score": st.column_config.ProgressColumn("Health score", min_value=0, max_value=100),
                                "mrr": st.column_config.NumberColumn(format="$%d")})

st.subheader("Organization drill-down")
account_options = portfolio[["account", "organization_id"]].drop_duplicates().sort_values("account")
selected_account = st.selectbox("Select an organization", account_options.account.tolist())
selected_org = int(account_options.loc[account_options.account == selected_account, "organization_id"].iloc[0])

with DB_LOCK:
    detail = con.execute("""
    SELECT organization_id, org_name, industry, country, employee_band, acquisition_channel,
           health_score, health_segment, mrr, active_users, product_events, last_activity
    FROM customer_health WHERE organization_id = ?
    """, [selected_org]).df()
detail_row = detail.iloc[0] if not detail.empty else None
if detail_row is not None:
    detail_cols = st.columns(6)
    detail_cols[0].metric("Health score", f"{int(detail_row.health_score)}/100")
    detail_cols[1].metric("Segment", detail_row.health_segment)
    detail_cols[2].metric("Current MRR", f"${float(detail_row.mrr):,.0f}")
    detail_cols[3].metric("Active users", f"{int(detail_row.active_users):,}")
    detail_cols[4].metric("Product events", f"{int(detail_row.product_events):,}")
    detail_cols[5].metric("Last activity", str(detail_row.last_activity))

    detail_left, detail_right = st.columns(2)
    with DB_LOCK:
        account_history = con.execute("""
        SELECT month, mrr, billed_revenue, active_users, product_events, seats, last_activity
        FROM fct_monthly_account_metrics
        WHERE organization_id = ? ORDER BY month
        """, [selected_org]).df()
    with detail_left:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=account_history.month, y=account_history.mrr,
                                 name="Contracted MRR", mode="lines+markers", line=dict(color="#60a5fa", width=3)))
        fig.add_trace(go.Bar(x=account_history.month, y=account_history.billed_revenue,
                             name="Billed revenue", marker_color="#a78bfa", opacity=.55))
        fig.update_layout(template="plotly_dark", title="Account revenue history", height=330,
                          margin=dict(l=0,r=0,t=40,b=0), legend=dict(orientation="h"))
        st.plotly_chart(fig, width="stretch")
    with detail_right:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=account_history.month, y=account_history.active_users,
                                 name="Active users", mode="lines+markers", line=dict(color="#34d399", width=3)))
        fig.add_trace(go.Bar(x=account_history.month, y=account_history.product_events,
                             name="Product events", marker_color="#fbbf24", opacity=.55))
        fig.update_layout(template="plotly_dark", title="Account product engagement", height=330,
                          margin=dict(l=0,r=0,t=40,b=0), legend=dict(orientation="h"))
        st.plotly_chart(fig, width="stretch")

    with DB_LOCK:
        subscription_history = con.execute("""
        SELECT s.subscription_id, p.plan_name, p.tier, s.started_on, s.ended_on,
               s.seats, p.monthly_price + p.seat_price * s.seats AS contracted_mrr,
               COALESCE(s.cancel_reason, 'Active') AS status
        FROM subscriptions s JOIN plans p USING (plan_id)
        WHERE s.organization_id = ? ORDER BY s.started_on DESC
        """, [selected_org]).df()
    st.caption(f"{detail_row.org_name} · {detail_row.industry} · {detail_row.country} · {detail_row.employee_band}")
    st.dataframe(subscription_history, width="stretch", hide_index=True,
                 column_config={"contracted_mrr": st.column_config.NumberColumn(format="$%d")})
