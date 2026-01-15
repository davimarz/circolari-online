import os
import sys
import streamlit as st
import pandas as pd
from datetime import datetime
from database import init_database, test_connection_simple, get_circolari, insert_circolare, get_robot_logs

# ==================== CONFIGURAZIONE ====================
st.set_page_config(
    page_title="Bacheca Circolari IC Anna Frank",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.title("🔧 Sistema di Debug")
    
    # Informazioni ambiente
    st.subheader("🎯 Ambiente")
    st.code(f"Python: {sys.version.split()[0]}")
    
    env_vars = {
        'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT', 'Non rilevato'),
        'PORT': os.environ.get('PORT', 'Non impostato'),
    }
    
    for key, value in env_vars.items():
        st.text(f"{key}: {value}")
    
    # Configurazione database
    st.markdown("---")
    st.subheader("🗄️ Database")
    
    db_config = {
        'Host': 'switchback.proxy.rlwy.net',
        'Porta': '53723',
        'Utente': 'postgres',
        'Database': 'railway'
    }
    
    for key, value in db_config.items():
        st.text(f"{key}: {value}")
    
    # Test connessione
    st.markdown("---")
    st.subheader("🧪 Test")
    
    if st.button("🔍 Test Connessione", type="primary", use_container_width=True):
        with st.spinner("Test in corso..."):
            success, message = test_connection_simple()
            if success:
                st.success(message)
            else:
                st.error(message)

# ==================== INTESTAZIONE ====================
st.title("📄 Bacheca Circolari IC Anna Frank")
st.subheader("Istituto Comprensivo Anna Frank - Agrigento")

st.markdown("**Sistema Automatico • Hosting su Railway • Realizzato da Prof. Davide Marziano**")

# ==================== SEZIONE DATABASE ====================
st.markdown("---")
st.header("🔧 Database Railway")

col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 Test Rapido", type="primary", use_container_width=True):
        with st.spinner("Test..."):
            success, message = test_connection_simple()
            if success:
                st.success(message)
            else:
                st.error(message)

with col2:
    if st.button("🔄 Inizializza", type="secondary", use_container_width=True):
        with st.spinner("Inizializzazione..."):
            result = init_database()
            if "✅" in result:
                st.success(result)
            else:
                st.error(result)

# ==================== SEZIONE CIRCOLARI ====================
st.markdown("---")
st.header("📋 Circolari")

tab1, tab2, tab3 = st.tabs(["📥 Visualizza", "📤 Inserisci", "📊 Logs Robot"])

with tab1:
    st.subheader("Elenco Circolari")
    
    if st.button("🔄 Carica Circolari", type="primary"):
        with st.spinner("Caricamento..."):
            df = get_circolari(50)
            
            if not df.empty:
                st.success(f"✅ {len(df)} circolari")
                
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id": "ID",
                        "titolo": "Titolo",
                        "data_pubblicazione": "Data",
                        "categoria": "Categoria",
                        "firmatario": "Firmatario",
                        "fonte": "Fonte"
                    }
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Totale", len(df))
                with col2:
                    if not df.empty:
                        st.metric("Ultima", df['data_pubblicazione'].max().strftime('%d/%m/%Y'))
            else:
                st.warning("⚠️ Nessuna circolare")
                st.info("Il database è vuoto o robot non ancora eseguito")

with tab2:
    st.subheader("Nuova Circolare")
    
    with st.form("nuova_circolare"):
        titolo = st.text_input("Titolo*", placeholder="Titolo circolare")
        contenuto = st.text_area("Contenuto*", placeholder="Testo...", height=150)
        categoria = st.selectbox("Categoria", ["Generale", "Didattica", "Amministrativa", "Urgente"])
        firmatario = st.text_input("Firmatario", placeholder="Nome firmatario")
        
        submitted = st.form_submit_button("📤 Salva", type="primary")
        
        if submitted:
            if titolo and contenuto:
                with st.spinner("Salvataggio..."):
                    success, message = insert_circolare(
                        titolo=titolo,
                        contenuto=contenuto,
                        categoria=categoria,
                        firmatario=firmatario
                    )
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            else:
                st.error("Compila tutti i campi obbligatori (*)")

with tab3:
    st.subheader("Logs Robot")
    
    if st.button("🔄 Carica Logs", type="primary"):
        with st.spinner("Caricamento logs..."):
            df_logs = get_robot_logs(20)
            
            if not df_logs.empty:
                st.success(f"✅ {len(df_logs)} logs")
                
                st.dataframe(
                    df_logs,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "tipo": "Tipo",
                        "messaggio": "Messaggio",
                        "dettagli": "Dettagli",
                        "created_at": "Data/ora"
                    }
                )
            else:
                st.info("Nessun log disponibile")

# ==================== INFORMAZIONI ====================
st.markdown("---")
st.header("⚙️ Sistema")

st.markdown("""
**Sistema 100% Railway - Automatico**

- **Piattaforma**: Railway.app (WebApp + PostgreSQL)
- **Database**: PostgreSQL su Railway
- **Sicurezza**: HTTPS/SSL automatico
- **Aggiornamento**: Auto-refresh

*Deploy automatico • Always online 24/7*
""")

# ==================== FOOTER ====================
st.markdown("---")
st.caption(f"© {datetime.now().year} IC Anna Frank - Agrigento • Versione 2.0 • {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Auto-test all'avvio
if os.environ.get('RAILWAY_ENVIRONMENT'):
    with st.spinner("Verifica automatica..."):
        success, message = test_connection_simple()
        if success:
            st.sidebar.success("✅ Connessione OK all'avvio")
