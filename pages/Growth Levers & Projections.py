import streamlit as st
import pandas as pd

# --------------------
# Page Configuration
# --------------------
st.set_page_config(
    page_title="Growth Levers & Projections",
    page_icon="📈",
    layout="wide"
)

# --------------------
# Sidebar
# --------------------
st.logo("assets/sprinto_logo.png")

# --------------------
# Data Loading and Baseline Calculation
# This function loads all data to calculate the current "baseline" metrics for the sliders.
# --------------------
@st.cache_data
# REPLACE the existing load_baselines function with this one

@st.cache_data
def load_baselines():
    try:
        marketing_df = pd.read_csv("data/sprinto_database - marketing.csv")
        service_df = pd.read_csv("data/sprinto_database - service.csv")

        # --- FIX: Convert date columns from string to datetime ---
        marketing_df['date'] = pd.to_datetime(marketing_df['date'])
        service_df['date'] = pd.to_datetime(service_df['date'])

        # --- Calculate Baselines ---
        # Marketing Funnel Rates
        total_mql = marketing_df['mql'].sum()
        total_sal = marketing_df['sal'].sum()
        total_sql = marketing_df['sql'].sum()
        total_closed = marketing_df['closed'].sum()
        
        baseline_mql_sal_rate = total_sal / total_mql
        baseline_sal_sql_rate = total_sql / total_sal
        baseline_win_rate = total_closed / total_sql

        # Avg MQLs per month
        num_months_marketing = (marketing_df['date'].max() - marketing_df['date'].min()).days / 30.44
        baseline_avg_mqls = total_mql / num_months_marketing if num_months_marketing > 0 else 0

        # Avg Deal Size (ACV)
        baseline_avg_deal_size = service_df['growth_mrr'].sum() / service_df['growth_accounts'].sum() if service_df['growth_accounts'].sum() > 0 else 0
        
        # Churn Rate
        baseline_churn_rate = service_df['churn_mrr'].sum() / service_df['book_of_business_bom'].sum() if service_df['book_of_business_bom'].sum() > 0 else 0

        # Current Book of Business (take latest EOM)
        latest_mrr = service_df.sort_values('date', ascending=False).iloc[0]['book_of_business_eom']
        
        return {
            "mql_sal_rate": baseline_mql_sal_rate,
            "sal_sql_rate": baseline_sal_sql_rate,
            "win_rate": baseline_win_rate,
            "avg_mqls": baseline_avg_mqls,
            "avg_deal_size": baseline_avg_deal_size,
            "churn_rate": baseline_churn_rate,
            "current_mrr": latest_mrr,
        }
    except FileNotFoundError:
        st.error("One or more data files were not found. Please ensure all CSV files are in the `data/` directory.")
        return None

baselines = load_baselines()

if baselines is None:
    st.stop()

# --------------------
# Main Page Content
# --------------------
st.title("📈 Growth Levers & Projections")
st.markdown("An interactive simulator to model the impact of strategic changes on GTM outcomes.")
st.divider()

# Create the two-column layout
col1, col2 = st.columns(2, gap="large")


# =================================================================================================
# COLUMN 1: The "Why" (Your Recommendations)
# =================================================================================================
with col1:
    st.header("Strategic Recommendations")
    
    with st.expander("🚀 Marketing Levers", expanded=True):
        st.markdown(
            """
            - **Recommendation:** Implement an automated lead nurturing sequence for MQLs.
            - **Assumed Impact:** This could improve the `MQL-to-SAL` conversion rate by **10%**.
            """
        )
        st.markdown("---")
        st.markdown(
            """
            - **Recommendation:** Refine ad targeting to focus on higher-intent keywords.
            - **Assumed Impact:** This could increase the `SAL-to-SQL` conversion rate by **5%**.
            """
        )

    with st.expander("💰 Sales Levers", expanded=True):
        st.markdown(
            """
            - **Recommendation:** Implement a value-based selling training program for the sales team.
            - **Assumed Impact:** This could increase the `Average Deal Size` by **$1,500**.
            """
        )
        st.markdown("---")
        st.markdown(
            """
            - **Recommendation:** Introduce a more rigorous qualification process at the SQL stage.
            - **Assumed Impact:** This could improve the `Win Rate` by **5%**.
            """
        )

    with st.expander("🤝 Customer Success Levers", expanded=True):
        st.markdown(
            """
            - **Recommendation:** Launch a proactive customer onboarding program.
            - **Assumed Impact:** This could decrease the `Monthly Revenue Churn Rate` by **0.1%**.
            """
        )
        st.markdown("---")
        st.markdown(
            """
            - **Recommendation:** Introduce a new feature tier for existing customers.
            - **Assumed Impact:** This could create a `Monthly Expansion Rate` of **0.5%**.
            """
        )

