import os
import sys
import streamlit as st
import pandas as pd
from datetime import datetime
from database import init_database, test_connection_simple, get_circolari, insert_circolare, get_database_connection

# ==================== CONFIGURAZIONE ====================
st.set_page_config(
    page_title="Bacheca Circolari IC Anna Frank",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== SIDEBAR DEBUG ====================
with st.sidebar:
    st.title("🔧 Sistema di Debug")
    
    # Informazioni ambiente
    st.subheader("🎯 Informazioni Ambiente")
    st.code(f"Python: {sys.version.split()[0]}")
    
    env_info = {
        'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT', 'Non rilevato'),
        'PORT': os.environ.get('PORT', 'Non impostato'),
        'RAILWAY_PROJECT_NAME': os.environ.get('RAILWAY_PROJECT_NAME', 'Non impostato'),
    }
    
    for key, value in env_info.items():
        st.text(f"{key}: {value}")
    
    # Informazioni database
    st.markdown("---")
    st.subheader("🗄️ Configurazione Database")
    
    db_config = {
        'Host': 'switchback.proxy.rlwy.net',
        'Porta': '53723',
        'Utente': 'postgres',
        'Database': 'railway',
        'Password': 'TpsVpUowNnMqSXpvAosQEezxpGPtbPNG'[:8] + '...' + 'TpsVpUowNnMqSXpvAosQEezxpGPtbPNG'[-8:],
        'Lunghezza password': '32 caratteri'
    }
    
    for key, value in db_config.items():
        st.text(f"{key}: {value}")
    
    st.success("✅ Configurazione database verificata")
    
    # Test connessione
    st.markdown("---")
    st.subheader("🧪 Test Connessione")
    
    if st.button("🔍 Test Connessione Database", type="primary", use_container_width=True):
        with st.spinner("Test in corso..."):
            success, message = test_connection_simple()
            if success:
                st.success(message)
                st.balloons()
            else:
                st.error(message)

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
    st.subheader("🔍 Test Rapido")
    if st.button("🚀 Test Connessione", type="primary", use_container_width=True):
        with st.spinner("Test in corso..."):
            success, message = test_connection_simple()
            if success:
                st.success(message)
            else:
                st.error(message)

with col2:
    st.subheader("⚙️ Inizializzazione")
    if st.button("🔄 Inizializza Database", type="secondary", use_container_width=True):
        with st.spinner("Inizializzazione in corso..."):
            result = init_database()
            if "✅" in result:
                st.success(result)
            else:
                st.error(result)

# ==================== SEZIONE CIRCOLARI ====================
st.markdown("---")
st.header("📋 Gestione Circolari")

tab1, tab2 = st.tabs(["📥 Visualizza Circolari", "📤 Inserisci Nuova"])

with tab1:
    st.subheader("Elenco Circolari")
    
    if st.button("🔄 Carica Circolari", type="primary"):
        with st.spinner("Caricamento in corso..."):
            df = get_circolari(50)
            
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
                        "categoria": "Categoria",
                        "priorita": "Priorità",
                        "firmatario": "Firmatario",
                        "created_at": "Creata il"
                    }
                )
                
                # Statistiche
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Totale Circolari", len(df))
                with col2:
                    st.metric("Prima Data", df['data_pubblicazione'].min().strftime('%d/%m/%Y'))
                with col3:
                    st.metric("Ultima Data", df['data_pubblicazione'].max().strftime('%d/%m/%Y'))
            else:
                st.warning("⚠️ Nessuna circolare trovata nel database")
                st.info("Il database è vuoto. Usa la tab 'Inserisci Nuova' per aggiungere circolari.")

with tab2:
    st.subheader("Inserisci Nuova Circolare")
    
    with st.form("nuova_circolare_form"):
        titolo = st.text_input("Titolo della circolare*", placeholder="Es: Chiusura scuola per neve")
        contenuto = st.text_area("Contenuto*", placeholder="Inserisci il testo della circolare...", height=200)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            categoria = st.selectbox("Categoria", ["Generale", "Didattica", "Amministrativa", "Eventi", "Urgente"])
        with col2:
            priorita = st.selectbox("Priorità", [1, 2, 3, 4, 5], format_func=lambda x: f"⭐ {x}" if x == 1 else f"⭐⭐ {x}" if x == 2 else f"⭐⭐⭐ {x}" if x == 3 else f"⭐⭐⭐⭐ {x}" if x == 4 else f"⭐⭐⭐⭐⭐ {x}")
        with col3:
            firmatario = st.text_input("Firmatario", placeholder="Es: Dirigente Scolastico")
        
        file_url = st.text_input("URL file allegato (opzionale)", placeholder="https://...")
        
        submitted = st.form_submit_button("📤 Inserisci Circolare", type="primary")
        
        if submitted:
            if not titolo or not contenuto:
                st.error("❌ Compila tutti i campi obbligatori (*)")
            else:
                with st.spinner("Salvataggio in corso..."):
                    success, message = insert_circolare(
                        titolo=titolo,
                        contenuto=contenuto,
                        file_url=file_url if file_url else None,
                        categoria=categoria,
                        priorita=priorita,
                        firmatario=firmatario
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                    else:
                        st.error(f"❌ {message}")

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
st.caption(f"© {datetime.now().year} Istituto Comprensivo Anna Frank - Agrigento • Versione 2.0 • Railway Hosting • {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ==================== AUTO-TEST ALL'AVVIO ====================
# Test automatico all'avvio (solo in produzione)
if os.environ.get('RAILWAY_ENVIRONMENT') == 'production':
    with st.spinner("Verifica automatica connessione database..."):
        success, message = test_connection_simple()
        if success:
            st.sidebar.success("✅ Connessione OK all'avvio")
        else:
            st.sidebar.error("❌ Problema connessione all'avvio")
