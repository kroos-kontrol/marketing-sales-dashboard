import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --------------------
# Page Configuration
# --------------------
st.set_page_config(
    page_title="Sales Performance",
    page_icon="⚙️",
    layout="wide"
)

# --------------------
# Sidebar
# --------------------
st.logo("assets/sprinto_logo.png")

# --------------------
# Data Loading and Preparation
# --------------------
@st.cache_data
def load_data():
    try:
        sales_df = pd.read_csv("data/sprinto_database - sales.csv")
        service_df = pd.read_csv("data/sprinto_database - service.csv")

        sales_df['date'] = pd.to_datetime(sales_df['date'])
        service_df['date'] = pd.to_datetime(service_df['date'])
        
        sales_df['month_year'] = sales_df['date'].dt.to_period('M').dt.to_timestamp()
        service_df['month_year'] = service_df['date'].dt.to_period('M').dt.to_timestamp()

        monthly_service = service_df.groupby('month_year').agg(
            total_growth_mrr=('growth_mrr', 'sum'),
            total_growth_accounts=('growth_accounts', 'sum')
        ).reset_index()
        monthly_service['avg_deal_size'] = monthly_service['total_growth_mrr'] / monthly_service['total_growth_accounts']
        
        merged_df = pd.merge(sales_df, monthly_service[['month_year', 'avg_deal_size']], on='month_year', how='left')
        
        merged_df['quota_attainment'] = (merged_df['sales'] / merged_df['quota'])
        
        return merged_df

    except FileNotFoundError as e:
        st.error(f"Error: A data file was not found. Please check the file path. Details: {e}")
        return None

df = load_data()

if df is None:
    st.stop()

# --- Benchmarks Dictionary ---
benchmarks = {
    "Quota Attainment": {"value": 0.75, "source": "SaaS Industry Standard", "url": "#"},
    "Percent of Reps at Quota": {"value": 0.50, "source": "Internal Company Goal", "url": "#"},
    "Sales Cycle": {"value": 92, "source": "GRC Software Benchmark Report", "url": "#"},
    "Pipeline Coverage": {"value": 4.0, "source": "Best Practice for B2B Sales", "url": "#"}
}

# --------------------
# Main Page Content
# --------------------
st.title("⚙️ Sales Performance Dashboard")

# --- Filters ---
st.sidebar.header("Filters")
selected_manager = st.sidebar.multiselect("Manager", options=df['manager'].unique(), default=df['manager'].unique())
reps_in_selected_manager = df[df['manager'].isin(selected_manager)]['sales_rep'].unique()
selected_rep = st.sidebar.multiselect("Sales Rep", options=reps_in_selected_manager, default=reps_in_selected_manager)

# --- Filter Dataframe ---
filtered_df = df[(df['manager'].isin(selected_manager)) & (df['sales_rep'].isin(selected_rep))]

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# --- KPIs: The Scoreboard ---
total_sales = int(filtered_df['sales'].sum())
total_quota = int(filtered_df['quota'].sum())
overall_attainment = total_sales / total_quota if total_quota > 0 else 0
reps_met_quota = filtered_df.groupby('sales_rep')['quota_attainment'].mean().reset_index()
reps_met_quota = reps_met_quota[reps_met_quota['quota_attainment'] >= 1]
percent_reps_met_quota = len(reps_met_quota) / len(filtered_df['sales_rep'].unique()) if len(filtered_df['sales_rep'].unique()) > 0 else 0
company_avg_deal_size = df['avg_deal_size'].mean()

st.header("Overall Scoreboard")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric(label="Total Sales", value=f"${total_sales:,.0f}")
kpi2.metric(label="Overall Quota Attainment", value=f"{overall_attainment:.1%}", help=f"Benchmark: {benchmarks['Quota Attainment']['value']:.0%}")
kpi3.metric(label="% of Reps at Quota", value=f"{percent_reps_met_quota:.1%}", help=f"Benchmark: {benchmarks['Percent of Reps at Quota']['value']:.0%}")
kpi4.metric(label="Avg. Deal Size (Monthly)", value=f"${company_avg_deal_size:,.0f}")

st.divider()

