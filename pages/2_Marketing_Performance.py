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
# st.logo("assets/large_logo.png")

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
    "MRR per Dollar Spend": {"value": 0.21, "source": "derived using 3:1 LTV:CAC Ratio (36M LTV)", "url": "https://callin.io/b2b-saas-marketing-benchmarks/"},
    "MQL to SAL Rate": {"value": 0.61, "source": "Data Mania & Gartner", "url": "https://www.data-mania.com/blog/mql-to-sql-conversion-rate-benchmarks-2025/"},
    "SAL to SQL Rate": {"value": 0.40, "source": "Gartner Sales Development Metrics", "url": "https://www.gartner.com/smarterwithgartner/sales-development-metrics-assessing-low-conversion-rates"},
    "SQL to Closed Rate": {"value": 0.20, "source": "Gartner Sales Development Metrics", "url": "https://www.gartner.com/smarterwithgartner/sales-development-metrics-assessing-low-conversion-rates"}
}
# Cross Functional Assumptions:
GROSS_MARGIN = 0.80 # 80%
SALES_COST_MULTIPLIER = 5 # Total S&M Spend = Campaign Cost * 5

# --------------------
# Main Page Content
# --------------------
st.title("🔬 Marketing Performance Dashboard")
# st.markdown("Analyze campaign performance, funnel conversions, and return on investment.")

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

# Define the benchmarks for this chart
cpa_benchmark = 4000
conversion_benchmark = 0.05 # 5%

fig_bubble = px.scatter(
    marketing_df,
    x="cpa_closed",
    y="mql_to_closed_rate",
    size="mrr",
    color="campaign_name",
    hover_name="campaign_name",
    size_max=60,
    labels={ # UPDATED: Label with $
        "cpa_closed": f"Campaign Cost per Closed Customer ($) - Lower is Better",
        "mql_to_closed_rate": "MQL to Closed Conversion Rate (%) - Higher is Better",
        "mrr": "Total MRR"
    },
    title="Campaign Efficiency vs. Effectiveness"
)

# NEW: Add benchmark lines to create quadrants
fig_bubble.add_vline(
    x=cpa_benchmark,
    line_width=2, line_dash="dash", line_color="red",
    annotation_text=f"CPA Benchmark (${cpa_benchmark:,.0f})",
    annotation_position="bottom right"
)
fig_bubble.add_hline(
    y=conversion_benchmark,
    line_width=2, line_dash="dash", line_color="red",
    annotation_text=f"Conversion Benchmark ({conversion_benchmark:.0%})",
    annotation_position="bottom right"
)

fig_bubble.update_layout(showlegend=False)
# Format axes as currency and percentage
fig_bubble.update_xaxes(tickprefix="$", tickformat=",.0f")
fig_bubble.update_yaxes(tickformat=".1%")

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
📊 **Overall Funnel Performance**

- Strong Funnel Efficiency: Overall, the **MRR per dollar spent** and **funnel conversion ratios** (e.g., MQL to SQL, SAL to SQL, etc.) exceeded industry benchmarks, indicating strong marketing and sales alignment across most campaigns.
    
- Win Rate Below Benchmark:Despite overall funnel efficiency, the **opportunity-to-win conversion rate (Win Rate)** lagged behind, sitting at **13.3% vs. 20% benchmark**. This suggests potential gaps in late-stage sales execution or opportunity qualification.
    
🌟 **Top-Performing Campaign** 

Cloud Best Practices Seminar: This campaign outperformed all benchmarks, with a win rate of 28.5%, significantly exceeding the 20% benchmark. It was the only campaign with a win rate above the industry standard, suggesting high-quality leads and strong alignment between marketing, SDRs, and AEs.

🚩 **Underperforming Campaigns** 

Low SQL to Trial Conversion:  
- CS Users Whitepaper (4%)  
- Chicago Sales Conference (2%)  
- Hong Kong Sales Conference (6%)

This may indicate:  
- Low buyer intent at the SQL stage despite initial interest.  
- Gaps in SDR qualification or misalignment between SDR evaluation and AE expectations.  
- Lack of compelling trial triggers or friction in moving from conversation to product experience.

📈 **High-Volume but Cost-Inefficient Campaign**  
Salesforce Summit: This was the largest campaign by volume, delivering MQL-to-Close conversions above benchmark, but at a ~40% higher cost per closed customer than the $4000 benchmark. Additionally, its SQL to Closed rate was 16.3%, below the 20% benchmark, suggesting potential room to improve AE close effectiveness or refine SQL quality.

🔻 **Lowest Performing Campaign**  
Chicago Sales Conference: This campaign had the highest cost per closed customer ($8333), more than 2x the benchmark, and conversion from MQL to Close was just 2% vs. 5% benchmark. This indicates a clear lack of ROI and signals a need for re-evaluation or redesign of similar event-led campaigns.
    """
)


st.subheader("Recommended Actions & Levers")
st.success(
    """
**1) Double Down on High-Intent, Educational Campaigns**: Replicate and scale campaigns like the Cloud Best Practices Seminar that focus on actionable insights and real-world use cases.

**2) Strengthen SDR–AE Handoff and Late-Stage Sales Execution**: Review qualification criteria and alignment between SDRs and AEs for high-volume events like Salesforce Summit.

**3) Audit Audience Quality and Campaign Fit for Underperforming Initiatives**: Conduct a post-mortem on campaigns like Chicago Sales Conference, Hong Kong Sales Conference, and CS Users Whitepaper to understand audience quality, messaging mismatch, or qualification gaps.

**4) Discontinue Participation in the Chicago Sales Conference**: Opt out of future editions unless the format, targeting, or audience curation changes significantly.
    """
)


st.subheader("Assumptions")
st.warning(
    """
**Assumptions**

1. **SQL Stage Definition**  
   - SQL stage is assumed to represent the point where an opportunity has been created because the SDR has confirmed a meeting.  
   - Therefore, SQL to Closed Rate can be used interchangeably with Win Rate.

2. **MQL to Closed Conversion Benchmark**  
   - Calculated using funnel benchmarks:  
     MQL → SAL → SQL → Closed Won = 41% * 61% * 20%

3. **Campaign Cost per Closed Customer & MRR per Dollar Spent**  
   - Benchmarks are based on:  
     - Target LTV/CAC ratio: 3:1  
     - Customer lifetime: 36 months  
     - Average Revenue per Year (ACV): $10,000 → LTV = 10,000 × 3  
     - Target CAC: LTV / 3 = $10,000  
     - Campaign cost assumption: 40% of CAC → Target campaign cost = $4,000  
     - MRR per Dollar Spent: Benchmark = $833.33 MRR / $4,000 Ad Spend ≈ 0.21
    """
)

st.subheader("Benchmark Sources")
for key, value in benchmarks.items():
    st.markdown(f"- **{key}**:  [{value['source']}]({value['url']}).")