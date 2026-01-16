"""
app.py - Versione SEMPLIFICATA
Applicazione Streamlit per visualizzare circolari
"""

import streamlit as st
from datetime import datetime
import database as db

# ==============================================================================
# 🛑 CONFIGURAZIONE PAGINA
# ==============================================================================

st.set_page_config(
    page_title="Circolari Online",
    page_icon="📚",
    layout="wide"
)

# ==============================================================================
# 🛑 CSS PERSONALIZZATO
# ==============================================================================

st.markdown("""
<style>
/* Header */
.main-title {
    font-size: 2.5rem;
    color: #1E88E5;
    margin-bottom: 1rem;
}

/* Card circolare */
.circolare-card {
    background-color: white;
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    border-left: 4px solid #1E88E5;
}

/* Badge allegati */
.allegato-badge {
    display: inline-block;
    background-color: #E3F2FD;
    color: #1565C0;
    padding: 0.3rem 0.8rem;
    border-radius: 15px;
    font-size: 0.85rem;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
}

/* Pulsanti */
.stButton button {
    border-radius: 8px;
    font-weight: 600;
}

/* Status database */
.db-status-connected {
    color: #2E7D32;
    font-weight: bold;
}

.db-status-disconnected {
    color: #D32F2F;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🛑 HEADER
# ==============================================================================

def render_header():
    """Renderizza l'header della pagina"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<h1 class="main-title">📚 Circolari Online</h1>', unsafe_allow_html=True)
        st.markdown("**Visualizzazione circolari scolastiche**")
    
    with col2:
        # Test connessione database
        test_result = db.test_connection()
        if test_result["status"] == "connected":
            st.markdown('<span class="db-status-connected">✅ Database Connesso</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="db-status-disconnected">❌ Database Offline</span>', unsafe_allow_html=True)
    
    st.markdown("---")

# ==============================================================================
# 🛑 ELENCO CIRCOLARI
# ==============================================================================

def render_circolari():
    """Renderizza l'elenco delle circolari"""
    # Pulsante aggiorna
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 📋 Elenco Circolari")
    
    with col2:
        if st.button("🔄 Aggiorna", use_container_width=True):
            st.rerun()
    
    # Carica circolari
    circolari = db.get_circolari_recenti(limite=100)
    
    if not circolari:
        st.info("📭 Nessuna circolare disponibile.")
        st.write("Il robot GitHub Actions esegue automaticamente ogni giorno alle 8:00 UTC.")
        return
    
    # Mostra numero circolari
    st.success(f"**{len(circolari)} circolari disponibili**")
    
    # Mostra ogni circolare
    for circ in circolari:
        with st.container():
            st.markdown('<div class="circolare-card">', unsafe_allow_html=True)
            
            # Titolo e data
            st.markdown(f"### {circ['titolo']}")
            st.markdown(f"**Data:** {circ['data_formattata']}")
            
            # Allegati
            allegati = circ.get('allegati', [])
            if allegati and len(allegati) > 0:
                st.markdown("**Allegati:**")
                
                # Mostra ogni allegato come badge
                for allegato in allegati:
                    if allegato.strip():  # Salta stringhe vuote
                        st.markdown(f'<span class="allegato-badge">📎 {allegato}</span>', unsafe_allow_html=True)
            
            # Contenuto
            st.markdown("---")
            st.markdown("**Contenuto:**")
            st.write(circ['contenuto'])
            
            st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 🛑 SIDEBAR
# ==============================================================================

def render_sidebar():
    """Renderizza la sidebar"""
    with st.sidebar:
        st.markdown("### ℹ️ Informazioni")
        
        # Test connessione
        test_result = db.test_connection()
        
        if test_result["status"] == "connected":
            st.success("Database connesso")
            st.write("**Host:** postgres.railway.internal")
            st.write("**Porta:** 5432")
        else:
            st.error("Database non connesso")
        
        # Statistiche semplici
        circolari = db.get_circolari_recenti(limite=1000)
        if circolari:
            st.metric("Circolari totali", len(circolari))
            
            # Data ultima circolare
            if circolari:
                ultima_data = circolari[0].get('data_formattata', 'N/A')
                st.write(f"**Ultima circolare:** {ultima_data}")
        
        # Informazioni robot
        st.markdown("---")
        st.markdown("### 🤖 Robot")
        st.write("Il robot si esegue automaticamente:")
        st.write("- **Ogni giorno** alle 8:00 UTC (9:00 Italia)")
        st.write("- **Manualmente** su GitHub Actions")
        
        # Link utili
        st.markdown("---")
        st.markdown("### 🔗 Link utili")
        st.write("[🌐 App Streamlit](https://circolari-online-production.up.railway.app)")
        st.write("[🤖 GitHub Actions](https://github.com/tuo-user/circolari-online/actions)")

# ==============================================================================
# 🛑 MAIN APP
# ==============================================================================

def main():
    """Funzione principale"""
    # Render header
    render_header()
    
    # Render sidebar
    render_sidebar()
    
    # Render circolari
    render_circolari()
    
    # Footer
    st.markdown("---")
    st.caption(f"© {datetime.now().year} Circolari Online • Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ==============================================================================
# 🛑 AVVIO
# ==============================================================================

if __name__ == "__main__":
    main()
