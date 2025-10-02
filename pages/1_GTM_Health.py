import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --------------------
# Page Configuration
# --------------------
st.set_page_config(page_title="GTM Health", page_icon="🔗", layout="wide")

# --------------------
# Sidebar
# --------------------
st.logo("assets/sprinto_logo.png")

# --------------------
# Assumptions
# --------------------
GROSS_MARGIN = 0.80 # 80%
SALES_COST_MULTIPLIER = 3 # Total S&M Spend = Marketing Campaign Cost * 3

# --------------------
# Data Loading and Metric Calculation (REWRITTEN LOGIC)
# --------------------
@st.cache_data
# REPLACE the existing load_and_calculate_metrics function with this corrected one

@st.cache_data
# REPLACE the existing load_and_calculate_metrics function with this one

@st.cache_data
# REPLACE the existing load_and_calculate_metrics function with this one

@st.cache_data
def load_and_calculate_metrics():
    try:
        marketing_df = pd.read_csv("data/sprinto_database - marketing.csv")
        service_df = pd.read_csv("data/sprinto_database - service.csv")

        # --- Prepare dataframes ---
        marketing_df['date'] = pd.to_datetime(marketing_df['date'])
        service_df['date'] = pd.to_datetime(service_df['date'])
        marketing_df['month_year'] = marketing_df['date'].dt.to_period('M').dt.to_timestamp()
        service_df['month_year'] = service_df['date'].dt.to_period('M').dt.to_timestamp()

        # --- Aggregate data by month ---
        monthly_marketing = marketing_df.groupby('month_year').agg(
            total_marketing_cost=('cost', 'sum'),
            total_mqls=('mql', 'sum')
        ).reset_index()
        monthly_service = service_df.groupby('month_year').agg(
            total_new_customers=('growth_accounts', 'sum'),
            bom_mrr=('book_of_business_bom', 'sum'),
            bom_accounts=('customer_accounts_bom', 'sum')
        ).reset_index()

        # --- Create a complete date range ---
        start_date = service_df['month_year'].min()
        end_date = service_df['month_year'].max()
        all_months = pd.DataFrame({'month_year': pd.date_range(start=start_date, end=end_date, freq='MS')})

        # --- Merge aggregated data ---
        gtm_df = pd.merge(all_months, monthly_service, on='month_year', how='left')
        gtm_df = pd.merge(gtm_df, monthly_marketing, on='month_year', how='left')
        gtm_df['total_marketing_cost'] = gtm_df['total_marketing_cost'].fillna(0)
        gtm_df['total_mqls'] = gtm_df['total_mqls'].fillna(0)
        # Forward fill service data for months without activity to stabilize calculations
        gtm_df[['bom_mrr', 'bom_accounts', 'total_new_customers']] = gtm_df[['bom_mrr', 'bom_accounts', 'total_new_customers']].ffill()

        # --- Calculate Metrics ---
        gtm_df['arpa'] = gtm_df['bom_mrr'] / gtm_df['bom_accounts']
        
        # --- UPDATED: Calculate LTV using the fixed benchmark churn rate ---
        benchmark_monthly_churn = 0.004 # 0.4%
        gtm_df['ltv'] = (gtm_df['arpa'] * GROSS_MARGIN) / benchmark_monthly_churn

        # Cumulative CAC Calculation
        gtm_df['total_sm_spend'] = gtm_df['total_marketing_cost'] * SALES_COST_MULTIPLIER
        gtm_df['cumulative_sm_spend'] = gtm_df['total_sm_spend'].cumsum()
        gtm_df['cumulative_new_customers'] = gtm_df['total_new_customers'].cumsum()
        gtm_df['cumulative_cac'] = gtm_df['cumulative_sm_spend'] / gtm_df['cumulative_new_customers']

        # Final Ratio Metrics
        gtm_df['ltv_cac_ratio'] = gtm_df['ltv'] / gtm_df['cumulative_cac']
        gtm_df['payback_period'] = gtm_df['cumulative_cac'] / (gtm_df['arpa'] * GROSS_MARGIN)
        gtm_df['lead_to_customer_rate'] = gtm_df['total_new_customers'] / gtm_df['total_mqls']
        
        return gtm_df.fillna(0)

    except FileNotFoundError as e:
        st.error(f"Error: A data file was not found. Please check file paths. Details: {e}")
        return None

