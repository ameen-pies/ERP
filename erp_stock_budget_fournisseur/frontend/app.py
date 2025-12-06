"""
Interface Streamlit pour l'ERP - MongoDB Edition
"""
import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Configuration
st.set_page_config(
    page_title="ERP System", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

def style_chart(fig, title=None):
    """Applique un style moderne et cohérent aux graphiques Plotly"""
    fig.update_layout(
        template="plotly_white",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_family="Inter",
        title_font_size=18,
        title_font_color="#0f172a",
        title_x=0.05,
        margin=dict(t=60, l=20, r=20, b=20),
        hoverlabel=dict(
            bgcolor="white",
            font_size=14,
            font_family="Inter",
            bordercolor="#e2e8f0"
        ),
        colorway=["#06b6d4", "#0891b2", "#155e75", "#22d3ee", "#67e8f9"]
    )
    if title:
        fig.update_layout(title=title)
    
    # Style des axes
    fig.update_xaxes(
        showgrid=False, 
        linecolor='#e2e8f0', 
        tickfont=dict(color='#64748b')
    )
    fig.update_yaxes(
        showgrid=True, 
        gridcolor='#f1f5f9', 
        linecolor='#e2e8f0', 
        tickfont=dict(color='#64748b')
    )
    return fig

# Styles CSS personnalisés modernes
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Force dark text in main content */
    .main [data-testid="stMarkdownContainer"] {
        color: #0f172a;
    }
    
    .main p, .main span, .main div {
        color: #1e293b;
    }
    
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
        color: #0f172a !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #f0fdfa 0%, #e0f2fe 100%);
        padding: 2rem;
    }
    
    .block-container {
        background: #ffffff;
        border-radius: 20px;
        padding: 2.5rem !important;
        box-shadow: 0 20px 60px rgba(6, 182, 212, 0.15);
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* Header styling */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        letter-spacing: -1px;
        animation: fadeInDown 0.6s ease;
    }
    
    .subtitle {
        text-align: center;
        color: #475569;
        font-size: 1.1rem;
        margin-bottom: 2.5rem;
        font-weight: 500;
    }
    
    /* Sidebar styling - Fond clair avec texte foncé */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f0fdfa 0%, #ccfbf1 100%);
        padding: 2rem 1rem;
        border-right: 2px solid #06b6d4;
    }
    
    [data-testid="stSidebar"] .element-container {
        color: #0f172a;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #0f172a !important;
        font-weight: 600;
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        color: #0f172a !important;
        font-weight: 500;
        font-size: 1rem;
    }
    
    [data-testid="stSidebar"] [role="radiogroup"] label {
        background: rgba(6, 182, 212, 0.15);
        padding: 0.75rem 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        border-left: 3px solid transparent;
        color: #0f172a !important;
    }
    
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(6, 182, 212, 0.3);
        border-left-color: #06b6d4;
        transform: translateX(5px);
    }
    
    /* Force dark text in sidebar - ULTRA PRIORITY */
    [data-testid="stSidebar"] * {
        color: #0f172a !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] *,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        color: #0f172a !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        color: #1e293b !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-weight: 700;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #0f172a !important;
    }
    
    [data-testid="stSidebar"] [role="radiogroup"] {
        color: #0f172a !important;
    }
    
    [data-testid="stSidebar"] [role="radiogroup"] > div {
        color: #0f172a !important;
    }
    
    /* Metric cards modern design */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="metric-container"] {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1.5px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(6, 182, 212, 0.15);
        border-color: #06b6d4;
    }
    
    /* Button styling */
    .stButton > button {
        background: #06b6d4;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        background: #0891b2;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(6, 182, 212, 0.3);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: #ffffff !important;
        color: #06b6d4 !important;
        border: 1.5px solid #06b6d4 !important;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stDownloadButton > button:hover {
        background: #e0f2fe !important;
        border-color: #0891b2 !important;
    }
    
    /* Form styling */
    [data-testid="stForm"] {
        background: #ffffff;
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #cbd5e1;
    }
    
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        border-radius: 8px !important;
        border: 1.5px solid #cbd5e1 !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
        color: #0f172a !important;
        background-color: #ffffff !important;
    }
    
    /* Force tous les conteneurs d'input en blanc */
    .stTextInput > div,
    .stSelectbox > div,
    .stTextArea > div,
    .stNumberInput > div {
        background-color: #ffffff !important;
    }
    
    /* Number Input - boutons incrémenter/décrémenter */
    .stNumberInput {
        background-color: #ffffff;
    }
    
    .stNumberInput > div > div {
        background-color: #ffffff !important;
    }
    
    .stNumberInput button {
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
        border-radius: 4px;
        transition: all 0.2s ease;
    }
    
    .stNumberInput button:hover {
        background-color: #e0f2fe !important;
        border-color: #06b6d4 !important;
        color: #06b6d4 !important;
    }
    
    .stNumberInput button svg {
        color: #64748b !important;
    }
    
    .stNumberInput button:hover svg {
        color: #06b6d4 !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #94a3b8;
    }
    
    /* Table styling - Enhanced */
    [data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        background: white !important;
        margin-bottom: 1.5rem !important;
        padding: 0.5rem !important;
    }
    
    /* Target the internal container of the dataframe if possible */
    [data-testid="stDataFrame"] > div {
        border-radius: 8px !important;
    }

    /* Chart styling */
    [data-testid="stPlotlyChart"] {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
        transition: transform 0.2s ease;
    }
    
    [data-testid="stPlotlyChart"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    /* Text Area - champs texte long */
    .stTextArea textarea {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        color: #0f172a !important;
        min-height: 100px;
    }
    
    .stTextArea textarea:focus {
        border-color: #06b6d4 !important;
        box-shadow: 0 0 0 4px rgba(6, 182, 212, 0.1) !important;
    }
    
    .stTextArea > div {
        background-color: #ffffff !important;
    }
    
    /* Labels des formulaires */
    .main label {
        color: #1e293b !important;
        font-weight: 500;
    }
    
    /* Text dans les selectbox */
    .main [data-baseweb="select"] {
        color: #0f172a;
        background-color: #ffffff;
    }
    
    /* Multiselect styling */
    .stMultiSelect [data-baseweb="select"] {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1;
        border-radius: 8px;
    }
    
    .stMultiSelect [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #0f172a;
    }
    
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #e0f2fe !important;
        color: #0c4a6e !important;
        border: 1px solid #06b6d4;
    }
    
    /* Dropdown menu styling */
    [data-baseweb="popover"] {
        background-color: #ffffff !important;
    }
    
    [data-baseweb="menu"] {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    [role="option"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        padding: 0.75rem 1rem;
    }
    
    [role="option"]:hover {
        background-color: #f0f9ff !important;
        color: #06b6d4 !important;
    }
    
    [aria-selected="true"][role="option"] {
        background-color: #e0f2fe !important;
        color: #0c4a6e !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #06b6d4;
        box-shadow: 0 0 0 4px rgba(6, 182, 212, 0.1);
        background-color: #ffffff;
        outline: none;
    }
    
    /* Selectbox menu dropdown */
    [data-baseweb="select"] {
        background-color: #ffffff !important;
    }
    
    [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    
    [data-baseweb="select"] svg {
        color: #64748b !important;
    }
    
    [data-baseweb="select"] input {
        color: #0f172a !important;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: #ffffff;
        border-bottom: 2px solid #e2e8f0;
        padding: 0 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 10px 10px 0 0;
        padding: 1rem 2rem;
        font-weight: 600;
        color: #64748b;
        border: none;
        transition: all 0.3s ease;
        border-bottom: 3px solid transparent;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #f8fafc;
        color: #06b6d4;
    }
    
    .stTabs [aria-selected="true"] {
        background: #ffffff;
        color: #06b6d4;
        border-bottom: 3px solid #06b6d4;
        font-weight: 700;
    }
    
    /* Dataframe styling */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        border: 1.5px solid #e2e8f0;
        background-color: #ffffff;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    [data-testid="stDataFrame"] * {
        color: #0f172a !important;
    }
    
    [data-testid="stDataFrame"] thead {
        background-color: #f8fafc;
        font-weight: 600;
    }
    
    /* Alert boxes */
    .stAlert {
        border-radius: 12px;
        border: 1.5px solid;
        padding: 1rem 1.5rem;
        font-weight: 500;
        background: #ffffff;
    }
    
    [data-baseweb="notification"] {
        border-radius: 12px;
        border-left: 4px solid;
    }
    
    /* Success box */
    .element-container div[data-baseweb="notification"][kind="success"] {
        background: #f0fdf4;
        border-color: #22c55e;
        color: #166534;
    }
    
    /* Error box */
    .element-container div[data-baseweb="notification"][kind="error"] {
        background: #fef2f2;
        border-color: #ef4444;
        color: #991b1b;
    }
    
    /* Info box */
    .element-container div[data-baseweb="notification"][kind="info"] {
        background: #f0f9ff;
        border-color: #06b6d4;
        color: #0c4a6e;
    }
    
    /* Warning box */
    .element-container div[data-baseweb="notification"][kind="warning"] {
        background: #fffbeb;
        border-color: #f59e0b;
        color: #78350f;
    }
    
    /* Expander styling */
    [data-testid="stExpander"] {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    [data-testid="stExpander"] summary {
        font-weight: 600;
        color: #0f172a;
        background-color: #f8fafc;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #06b6d4 0%, #0891b2 100%);
        border-radius: 10px;
    }
    
    /* Force mode clair global pour tous les widgets */
    [data-testid="stVerticalBlock"] > div,
    [data-testid="stHorizontalBlock"] > div {
        background-color: transparent !important;
    }
    
    /* Tous les labels et textes en couleur foncée */
    label, .stMarkdown label, [data-testid="stWidgetLabel"] {
        color: #0f172a !important;
    }
    
    /* Forcer fond blanc sur TOUS les champs input/select/textarea */
    input, select, textarea {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    
    /* Number input - forcer fond blanc sur conteneurs */
    .stNumberInput [data-baseweb="input"] {
        background-color: #ffffff !important;
    }
    
    .stNumberInput [data-baseweb="base-input"] {
        background-color: #ffffff !important;
    }
    
    /* Selectbox - forcer fond blanc */
    .stSelectbox [data-baseweb="select"] {
        background-color: #ffffff !important;
    }
    
    .stSelectbox [data-baseweb="select"] > div {
        background-color: #ffffff !important;
    }
    
    /* Column Config widgets */
    [data-testid="stNumberInput-StepUp"],
    [data-testid="stNumberInput-StepDown"] {
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        color: #64748b !important;
    }
    
    [data-testid="stNumberInput-StepUp"]:hover,
    [data-testid="stNumberInput-StepDown"]:hover {
        background-color: #e0f2fe !important;
        color: #06b6d4 !important;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: #ffffff !important;
        color: #06b6d4 !important;
        border: 1.5px solid #06b6d4 !important;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stDownloadButton > button:hover {
        background: #e0f2fe !important;
        border-color: #0891b2 !important;
    }
    
    /* Animations */
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
    
    /* Checkbox and Radio Button styling */
    .stCheckbox, .stRadio {
        color: #0f172a !important;
    }
    
    [data-testid="stCheckbox"] label {
        color: #0f172a !important;
    }
    
    .stCheckbox > label > div {
        background-color: #ffffff;
        border: 1.5px solid #cbd5e1;
    }
    
    /* Slider styling */
    .stSlider {
        color: #0f172a;
    }
    
    .stSlider [data-baseweb="slider"] {
        background-color: #ffffff;
    }
    
    .stSlider [data-baseweb="slider"] > div > div {
        background-color: #e2e8f0 !important;
    }
    
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background-color: #06b6d4 !important;
    }
    
    /* Date Input styling */
    .stDateInput > div > div > input {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        color: #0f172a !important;
        border-radius: 8px;
    }
    
    .stDateInput button {
        background-color: #ffffff !important;
        color: #64748b !important;
    }
    
    .stDateInput button:hover {
        color: #06b6d4 !important;
    }
    
    /* Time Input styling */
    .stTimeInput > div > div > input {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        color: #0f172a !important;
        border-radius: 8px;
    }
    
    /* Column Config et widgets spéciaux */
    [data-testid="stNumberInput-StepUp"],
    [data-testid="stNumberInput-StepDown"] {
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        color: #64748b !important;
    }
    
    [data-testid="stNumberInput-StepUp"]:hover,
    [data-testid="stNumberInput-StepDown"]:hover {
        background-color: #e0f2fe !important;
        color: #06b6d4 !important;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background-color: #06b6d4 !important;
    }
    
    .stProgress > div > div > div {
        background-color: #e2e8f0 !important;
    }
    
    /* Custom cards */
    .metric-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #06b6d4;
        border: 1.5px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin: 1rem 0;
        transition: all 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateX(3px);
        box-shadow: 0 4px 12px rgba(6, 182, 212, 0.15);
        border-left-color: #0891b2;
    }
    
    .success-box {
        background: #f0fdf4;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #22c55e;
        border: 1.5px solid #bbf7d0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin: 1rem 0;
    }
    
    .error-box {
        background: #fef2f2;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #ef4444;
        border: 1.5px solid #fecaca;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin: 1rem 0;
    }
    
    /* Chart container */
    .js-plotly-plot {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Fonction helper pour les requêtes API
def api_call(method: str, endpoint: str, data: dict = None, params: dict = None):
    """Effectue un appel API avec gestion d'erreurs"""
    try:
        url = f"{API_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        
        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            error_detail = response.json().get('detail', 'Erreur inconnue')
            return False, error_detail
            
    except requests.exceptions.ConnectionError:
        return False, " Backend non accessible. Vérifiez que le serveur tourne sur le port 8000."
    except requests.exceptions.Timeout:
        return False, " Timeout: Le serveur met trop de temps à répondre."
    except Exception as e:
        return False, f" Erreur: {str(e)}"

# Header principal moderne
st.markdown('<div class="main-header">ERP System</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Plateforme de Gestion Intégrée - MongoDB Edition</div>', unsafe_allow_html=True)

# Vérification de l'état du système
with st.sidebar:    
    # Statistiques
    st.markdown("### Statistiques")
    success_stats, stats = api_call("GET", "/stats")
    
    if success_stats:
        st.metric("Fournisseurs", stats.get("suppliers", 0))
        st.metric("Budgets", stats.get("budgets", 0))
        st.metric("Articles Stock", stats.get("stock_items", 0))
        st.metric("Mouvements", stats.get("stock_movements", 0))

# Navigation
st.sidebar.markdown("---")
module = st.sidebar.radio(
    "Modules ERP",
    ["1. Référentiel Fournisseurs", "2. Contrôle Budgétaire", "3. Gestion Stock & Compta"],
    index=0
)

# ==================== MODULE 1: FOURNISSEURS ====================

if "Fournisseurs" in module:
    st.markdown("## Gestion du Référentiel Fournisseurs")
    st.markdown("")
    
    tab1, tab2, tab3 = st.tabs(["Nouvelle Demande", "Liste des Fournisseurs", "Validation"])
    
    with tab1:
        st.subheader("Créer une Demande de Référencement")
        
        with st.form("supplier_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Raison Sociale *", placeholder="Ex: Acme Corporation")
                tax_id = st.text_input("Matricule Fiscal *", placeholder="Ex: 123456789")
                category = st.selectbox("Catégorie *", [
                    "Matières Premières", "Services", "IT", "Logistique", "Conseil", "Autre"
                ])
            
            with col2:
                email = st.text_input("Email", placeholder="contact@acme.com")
                phone = st.text_input("Téléphone", placeholder="+216 XX XXX XXX")
                address = st.text_area("Adresse", placeholder="Adresse complète")
            
            submitted = st.form_submit_button(" Initier Référencement", use_container_width=True)
        
        if submitted:
            if not name or not tax_id or not category:
                st.error(" Les champs marqués * sont obligatoires")
            else:
                payload = {
                    "name": name,
                    "tax_id": tax_id,
                    "category": category,
                    "email": email if email else None,
                    "phone": phone if phone else None,
                    "address": address if address else None
                }
                
                success, result = api_call("POST", "/suppliers/", payload)
                
                if success:
                    st.success(f"Demande créée avec succès!")
                    st.json(result)
                    st.balloons()
                else:
                    st.error(f"{result}")
    
    with tab2:
        st.subheader("Liste des Fournisseurs")
        
        # Filtres avancés
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            search_query = st.text_input("Rechercher", placeholder="Nom, Tax ID, Email...")
        
        with col2:
            status_filter = st.selectbox("Statut", [
                "Tous", "PENDING_APPROVAL", "ACTIVE", "REJECTED", "DRAFT"
            ])
        
        with col3:
            category_filter = st.selectbox("Catégorie", [
                "Toutes", "Matières Premières", "Services", "IT", "Logistique", "Conseil", "Autre"
            ])
        
        with col4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Actualiser", use_container_width=True):
                st.rerun()
        
        # Récupération des fournisseurs
        params = {} if status_filter == "Tous" else {"status_filter": status_filter}
        success, suppliers = api_call("GET", "/suppliers/", params=params)
        
        if success and suppliers:
            df = pd.DataFrame(suppliers)
            
            # Filtrage par recherche
            if search_query:
                df = df[
                    df["name"].str.contains(search_query, case=False, na=False) |
                    df["tax_id"].str.contains(search_query, case=False, na=False) |
                    df["email"].fillna("").str.contains(search_query, case=False, na=False)
                ]
            
            # Filtrage par catégorie
            if category_filter != "Toutes":
                df = df[df["category"] == category_filter]
            
            # Métriques
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total", len(df))
            with col2:
                active_count = len(df[df["status"] == "ACTIVE"])
                st.metric("Actifs", active_count)
            with col3:
                pending_count = len(df[df["status"] == "PENDING_APPROVAL"])
                st.metric("En attente", pending_count)
            with col4:
                rejected_count = len(df[df["status"] == "REJECTED"])
                st.metric("Rejetés", rejected_count)
            
            st.markdown("")
            
            # Affichage avec formatage
            df_display = df[["id", "name", "tax_id", "category", "status", "created_at"]].copy()
            df_display["created_at"] = pd.to_datetime(df_display["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
            
            st.markdown("### Liste des Fournisseurs")
            st.dataframe(
                df_display,
                use_container_width=True,
                column_config={
                    "id": "ID",
                    "name": "Raison Sociale",
                    "tax_id": "Matricule Fiscal",
                    "category": "Catégorie",
                    "status": st.column_config.TextColumn("Statut", width="medium"),
                    "created_at": "Date Création"
                },
                hide_index=True
            )
            
            # Export CSV
            csv = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Exporter en CSV",
                data=csv,
                file_name=f"fournisseurs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
            
            st.markdown("")
            
            # Graphiques
            col1, col2 = st.columns(2)
            
            with col1:
                # Répartition par statut
                status_counts = df["status"].value_counts()
                fig = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Répartition par Statut",
                    color_discrete_sequence=px.colors.sequential.Teal
                )
                fig = style_chart(fig)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Répartition par catégorie
                category_counts = df["category"].value_counts()
                fig2 = px.bar(
                    x=category_counts.index,
                    y=category_counts.values,
                    title="Fournisseurs par Catégorie",
                    labels={"x": "Catégorie", "y": "Nombre"},
                    color=category_counts.values,
                    color_continuous_scale="Teal"
                )
                fig2 = style_chart(fig2)
                st.plotly_chart(fig2, use_container_width=True)
            
        elif not success:
            st.warning(suppliers)
        else:
            st.info("Aucun fournisseur enregistré")
    
    with tab3:
        st.subheader("Validation des Demandes en Attente")
        
        success, suppliers = api_call("GET", "/suppliers/", params={"status_filter": "PENDING_APPROVAL"})
        
        if success and suppliers:
            for supplier in suppliers:
                with st.expander(f" {supplier['name']} - {supplier['id']}"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Matricule Fiscal:** {supplier['tax_id']}")
                        st.write(f"**Catégorie:** {supplier['category']}")
                        st.write(f"**Email:** {supplier.get('email', 'N/A')}")
                        st.write(f"**Conformité:** {'Vérifiée' if supplier.get('compliance_checked') else 'En attente'}")
                    
                    with col2:
                        if st.button("Valider", key=f"validate_{supplier['id']}"):
                            success_val, result_val = api_call("PUT", f"/suppliers/{supplier['id']}/validate")
                            if success_val:
                                st.success(result_val["message"])
                                st.rerun()
                            else:
                                st.error(result_val)
                    
                    with col3:
                        if st.button("Rejeter", key=f"reject_{supplier['id']}"):
                            reason = st.text_input("Raison du rejet", key=f"reason_{supplier['id']}")
                            success_rej, result_rej = api_call(
                                "PUT", 
                                f"/suppliers/{supplier['id']}/reject",
                                params={"reason": reason}
                            )
                            if success_rej:
                                st.warning("Demande rejetée")
                                st.rerun()
        else:
            st.info("Aucune demande en attente de validation")

# ==================== MODULE 2: BUDGET ====================

elif "Budgétaire" in module:
    st.markdown("## Contrôle Budgétaire et Conformité")
    st.markdown("")
    
    tab1, tab2, tab3 = st.tabs(["Vue d'ensemble", "Nouvelle Transaction", "Historique"])
    
    with tab1:
        st.subheader("État des Budgets par Département")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Actualiser Budgets", use_container_width=True):
                st.rerun()
        
        success, budget_status = api_call("GET", "/budget/status")
        
        if success and budget_status:
            cols = st.columns(len(budget_status))
            
            for idx, (dept, data) in enumerate(budget_status.items()):
                with cols[idx]:
                    available = data["available"]
                    allocated = data["allocated"]
                    used = data["used"]
                    usage_pct = data["usage_percentage"]
                    
                    st.metric(
                        label=f"{dept}",
                        value=f"{available:,.0f} €",
                        delta=f"{usage_pct:.1f}% utilisé"
                    )
                    
                    # Barre de progression
                    st.progress(usage_pct / 100)
                    st.caption(f"{used:,.0f} € / {allocated:,.0f} €")
            
            st.markdown("")
            
            # Graphiques
            df_budget = pd.DataFrame(budget_status).T.reset_index()
            df_budget.columns = ["Département", "Alloué", "Utilisé", "Disponible", "Usage%"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Graphique en barres empilées
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name="Utilisé", 
                    x=df_budget["Département"], 
                    y=df_budget["Utilisé"], 
                    marker_color="#ef4444"
                ))
                fig.add_trace(go.Bar(
                    name="Disponible", 
                    x=df_budget["Département"], 
                    y=df_budget["Disponible"], 
                    marker_color="#06b6d4"
                ))
                
                fig = style_chart(fig, title="Répartition Budgétaire par Département")
                fig.update_layout(
                    barmode="stack",
                    xaxis_title="Département",
                    yaxis_title="Montant (€)",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Graphique en jauge pour taux d'utilisation moyen
                avg_usage = df_budget["Usage%"].mean()
                
                fig2 = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=avg_usage,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Taux d'Utilisation Moyen"},
                    delta={'reference': 70},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "#06b6d4"},
                        'steps': [
                            {'range': [0, 50], 'color': "#ccfbf1"},
                            {'range': [50, 75], 'color': "#5eead4"},
                            {'range': [75, 100], 'color': "#0891b2"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ))
                fig2 = style_chart(fig2)
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)
            
            # Tableau détaillé
            st.markdown("### Détails par Département")
            st.dataframe(
                df_budget,
                use_container_width=True,
                column_config={
                    "Département": st.column_config.TextColumn("Département", width="medium"),
                    "Alloué": st.column_config.NumberColumn("Alloué (€)", format="%.2f"),
                    "Utilisé": st.column_config.NumberColumn("Utilisé (€)", format="%.2f"),
                    "Disponible": st.column_config.NumberColumn("Disponible (€)", format="%.2f"),
                    "Usage%": st.column_config.ProgressColumn("Utilisation", format="%.1f%%", min_value=0, max_value=100)
                },
                hide_index=True
            )
        else:
            st.warning("Aucun budget configuré. Créez-en un d'abord!")
            
            with st.form("create_budget"):
                st.subheader("Créer un Budget")
                dept_name = st.text_input("Nom du Département")
                allocated_amount = st.number_input("Montant Alloué (€)", min_value=0.0, step=1000.0)
                
                if st.form_submit_button("Créer"):
                    payload = {"department": dept_name, "allocated": allocated_amount, "used": 0.0}
                    success_create, result_create = api_call("POST", "/budget/", payload)
                    
                    if success_create:
                        st.success(" Budget créé!")
                        st.rerun()
                    else:
                        st.error(result_create)
    
    with tab2:
        st.subheader("Soumettre une Transaction")
        
        success, budget_status = api_call("GET", "/budget/status")
        
        if success and budget_status:
            with st.form("transaction_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    dept_choice = st.selectbox("Département *", list(budget_status.keys()))
                    amount = st.number_input("Montant (€) *", min_value=0.0, step=100.0)
                
                with col2:
                    description = st.text_input("Description *", placeholder="Ex: Achat serveurs")
                    reference = st.text_input("Référence", placeholder="Ex: BC-2024-001")
                
                submitted_trx = st.form_submit_button("Vérifier & Engager", use_container_width=True)
            
            if submitted_trx:
                payload = {
                    "department": dept_choice,
                    "amount": amount,
                    "description": description,
                    "reference": reference if reference else None
                }
                
                success_check, result_check = api_call("POST", "/budget/check", payload)
                
                if success_check:
                    status_trx = result_check["status"]
                    
                    if status_trx == "VALIDATED":
                        st.success("TRANSACTION VALIDÉE")
                        st.json(result_check)
                        st.balloons()
                    elif status_trx == "REJECTED":
                        st.error("TRANSACTION REJETÉE")
                        st.error(f"**Raison:** {result_check['reason']}")
                        st.info(result_check['details'])
                    elif status_trx == "BLOCKED":
                        st.warning("VALIDATION HIÉRARCHIQUE REQUISE")
                        st.warning(f"**Raison:** {result_check['reason']}")
                        st.info(result_check['details'])
                        st.code(f"Transaction ID: {result_check.get('transaction_id')}")
                else:
                    st.error(result_check)
        else:
            st.warning("Créez d'abord un budget dans l'onglet 'Vue d'ensemble'")
    
    with tab3:
        st.subheader("Historique des Transactions")
        
        # Filtres
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            dept_filter = st.selectbox("Filtrer par département", ["Tous"] + list(budget_status.keys()) if success and budget_status else ["Tous"])
        
        with col2:
            limit = st.number_input("Nombre de transactions", min_value=10, max_value=500, value=50, step=10)
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Actualiser", key="refresh_trx", use_container_width=True):
                st.rerun()
        
        params = {"limit": limit}
        if dept_filter != "Tous":
            params["department"] = dept_filter
        
        success, transactions = api_call("GET", "/budget/transactions", params=params)
        
        if success and transactions:
            df_trx = pd.DataFrame(transactions)
            df_trx["created_at"] = pd.to_datetime(df_trx["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
            
            # Métriques
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Transactions", len(df_trx))
            with col2:
                total_amount = df_trx["amount"].sum()
                st.metric("Montant Total", f"{total_amount:,.0f} €")
            with col3:
                validated = len(df_trx[df_trx["status"] == "VALIDATED"])
                st.metric("Validées", validated)
            with col4:
                avg_amount = df_trx["amount"].mean()
                st.metric("Montant Moyen", f"{avg_amount:,.0f} €")
            
            st.markdown("")
            
            # Tableau
            st.dataframe(
                df_trx[["id", "department", "amount", "description", "status", "created_at"]],
                use_container_width=True,
                column_config={
                    "id": "ID",
                    "department": "Département",
                    "amount": st.column_config.NumberColumn("Montant (€)", format="%.2f"),
                    "description": "Description",
                    "status": "Statut",
                    "created_at": "Date"
                },
                hide_index=True
            )
            
            # Export
            csv = df_trx.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Exporter en CSV",
                data=csv,
                file_name=f"transactions_budget_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
            
            # Graphique évolution
            st.markdown("### Évolution des Dépenses")
            df_trx_chart = df_trx.copy()
            df_trx_chart["date"] = pd.to_datetime(df_trx_chart["created_at"])
            df_trx_chart = df_trx_chart.sort_values("date")
            df_trx_chart["cumul"] = df_trx_chart["amount"].cumsum()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_trx_chart["date"],
                y=df_trx_chart["cumul"],
                mode='lines+markers',
                name='Cumul',
                line=dict(color='#06b6d4', width=3),
                fill='tozeroy'
            ))
            fig = style_chart(fig, title="Cumul des Dépenses dans le Temps")
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Montant Cumulé (€)",
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune transaction enregistrée")

# ==================== MODULE 3: STOCK ====================

elif "Stock" in module:
    st.markdown("## Gestion Stock & Comptabilité")
    st.markdown("")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Réception", "Stock Actuel", "Mouvements", "Compta"])
    
    with tab1:
        st.subheader("Réception de Marchandises")
        
        with st.form("stock_reception"):
            col1, col2 = st.columns(2)
            
            with col1:
                item_id = st.text_input("Référence Article *", placeholder="Ex: REF-001")
                quantity = st.number_input("Quantité *", min_value=1, step=1)
                unit_price = st.number_input("Prix Unitaire (€) *", min_value=0.0, step=0.01)
            
            with col2:
                movement_type = st.selectbox("Type Mouvement", ["IN", "OUT"])
                project_id = st.text_input("Code Projet (Optionnel)", placeholder="Ex: PRJ-ALPHA")
                reference = st.text_input("Référence", placeholder="Ex: BL-2024-001")
            
            description = st.text_area("Description", placeholder="Détails du mouvement")
            
            submitted_stock = st.form_submit_button("Confirmer Réception", use_container_width=True)
        
        if submitted_stock:
            payload = {
                "item_id": item_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "movement_type": movement_type,
                "project_id": project_id if project_id else None,
                "reference": reference if reference else None,
                "description": description if description else None
            }
            
            success_mov, result_mov = api_call("POST", "/stock/receive", payload)
            
            if success_mov:
                st.success("Transaction Intégrée avec Succès!")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Stock", f"{result_mov['stock_level']} unités")
                
                with col2:
                    st.metric("Valeur", f"{result_mov['accounting_entry']['amount']:.2f} €")
                
                with col3:
                    st.metric("Projet", result_mov['project_status'][:20])
                
                with st.expander(" Détails de la Transaction"):
                    st.json(result_mov)
            else:
                st.error(result_mov)
    
    with tab2:
        st.subheader("État du Stock")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_item = st.text_input("Rechercher un article", placeholder="ID ou nom...")
        
        with col2:
            show_low_stock = st.checkbox("Stock faible uniquement")
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Actualiser", key="refresh_stock", use_container_width=True):
                st.rerun()
        
        params = {"low_stock_only": show_low_stock}
        success, stock_items = api_call("GET", "/stock/items", params=params)
        
        if success and stock_items:
            df_stock = pd.DataFrame(stock_items)
            
            # Filtrage par recherche
            if search_item:
                df_stock = df_stock[
                    df_stock["item_id"].str.contains(search_item, case=False, na=False) |
                    df_stock["item_name"].str.contains(search_item, case=False, na=False)
                ]
            
            # Calcul valeur totale
            df_stock["valeur_totale"] = df_stock["quantity"] * df_stock["unit_price"]
            
            # Métriques
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Articles", len(df_stock))
            with col2:
                total_qty = df_stock["quantity"].sum()
                st.metric("Quantité Totale", f"{total_qty:.0f}")
            with col3:
                total_value = df_stock["valeur_totale"].sum()
                st.metric("Valeur Stock", f"{total_value:,.0f} €")
            with col4:
                low_stock = df_stock[df_stock["quantity"] < df_stock["min_threshold"]]
                st.metric("Alertes", len(low_stock), delta=f"-{len(low_stock)}" if len(low_stock) > 0 else "0", delta_color="inverse")
            
            st.markdown("")
            
            # Tableau
            st.dataframe(
                df_stock[["item_id", "item_name", "quantity", "unit", "unit_price", "min_threshold", "valeur_totale"]],
                use_container_width=True,
                column_config={
                    "item_id": "Référence",
                    "item_name": "Nom",
                    "quantity": st.column_config.NumberColumn("Quantité", format="%.0f"),
                    "unit": "Unité",
                    "unit_price": st.column_config.NumberColumn("Prix Unit. (€)", format="%.2f"),
                    "min_threshold": st.column_config.NumberColumn("Seuil Min", format="%.0f"),
                    "valeur_totale": st.column_config.NumberColumn("Valeur Totale (€)", format="%.2f")
                },
                hide_index=True
            )
            
            # Export
            csv = df_stock.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Exporter en CSV",
                data=csv,
                file_name=f"stock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
            
            st.markdown("")
            
            # Alertes stock faible
            if not low_stock.empty:
                st.warning(f"**{len(low_stock)} article(s) en stock faible!**")
                
                with st.expander("Voir les articles en alerte"):
                    for _, item in low_stock.iterrows():
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.error(f"**{item['item_id']}** - {item['item_name']}")
                        with col2:
                            st.write(f"Stock: {item['quantity']:.0f} {item['unit']}")
                        with col3:
                            st.write(f"Seuil: {item['min_threshold']:.0f}")
            
            # Graphique Top 10 valeur
            st.markdown("### Top 10 Articles par Valeur")
            top10 = df_stock.nlargest(10, 'valeur_totale')
            fig = px.bar(
                top10,
                x='item_id',
                y='valeur_totale',
                title='Top 10 Articles par Valeur',
                labels={'item_id': 'Article', 'valeur_totale': 'Valeur (€)'},
                color='valeur_totale',
                color_continuous_scale='Teal'
            )
            fig = style_chart(fig)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun article en stock")
    
    with tab3:
        st.subheader("Historique des Mouvements")
        
        # Filtres
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            item_filter = st.text_input("Filtrer par article", placeholder="Référence article...")
        
        with col2:
            type_filter = st.selectbox("Type", ["Tous", "IN", "OUT"])
        
        with col3:
            limit_mov = st.number_input("Limite", min_value=10, max_value=500, value=100, step=10, key="limit_mov")
        
        with col4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Actualiser", key="refresh_mov", use_container_width=True):
                st.rerun()
        
        params = {"limit": limit_mov}
        if item_filter:
            params["item_id"] = item_filter
        if type_filter != "Tous":
            params["movement_type"] = type_filter
        
        success, movements = api_call("GET", "/stock/movements", params=params)
        
        if success and movements:
            df_mov = pd.DataFrame(movements)
            df_mov["created_at"] = pd.to_datetime(df_mov["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
            
            # Métriques
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Mouvements", len(df_mov))
            with col2:
                total_in = df_mov[df_mov["movement_type"] == "IN"]["total_value"].sum()
                st.metric("Entrées", f"{total_in:,.0f} €")
            with col3:
                total_out = df_mov[df_mov["movement_type"] == "OUT"]["total_value"].sum()
                st.metric("Sorties", f"{total_out:,.0f} €")
            with col4:
                balance = total_in - total_out
                st.metric("Solde", f"{balance:,.0f} €", delta=f"{balance:,.0f} €")
            
            st.markdown("")
            
            # Tableau
            st.dataframe(
                df_mov[["id", "item_id", "quantity", "movement_type", "total_value", "project_id", "created_at"]],
                use_container_width=True,
                column_config={
                    "id": "ID",
                    "item_id": "Article",
                    "quantity": st.column_config.NumberColumn("Quantité", format="%.0f"),
                    "movement_type": "Type",
                    "total_value": st.column_config.NumberColumn("Valeur (€)", format="%.2f"),
                    "project_id": "Projet",
                    "created_at": "Date"
                },
                hide_index=True
            )
            
            # Export
            csv = df_mov.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Exporter en CSV",
                data=csv,
                file_name=f"mouvements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
            
            st.markdown("")
            
            # Graphiques
            col1, col2 = st.columns(2)
            
            with col1:
                # Évolution temporelle
                df_mov_chart = df_mov.copy()
                df_mov_chart["date"] = pd.to_datetime(df_mov_chart["created_at"])
                df_mov_chart = df_mov_chart.sort_values("date")
                
                fig = px.line(
                    df_mov_chart, 
                    x="date", 
                    y="total_value", 
                    color="movement_type",
                    title="Évolution des Mouvements",
                    labels={"date": "Date", "total_value": "Valeur (€)", "movement_type": "Type"}
                )
                fig = style_chart(fig)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Répartition IN/OUT
                type_totals = df_mov.groupby("movement_type")["total_value"].sum()
                fig2 = px.pie(
                    values=type_totals.values,
                    names=type_totals.index,
                    title="Répartition Entrées/Sorties",
                    color_discrete_sequence=["#06b6d4", "#0891b2"]
                )
                fig2 = style_chart(fig2)
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Aucun mouvement enregistré")
    
    with tab4:
        st.subheader("Journal Comptable")
        
        success, journal = api_call("GET", "/stock/accounting/journal", params={"limit": 100})
        
        if success and journal:
            df_journal = pd.DataFrame(journal)
            df_journal["date"] = pd.to_datetime(df_journal["date"]).dt.strftime("%Y-%m-%d %H:%M")
            
            st.dataframe(
                df_journal[["id", "entry_type", "debit_account", "credit_account", "amount", "date"]],
                use_container_width=True,
                hide_index=True
            )
            
            # Total
            total_amount = df_journal["amount"].sum()
            st.metric(" Total des Écritures", f"{total_amount:,.2f} €")
        else:
            st.info("Aucune écriture comptable")


