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
    margin-bottom: 0.5rem;
}

.subtitle {
    color: #666;
    margin-bottom: 1.5rem;
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

/* Footer */
.footer {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #eee;
    color: #666;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🛑 HEADER
# ==============================================================================

def render_header():
    """Renderizza l'header della pagina"""
    st.markdown('<h1 class="main-title">📚 Circolari Online</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Circolari scolastiche aggiornate automaticamente</p>', unsafe_allow_html=True)
    st.markdown("---")

# ==============================================================================
# 🛑 ELENCO CIRCOLARI
# ==============================================================================

def render_circolari():
    """Renderizza l'elenco delle circolari"""
    # Carica circolari
    circolari = db.get_circolari()
    
    if not circolari:
        st.info("📭 Al momento non ci sono circolari disponibili.")
        st.write("Il sistema si aggiorna automaticamente ogni ora.")
        return
    
    # Mostra ogni circolare
    for circ in circolari:
        with st.container():
            st.markdown('<div class="circolare-card">', unsafe_allow_html=True)
            
            # Titolo e data
            st.markdown(f"### {circ['titolo']}")
            
            # Data formattata (usa la colonna giusta)
            data_display = circ.get('data_formattata') or circ.get('data_pubblicazione')
            if data_display:
                st.markdown(f"**Data pubblicazione:** {data_display}")
            
            # Allegati
            allegati_raw = circ.get('allegati', '')
            if allegati_raw:
                # Converti stringa in lista
                if isinstance(allegati_raw, str):
                    allegati = [a.strip() for a in allegati_raw.split(',') if a.strip()]
                else:
                    allegati = allegati_raw
                
                if allegati:
                    st.markdown("**Allegati:**")
                    # Mostra ogni allegato come badge
                    for allegato in allegati:
                        st.markdown(f'<span class="allegato-badge">📎 {allegato}</span>', unsafe_allow_html=True)
            
            # Contenuto
            st.markdown("---")
            st.markdown("**Contenuto:**")
            st.write(circ.get('contenuto', 'Nessun contenuto disponibile'))
            
            st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 🛑 SIDEBAR (SOLO INFO SEMPLICI)
# ==============================================================================

def render_sidebar():
    """Renderizza la sidebar semplificata"""
    with st.sidebar:
        st.markdown("### 📊 Statistiche")
        
        # Statistiche semplici
        circolari = db.get_circolari()
        if circolari:
            st.metric("Circolari disponibili", len(circolari))
        
        # Auto-refresh info
        st.markdown("---")
        st.markdown("### 🔄 Aggiornamento")
        st.write("Le circolari si aggiornano **automaticamente** ogni ora.")

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
    
    # Footer semplice
    st.markdown("---")
    st.markdown(f'<div class="footer">© {datetime.now().year} Circolari Online • Ultimo aggiornamento: {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>', unsafe_allow_html=True)

# ==============================================================================
# 🛑 AVVIO
# ==============================================================================

if __name__ == "__main__":
    main()