gtm_df = load_and_calculate_metrics()

if gtm_df is None:
    st.stop()

# --------------------
# Main Page Content
# --------------------
st.title("🔗 Go-to-Market (GTM) Health Dashboard")

# --- Filters ---
st.sidebar.header("Filters")
min_date = gtm_df['month_year'].min()
max_date = gtm_df['month_year'].max()
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
start_date, end_date = date_range
filtered_df = gtm_df[(gtm_df['month_year'] >= pd.to_datetime(start_date)) & (gtm_df['month_year'] <= pd.to_datetime(end_date))]

if filtered_df.empty:
    st.warning("No data available for the selected date range.")
    st.stop()

# --- Calculate aggregate KPIs for the selected period ---
avg_ltv = filtered_df['ltv'].mean()
# Overall CAC is the latest cumulative CAC in the selected period
overall_cac = filtered_df['cumulative_cac'].iloc[-1] if not filtered_df.empty else 0
ltv_cac_ratio = avg_ltv / overall_cac if overall_cac > 0 else 0
avg_payback_period = filtered_df['payback_period'].mean()

# --- KPI Scorecard (UPDATED) ---
st.header("GTM Health Scorecard")
kpi_cols = st.columns(4)
kpi_cols[0].metric(
    "LTV:CAC Ratio",
    f"{ltv_cac_ratio:.1f}x",
    help="Benchmark: > 3x. Measures the ROI of your GTM engine."
)
kpi_cols[1].metric(
    "CAC Payback Period",
    f"{avg_payback_period:.1f} months",
    help="Benchmark: < 12 months. Time to recoup acquisition cost."
)
kpi_cols[2].metric("Avg. Lifetime Value (LTV)", f"${avg_ltv:,.0f}")
kpi_cols[3].metric("Overall Blended CAC", f"${overall_cac:,.0f}", help="The cumulative, blended cost to acquire a customer.")

st.divider()

# --- Health Trend Chart ---
st.header("GTM Health Trends Over Time")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=filtered_df['month_year'], y=filtered_df['ltv_cac_ratio'],
    name='LTV:CAC Ratio', mode='lines+markers'
))
fig.add_trace(go.Scatter(
    x=filtered_df['month_year'], y=filtered_df['payback_period'],
    name='Payback Period (Months)', mode='lines+markers', yaxis='y2'
))
fig.add_hline(y=3, line_width=2, line_dash="dash", line_color="green", annotation_text="3:1 LTV:CAC Benchmark")
fig.update_layout(
    yaxis=dict(title='LTV:CAC Ratio (x)'),
    yaxis2=dict(title='Payback Period (Months)', overlaying='y', side='right'),
    title='LTV:CAC Ratio vs. CAC Payback Period'
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Final Sections (UPDATED) ---
st.subheader("Assumptions")
st.warning(
    f"""
    - **LTV Calculation:** Lifetime Value is calculated using a fixed, benchmark monthly revenue churn rate of **0.4%** for stability, rather than the fluctuating churn rate from the source data.
    - **Gross Margin:** Assumed to be **{GROSS_MARGIN:.0%}**, a standard for B2B SaaS.
    - **Total Sales & Marketing Cost:** Assumed to be **{SALES_COST_MULTIPLIER}x** the marketing campaign spend to account for salaries and overhead.
    - **CAC Calculation:** Customer Acquisition Cost is calculated on a **cumulative basis** to provide a stable trend.
    """
)
st.subheader("Benchmark Sources")
st.markdown("- **LTV:CAC Ratio (3:1)** and **Payback Period (<12m)** are widely accepted benchmarks for healthy, venture-backed SaaS companies.")