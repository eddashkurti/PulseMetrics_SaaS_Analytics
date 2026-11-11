"""PulseMetrics executive and revenue-operations dashboard."""
from pathlib import Path
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
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
    for table in ["plans", "organizations", "users", "subscriptions", "invoices", "usage_events"]:
        path = (ROOT / "data" / f"{table}.parquet").as_posix()
        con.execute(f"CREATE OR REPLACE VIEW {table} AS SELECT * FROM read_parquet('{path}')")
    return con

con = get_connection()

@st.cache_data
def bounds():
    return con.execute("SELECT min(period_start), max(period_end) FROM invoices").fetchone()

@st.cache_data
def options():
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
WITH invoice_agg AS (
  SELECT s.organization_id, SUM(i.amount) AS revenue
  FROM invoices i JOIN subscriptions s USING(subscription_id)
  WHERE i.status IN ('paid','active') GROUP BY 1
), subscription_agg AS (
  SELECT organization_id, SUM(seats) AS seats, MAX(plan_id) AS plan_id
  FROM subscriptions WHERE ended_on IS NULL GROUP BY 1
), usage_agg AS (
  SELECT organization_id, COUNT(*) AS product_events, MAX(occurred_at)::DATE AS last_activity
  FROM usage_events GROUP BY 1
)
SELECT o.org_name AS account, o.industry, o.country, o.employee_band,
       COALESCE(p.tier,'No plan') AS tier, COALESCE(ia.revenue,0) AS revenue,
       COALESCE(sa.seats,0) AS seats, COALESCE(ua.product_events,0) AS product_events,
       ua.last_activity
FROM organizations o JOIN scoped_orgs so USING(organization_id)
LEFT JOIN subscription_agg sa USING(organization_id)
LEFT JOIN plans p ON p.plan_id=sa.plan_id
LEFT JOIN invoice_agg ia USING(organization_id)
LEFT JOIN usage_agg ua USING(organization_id)
ORDER BY revenue DESC
""", [*selected_industries, *selected_tiers])
st.dataframe(portfolio, width="stretch", hide_index=True, column_config={"revenue": st.column_config.NumberColumn(format="$%d")})
