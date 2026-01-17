"""
Circolari ARGO - Interfaccia minimalista
"""

import streamlit as st
from datetime import datetime
import database as db

# Config
st.set_page_config(
    page_title="Circolari",
    page_icon="📄",
    layout="wide"
)

# CSS Minimalista
st.markdown("""
<style>
* { font-family: -apple-system, system-ui, sans-serif; margin: 0; padding: 0; }

.container { max-width: 900px; margin: 0 auto; padding: 0.5rem; }

.header { text-align: center; margin-bottom: 1rem; padding: 0.5rem 0; }
.title { font-size: 1.6rem; color: #1e40af; margin: 0; }
.subtitle { color: #6b7280; font-size: 0.85rem; margin: 0.2rem 0; }

.card { 
    background: white; 
    border-radius: 5px; 
    padding: 0.7rem; 
    margin: 0 0 0.5rem 0;
    border-left: 3px solid #3b82f6;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.badge { 
    background: #3b82f6; 
    color: white; 
    padding: 0.15rem 0.5rem; 
    border-radius: 3px; 
    font-size: 0.7rem; 
    display: inline-block; 
    margin-bottom: 0.3rem;
}
.old { background: #9ca3af; }

.titolo { 
    font-size: 0.95rem; 
    font-weight: 600; 
    color: #1f2937; 
    margin: 0 0 0.2rem 0;
}

.contenuto { 
    color: #4b5563; 
    font-size: 0.8rem; 
    line-height: 1.4; 
    margin: 0.2rem 0 0 0;
}

.footer { 
    margin-top: 1.2rem; 
    padding-top: 0.6rem; 
    border-top: 1px solid #e5e7eb; 
    color: #9ca3af; 
    font-size: 0.7rem; 
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<div class="container">', unsafe_allow_html=True)
    
    # Header
    st.markdown('<div class="header"><h1 class="title">📄 Circolari</h1><p class="subtitle">Comunicazioni scolastiche</p></div>', unsafe_allow_html=True)
    
    # Carica circolari
    circolari = db.get_circolari()
    
    if not circolari:
        st.info("Nessuna circolare disponibile")
        return
    
    # Contatore
    st.write(f"**{len(circolari)} circolari**")
    
    # Mostra circolari
    for circ in circolari:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        # Data
        giorni_fa = circ.get('giorni_fa', 99)
        data_str = circ.get('data_formattata', '')
        
        if giorni_fa == 0:
            label = "🆕 Oggi"
            badge_class = "badge"
        elif giorni_fa == 1:
            label = "Ieri"
            badge_class = "badge"
        elif giorni_fa <= 7:
            label = f"{giorni_fa}g fa"
            badge_class = "badge"
        else:
            label = data_str
            badge_class = "badge old"
        
        st.markdown(f'<span class="{badge_class}">{label}</span>', unsafe_allow_html=True)
        
        # Titolo
        titolo = circ.get('titolo', '')
        if titolo:
            st.markdown(f'<div class="titolo">{titolo}</div>', unsafe_allow_html=True)
        
        # Contenuto
        contenuto = circ.get('contenuto', '')
        if contenuto:
            anteprima = contenuto[:120] + ("..." if len(contenuto) > 120 else "")
            st.markdown(f'<div class="contenuto">{anteprima}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown(f'''
    <div class="footer">
        Aggiornato: {datetime.now().strftime('%d/%m/%Y %H:%M')}<br>
        <span style="color: #d1d5db;">Circolari ARGO</span>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
