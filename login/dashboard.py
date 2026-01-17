# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import os

# Page configuration
st.set_page_config(
    page_title="ERP - Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit UI
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    iframe {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100vh;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# Check if user is authenticated
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.error("❌ Please login first")
    st.stop()

# Get user data
user_data = st.session_state.get('user_data', {})
user_role = user_data.get('role', 'user')
user_name = user_data.get('full_name', 'User')

# Read the index.html file
current_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(current_dir, "index.html")

try:
    with open(index_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Inject user data into the HTML
    html_content = html_content.replace(
        "const userRole = urlParams.get('role') || 'user';",
        f"const userRole = '{user_role}';"
    )
    html_content = html_content.replace(
        "const userName = urlParams.get('name') || 'User';",
        f"const userName = '{user_name}';"
    )
    
    # Display the HTML
    components.html(html_content, height=800, scrolling=True)
    
except FileNotFoundError:
    st.error(f"❌ index.html not found at: {index_path}")
    st.info("Please make sure index.html is in the same directory as app.py")