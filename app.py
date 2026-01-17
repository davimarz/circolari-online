"""
Circolari ARGO - Visualizzatore Minimalista
"""

import streamlit as st
from datetime import datetime
import database as db

# Configurazione pagina
st.set_page_config(
    page_title="Circolari ARGO",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS minimalista
st.markdown("""
<style>
/* Header semplice */
.main-header {
    text-align: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #e0e0e0;
}

/* Card circolare */
.circolare-card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-left: 4px solid #3B82F6;
}

.data-badge {
    background: #3B82F6;
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 4px;
    font-size: 0.9rem;
    display: inline-block;
    margin-bottom: 0.5rem;
}

.data-vecchia {
    background: #6B7280;
}

.allegato-badge {
    background: #F3F4F6;
    color: #374151;
    padding: 0.3rem 0.8rem;
    border-radius: 4px;
    font-size: 0.9rem;
    display: inline-block;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
}

.contenuto {
    background: #F9FAFB;
    padding: 1rem;
    border-radius: 6px;
    margin: 1rem 0;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

def main():
    """App principale"""
    # Header
    st.markdown('<div class="main-header"><h1>📋 Circolari ARGO</h1></div>', unsafe_allow_html=True)
    
    # Statistiche
    circolari = db.get_circolari_ultimi_30_giorni()
    
    if not circolari:
        st.info("📭 Nessuna circolare disponibile")
        return
    
    # Contatore
    st.caption(f"**{len(circolari)}** circolari disponibili")
    
    # Mostra circolari in ordine cronologico inverso
    for circ in circolari:
        with st.container():
            st.markdown('<div class="circolare-card">', unsafe_allow_html=True)
            
            # Data con badge colorato
            giorni_fa = circ.get('giorni_fa', 99)
            data_str = circ.get('data_formattata', '')
            
            if giorni_fa == 0:
                badge_class = "data-badge"
                label = "🆕 OGGI"
            elif giorni_fa == 1:
                badge_class = "data-badge"
                label = "📅 IERI"
            elif giorni_fa <= 7:
                badge_class = "data-badge"
                label = f"{giorni_fa} giorni fa"
            else:
                badge_class = "data-badge data-vecchia"
                label = data_str
            
            st.markdown(f'<span class="{badge_class}">{label}</span>', unsafe_allow_html=True)
            
            # Titolo
            if circ.get('titolo'):
                st.markdown(f'### {circ["titolo"]}')
            
            # Allegati
            allegati_raw = circ.get('allegati', '')
            if allegati_raw and isinstance(allegati_raw, str):
                allegati = [a.strip() for a in allegati_raw.split(',') if a.strip()]
                if allegati:
                    st.write("**Allegati:**")
                    for allegato in allegati[:3]:  # Max 3 allegati
                        st.markdown(f'<span class="allegato-badge">📎 {allegato}</span>', unsafe_allow_html=True)
            
            # Contenuto
            contenuto = circ.get('contenuto', '')
            if contenuto:
                st.markdown('<div class="contenuto">', unsafe_allow_html=True)
                st.write(contenuto)
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

if __name__ == "__main__":
    main()
