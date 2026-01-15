import os
import sys
import streamlit as st
import pandas as pd
from database import init_database, test_database_connection, get_circolari

# ==================== CONFIGURAZIONE ====================
st.set_page_config(
    page_title="Bacheca Circolari IC Anna Frank",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== DEBUG SIDEBAR ====================
with st.sidebar:
    st.title("🔧 Sistema di Debug")
    
    # Mostra ambiente
    st.subheader("Informazioni Ambiente")
    st.code(f"Python: {sys.version}")
    
    # Mostra variabili d'ambiente (solo alcune)
    env_vars = {
        'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT', 'Non rilevato'),
        'PORT': os.environ.get('PORT', 'Non impostato'),
        'DATABASE_URL_LENGTH': len(os.environ.get('DATABASE_URL', ''))
    }
    
    for key, value in env_vars.items():
        st.text(f"{key}: {value}")
    
    # Mostra DATABASE_URL (censurata)
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Censura password per sicurezza
        if '@' in db_url:
            parts = db_url.split('@')
            safe_url = parts[0].split(':')
            if len(safe_url) > 2:
                safe_url[2] = '***'  # Nascondi password
            db_url_display = ':'.join(safe_url) + '@' + parts[1]
        else:
            db_url_display = db_url
        
        st.text_area("DATABASE_URL (censurata):", db_url_display, height=100)
        
        # Controlla se è URL interno o pubblico
        if 'railway.internal' in db_url:
            st.error("⚠️ ATTENZIONE: URL INTERNO del database")
            st.info("Devi usare l'URL PUBLICO: switchback.proxy.rlwy.net:53723")
        else:
            st.success("✅ URL PUBBLICO del database")
    else:
        st.error("❌ DATABASE_URL NON TROVATA")
    
    st.markdown("---")

# ==================== INTESTAZIONE PRINCIPALE ====================
st.title("📄 Bacheca Circolari IC Anna Frank")
st.subheader("Istituto Comprensivo Anna Frank - Agrigento")

st.markdown("""
**Sistema Automatico • Hosting su Railway • Realizzato da Prof. Davide Marziano**
""")

# ==================== SEZIONE DATABASE ====================
st.markdown("---")
st.header("🔧 Configurazione e Verifica Database")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Test Connessione")
    if st.button("🔍 Test Rapido Connessione", type="primary", use_container_width=True):
        with st.spinner("Test in corso..."):
            success, message = test_database_connection()
            if success:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")

with col2:
    st.subheader("Inizializzazione")
    if st.button("🔄 Inizializza/Verifica Database", type="secondary", use_container_width=True):
        with st.spinner("Inizializzazione in corso..."):
            result = init_database()
            if "✅" in result:
                st.success(result)
            else:
                st.error(result)

# ==================== SEZIONE PRINCIPALE APP ====================
st.markdown("---")
st.header("📋 Elenco Circolari")

# Pulsante per caricare circolari
if st.button("📥 Carica Circolari dal Database"):
    with st.spinner("Caricamento in corso..."):
        df = get_circolari(100)
        
        if not df.empty:
            st.success(f"✅ Trovate {len(df)} circolari")
            
            # Mostra tabella
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "ID",
                    "titolo": "Titolo",
                    "data_pubblicazione": "Data",
                    "file_url": "File",
                    "contenuto": "Contenuto",
                    "created_at": "Creato il"
                }
            )
            
            # Statistiche
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Totale Circolari", len(df))
            with col2:
                st.metric("Prima Data", df['data_pubblicazione'].min())
            with col3:
                st.metric("Ultima Data", df['data_pubblicazione'].max())
        else:
            st.warning("⚠️ Nessuna circolare trovata nel database")
            st.info("Il database è vuoto o ci sono problemi di connessione.")

# ==================== SEZIONE INFORMAZIONI SISTEMA ====================
st.markdown("---")
st.header("⚙️ Informazioni Sistema")

st.markdown("""
### Sistema 100% Railway - Completamente Automatico

- **Piattaforma**: Railway.app (WebApp + Database PostgreSQL)
- **Database**: PostgreSQL su Railway (1GB storage gratuito)
- **Velocità**: Server Europei - HTTPS automatico
- **Sicurezza**: SSL/TLS - Connessioni cifrate
- **Aggiornamento**: Auto-refresh ogni 5 minuti

*Deploy automatico • Zero manutenzione • Always online 24/7*
""")

# ==================== FOOTER ====================
st.markdown("---")
st.caption("© 2025 Istituto Comprensivo Anna Frank - Agrigento • Versione 2.0 • Railway Hosting")

# ==================== AUTO-RUN DEBUG ====================
# Esegue automaticamente un test all'avvio (solo in debug)
if os.environ.get('RAILWAY_ENVIRONMENT'):
    with st.sidebar:
        if st.button("🔄 Auto-test all'avvio"):
            success, message = test_database_connection()
            if success:
                st.balloons()
