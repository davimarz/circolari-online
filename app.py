"""
app.py - Visualizzatore circolari ARGO
Versione senza sidebar - Interfaccia pulita
"""

import streamlit as st
from datetime import datetime
import database as db

# ==============================================================================
# 🛑 CONFIGURAZIONE PAGINA
# ==============================================================================

st.set_page_config(
    page_title="Circolari ARGO Online",
    page_icon="📋",
    layout="wide"
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

/* Badge data */
.data-badge {
    display: inline-block;
    background: linear-gradient(135deg, #3B82F6, #1D4ED8);
    color: white;
    padding: 0.5rem 1.2rem;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 600;
    margin-bottom: 1rem;
    box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.data-vecchia {
    background: linear-gradient(135deg, #6B7280, #4B5563) !important;
}

/* Badge allegati */
.allegato-badge {
    display: inline-flex;
    align-items: center;
    background: linear-gradient(135deg, #F0F9FF, #E0F2FE);
    color: #0369A1;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 500;
    margin-right: 0.8rem;
    margin-bottom: 0.8rem;
    border: 1px solid #BAE6FD;
    transition: all 0.2s ease;
    cursor: pointer;
}

.allegato-badge:hover {
    background: linear-gradient(135deg, #E0F2FE, #BAE6FD);
    transform: scale(1.05);
    box-shadow: 0 2px 8px rgba(2, 132, 199, 0.2);
}

/* Contenuto circolare */
.contenuto-circolare {
    background-color: #F8FAFC;
    padding: 1.5rem;
    border-radius: 10px;
    margin: 1.5rem 0;
    border: 1px solid #E2E8F0;
    font-size: 1rem;
    line-height: 1.7;
    white-space: pre-line;
    color: #334155;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}

.contenuto-circolare strong {
    color: #1E3A8A;
    font-weight: 700;
}

/* Footer */
.footer {
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 2px solid #E5E7EB;
    color: #6B7280;
    font-size: 0.9rem;
    text-align: center;
}

/* Responsive */
@media (max-width: 768px) {
    .main-title {
        font-size: 2rem;
    }
    
    .circolare-card {
        padding: 1.2rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🛑 HEADER
# ==============================================================================

def render_header():
    """Renderizza l'header della pagina"""
    st.markdown('<h1 class="main-title">📋 CIRCOLARI ONLINE</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Portale circolari scolastiche</p>', unsafe_allow_html=True)
    st.markdown("---")

# ==============================================================================
# 🛑 ELENCO CIRCOLARI
# ==============================================================================

def render_circolari():
    """Renderizza l'elenco delle circolari"""
    # Carica circolari degli ultimi 30 giorni
    circolari = db.get_circolari_ultimi_30_giorni()
    
    if not circolari:
        st.info("""
        📭 **Al momento non ci sono circolari disponibili.**
        
        Le circolari si aggiornano automaticamente.
        """)
        return
    
    # Contatore circolari
    st.markdown(f"### 📋 **{len(circolari)} Circolari disponibili**")
    
    # Mostra ogni circolare in ordine decrescente di data
    for circ in circolari:
        with st.container():
            st.markdown('<div class="circolare-card">', unsafe_allow_html=True)
            
            # Data
            giorni_fa = circ.get('giorni_fa', 99)
            
            data_display = circ.get('data_visualizzazione') or circ.get('data_formattata') or circ.get('data_pubblicazione')
            
            if isinstance(data_display, str):
                data_str = data_display
            else:
                data_str = data_display.strftime('%d/%m/%Y')
            
            # Colore badge in base all'età
            if giorni_fa == 0:
                badge_class = "data-badge"
                tempo = "🆕 OGGI"
            elif giorni_fa == 1:
                badge_class = "data-badge"
                tempo = "📅 IERI"
            elif giorni_fa <= 7:
                badge_class = "data-badge"
                tempo = f"📅 {giorni_fa} GIORNI FA"
            else:
                badge_class = "data-badge data-vecchia"
                tempo = f"📅 {data_str}"
            
            st.markdown(f'<span class="{badge_class}">{tempo}</span>', unsafe_allow_html=True)
            
            # Titolo
            if circ.get('titolo'):
                titolo = circ['titolo']
                st.markdown(f'<div style="font-size: 1.4rem; font-weight: 700; color: #1E3A8A; margin-top: 0.5rem;">{titolo}</div>', unsafe_allow_html=True)
            
            # Allegati
            allegati_raw = circ.get('allegati', '')
            if allegati_raw:
                if isinstance(allegati_raw, str):
                    allegati = [a.strip() for a in allegati_raw.split(',') if a.strip()]
                else:
                    allegati = allegati_raw
                
                if allegati:
                    st.markdown("**📎 Documenti allegati:**")
                    
                    # Mostra allegati in una griglia
                    cols = st.columns(3)
                    for idx, allegato in enumerate(allegati):
                        col_idx = idx % 3
                        with cols[col_idx]:
                            st.markdown(f'<div class="allegato-badge" title="Clicca per scaricare">📄 {allegato}</div>', unsafe_allow_html=True)
            
            # Contenuto della circolare
            st.markdown("---")
            st.markdown("**📝 Contenuto della circolare:**")
            
            contenuto = circ.get('contenuto', 'Nessun contenuto disponibile')
            
            # Formatta il contenuto
            contenuto_formattato = contenuto.replace('Da:', '**Da:**').replace('Oggetto:', '**Oggetto:**').replace('CIRCOLARE', '**CIRCOLARE**')
            
            st.markdown(f'<div class="contenuto-circolare">{contenuto_formattato}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 🛑 MAIN APP
# ==============================================================================

def main():
    """Funzione principale"""
    # Inizializza database
    if not hasattr(st.session_state, 'db_inizializzato'):
        if db.init_db():
            st.session_state.db_inizializzato = True
    
    # Render header
    render_header()
    
    # Render circolari
    render_circolari()
    
    # Footer
    st.markdown("---")
    
    oggi = datetime.now()
    
    st.markdown(f'''
    <div class="footer">
    <div style="font-size: 1.1rem; font-weight: 600; color: #1E3A8A; margin-bottom: 0.5rem;">
        © {oggi.year} Circolari Online
    </div>
    <div style="color: #9CA3AF; font-size: 0.85rem;">
        Ultimo aggiornamento: {oggi.strftime('%d/%m/%Y %H:%M')}
    </div>
    </div>
    ''', unsafe_allow_html=True)

# ==============================================================================
# 🛑 AVVIO
# ==============================================================================

if __name__ == "__main__":
    main()
