import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# ============================================
# CONFIGURAZIONE PAGINA
# ============================================
st.set_page_config(
    page_title="Bacheca Circolari IC Anna Frank",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ... (CSS rimane uguale) ...

# ============================================
# FUNZIONI DATABASE POSTGRESQL (PRIVATO)
# ============================================
def get_db_connection():
    """Crea connessione PRIVATA al database PostgreSQL su Railway"""
    try:
        # Railway fornisce DATABASE_URL automaticamente (connessione PRIVATA)
        # NON usare DATABASE_PUBLIC_URL per evitare costi
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            st.error("""
            ❌ DATABASE_URL non configurato su Railway
            
            **Risoluzione:**
            1. Vai su Railway Dashboard → Variables
            2. Usa DATABASE_URL (non DATABASE_PUBLIC_URL)
            3. Se non vedi DATABASE_URL, riavvia il database PostgreSQL
            """)
            return None
        
        # Connessione PRIVATA a PostgreSQL (zero egress fees)
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
        
    except Exception as e:
        st.error(f"❌ Errore connessione database PRIVATO: {str(e)}")
        st.info("""
        **Verifica:**
        1. Il database PostgreSQL è attivo su Railway
        2. Stai usando DATABASE_URL (privata)
        3. La variabile è impostata correttamente
        """)
        return None

# ... (resto del file invariato) ...
