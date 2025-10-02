import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --------------------
# Page Configuration
# --------------------
st.set_page_config(
    page_title="Customer Success",
    page_icon=" flywheel",
    layout="wide"
)

# --------------------
# Sidebar
# --------------------
# st.logo("assets/sprinto_logo.png")

# --------------------
# Data Loading and Preparation
# --------------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("data/sprinto_database - service.csv")
        df['date'] = pd.to_datetime(df['date'])
        
        # --- Calculate Core Metrics ---
        # Gross Revenue Retention (GRR)
        df['grr'] = (df['book_of_business_bom'] - df['churn_mrr']) / df['book_of_business_bom']
        
        # Revenue and Customer Churn Rates
        df['revenue_churn_rate'] = df['churn_mrr'] / df['book_of_business_bom']
        df['customer_churn_rate'] = df['churn_accounts'] / df['customer_accounts_bom']
        
        # Average Revenue Per Account (ARPA)
        df['arpa'] = df['book_of_business_bom'] / df['customer_accounts_bom']
        
        # Net MRR Growth
        df['net_mrr_growth'] = df['growth_mrr'] - df['churn_mrr']
        
        return df

    except FileNotFoundError as e:
        st.error(f"Error: The file was not found. Please check the file path. Details: {e}")
        return None

df = load_data()

if df is None:
    st.stop()

# --- Benchmarks Dictionary ---
benchmarks = {
    "NRR": {"value": 1.20, "source": "Wudpecker", "url": "https://www.wudpecker.io/blog/retention-benchmarks-for-b2b-saas-in-2025"},
    "GRR": {"value": 0.95, "source": "Wudpecker", "url": "https://www.wudpecker.io/blog/retention-benchmarks-for-b2b-saas-in-2025"},
    "Monthly Revenue Churn": {"value": 0.004, "source": "Hubfi", "url": "https://www.hubifi.com/blog/calculate-saas-churn-rate"}
}

# --------------------
# Main Page Content
# --------------------
st.title(" Customer Success Dashboard")
# st.markdown("Analyze customer retention, revenue churn, and account growth.")

# --- Filters ---
# st.sidebar.header("Filters")
# min_date = df['date'].min()
# max_date = df['date'].max()
# date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
start_date = df['date'].min()
end_date = df['date'].max()
# start_date, end_date = date_range

# --- Filter Dataframe ---
filtered_df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]

if filtered_df.empty:
    st.warning("No data available for the selected date range.")
    st.stop()

# --- KPIs: The Health Check ---
# REPLACE the existing KPI section with this one

st.header("Health Check (Period Averages)")

# --- NEW: Calculate averages over the entire filtered period ---
avg_grr = filtered_df['grr'].mean()
avg_rev_churn = filtered_df['revenue_churn_rate'].mean()
avg_arpa = filtered_df['arpa'].mean()

# The Target Expansion MRR is forward-looking, so it should still be based on the latest month's data.
latest_month = filtered_df.sort_values('date', ascending=False).iloc[0]
target_nrr = benchmarks['NRR']['value']
starting_mrr = latest_month['book_of_business_bom']
churn_mrr = latest_month['churn_mrr']
target_expansion_mrr = (target_nrr * starting_mrr) - starting_mrr + churn_mrr

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    # UPDATED: Use average GRR and a new label
    st.metric(label="Avg. Monthly GRR", value=f"{avg_grr:.1%}")
    st.markdown(f"Benchmark: >{benchmarks['GRR']['value']:.0%}")

with kpi2:
    # UPDATED: Use average churn and a new label
    st.metric(label="Avg. Monthly Revenue Churn", value=f"{avg_rev_churn:.2%}")
    st.markdown(f"Benchmark: <{benchmarks['Monthly Revenue Churn']['value']:.1%}")

with kpi3:
    # The main metric remains the average over the period
    st.metric(label="Avg. Revenue Per Account", value=f"${avg_arpa:,.0f}")
    
    # --- UPDATED: Trend calculation now compares first vs. last month ---
    if len(filtered_df) > 1:
        # Sort by date to easily find the first and last entry
        sorted_df = filtered_df.sort_values('date')
        first_month_arpa = sorted_df.iloc[0]['arpa']
        last_month_arpa = sorted_df.iloc[-1]['arpa']
        
        # Determine trend direction and color
        if last_month_arpa > first_month_arpa:
            trend_text = "▲ Trending Up"
            color = "green"
        else:
            trend_text = "▼ Trending Down"
            color = "red"
            
        st.markdown(f"<span style='color:{color};'>{trend_text}</span> (vs. first month)", unsafe_allow_html=True)

