import streamlit as st

st.set_page_config(
    page_title="Sprinto GTM Dashboard - Intro",
    page_icon="👋",
    layout="wide"
)

# st.logo("assets/1.png")

# --- 1. Main Title and Welcome ---
st.title("Go-to-Market Performance Dashboard")
st.markdown(
    """
    Welcome to the Sprinto GTM Performance Dashboard. This interactive tool provides an integrated view of our Marketing, Sales, and Customer Success data. 
    """
)
st.divider()

# --- 2. Key Insights & Recommendations ---
st.header("📌 Key Insights & Recommendations (TL;DR)")
st.markdown(
    """
##### This project analyzed performance across **Marketing**, **Sales**, and **Customer Success** to identify high-impact levers for revenue growth.

- 🚀 **Marketing:** While **MRR per dollar spent** and **funnel conversions** exceeded benchmarks, the **win rate** lagged. Campaigns like *Cloud Best Practices Seminar* outperformed, while others (e.g., *Chicago Sales Conference*) showed poor **SQL-to-Trial** conversion.  
  ✅ **Solution:** Double down on use case/best practices based campaigns, refine lead quality, and optimize underperforming campaign strategies.

- 💰 **Sales:** Overall **quota attainment** was healthy at **90%**, but **rep-level consistency** was lacking. Only **38.1% of reps** met quota, and **Manager 4’s team** significantly underperformed.  
  🔧 **Solution:** Improve ramp-up and coaching for underperformers, replicate best practices from standout reps and Manager 3, and reassess lead distribution fairness.

- 🤝 **Customer Success:** Strong retention with **99.9% GRR** and near-zero churn. However, **no expansion revenue** was observed.  
  📈 **Solution:** Activate cross-sell/upsell programs, leverage customer champions for marketing, and support sales via referrals.

🧪 These insights are now operationalized into a **simulation tool**, where users can experiment with levers across functions to forecast revenue impact.
    """
)


st.divider()

# --- 3. My Approach ---
st.header("My Approach to This Case Study")
st.markdown(
    """
- I started by clearly outlining the key business questions and defining KPIs across Marketing, Sales, and Customer Success. Once that was in place, I cleaned and restructured the data to make it analysis-ready.
- Each dashboard was built to answer specific operational questions. For example, I used funnel charts to pinpoint conversion issues, heatmaps to assess rep consistency, and bubble charts to evaluate campaign efficiency.
- Where raw data was incomplete (like for LTV and CAC), I filled the gaps using benchmarks and realistic models. This allowed me to generate directional insights even in the absence of full data.
- Finally, I built an interactive simulator that connects strategic recommendations with outcomes. Instead of just reporting on the past, the tool lets users test growth levers and instantly see their impact.
    """
)


st.divider()

# --- 4. How to Navigate This Dashboard ---
st.header("How to Navigate")
st.markdown(
    """
    Use the sidebar on the left to navigate to the different sections of the analysis:
    - **🔬 Marketing Performance:** A deep-dive into campaign performance, costs, and funnel metrics.
    - **⚙️ Sales Performance:** An analysis of quota attainment, rep/manager performance, and sales pipeline health.
    - **🤝 Customer Success:** A view of customer retention, churn, and revenue growth.
    - **📈 Growth Levers & Projections:** An interactive simulator to model the impact of strategic decisions.
    """
)