# --- Performance Over Time ---
st.header("Performance Over Time")
monthly_perf = filtered_df.groupby('month_year').agg(total_sales=('sales', 'sum'), total_quota=('quota', 'sum')).reset_index()
fig_time = go.Figure()
fig_time.add_trace(go.Bar(x=monthly_perf['month_year'], y=monthly_perf['total_sales'], name='Sales'))
fig_time.add_trace(go.Scatter(x=monthly_perf['month_year'], y=monthly_perf['total_quota'], name='Quota', mode='lines+markers'))
st.plotly_chart(fig_time, use_container_width=True)

st.divider()

# --- Leaderboards & Distribution ---
st.header("Leaderboards & Distribution")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Manager Performance")
    # UPDATED CALCULATION LOGIC
    manager_perf_agg = filtered_df.groupby('manager').agg(
        total_sales=('sales', 'sum'),
        total_quota=('quota', 'sum')
    ).reset_index()
    manager_perf_agg['quota_attainment'] = manager_perf_agg['total_sales'] / manager_perf_agg['total_quota']
    manager_perf = manager_perf_agg.sort_values('quota_attainment', ascending=False)
    
    # The rest of the chart code remains the same
    fig_manager = px.bar(manager_perf, x='quota_attainment', y='manager', orientation='h', title="Avg. Quota Attainment by Manager", text='quota_attainment')
    fig_manager.update_traces(texttemplate='%{text:.1%}', textposition='outside')
    max_manager_attainment = manager_perf['quota_attainment'].max()
    fig_manager.update_layout(xaxis_range=[0, max_manager_attainment * 1.15])
    st.plotly_chart(fig_manager, use_container_width=True)

with col2:
    st.subheader("Rep Performance Distribution")
    fig_dist = px.histogram(filtered_df.groupby('sales_rep')['quota_attainment'].mean(), x="quota_attainment", title="Distribution of Rep Attainment")
    fig_dist.update_layout(xaxis_title="Average Quota Attainment", yaxis_title="Number of Reps")
    st.plotly_chart(fig_dist, use_container_width=True)

# NEW: Performance Tiers Section
st.subheader("Performance Tiers (Top 20% / Core 70% / Bottom 10%)")
rep_attainment = filtered_df.groupby('sales_rep')['quota_attainment'].mean()
top_20_threshold = rep_attainment.quantile(0.8)
bottom_10_threshold = rep_attainment.quantile(0.1)
top_performers = rep_attainment[rep_attainment >= top_20_threshold].index.tolist()
bottom_performers = rep_attainment[rep_attainment <= bottom_10_threshold].index.tolist()
middle_performers = rep_attainment[(rep_attainment > bottom_10_threshold) & (rep_attainment < top_20_threshold)].index.tolist()
tier1, tier2, tier3 = st.columns(3)
with tier1:
    st.success("🏆 Top 20%")
    st.write(top_performers)
with tier2:
    st.info("👍 Core 70%")
    st.write(middle_performers)
with tier3:
    st.error("🚨 Bottom 10%")
    st.write(bottom_performers)

st.divider()
st.header("Monthly Rep Performance Heatmap")

# --- Step 1: Create the Pivot Table ---
# We create a table with reps as rows and months as columns.
# The value in each cell is the quota attainment for that rep in that month.
# We use the raw 'month_year' (datetime object) for columns to ensure correct chronological sorting.
rep_monthly_pivot = filtered_df.pivot_table(
    index='sales_rep',
    columns='month_year',
    values='quota_attainment',
    aggfunc='mean' # Since there's one entry per rep/month, 'mean' just selects that value.
)

# --- Step 2: Prepare the Data for Plotting ---
# Transpose the table so months become the rows (Y-axis) and reps become columns (X-axis).
# This is better for visualization if you have more reps than months.
transposed_pivot = rep_monthly_pivot.T

# Create a naturally sorted list of sales rep names for the x-axis.
# This ensures "Rep 10" comes after "Rep 9", not after "Rep 1".
try:
    sorted_rep_names = sorted(transposed_pivot.columns, key=lambda x: int(x.split(' ')[1]))
    # Re-order the columns in our final dataframe based on this sorted list.
    final_pivot_for_chart = transposed_pivot[sorted_rep_names]
