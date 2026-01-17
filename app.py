"""
app.py - Visualizzatore circolari ARGO
Interfaccia ottimizzata per i dati ARGO reali
"""

import streamlit as st
from datetime import datetime, timedelta
import database as db

# ==============================================================================
# 🛑 CONFIGURAZIONE PAGINA
# ==============================================================================

st.set_page_config(
    page_title="Circolari ARGO Online",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 🛑 CSS PERSONALIZZATO ARGO
# ==============================================================================

st.markdown("""
<style>
/* Header stile istituzionale */
.main-title {
    font-size: 2.8rem;
    color: #1E3A8A;
    margin-bottom: 0.3rem;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.subtitle {
    color: #4B5563;
    margin-bottom: 2rem;
    font-size: 1.2rem;
    text-align: center;
    font-weight: 400;
}

/* Card circolare stile ARGO */
.circolare-card {
    background: linear-gradient(145deg, #FFFFFF, #F9FAFB);
    border-radius: 12px;
    padding: 1.8rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    border-left: 6px solid #3B82F6;
    border-top: 1px solid #E5E7EB;
    border-right: 1px solid #E5E7EB;
    border-bottom: 2px solid #E5E7EB;
    transition: all 0.3s ease;
}

.circolare-card:hover {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    transform: translateY(-2px);
    border-left-color: #1D4ED8;
}

/* Bad
