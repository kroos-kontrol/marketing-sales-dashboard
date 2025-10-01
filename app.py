import streamlit as st

# Set the page configuration
# This must be the first Streamlit command in your app
st.set_page_config(
    page_title="Executive Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Executive Summary")
st.markdown("## The Command Center for Marketing, Sales, and Customer Success")

st.sidebar.success("Select a dashboard page above.")

st.write("This is the main overview page. Use the sidebar to navigate to detailed dashboards.")