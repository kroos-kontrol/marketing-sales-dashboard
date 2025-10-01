import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------
# Page Configuration
# --------------------
st.set_page_config(page_title="Marketing Performance", page_icon="🔬", layout="wide")

# --------------------
# Sidebar
# --------------------
st.logo("assets/sprinto_logo.png")

# --------------------
# Data Loading & Preparation
# --------------------
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])
        # --- Calculated Columns ---
        df['mrr_per_dollar'] = df['mrr'] / df['cost']
        df['cpa_closed'] = df['cost'] / df['closed']
        df['mql_to_sal_rate'] = df['sal'] / df['mql']
        df['sal_to_sql_rate'] = df['sql'] / df['sal']
        df['sql_to_closed_rate'] = df['closed'] / df['sql']
        return df
    except FileNotFoundError:
        st.error(f"Error: File not found at {file_path}. Please check the file path.")
        return None

marketing_df = load_data("data/sprinto_database - marketing.csv")

if marketing_df is None:
    st.stop()

# --- Benchmarks Data (UPDATED) ---
benchmarks = {
    "MRR per Dollar Spend": {"value": 0.17, "source": "derived using 4:1 ROAS (24M LTV)", "url": "https://callin.io/b2b-saas-marketing-benchmarks/"},
    "MQL to SAL Rate": {"value": 0.61, "source": "Data Mania & Gartner", "url": "https://www.data-mania.com/blog/mql-to-sql-conversion-rate-benchmarks-2025/"},
    "SAL to SQL Rate": {"value": 0.18, "source": "Gartner Sales Development Metrics", "url": "https://www.gartner.com/smarterwithgartner/sales-development-metrics-assessing-low-conversion-rates"},
    "SQL to Closed Rate": {"value": 0.20, "source": "Gartner Sales Development Metrics", "url": "https://www.gartner.com/smarterwithgartner/sales-development-metrics-assessing-low-conversion-rates"}
}

# --------------------
# Main Page Content
# --------------------
st.title("🔬 Marketing Performance Dashboard")
st.markdown("Analyze campaign performance, funnel conversions, and return on investment.")

campaign_options = ['All Campaigns'] + list(marketing_df['campaign_name'].unique())
st.sidebar.header("Filters")
selected_campaign = st.sidebar.selectbox("Select a Campaign", options=campaign_options)

if selected_campaign == 'All Campaigns':
    filtered_df = marketing_df
else:
    filtered_df = marketing_df[marketing_df['campaign_name'] == selected_campaign]

if filtered_df.empty:
    st.warning("No data available for the selected campaign.")
    st.stop()

# --- Aggregate Metrics ---
total_mql = int(filtered_df['mql'].sum())
total_sal = int(filtered_df['sal'].sum())
total_sql = int(filtered_df['sql'].sum())
total_closed = int(filtered_df['closed'].sum())
total_cost = int(filtered_df['cost'].sum())
total_mrr = int(filtered_df['mrr'].sum())
overall_mrr_per_dollar = total_mrr / total_cost if total_cost > 0 else 0
mql_sal_rate = total_sal / total_mql if total_mql > 0 else 0
sal_sql_rate = total_sql / total_sal if total_sal > 0 else 0
sql_closed_rate = total_closed / total_sql if total_sql > 0 else 0

# --------------------
# Display KPIs (UPDATED)
# --------------------
st.header("Overall Performance")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric(label="MRR per Dollar Spend", value=f"${overall_mrr_per_dollar:.2f}")
    st.markdown(f"Benchmark: ${benchmarks['MRR per Dollar Spend']['value']:.2f}")
with kpi2:
    st.metric(label="MQL to SAL Rate", value=f"{mql_sal_rate:.1%}")
    st.markdown(f"Benchmark: {benchmarks['MQL to SAL Rate']['value']:.0%}")
with kpi3:
    st.metric(label="SAL to SQL Rate", value=f"{sal_sql_rate:.1%}")
    st.markdown(f"Benchmark: {benchmarks['SAL to SQL Rate']['value']:.0%}")