with kpi4:
    # This metric remains the same as it's a forward-looking target
    st.metric(
        label="Target Expansion MRR",
        value=f"${target_expansion_mrr:,.0f}",
        help="Based on the latest month's starting MRR, this is the upsell needed to hit the NRR goal."
    )
    st.markdown(f"Benchmark: >{benchmarks['NRR']['value']:.1%}")

st.divider()

# --- Visualizations ---
st.header("Trends and Analysis")
chart1, chart2 = st.columns(2)

st.header("Churn Analysis")
chart1, chart2 = st.columns(2)

with chart1:
    st.subheader("Monthly Revenue Churn Rate")
    fig_rev_churn = px.line(filtered_df, x='date', y='revenue_churn_rate', title="Revenue Churn vs. Target")
    fig_rev_churn.update_yaxes(tickformat=".2%")
    fig_rev_churn.add_hline(y=benchmarks['Monthly Revenue Churn']['value'], line_width=2, line_dash="dash", line_color="red", annotation_text="Target")
    st.plotly_chart(fig_rev_churn, use_container_width=True)

with chart2:
    st.subheader("Monthly Customer Churn Rate")
    fig_cust_churn = px.line(filtered_df, x='date', y='customer_churn_rate', title="Customer Churn Trend")
    fig_cust_churn.update_yaxes(tickformat=".2%")
    # You can add a benchmark for customer churn here if you have one
    st.plotly_chart(fig_cust_churn, use_container_width=True)

st.divider() # Add a divider for better separation

st.subheader("Monthly MRR Movement")
fig_waterfall = go.Figure()
# Add bars for each component
fig_waterfall.add_trace(go.Bar(x=filtered_df['date'], y=filtered_df['growth_mrr'], name='New Business MRR', marker_color='green'))
fig_waterfall.add_trace(go.Bar(x=filtered_df['date'], y=-filtered_df['churn_mrr'], name='Churned MRR', marker_color='red'))
# Customize layout
fig_waterfall.update_layout(
    barmode='relative',
    title_text='New MRR vs. Churned MRR Each Month',
    xaxis_title='Month',
    yaxis_title='MRR Change'
)
st.plotly_chart(fig_waterfall, use_container_width=True)

st.divider()

st.subheader("ARPA (Average Revenue Per Account) Trend")
fig_arpa = px.line(
    filtered_df,
    x='date',
    y='arpa',
    title="Monthly ARPA Trend",
    labels={'arpa': 'ARPA ($)', 'date': 'Date'}
)
fig_arpa.update_traces(mode='lines+markers')
st.plotly_chart(fig_arpa, use_container_width=True)

st.divider()

# --- Final Sections ---
st.subheader("Analyst Insights")
st.info(
    """
📊 **Overall Services Team Performance**

- **Strong Customer Retention:**  
  - The team has excelled in retaining customers, both in dollar terms and in total customers.  
  - **Revenue churn** and **customer churn** are well below industry benchmarks:  
    - Average Monthly Revenue Churn: 0.04% (vs 0.4% benchmark)  
    - Average Monthly GRR: 99.9% (vs >90% benchmark)  
  - Monthly customer churn rates are trending downwards, reflecting the team’s effectiveness in logo retention.

- **Increasing Revenue per Account (ARPA):**  
  - ARPA has been trending upwards, indicating strong account management and satisfaction.

🚀 **Areas for Improvement**

- **Focus on Expansion Revenue:**  
  - Currently, all Growth MRR is coming from New Business, suggesting limited upsell or cross-sell activity.  
  - To meet the Net Revenue Retention (NRR) benchmark >120%, the Services team should increase expansion revenue from existing accounts.
    """
)
st.subheader("Recommendations and Levers")
st.success(
    """
**Services Team Recommendations**

1) **Drive Expansion Revenue:**  
- Identify opportunities to upsell or cross-sell within the existing customer base to boost Growth MRR and help achieve the Net Revenue Retention (NRR) benchmark of >120%.

2) **Leverage Customer Champions for Marketing Initiatives:**  
- Engage long-term, satisfied customers to support marketing campaigns similar to the "Cloud Best Practices Seminar."  
- Enable these champions to participate in or lead seminars, sharing use cases and best practices.

3) **Support Sales Through Referrals:**  
- Collaborate with the Sales team to generate warmer introductions via referrals from existing customers, helping accelerate deal cycles and improve conversion rates.
    """
)


st.subheader("Assumptions")
st.warning(
    """
    - **Expansion MRR:** The dataset does not contain Expansion MRR from existing customers. The 'growth_mrr' is assumed to be from new business only. As a result, Net Revenue Retention (NRR) cannot be calculated and is modeled as a target.
    """
)

st.subheader("Benchmark Sources")
for key, value in benchmarks.items():
    st.markdown(f"- **{key}**: [{value['source']}]({value['url']}).")