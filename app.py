"""
app.py - Visualizzatore circolari ARGO
Mostra le circolari in ordine decrescente di data (ultimi 30 giorni)
"""

import streamlit as st
from datetime import datetime, timedelta
import database as db

# ==============================================================================
# 🛑 CONFIGURAZIONE PAGINA
# ==============================================================================

st.set_page_config(
    page_title="Circolari Online - ARGO",
    page_icon="📚",
    layout="wide"
)

# ==============================================================================
# 🛑 CSS PERSONALIZZATO PER ARGO
# ==============================================================================

st.markdown("""
<style>
/* Header stile ARGO */
.main-title {
    font-size: 2.5rem;
    color: #1E3A8A;
    margin-bottom: 0.5rem;
    font-weight: 700;
}

.subtitle {
    color: #4B5563;
    margin-bottom: 1.5rem;
    font-size: 1.1rem;
}

/* Card circolare stile tabella ARGO */
.circolare-card {
    background-color: #FFFFFF;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    border-left: 5px solid #3B82F6;
    border-top: 1px solid #E5E7EB;
    border-right: 1px solid #E5E7EB;
    border-bottom: 1px solid #E5E7EB;
}

/* Badge data */
.data-badge {
    display: inline-block;
    background-color: #EFF6FF;
    color: #1D4ED8;
    padding: 0.4rem 1rem;
    border-radius: 6px;
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 0.8rem;
}

/* Badge allegati */
.allegato-badge {
    display: inline-block;
    background-color: #F0F9FF;
    color: #0369A1;
    padding: 0.3rem 0.8rem;
    border-radius: 4px;
    font-size: 0.85rem;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
    border: 1px solid #BAE6FD;
}

/* Badge categoria */
.categoria-badge {
    display: inline-block;
    background-color: #F3F4F6;
    color: #374151;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.8rem;
    margin-left: 0.5rem;
}

/* Contenuto circolare */
.contenuto-circolare {
    background-color: #F9FAFB;
    padding: 1rem;
    border-radius: 6px;
    margin-top: 1rem;
    border: 1px solid #E5E7EB;
    font-size: 0.95rem;
    line-height: 1.6;
    white-space: pre-line;
}

/* Footer */
.footer {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #E5E7EB;
    color: #6B7280;
    font-size: 0.9rem;
}

/* Statistiche sidebar */
.stat-box {
    background-color: #F9FAFB;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    border: 1px solid #E5E7EB;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🛑 HEADER
# ==============================================================================

def render_header():
    """Renderizza l'header della pagina"""
    st.markdown('<h1 class="main-title">📋 Circolari Scolastiche</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Circolari dalla bacheca ARGO • Ordine decrescente di data • Ultimi 30 giorni</p>', unsafe_allow_html=True)
    st.markdown("---")

# ==============================================================================
# 🛑 ELENCO CIRCOLARI
# ==============================================================================

def render_circolari():
    """Renderizza l'elenco delle circolari in ordine decrescente di data"""
    # Carica circolari (solo ultimi 30 giorni)
    circolari = db.get_circolari_ultimi_30_giorni()
    
    if not circolari:
        st.info("📭 Al momento non ci sono circolari disponibili negli ultimi 30 giorni.")
        st.write("Il sistema si aggiorna automaticamente ogni ora dalla bacheca ARGO.")
        return
    
    # Mostra ogni circolare in ordine decrescente
    for circ in circolari:
        with st.container():
            st.markdown('<div class="circolare-card">', unsafe_allow_html=True)
            
            # Data in badge
            data_display = circ.get('data_formattata') or circ.get('data_pubblicazione')
            if data_display:
                if isinstance(data_display, str):
                    data_str = data_display
                else:
                    data_str = data_display.strftime('%d/%m/%Y')
                
                # Mostra anche "giorni fa"
                giorni_fa = circ.get('giorni_fa')
                if giorni_fa is not None:
                    if giorni_fa == 0:
                        giorni_text = " (oggi)"
                    elif giorni_fa == 1:
                        giorni_text = " (ieri)"
                    else:
                        giorni_text = f" ({int(giorni_fa)} giorni fa)"
                else:
                    giorni_text = ""
                
                st.markdown(f'<span class="data-badge">📅 {data_str}{giorni_text}</span>', unsafe_allow_html=True)
            
            # Titolo
            titolo = circ.get('titolo', 'Senza titolo')
            st.markdown(f"### {titolo}")
            
            # Allegati
            allegati_raw = circ.get('allegati', '')
            if allegati_raw:
                # Converti stringa in lista
                if isinstance(allegati_raw, str):
                    allegati = [a.strip() for a in allegati_raw.split(',') if a.strip()]
                else:
                    allegati = allegati_raw
                
                if allegati:
                    st.markdown("**Allegati disponibili:**")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        for allegato in allegati:
                            st.markdown(f'<span class="allegato-badge">📎 {allegato}</span>', unsafe_allow_html=True)
                    with col2:
                        if st.button("📥 Scarica tutti", key=f"scarica_{circ['id']}"):
                            st.info(f"Download di {len(allegati)} allegati")
            
            # Contenuto
            st.markdown("---")
            st.markdown("**Contenuto della circolare:**")
            contenuto = circ.get('contenuto', 'Nessun contenuto disponibile')
            st.markdown(f'<div class="contenuto-circolare">{contenuto}</div>', unsafe_allow_html=True)
            
            # Metadata footer
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if circ.get('created_at'):
                    created = circ['created_at']
                    if isinstance(created, str):
                        st.caption(f"🕒 Inserita: {created}")
                    else:
                        st.caption(f"🕒 Inserita: {created.strftime('%d/%m/%Y %H:%M')}")
            
            st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 🛑 SIDEBAR
# ==============================================================================

def render_sidebar():
    """Renderizza la sidebar con statistiche"""
    with st.sidebar:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.markdown("### 📊 Statistiche")
        
        # Carica circolari
        circolari = db.get_circolari_ultimi_30_giorni()
        
        if circolari:
            # Totale circolari
            st.metric("Circolari disponibili", len(circolari))
            
            # Data più recente e più vecchia
            date_circolari = [c.get('data_pubblicazione') for c in circolari if c.get('data_pubblicazione')]
            if date_circolari:
                data_recente = max(date_circolari)
                data_vecchia = min(date_circolari)
                
                if isinstance(data_recente, str):
                    st.metric("Più recente", data_recente)
                else:
                    st.metric("Più recente", data_recente.strftime('%d/%m/%Y'))
                
                giorni_coperti = (data_recente - data_vecchia).days + 1
                st.metric("Giorni coperti", giorni_coperti)
            
            # Allegati totali
            totale_allegati = 0
            for circ in circolari:
                allegati = circ.get('allegati', '')
                if allegati:
                    if isinstance(allegati, str):
                        totale_allegati += len([a for a in allegati.split(',') if a.strip()])
                    else:
                        totale_allegati += len(allegati)
            
            if totale_allegati > 0:
                st.metric("Allegati totali", totale_allegati)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Info aggiornamento
        st.markdown("---")
        st.markdown("### 🔄 Aggiornamento")
        st.write("**Fonte:** Bacheca ARGO")
        st.write("**Frequenza:** Ogni ora")
        st.write("**Periodo:** Ultimi 30 giorni")
        st.write(f"**Ora attuale:** {datetime.now().strftime('%H:%M')}")

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
    oggi = datetime.now()
    trenta_giorni_fa = oggi - timedelta(days=30)
    
    st.markdown(f'''
    <div class="footer">
    © {oggi.year} Circolari Online - ARGO<br>
    Visualizzate le circolari dal <strong>{trenta_giorni_fa.strftime('%d/%m/%Y')}</strong> al <strong>{oggi.strftime('%d/%m/%Y')}</strong><br>
    Ultimo aggiornamento: {oggi.strftime('%d/%m/%Y %H:%M')}
    </div>
    ''', unsafe_allow_html=True)

# ==============================================================================
# 🛑 AVVIO
# ==============================================================================

if __name__ == "__main__":
    main()