with kpi4:
    st.metric(label="SQL to Closed Rate", value=f"{sql_closed_rate:.1%}")
    st.markdown(f"Benchmark: {benchmarks['SQL to Closed Rate']['value']:.0%}")

st.markdown("---")

# --------------------
# Visualizations (UPDATED)
# --------------------
col1, col2 = st.columns(2)
with col1:
    st.subheader("Conversion Funnel")
    funnel_data = filtered_df[['mql', 'sal', 'sql', 'closed']].sum().reset_index()
    funnel_data.columns = ['stage', 'count']
    fig_funnel = px.funnel(funnel_data, x='count', y='stage', title="Overall Lead to Customer Funnel")
    fig_funnel.update_traces(textinfo="value+percent previous") # Adds percentages
    st.plotly_chart(fig_funnel, use_container_width=True)

with col2:
    st.subheader("Campaign MRR per Dollar Spend")
    campaign_perf = marketing_df.sort_values('mrr_per_dollar', ascending=True)
    campaign_perf['color'] = campaign_perf['mrr_per_dollar'].apply(lambda x: '#0056fc' if x >= benchmarks['MRR per Dollar Spend']['value'] else 'lightgrey')
    fig_bar = px.bar(
        campaign_perf, x='mrr_per_dollar', y='campaign_name', orientation='h',
        title="Campaign Performance vs. Benchmark", labels={'mrr_per_dollar': 'MRR per $ Spent', 'campaign_name': 'Campaign'},
        text='mrr_per_dollar'
    )
    fig_bar.update_traces(marker_color=campaign_perf['color'], texttemplate='$%{text:.2f}', textposition='outside')
    fig_bar.add_vline(x=benchmarks['MRR per Dollar Spend']['value'], line_width=2, line_dash="dash", line_color="red", annotation_text="Benchmark")
    max_value = campaign_perf['mrr_per_dollar'].max()
    fig_bar.update_layout(xaxis_range=[0, max_value * 1.15]) # Fixes axis range
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# Scatter Plot
st.subheader("Campaign Performance Matrix")
# Calculate MQL to Closed Rate for the scatter plot
marketing_df['mql_to_closed_rate'] = marketing_df['closed'] / marketing_df['mql']

fig_bubble = px.scatter(
    marketing_df,
    x="cpa_closed",
    y="mql_to_closed_rate",
    size="mrr",
    color="campaign_name",
    hover_name="campaign_name",
    size_max=60, # Adjust for bubble size scaling
    labels={
        "cpa_closed": "Cost per Closed Customer (Lower is Better)",
        "mql_to_closed_rate": "MQL to Closed Conversion Rate (Higher is Better)",
        "mrr": "Total MRR"
    },
    title="Campaign Efficiency vs. Effectiveness"
)

fig_bubble.update_layout(showlegend=False)
st.plotly_chart(fig_bubble, use_container_width=True)

st.markdown("---")
# Table with the details

st.subheader("Campaign Details")
# Create a dataframe for display with calculated metrics
display_df = marketing_df[['campaign_name', 'mrr_per_dollar', 'cpa_closed', 'mql_to_sal_rate', 'sal_to_sql_rate', 'sql_to_closed_rate', 'mrr', 'cost']].set_index('campaign_name')

st.dataframe(
    display_df.style.format({
        'mrr_per_dollar': '${:.2f}',
        'cpa_closed': '${:,.2f}',
        'mql_to_sal_rate': '{:.1%}',
        'sal_to_sql_rate': '{:.1%}',
        'sql_to_closed_rate': '{:.1%}',
        'mrr': '${:,.0f}',
        'cost': '${:,.0f}'
    })
)

# --------------------
# Insights & Footnotes (UPDATED)
# --------------------
st.markdown("---")
st.subheader("Analyst Insights")
st.info(
    """
    - **Top Performer:** Identify which campaign has the highest MRR per dollar spend and why.
    - **Area for Review:** Point out the campaign with the lowest return and diagnose potential issues based on its funnel conversion rates.
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
    st.markdown(f"- **{key}**:  [{value['source']}]({value['url']}).")