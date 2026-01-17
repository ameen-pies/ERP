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
    initial_sidebar_state="collapsed"
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
        colorway=["#64748b", "#475569", "#334155", "#94a3b8", "#cbd5e1"]
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
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 2rem;
    }
    
    .block-container {
        background: #ffffff;
        border-radius: 20px;
        padding: 2.5rem !important;
        box-shadow: 0 20px 60px rgba(100, 116, 139, 0.15);
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* Header styling */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #94a3b8 0%, #cbd5e1 50%, #e2e8f0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        letter-spacing: -1px;
        animation: fadeInDown 0.6s ease;
    }
    
    .subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2.5rem;
        font-weight: 500;
    }
    
    /* Sidebar styling - Fond clair avec texte foncé */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 2rem 1rem;
        border-right: 2px solid #cbd5e1;
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
        background: rgba(203, 213, 225, 0.3);
        padding: 0.75rem 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        border-left: 3px solid transparent;
        color: #475569 !important;
    }
    
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(203, 213, 225, 0.5);
        border-left-color: #94a3b8;
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
    
    /* Navigation bar styling */
    .nav-container {
        background: linear-gradient(90deg, #cbd5e1 0%, #e2e8f0 50%, #f1f5f9 100%);
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(203, 213, 225, 0.3);
    }
    
    .nav-button {
        background: transparent !important;
        color: #64748b !important;
        border: 2px solid rgba(203, 213, 225, 0.5) !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    .nav-button:hover {
        background: rgba(241, 245, 249, 0.6) !important;
        border-color: #94a3b8 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(148, 163, 184, 0.2) !important;
    }
    
    /* Metric cards modern design */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        color: #94a3b8;
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
        box-shadow: 0 4px 12px rgba(148, 163, 184, 0.2);
        border-color: #cbd5e1;
    }
    
    /* Button styling */
    .stButton > button {
        background: #94a3b8;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(148, 163, 184, 0.2);
    }
    
    .stButton > button:hover {
        background: #cbd5e1;
        color: #475569;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(148, 163, 184, 0.3);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
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
        border-color: #cbd5e1 !important;
        color: #94a3b8 !important;
    }
    
    .stNumberInput button svg {
        color: #94a3b8 !important;
    }
    
    .stNumberInput button:hover svg {
        color: #cbd5e1 !important;
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
        border-color: #cbd5e1 !important;
        box-shadow: 0 0 0 4px rgba(203, 213, 225, 0.2) !important;
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
        color: #64748b !important;
        border: 1px solid #cbd5e1;
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
        color: #94a3b8 !important;
    }
    
    [aria-selected="true"][role="option"] {
        background-color: #f1f5f9 !important;
        color: #64748b !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stTextArea > div > div > textarea:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #cbd5e1;
        box-shadow: 0 0 0 4px rgba(203, 213, 225, 0.2);
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
        color: #94a3b8 !important;
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
        color: #94a3b8;
        border: none;
        transition: all 0.3s ease;
        border-bottom: 3px solid transparent;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #f8fafc;
        color: #94a3b8;
    }
    
    .stTabs [aria-selected="true"] {
        background: #ffffff;
        color: #64748b;
        border-bottom: 3px solid #cbd5e1;
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
        border-color: #cbd5e1;
        color: #475569;
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
        background: linear-gradient(90deg, #cbd5e1 0%, #e2e8f0 50%, #f1f5f9 100%);
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
        color: #475569 !important;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: #ffffff !important;
        color: #94a3b8 !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stDownloadButton > button:hover {
        background: #f8fafc !important;
        border-color: #94a3b8 !important;
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
        background-color: #cbd5e1 !important;
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
        color: #94a3b8 !important;
    }
    
    .stDateInput button:hover {
        color: #cbd5e1 !important;
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
        border: 1px solid #e2e8f0 !important;
        color: #94a3b8 !important;
    }
    
    [data-testid="stNumberInput-StepUp"]:hover,
    [data-testid="stNumberInput-StepDown"]:hover {
        background-color: #f1f5f9 !important;
        color: #cbd5e1 !important;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background-color: #cbd5e1 !important;
    }
    
    .stProgress > div > div > div {
        background-color: #e2e8f0 !important;
    }
    
    /* Custom cards */
    .metric-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #cbd5e1;
        border: 1.5px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(148, 163, 184, 0.1);
        margin: 1rem 0;
        transition: all 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateX(3px);
        box-shadow: 0 4px 12px rgba(148, 163, 184, 0.2);
        border-left-color: #94a3b8;
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
        
        # Vérifier si la réponse est vide
        if not response.text or response.text.strip() == '':
            if response.status_code in [200, 201, 204]:
                return True, []  # Réponse vide mais succès
            else:
                return False, f"Erreur {response.status_code}: Réponse vide du serveur"
        
        # Essayer de parser le JSON
        try:
            response_json = response.json()
        except ValueError as json_err:
            # Si le JSON ne peut pas être parsé, retourner le texte brut
            return False, f"Erreur de parsing JSON: {str(json_err)}. Réponse: {response.text[:200]}"
        
        if response.status_code in [200, 201]:
            return True, response_json
        else:
            error_detail = response_json.get('detail', f'Erreur {response.status_code}: {response.text[:200]}')
            return False, error_detail
            
    except requests.exceptions.ConnectionError:
        return False, " Backend non accessible. Vérifiez que le serveur tourne sur le port 8000."
    except requests.exceptions.Timeout:
        return False, " Timeout: Le serveur met trop de temps à répondre."
    except Exception as e:
        return False, f" Erreur: {str(e)}"

# Header principal moderne
st.markdown('<div class="main-header">ERP System</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Plateforme de Gestion Intégrée</div>', unsafe_allow_html=True)

st.markdown("---")

# Styles pour les statistiques modernes
st.markdown("""
<style>
    .stat-card-modern {
        background: #ffffff;
        border: none;
        border-radius: 20px;
        padding: 2rem 1.5rem;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(71, 85, 105, 0.08), 0 1px 3px rgba(71, 85, 105, 0.04);
        position: relative;
        overflow: hidden;
        border-top: 3px solid transparent;
        background-clip: padding-box;
    }
    
    .stat-card-modern::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #475569 0%, #64748b 50%, #94a3b8 100%);
    }
    
    .stat-card-modern::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.1), transparent);
        transition: left 0.5s ease;
    }
    
    .stat-card-modern:hover {
        transform: translateY(-6px) scale(1.02);
        box-shadow: 0 20px 40px rgba(71, 85, 105, 0.15), 0 8px 16px rgba(71, 85, 105, 0.1);
        border-top-color: #64748b;
    }
    
    .stat-card-modern:hover::after {
        left: 100%;
    }
    
    .stat-value-modern {
        font-size: 3rem;
        font-weight: 900;
        color: #0f172a;
        margin: 1rem 0 0.5rem 0;
        line-height: 1;
        letter-spacing: -1px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stat-label-modern {
        font-size: 0.7rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 700;
        margin-top: 0.75rem;
    }
    
    .stat-subvalue-modern {
        font-size: 0.8rem;
        color: #475569;
        margin-top: 0.75rem;
        font-weight: 600;
        padding-top: 0.5rem;
        border-top: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Barre de statistiques modernisée
stat_col1, stat_col2 = st.columns([5, 1])

with stat_col1:
    st.markdown("### Statistiques du Système")

with stat_col2:
    if st.button("Actualiser", key="refresh_stats", use_container_width=True):
        st.cache_clear()
        st.rerun()

success_stats, stats = api_call("GET", "/stats")

if success_stats:
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f'''
        <div class="stat-card-modern">
            <div class="stat-value-modern">{stats.get('suppliers', 0)}</div>
            <div class="stat-label-modern">Fournisseurs</div>
            <div class="stat-subvalue-modern">{stats.get('suppliers_active', 0)} actifs</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="stat-card-modern">
            <div class="stat-value-modern">{stats.get('stock_items', 0)}</div>
            <div class="stat-label-modern">Articles Stock</div>
            <div class="stat-subvalue-modern">{stats.get('total_stock_quantity', 0):.0f} unités</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        total_stock_value = stats.get('total_stock_value', 0)
        st.markdown(f'''
        <div class="stat-card-modern">
            <div class="stat-value-modern">{total_stock_value:,.0f}€</div>
            <div class="stat-label-modern">Valeur Stock</div>
            <div class="stat-subvalue-modern">Total inventaire</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
        <div class="stat-card-modern">
            <div class="stat-value-modern">{stats.get('departments', 0)}</div>
            <div class="stat-label-modern">Départements</div>
            <div class="stat-subvalue-modern">{stats.get('budgets', 0)} budgets</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col5:
        st.markdown(f'''
        <div class="stat-card-modern">
            <div class="stat-value-modern">{stats.get('stock_movements', 0)}</div>
            <div class="stat-label-modern">Mouvements</div>
            <div class="stat-subvalue-modern">{stats.get('low_stock_items', 0)} stock faible</div>
        </div>
        ''', unsafe_allow_html=True)

st.markdown("---")

# Barre de navigation modernisée
st.markdown("---")
st.markdown("### Navigation")

# Initialiser la session state si nécessaire
if "selected_module" not in st.session_state:
    st.session_state.selected_module = "0. Gestion Départements"

nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

current_module = st.session_state.selected_module

# Styles pour les boutons de navigation modernes
st.markdown("""
<style>
    .nav-button-container {
        position: relative;
        display: flex;
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    button[data-testid*="nav_dept"],
    button[data-testid*="nav_fourn"],
    button[data-testid*="nav_budget"],
    button[data-testid*="nav_stock"] {
        background: #ffffff !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 1.5rem 2rem !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        letter-spacing: 1px !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 2px 6px rgba(71, 85, 105, 0.08), 0 1px 3px rgba(71, 85, 105, 0.04) !important;
        color: #475569 !important;
        text-transform: uppercase !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        position: relative !important;
        overflow: hidden !important;
        border-top: 2px solid transparent !important;
        width: 100% !important;
    }
    
    button[data-testid*="nav_dept"]::before,
    button[data-testid*="nav_fourn"]::before,
    button[data-testid*="nav_budget"]::before,
    button[data-testid*="nav_stock"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #475569 0%, #64748b 50%, #94a3b8 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    button[data-testid*="nav_dept"]:hover::before,
    button[data-testid*="nav_fourn"]:hover::before,
    button[data-testid*="nav_budget"]:hover::before,
    button[data-testid*="nav_stock"]:hover::before {
        opacity: 1;
    }
    
    button[data-testid*="nav_dept"]:hover,
    button[data-testid*="nav_fourn"]:hover,
    button[data-testid*="nav_budget"]:hover,
    button[data-testid*="nav_stock"]:hover {
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 0 12px 24px rgba(71, 85, 105, 0.15), 0 6px 12px rgba(71, 85, 105, 0.1) !important;
        background: #f8fafc !important;
        color: #334155 !important;
        border-top-color: #64748b !important;
    }
</style>
""", unsafe_allow_html=True)

# Appliquer le style actif selon le module sélectionné
active_style = "<style>"
if "Gestion Départements" in current_module:
    active_style += """
    button[data-testid*="nav_dept"] {
        background: linear-gradient(135deg, #475569 0%, #64748b 100%) !important;
        color: white !important;
        border-top: 2px solid #64748b !important;
        box-shadow: 0 10px 25px rgba(71, 85, 105, 0.25), 0 5px 10px rgba(71, 85, 105, 0.15) !important;
    }
    button[data-testid*="nav_dept"]::before {
        opacity: 1 !important;
        background: linear-gradient(90deg, #64748b 0%, #94a3b8 100%);
    }
    """
elif "Fournisseurs" in current_module:
    active_style += """
    button[data-testid*="nav_fourn"] {
        background: linear-gradient(135deg, #475569 0%, #64748b 100%) !important;
        color: white !important;
        border-top: 2px solid #64748b !important;
        box-shadow: 0 10px 25px rgba(71, 85, 105, 0.25), 0 5px 10px rgba(71, 85, 105, 0.15) !important;
    }
    button[data-testid*="nav_fourn"]::before {
        opacity: 1 !important;
        background: linear-gradient(90deg, #64748b 0%, #94a3b8 100%);
    }
    """
elif "Stock" in current_module:
    active_style += """
    button[data-testid*="nav_stock"] {
        background: linear-gradient(135deg, #475569 0%, #64748b 100%) !important;
        color: white !important;
        border-top: 2px solid #64748b !important;
        box-shadow: 0 10px 25px rgba(71, 85, 105, 0.25), 0 5px 10px rgba(71, 85, 105, 0.15) !important;
    }
    button[data-testid*="nav_stock"]::before {
        opacity: 1 !important;
        background: linear-gradient(90deg, #64748b 0%, #94a3b8 100%);
    }
    """

elif "Budgétaire" in current_module:
    active_style += """
    button[data-testid*="nav_budget"] {
        background: linear-gradient(135deg, #475569 0%, #64748b 100%) !important;
        color: white !important;
        border-top: 2px solid #64748b !important;
        box-shadow: 0 10px 25px rgba(71, 85, 105, 0.25), 0 5px 10px rgba(71, 85, 105, 0.15) !important;
    }
    button[data-testid*="nav_budget"]::before {
        opacity: 1 !important;
        background: linear-gradient(90deg, #64748b 0%, #94a3b8 100%);
    }
    """

active_style += "</style>"
st.markdown(active_style, unsafe_allow_html=True)

with nav_col1:
    btn_dept = st.button("Départements", use_container_width=True, key="nav_dept")
with nav_col2:
    btn_fournisseurs = st.button("Fournisseurs", use_container_width=True, key="nav_fourn")
with nav_col3:
    btn_budget = st.button("Budget", use_container_width=True, key="nav_budget")
with nav_col4:
    btn_stock = st.button("Stock & Compta", use_container_width=True, key="nav_stock")

# Déterminer le module sélectionné
if btn_dept:
    st.session_state.selected_module = "0. Gestion Départements"
elif btn_fournisseurs:
    st.session_state.selected_module = "1. Référentiel Fournisseurs"
elif btn_budget:
    st.session_state.selected_module = "2. Contrôle Budgétaire"
elif btn_stock:
    st.session_state.selected_module = "3. Gestion Stock & Compta"

# Initialiser la session state si nécessaire
if "selected_module" not in st.session_state:
    st.session_state.selected_module = "0. Gestion Départements"

module = st.session_state.selected_module

st.markdown("---")

# ==================== MODULE 0: GESTION DÉPARTEMENTS ====================

if "Gestion Départements" in module:
    st.markdown("## Gestion des Départements")
    st.markdown("")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Ajouter", "Lister", "Éditer", "Supprimer", "Budgets"])
    
    # ==================== TAB 1: AJOUTER UN DÉPARTEMENT ====================
    with tab1:
        st.subheader("Ajouter un nouveau département")
        
        with st.form("add_dept_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                dept_name = st.text_input("Nom du département *", placeholder="Ex: Direction Générale")
                dept_code = st.text_input("Code *", placeholder="Ex: DG", max_chars=10)
            
            with col2:
                dept_manager = st.text_input("Gestionnaire", placeholder="Ex: Jean Dupont")
                dept_email = st.text_input("Email", placeholder="Ex: contact@example.com")
            
            dept_description = st.text_area("Description", placeholder="Description optionnelle du département")
            
            submit = st.form_submit_button("Créer le département", use_container_width=True)
            
            if submit:
                if not dept_name or not dept_code:
                    st.error("Le nom et le code sont obligatoires")
                else:
                    payload = {
                        "name": dept_name,
                        "code": dept_code,
                        "manager": dept_manager if dept_manager else None,
                        "email": dept_email if dept_email else None,
                        "description": dept_description if dept_description else None
                    }
                    success, result = api_call("POST", "/departments/", payload)
                    
                    if success:
                        st.success(f"Département '{dept_name}' créé avec succès!")
                        st.json(result)
                    else:
                        st.error(f"Erreur: {result}")
    
    # ==================== TAB 2: LISTER LES DÉPARTEMENTS ====================
    with tab2:
        st.subheader("Liste des départements")
        
        if st.button(" Actualiser la liste", use_container_width=True):
            st.rerun()
        
        success_list, departments = api_call("GET", "/departments/")
        
        if success_list and departments:
            # Tableau
            df_depts = pd.DataFrame(departments)
            
            # Colonnes à afficher
            cols_to_show = ["id", "name", "code", "manager", "email", "status"]
            cols_available = [c for c in cols_to_show if c in df_depts.columns]
            df_display = df_depts[cols_available].copy()
            
            st.metric("Total de départements", len(departments))
            
            st.dataframe(
                df_display,
                use_container_width=True,
                column_config={
                    "id": st.column_config.TextColumn("ID", width="small"),
                    "name": st.column_config.TextColumn("Nom", width="medium"),
                    "code": st.column_config.TextColumn("Code", width="small"),
                    "manager": st.column_config.TextColumn("Gestionnaire", width="medium"),
                    "email": st.column_config.TextColumn("Email", width="medium"),
                    "status": st.column_config.TextColumn("Statut", width="small")
                },
                hide_index=True
            )
        elif not success_list:
            st.error(f"❌ Erreur: {departments}")
        else:
            st.info("Aucun département trouvé")
    
    # ==================== TAB 3: ÉDITER UN DÉPARTEMENT ====================
    with tab3:
        st.subheader("Éditer un département")
        
        success_list, departments = api_call("GET", "/departments/")
        
        if success_list and departments:
            # Sélectionner un département
            dept_options = {d["id"]: f"{d['name']} ({d['code']})" for d in departments}
            selected_id = st.selectbox(
                "Sélectionner un département à éditer",
                list(dept_options.keys()),
                format_func=lambda x: dept_options[x]
            )
            
            if selected_id:
                selected_dept = next((d for d in departments if d["id"] == selected_id), None)
                
                if selected_dept:
                    st.info(f"Édition: {selected_dept['name']} ({selected_dept['code']})")
                    
                    with st.form("edit_dept_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            edit_name = st.text_input(
                                "Nom du département",
                                value=selected_dept.get("name", "")
                            )
                            edit_code = st.text_input(
                                "Code",
                                value=selected_dept.get("code", ""),
                                max_chars=10,
                                disabled=True  # Code ne peut pas être modifié
                            )
                        
                        with col2:
                            edit_manager = st.text_input(
                                "Gestionnaire",
                                value=selected_dept.get("manager", "")
                            )
                            edit_email = st.text_input(
                                "Email",
                                value=selected_dept.get("email", "")
                            )
                        
                        edit_description = st.text_area(
                            "Description",
                            value=selected_dept.get("description", "")
                        )
                        
                        submit_edit = st.form_submit_button("Sauvegarder les modifications", use_container_width=True)
                        
                        if submit_edit:
                            update_payload = {
                                "name": edit_name,
                                "manager": edit_manager if edit_manager else None,
                                "email": edit_email if edit_email else None,
                                "description": edit_description if edit_description else None
                            }
                            success_update, result_update = api_call(
                                "PUT",
                                f"/departments/{selected_id}",
                                update_payload
                            )
                            
                            if success_update:
                                st.success("Département mis à jour avec succès!")
                                st.rerun()
                            else:
                                st.error(f"Erreur: {result_update}")
        else:
            st.error(f"❌ Erreur: {departments}")
    
    # ==================== TAB 4: SUPPRIMER UN DÉPARTEMENT ====================
    with tab4:
        st.subheader("Supprimer un département")
        st.warning("Attention: La suppression d'un département ne peut être annulée. Assurez-vous que le département n'est pas en cours d'utilisation.")
        
        success_list, departments = api_call("GET", "/departments/")
        
        if success_list and departments:
            dept_options = {d["id"]: f"{d['name']} ({d['code']})" for d in departments}
            selected_id_delete = st.selectbox(
                "Sélectionner un département à supprimer",
                list(dept_options.keys()),
                format_func=lambda x: dept_options[x],
                key="delete_select"
            )
            
            if selected_id_delete:
                selected_dept_delete = next((d for d in departments if d["id"] == selected_id_delete), None)
                
                if selected_dept_delete:
                    st.error(f" Département sélectionné: {selected_dept_delete['name']} ({selected_dept_delete['code']})")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Confirmer la suppression", use_container_width=True, key="confirm_delete"):
                            success_delete, result_delete = api_call(
                                "DELETE",
                                f"/departments/{selected_id_delete}"
                            )
                            
                            if success_delete:
                                st.success(f"Département '{selected_dept_delete['name']}' supprimé avec succès!")
                                st.rerun()
                            else:
                                st.error(f"Erreur: {result_delete}")
                    
                    with col2:
                        st.button("Annuler", use_container_width=True, key="cancel_delete")
        else:
            st.error(f"❌ Erreur: {departments}")
    
    # ==================== TAB 5: BUDGETS ====================
    with tab5:
        st.subheader("Gestion des Budgets")
        
        # Sub-tabs pour création et édition
        subtab1, subtab2 = st.tabs(["Créer un Budget", "Éditer un Budget"])
        
        # ==================== SUB-TAB 1: CRÉER UN BUDGET ====================
        with subtab1:
            st.subheader("Créer un nouveau budget")
            
            success_list, departments = api_call("GET", "/departments/")
            
            if success_list and departments:
                dept_options = {d["id"]: f"{d['name']} ({d['code']})" for d in departments}
                selected_dept_id = st.selectbox(
                    "Sélectionner un département *",
                    list(dept_options.keys()),
                    format_func=lambda x: dept_options[x],
                    key="create_budget_dept"
                )
                
                if selected_dept_id:
                    selected_dept = next((d for d in departments if d["id"] == selected_dept_id), None)
                    
                    with st.form("create_budget_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            dept_display = st.text_input(
                                "Département",
                                value=f"{selected_dept['name']} ({selected_dept['code']})",
                                disabled=True
                            )
                            allocated = st.number_input(
                                "Montant Alloué (€) *",
                                min_value=0.0,
                                step=1000.0,
                                value=50000.0
                            )
                        
                        with col2:
                            used = st.number_input(
                                "Montant Utilisé (€)",
                                min_value=0.0,
                                step=100.0,
                                value=0.0
                            )
                            st.info(f"**Disponible**: {allocated - used:,.2f} €")
                        
                        submit_create = st.form_submit_button("Créer le Budget", use_container_width=True)
                        
                        if submit_create:
                            payload = {
                                "department": selected_dept['name'],
                                "allocated": allocated,
                                "used": used
                            }
                            success_create, result_create = api_call("POST", "/budget/", payload)
                            
                            if success_create:
                                st.success(f"Budget créé pour {selected_dept['name']}!")
                                st.json(result_create)
                            else:
                                st.error(f"Erreur: {result_create}")
            else:
                st.error("Impossible de charger les départements")
        
        # ==================== SUB-TAB 2: ÉDITER UN BUDGET ====================
        with subtab2:
            st.subheader("Éditer un budget existant")
            
            success_budgets, budgets = api_call("GET", "/budget/")
            
            if success_budgets and budgets:
                budget_options = {b["id"]: f"{b['department']} - {b['allocated']:,.0f}€" for b in budgets}
                selected_budget_id = st.selectbox(
                    "Sélectionner un budget à éditer",
                    list(budget_options.keys()),
                    format_func=lambda x: budget_options[x],
                    key="edit_budget_select"
                )
                
                if selected_budget_id:
                    selected_budget = next((b for b in budgets if b["id"] == selected_budget_id), None)
                    
                    if selected_budget:
                        st.info(f" Édition: Budget de {selected_budget['department']}")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Alloué", f"{selected_budget['allocated']:,.2f} €")
                        with col2:
                            st.metric("Utilisé", f"{selected_budget['used']:,.2f} €")
                        with col3:
                            st.metric("Disponible", f"{selected_budget['available']:,.2f} €")
                        
                        with st.form("edit_budget_form"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                new_allocated = st.number_input(
                                    "Nouveau Montant Alloué (€)",
                                    min_value=0.0,
                                    value=selected_budget['allocated'],
                                    step=1000.0
                                )
                            
                            with col2:
                                new_used = st.number_input(
                                    "Nouveau Montant Utilisé (€)",
                                    min_value=0.0,
                                    value=selected_budget['used'],
                                    step=100.0
                                )
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                submit_update = st.form_submit_button(" Mettre à Jour", use_container_width=True)
                            
                            with col2:
                                submit_reset = st.form_submit_button(" Réinitialiser (used=0)", use_container_width=True)
                            
                            if submit_update:
                                update_payload = {
                                    "allocated": new_allocated,
                                    "used": new_used
                                }
                                success_update, result_update = api_call("PUT", f"/budget/update/{selected_budget_id}", update_payload)
                                if success_update:
                                    st.success("✓ Budget mis à jour avec succès!")
                                    st.rerun()
                                else:
                                    st.error(f"Erreur: {result_update}")
                            
                            if submit_reset:
                                reset_payload = {"used": 0}
                                success_reset, result_reset = api_call("PUT", f"/budget/reset/{selected_budget.get('department')}", reset_payload)
                                if success_reset:
                                    st.success("✓ Budget réinitialisé avec succès!")
                                    st.rerun()
                                else:
                                    st.error(f"Erreur: {result_reset}")
            else:
                st.info("Aucun budget trouvé. Créez-en un d'abord!")

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
            # Convertir les dates ISO8601 (peut contenir "Z" pour UTC)
            try:
                df_display["created_at"] = pd.to_datetime(df_display["created_at"], errors='coerce', utc=True)
                mask = df_display["created_at"].notna()
                df_display.loc[mask, "created_at"] = df_display.loc[mask, "created_at"].dt.strftime("%Y-%m-%d %H:%M")
                df_display.loc[~mask, "created_at"] = "Date invalide"
            except Exception:
                # Si la conversion échoue, garder les valeurs originales
                pass
            
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
                    
                    # Barre de progression (limité à 1.0 maximum pour st.progress)
                    progress_value = min(usage_pct / 100, 1.0)
                    st.progress(progress_value)
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
                    marker_color="#64748b"
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
                    delta={'reference': 70},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "#64748b"},
                        'steps': [
                            {'range': [0, 50], 'color': "#ccfbf1"},
                            {'range': [50, 75], 'color': "#5eead4"},
                            {'range': [75, 100], 'color': "#475569"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ))
                fig2 = style_chart(fig2, title="Taux d'Utilisation Moyen")
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
            st.info(" Les budgets se créent depuis le Module 0 - Gestion Départements, Onglet 'Budgets'")
    
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
            # Convertir les dates ISO8601 (peut contenir "Z" pour UTC)
            try:
                df_trx["created_at"] = pd.to_datetime(df_trx["created_at"], errors='coerce', utc=True)
                mask = df_trx["created_at"].notna()
                df_trx.loc[mask, "created_at"] = df_trx.loc[mask, "created_at"].dt.strftime("%Y-%m-%d %H:%M")
                df_trx.loc[~mask, "created_at"] = "Date invalide"
            except Exception:
                # Si la conversion échoue, garder les valeurs originales
                pass
            
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
            # Recréer le DataFrame avec les dates originales pour le graphique
            df_trx_chart = pd.DataFrame(transactions)
            df_trx_chart["date"] = pd.to_datetime(df_trx_chart["created_at"], errors='coerce', utc=True)
            df_trx_chart = df_trx_chart.sort_values("date")
            df_trx_chart["cumul"] = df_trx_chart["amount"].cumsum()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_trx_chart["date"],
                y=df_trx_chart["cumul"],
                mode='lines+markers',
                name='Cumul',
                line=dict(color='#64748b', width=3),
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
    
    # Charger les départements pour le sélecteur
    success_depts, departments = api_call("GET", "/departments")
    if success_depts and departments:
        dept_list = [d["name"] for d in departments]
    else:
        dept_list = []
        st.warning("Impossible de charger les départements")
    
    with tab1:
        st.subheader("Réception de Marchandises")
        
        with st.form("stock_reception"):
            col1, col2 = st.columns(2)
            
            with col1:
                item_id = st.text_input("Référence Article *", placeholder="Ex: REF-001")
                quantity = st.number_input("Quantité *", min_value=1, step=1)
                unit_price = st.number_input("Prix Unitaire (€) *", min_value=0.0, step=0.01)
            
            with col2:
                if dept_list:
                    department = st.selectbox("Département *", dept_list)
                else:
                    department = st.text_input("Département *", placeholder="Aucun département disponible")
                movement_type = st.selectbox("Type Mouvement", ["IN", "OUT"])
                project_id = st.text_input("Code Projet (Optionnel)", placeholder="Ex: PRJ-ALPHA")
            
            description = st.text_area("Description", placeholder="Détails du mouvement")
            
            submitted_stock = st.form_submit_button("Confirmer Réception", use_container_width=True)
        
        if submitted_stock:
            payload = {
                "item_id": item_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "department": department,
                "movement_type": movement_type,
                "project_id": project_id if project_id else None,
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
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_item = st.text_input("Rechercher un article", placeholder="ID ou nom...")
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Actualiser", key="refresh_stock", use_container_width=True):
                st.rerun()
        
        # Obtenir tous les articles
        success, stock_items = api_call("GET", "/stock/items")
        
        if not success:
            st.error(f"Erreur lors de la récupération des articles: {stock_items}")
        elif stock_items is None:
            st.warning("Aucune donnée reçue du serveur")
        elif isinstance(stock_items, list) and len(stock_items) == 0:
            st.info("Aucun article en stock pour le moment")
        elif success and stock_items:
            try:
                df_stock = pd.DataFrame(stock_items)
            
                # Vérifier que les colonnes nécessaires existent
                required_cols = ["item_id", "item_name", "quantity", "unit", "unit_price", "min_threshold"]
                missing_cols = [col for col in required_cols if col not in df_stock.columns]
                if missing_cols:
                    st.error(f"Colonnes manquantes dans les données: {', '.join(missing_cols)}")
                    st.json(stock_items[0] if stock_items else {})  # Afficher un exemple
                else:
                    # Filtrage par recherche
                    if search_item:
                        df_stock = df_stock[
                            df_stock["item_id"].str.contains(search_item, case=False, na=False) |
                            df_stock["item_name"].str.contains(search_item, case=False, na=False)
                        ]
                    
                    # Calcul valeur totale
                    df_stock["valeur_totale"] = df_stock["quantity"] * df_stock["unit_price"]
                    df_stock["is_low_stock"] = df_stock["quantity"] < df_stock["min_threshold"]
            
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
                        low_stock_count = len(df_stock[df_stock["is_low_stock"]])
                        st.metric("Alertes", low_stock_count, delta=f"-{low_stock_count}" if low_stock_count > 0 else "0", delta_color="inverse")
                    
                    st.markdown("")
                    st.write("### Tous les Articles du Stock")
            
                    # Préparer les colonnes pour l'affichage
                    df_display = df_stock[["item_id", "item_name", "quantity", "unit", "unit_price", "valeur_totale", "is_low_stock", "min_threshold"]].copy()
                    
                    # Créer la colonne d'affichage pour la quantité avec indicateur
                    df_display["qty_display"] = df_display.apply(
                        lambda row: f"[LOW] {row['quantity']:.0f}" if row['is_low_stock'] else f"[OK] {row['quantity']:.0f}",
                        axis=1
                    )
                    
                    # Tableau avec Streamlit dataframe
                    st.dataframe(
                        df_display[["item_id", "item_name", "qty_display", "unit", "unit_price", "valeur_totale"]].rename(columns={
                            "item_id": "Référence",
                            "item_name": "Nom",
                            "qty_display": "Quantité",
                            "unit": "Unité",
                            "unit_price": "Prix Unitaire (€)",
                            "valeur_totale": "Valeur (€)"
                        }),
                        use_container_width=True,
                        column_config={
                            "Référence": st.column_config.TextColumn("Référence", width="small"),
                            "Nom": st.column_config.TextColumn("Nom", width="medium"),
                            "Quantité": st.column_config.TextColumn("Quantité", width="small"),
                            "Unité": st.column_config.TextColumn("Unité", width="small"),
                            "Prix Unitaire (€)": st.column_config.NumberColumn("Prix Unitaire (€)", format="%.2f", width="small"),
                            "Valeur (€)": st.column_config.NumberColumn("Valeur (€)", format="%.2f", width="small")
                        },
                        hide_index=True
                    )
                    
                    st.markdown("")
                    
                    # Boutons de suppression pour les articles en stock faible
                    if df_display["is_low_stock"].any():
                        st.markdown("#### Articles en stock faible")
                        low_stock_df = df_display[df_display["is_low_stock"]]
                        
                        for idx, item in low_stock_df.iterrows():
                            col1, col2, col3 = st.columns([2, 2, 1])
                            with col1:
                                st.write(f"**{item['item_id']}** - {item['item_name']}")
                            with col2:
                                st.write(f"Quantité: {item['quantity']:.0f} {item['unit']} (Seuil: {item['min_threshold']:.0f})")
                            with col3:
                                if st.button(
                                    label="Supprimer",
                                    key=f"delete_{item['item_id']}_{idx}",
                                    help=f"Supprimer {item['item_id']}",
                                    use_container_width=True
                                ):
                                    success_del, result_del = api_call("DELETE", f"/stock/items/{item['item_id']}")
                                    
                                    if success_del:
                                        st.success(f"{item['item_id']} supprimé!")
                                        st.rerun()
                                    else:
                                        st.error(f"Erreur: {result_del}")
                    
                    st.markdown("---")
                    
                    # Export
                    csv = df_stock[["item_id", "item_name", "quantity", "unit", "unit_price", "min_threshold", "valeur_totale"]].to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Exporter en CSV",
                        data=csv,
                        file_name=f"stock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )
            except Exception as e:
                st.error(f"Erreur lors du traitement des données: {str(e)}")
                st.exception(e)
    
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
            # Convertir les dates ISO8601 (peut contenir "Z" pour UTC)
            try:
                df_mov["created_at"] = pd.to_datetime(df_mov["created_at"], errors='coerce', utc=True)
                mask = df_mov["created_at"].notna()
                df_mov.loc[mask, "created_at"] = df_mov.loc[mask, "created_at"].dt.strftime("%Y-%m-%d %H:%M")
                df_mov.loc[~mask, "created_at"] = "Date invalide"
            except Exception:
                # Si la conversion échoue, garder les valeurs originales
                pass
            
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
                # Recréer le DataFrame avec les dates originales pour le graphique
                df_mov_chart = pd.DataFrame(movements)
                df_mov_chart["date"] = pd.to_datetime(df_mov_chart["created_at"], errors='coerce', utc=True)
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
                    color_discrete_sequence=["#64748b", "#475569"]
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