# =================================================================================================
# COLUMN 2: The "What If" (The Simulator) - REVISED LAYOUT
# =================================================================================================
with col2:
    st.header("Interactive Simulator")

    # Create nested columns for the simulator itself
    input_col, output_col = st.columns(2, gap="large")

    with input_col:
        st.subheader("Levers (Inputs)")
        # --- Marketing Levers ---
        mqls_per_month = st.number_input("MQLs per Month", min_value=0, value=int(baselines['avg_mqls']))
        mql_sal_rate = st.slider("MQL-to-SAL Rate (%)", 0.0, 100.0, float(baselines['mql_sal_rate']*100), 0.5)
        sal_sql_rate = st.slider("SAL-to-SQL Rate (%)", 0.0, 100.0, float(baselines['sal_sql_rate']*100), 0.5)

        # --- Sales Levers ---
        win_rate = st.slider("Win Rate (%)", 0.0, 100.0, float(baselines['win_rate']*100), 0.5)
        avg_deal_size = st.number_input("Avg. Deal Size (ACV, $)", min_value=0, value=int(baselines['avg_deal_size']))
        target_quota = st.number_input("Sales Target Quota ($)", min_value=0, value=50000)

        # --- CS Levers ---
        churn_rate = st.slider("Monthly Revenue Churn (%)", 0.0, 5.0, float(baselines['churn_rate']*100), 0.05)
        expansion_rate = st.slider("Monthly Expansion Rate (%)", 0.0, 5.0, 0.5, 0.05)

    # --- CALCULATION ENGINE (this part sits in col2 but outside the nested columns) ---
    # Convert percentages from sliders
    mql_sal_rate /= 100
    sal_sql_rate /= 100
    win_rate /= 100
    churn_rate /= 100
    expansion_rate /= 100
    
    # Top of Funnel
    new_customers_per_month = mqls_per_month * mql_sal_rate * sal_sql_rate * win_rate
    new_mrr_per_month = new_customers_per_month * (avg_deal_size / 12)

    # Sales Planning
    required_pipeline = target_quota / win_rate if win_rate > 0 else 0
    required_coverage = required_pipeline / target_quota if target_quota > 0 else 0
    sales_velocity = ( (mqls_per_month * mql_sal_rate * sal_sql_rate) * (avg_deal_size/12) * win_rate) / (92/30.44) if win_rate > 0 else 0

    # Overall Revenue Growth
    current_mrr = baselines['current_mrr']
    expansion_mrr = current_mrr * expansion_rate
    churned_mrr = current_mrr * churn_rate
    net_new_mrr = new_mrr_per_month + expansion_mrr - churned_mrr
    nrr = ((current_mrr + expansion_mrr - churned_mrr) / current_mrr) if current_mrr > 0 else 0

    # Project ARR in 12 months
    projected_arr = (current_mrr + (net_new_mrr * 12)) * 12

    with output_col:
        st.subheader("Projections (Outputs)")
        
        st.markdown("##### Funnel & New Business")
        st.metric("Projected New Customers / mo", f"{new_customers_per_month:.1f}")
        st.metric("Projected New MRR / mo", f"${new_mrr_per_month:,.0f}")
        
        st.markdown("##### Sales Planning")
        st.metric("Required Pipeline to Hit Target", f"${required_pipeline:,.0f}")
        st.metric("Required Pipeline Coverage", f"{required_coverage:.1f}x", help="Benchmark: 4x")
        st.metric("Proj. Sales Velocity ($/mo)", f"${sales_velocity:,.0f}", help="Based on a 92-day sales cycle")

        st.markdown("##### Overall Revenue Growth")
        st.metric("Net New MRR / mo", f"${net_new_mrr:,.0f}")
        st.metric("Net Revenue Retention (NRR)", f"{nrr:.1%}")
        st.metric("Projected ARR in 12 Months", f"${projected_arr:,.0f}")

    st.divider()

# --- Assumptions Section ---
st.subheader("Assumptions for the Simulator")
st.warning(
    """
    - **Baseline Metrics:** The initial values in the sliders are the calculated historical averages from the entire dataset provided. They represent the "As-Is" state of the business.
    
    - **Linear Model:** The simulator assumes linear relationships. For example, a 10% increase in a conversion rate leads to a proportional increase in the output, without accounting for potential market saturation or diminishing returns.
    
    - **Starting MRR:** All revenue growth projections (Expansion, Churn, NRR) are calculated based on the most recent month's book of business from the dataset.
    
    - **Sales Cycle:** The 'Projected Sales Velocity' calculation uses a fixed, benchmark sales cycle of 92 days.
    """
)

# --- Benchmark Sources Section ---
st.subheader("Benchmark Sources")
st.markdown(
    """
    - **4x Pipeline Coverage:** Sourced from [Best Practices for B2B Sales](#). *(You can add the specific URL here)*
    - **92-day Sales Cycle:** Sourced from [GRC Software Benchmark Report](#). *(You can add the specific URL here)*
    """
)