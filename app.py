"""
Circolari ARGO - Interfaccia Minimalista
Senza barre orizzontali, font semplice, compatta
"""

import streamlit as st
from datetime import datetime
import database as db

# Configurazione pagina minimalista
st.set_page_config(
    page_title="Circolari ARGO",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS ULTRA MINIMALISTA
st.markdown("""
<style>
/* RESET e font semplice */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Header compatto */
.header {
    text-align: center;
    margin: 0 0 1.5rem 0;
    padding: 0;
}

.main-title {
    font-size: 2rem;
    color: #1e40af;
    margin: 0;
    font-weight: 600;
}

.subtitle {
    color: #6b7280;
    font-size: 0.95rem;
    margin: 0.3rem 0 0 0;
}

/* Card circolare ULTRA compatta */
.circolare-card {
    background: #ffffff;
    border-radius: 6px;
    padding: 1rem;
    margin: 0 0 0.8rem 0;
    border-left: 3px solid #3b82f6;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    transition: all 0.15s ease;
}

.circolare-card:hover {
    box-shadow: 0 2px 5px rgba(0,0,0,0.12);
}

/* Badge data minimo */
.data-badge {
    display: inline-block;
    background: #3b82f6;
    color: white;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 500;
    margin: 0 0 0.5rem 0;
}

.data-vecchia {
    background: #9ca3af;
}

/* Titolo compatto */
.titolo-circolare {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 0.5rem 0;
    line-height: 1.3;
}

/* Allegati minimali */
.allegati {
    margin: 0.5rem 0 0.8rem 0;
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
}

.allegato-item {
    background: #f3f4f6;
    color: #4b5563;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.8rem;
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
}

/* Contenuto compatto */
.contenuto {
    background: #f9fafb;
    padding: 0.8rem;
    border-radius: 4px;
    font-size: 0.9rem;
    line-height: 1.5;
    color: #374151;
    margin: 0.5rem 0 0 0;
    white-space: pre-line;
}

/* Footer minimalista */
.footer {
    margin: 2rem 0 0 0;
    padding: 1rem 0 0 0;
    border-top: 1px solid #e5e7eb;
    color: #9ca3af;
    font-size: 0.8rem;
    text-align: center;
}

/* Rimuovi tutte le barre orizzontali extra */
hr {
    margin: 0.5rem 0 !important;
    border: none !important;
    border-top: 1px solid #e5e7eb !important;
}

/* Spazi ridotti */
.stContainer {
    padding: 0 !important;
    margin: 0 !important;
}

/* Responsive */
@media (max-width: 768px) {
    .circolare-card {
        padding: 0.8rem;
    }
    
    .main-title {
        font-size: 1.6rem;
    }
}
</style>
""", unsafe_allow_html=True)

def main():
    """App principale minimalista"""
    
    # Header compatto
    st.markdown('<div class="header"><h1 class="main-title">📄 Circolari</h1><p class="subtitle">Portale comunicazioni scolastiche</p></div>', unsafe_allow_html=True)
    
    # Carica circolari
    circolari = db.get_circolari_ultimi_30_giorni()
    
    if not circolari:
        st.info("📭 Nessuna circolare disponibile")
        return
    
    # Contatore semplice
    st.markdown(f"**{len(circolari)} circolari disponibili**")
    
    # Spazio minimo
    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
    
    # Mostra circolari
    for circ in circolari:
        with st.container():
            st.markdown('<div class="circolare-card">', unsafe_allow_html=True)
            
            # Data con badge colorato
            giorni_fa = circ.get('giorni_fa', 99)
            data_str = circ.get('data_formattata', '')
            
            if giorni_fa == 0:
                badge_class = "data-badge"
                label = "🆕 Oggi"
            elif giorni_fa == 1:
                badge_class = "data-badge"
                label = "Ieri"
            elif giorni_fa <= 7:
                badge_class = "data-badge"
                label = f"{giorni_fa}g fa"
            else:
                badge_class = "data-badge data-vecchia"
                label = data_str
            
            st.markdown(f'<span class="{badge_class}">{label}</span>', unsafe_allow_html=True)
            
            # Titolo
            titolo = circ.get('titolo', '')
            if titolo:
                st.markdown(f'<div class="titolo-circolare">{titolo}</div>', unsafe_allow_html=True)
            
            # Allegati (solo se presenti)
            allegati_raw = circ.get('allegati', '')
            if allegati_raw and isinstance(allegati_raw, str):
                allegati = [a.strip() for a in allegati_raw.split(',') if a.strip()]
                if allegati:
                    st.markdown('<div class="allegati">', unsafe_allow_html=True)
                    for allegato in allegati[:2]:  # Max 2 per compattezza
                        st.markdown(f'<span class="allegato-item">📎 {allegato}</span>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Contenuto (solo anteprima)
            contenuto = circ.get('contenuto', '')
            if contenuto:
                # Anteprima di 200 caratteri
                anteprima = contenuto[:200] + ("..." if len(contenuto) > 200 else "")
                st.markdown(f'<div class="contenuto">{anteprima}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer minimalista
    oggi = datetime.now()
    st.markdown(f'''
    <div class="footer">
        <div>Aggiornato: {oggi.strftime('%d/%m/%Y %H:%M')}</div>
        <div style="margin-top: 0.3rem; color: #d1d5db;">Circolari ARGO</div>
    </div>
    ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