except (ValueError, IndexError):
    # Fallback if rep names are not in the "Rep X" format
    sorted_rep_names = sorted(transposed_pivot.columns)
    final_pivot_for_chart = transposed_pivot[sorted_rep_names]




# --- Step 4: Create the Heatmap Visualization ---
st.subheader("Heatmap Visual")
# We use the unformatted datetime index for plotting to ensure Plotly sorts it correctly.
fig_heatmap = px.imshow(
    final_pivot_for_chart,
    text_auto=".0%",
    aspect="auto",
    color_continuous_scale='RdYlGn',
    color_continuous_midpoint=benchmarks['Quota Attainment']['value'], # 75% midpoint
    title="Rep Quota Attainment % by Month",
    labels=dict(x="Sales Rep", y="Month", color="Attainment")
)

# Format the y-axis labels to be readable month names
fig_heatmap.update_yaxes(tickformat='%b %Y',dtick="M1")

st.plotly_chart(fig_heatmap, use_container_width=True)

st.divider()

# --- Sales Health Calculator (FIXED) ---
st.header("Sales Health Calculator")
with st.expander("Model Sales Requirements & Velocity", expanded=True):
    inputs, outputs = st.columns(2)
    with inputs:
        st.subheader("Levers (Inputs)")
        target_quota = st.number_input("Target Quota ($)", min_value=10000, value=50000, step=5000)
        win_rate = st.slider("Assumed Win Rate (%)", min_value=5.0, max_value=50.0, value=20.0, step=0.5) / 100
        num_opportunities_proxy = st.number_input("Number of Opportunities (e.g., SALs)", min_value=10, value=50, step=1)
    with outputs:
        st.subheader("Projections (Outputs)")
        required_pipeline = target_quota / win_rate if win_rate > 0 else 0
        required_coverage = required_pipeline / target_quota if target_quota > 0 else 0
        sales_cycle_days = benchmarks['Sales Cycle']['value']
        sales_velocity = (num_opportunities_proxy * company_avg_deal_size * win_rate) / sales_cycle_days if sales_cycle_days > 0 else 0
        st.metric(label="Required Pipeline to Hit Target", value=f"${required_pipeline:,.0f}")
        st.metric(label="Required Pipeline Coverage", value=f"{required_coverage:.1f}x", help=f"Benchmark: {benchmarks['Pipeline Coverage']['value']}x")
        st.metric(label="Projected Sales Velocity ($ per day)", value=f"${sales_velocity:,.0f}", help=f"Based on a {sales_cycle_days}-day sales cycle")

st.divider()

# --- NEW SECTIONS ---
st.subheader("Analyst Insights")
st.info(
    """
    - **What's Going Well:** The sales team is consistently performing above the 75% quota attainment benchmark. Manager 2's team, in particular, shows strong and consistent performance across all reps.
    - **Areas for Improvement:** While attainment is high, only 40% of reps are meeting their individual quotas, falling short of the 50% benchmark. This suggests that a few top performers may be masking a larger group of reps who are struggling. Rep 8, for example, shows highly volatile performance.
    """
)

st.subheader("Recommended Actions & Levers")
st.success(
    """
    - **For Standout Reps (e.g., Rep 1, Rep 5):** Analyze their deal cycles and strategies. Can their techniques be documented and used as a blueprint for training other reps?
    - **For Underperforming Reps (e.g., Rep 8):** Implement a Performance Improvement Plan (PIP). The heatmap shows inconsistent results, suggesting a potential need for more coaching on pipeline management or closing skills.
    - **For the Org:** Focus on coaching the large group of "middle performers." A small improvement across this group will have a greater impact on overall sales than trying to make top performers even better.
    """
)

st.subheader("Assumptions")
st.warning(
    """
    - **Average Deal Size:** The ADS is calculated as a monthly company-wide average from the service data, not on a per-rep basis.
    - **Sales Velocity:** The number of opportunities is a placeholder value. For a more accurate calculation, this should be linked to the SALs from the marketing data.
    - **Negative Sales:** Negative sales values are treated as deal reversals or clawbacks and are included in the total sales calculations.
    """
)

st.subheader("Benchmark Sources")
for key, value in benchmarks.items():
    st.markdown(f"- **{key}**: Sourced from [{value['source']}]({value['url']}).")