"""
app.py - Visualizzatore circolari ARGO
Interfaccia ottimizzata per i dati ARGO reali
"""

import streamlit as st
from datetime import datetime, timedelta
import database as db

# ==============================================================================
# 🛑 CONFIGURAZIONE PAGINA
# ==============================================================================

st.set_page_config(
    page_title="Circolari ARGO Online",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
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

/* Badge categoria */
.categoria-badge {
    display: inline-block;
    background-color: #EFF6FF;
    color: #1E40AF;
    padding: 0.4rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    margin-left: 1rem;
    border: 1px solid #BFDBFE;
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

/* Statistiche sidebar */
.stat-box {
    background: linear-gradient(135deg, #F8FAFC, #F1F5F9);
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    border: 1px solid #E2E8F0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.stat-title {
    color: #1E3A8A;
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Pulsanti */
.stButton > button {
    background: linear-gradient(135deg, #3B82F6, #1D4ED8);
    color: white;
    border: none;
    padding: 0.6rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #1D4ED8, #1E3A8A);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(29, 78, 216, 0.3);
}

/* Scrollbar personalizzata */
::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: #F1F5F9;
    border-radius: 5px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #3B82F6, #1D4ED8);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #1D4ED8, #1E3A8A);
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
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown('<h1 class="main-title">📋 CIRCOLARI ONLINE</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Portale circolari scolastiche • Aggiornamento automatico da ARGO</p>', unsafe_allow_html=True)
    
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
        📭 **Al momento non ci sono circolari disponibili negli ultimi 30 giorni.**
        
        Questo potrebbe significare che:
        - Il sistema ARGO non ha pubblicato nuove circolari
        - Il robot di aggiornamento è in esecuzione
        - Non ci sono circolari nella bacheca ARGO
        
        **Prossimo aggiornamento automatico:** tra pochi minuti
        """)
        return
    
    # Contatore circolari
    st.markdown(f"### 📋 **{len(circolari)} Circolari disponibili**")
    
    # Mostra ogni circolare in ordine decrescente di data
    for circ in circolari:
        with st.container():
            st.markdown('<div class="circolare-card">', unsafe_allow_html=True)
            
            # Riga superiore: Data + Categoria
            col_data, col_cat = st.columns([2, 3])
            
            with col_data:
                # Data con badge colorato in base all'età
                data_display = circ.get('data_visualizzazione') or circ.get('data_formattata') or circ.get('data_pubblicazione')
                giorni_fa = circ.get('giorni_fa', 99)
                
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
            
            with col_cat:
                # Mostra categoria se disponibile
                if circ.get('titolo'):
                    # Estrai eventuale categoria dal titolo
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
                    
                    # Pulsante scarica tutti
                    if st.button("⬇️ Scarica tutti gli allegati", key=f"scarica_tutti_{circ['id']}"):
                        st.success(f"Download avviato per {len(allegati)} allegati")
            
            # Contenuto della circolare
            st.markdown("---")
            st.markdown("**📝 Contenuto della circolare:**")
            
            contenuto = circ.get('contenuto', 'Nessun contenuto disponibile')
            
            # Formatta il contenuto per migliorare la leggibilità
            contenuto_formattato = contenuto.replace('Da:', '**Da:**').replace('Oggetto:', '**Oggetto:**').replace('CIRCOLARE', '**CIRCOLARE**')
            
            st.markdown(f'<div class="contenuto-circolare">{contenuto_formattato}</div>', unsafe_allow_html=True)
            
            # Metadata footer
            st.markdown("---")
            col_meta1, col_meta2, col_meta3 = st.columns(3)
            
            with col_meta1:
                if circ.get('created_at'):
                    created = circ['created_at']
                    if isinstance(created, str):
                        st.caption(f"🕒 **Inserita:** {created}")
                    else:
                        st.caption(f"🕒 **Inserita:** {created.strftime('%d/%m/%Y %H:%M')}")
            
            with col_meta2:
                if circ.get('pdf_url'):
                    st.caption(f"🔗 **URL originale:** [Apri]({circ['pdf_url']})")
            
            with col_meta3:
                if circ.get('id'):
                    st.caption(f"🆔 **ID circolare:** {circ['id']}")
            
            st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 🛑 SIDEBAR
# ==============================================================================

def render_sidebar():
    """Renderizza la sidebar con statistiche e controlli"""
    with st.sidebar:
        # Logo/Intestazione sidebar
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 1.8rem; font-weight: 800; color: #1E3A8A; margin-bottom: 0.5rem;">
                📊 DASHBOARD
            </div>
            <div style="color: #6B7280; font-size: 0.9rem;">
                Monitoraggio circolari ARGO
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Statistiche
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.markdown('<div class="stat-title">📈 STATISTICHE</div>', unsafe_allow_html=True)
        
        stats = db.get_statistiche()
        
        if stats:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Totale circolari", stats.get('totale', 0))
                st.metric("Ultimi 30 giorni", stats.get('ultimi_30_giorni', 0))
            
            with col2:
                st.metric("Oggi", stats.get('oggi', 0))
                st.metric("Con allegati", stats.get('con_allegati', 0))
            
            # Date estreme
            if stats.get('data_prima') and stats.get('data_ultima'):
                st.markdown("---")
                st.markdown("**📅 Periodo coperto:**")
                st.write(f"**Prima:** {stats['data_prima'].strftime('%d/%m/%Y')}")
                st.write(f"**Ultima:** {stats['data_ultima'].strftime('%d/%m/%Y')}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Controlli
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.markdown('<div class="stat-title">⚙️ CONTROLLI</div>', unsafe_allow_html=True)
        
        # Pulsante aggiornamento manuale
        if st.button("🔄 Aggiorna ora", use_container_width=True):
            st.info("Aggiornamento in corso...")
            st.rerun()
        
        # Filtro per data
        st.markdown("---")
        st.markdown("**🗓️ Filtra per data:**")
        
        oggi = datetime.now().date()
        trenta_giorni_fa = oggi - timedelta(days=30)
        
        data_inizio = st.date_input(
            "Da",
            value=trenta_giorni_fa,
            max_value=oggi
        )
        
        data_fine = st.date_input(
            "A",
            value=oggi,
            max_value=oggi
        )
        
        if st.button("🔍 Applica filtro", use_container_width=True):
            if data_inizio <= data_fine:
                circolari_filtrate = db.get_circolari_per_data(data_inizio, data_fine)
                st.session_state.circolari_filtrate = circolari_filtrate
                st.success(f"Trovate {len(circolari_filtrate)} circolari")
            else:
                st.error("Data inizio deve essere <= data fine")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Info sistema
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.markdown('<div class="stat-title">ℹ️ INFORMAZIONI</div>', unsafe_allow_html=True)
        
        st.write("**Fonte dati:** Bacheca ARGO")
        st.write("**Aggiornamento:** Ogni ora")
        st.write("**Periodo visualizzato:** Ultimi 30 giorni")
        st.write(f"**Ora attuale:** {datetime.now().strftime('%H:%M:%S')}")
        
        # Pulsante pulizia cache
        if st.button("🧹 Pulisci vecchie circolari", use_container_width=True, type="secondary"):
            eliminate = db.pulisci_circolari_vecchie()
            if eliminate > 0:
                st.success(f"Eliminate {eliminate} circolari vecchie")
            else:
                st.info("Nessuna circolare vecchia da eliminare")
        
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
    
    # Render sidebar
    render_sidebar()
    
    # Render circolari (filtrate o tutte)
    if hasattr(st.session_state, 'circolari_filtrate'):
        # Backup temporaneo per mostrare le circolari filtrate
        circolari_originali = db.get_circolari
        db.get_circolari = lambda: st.session_state.circolari_filtrate
        db.get_circolari_ultimi_30_giorni = lambda: st.session_state.circolari_filtrate
        
        render_circolari()
        
        # Ripristina funzione originale
        db.get_circolari = circolari_originali
        db.get_circolari_ultimi_30_giorni = circolari_originali
        
        if st.button("❌ Rimuovi filtro", type="secondary"):
            del st.session_state.circolari_filtrate
            st.rerun()
    else:
        render_circolari()
    
    # Footer
    st.markdown("---")
    
    oggi = datetime.now()
    trenta_giorni_fa = oggi - timedelta(days=30)
    
    st.markdown(f'''
    <div class="footer">
    <div style="font-size: 1.1rem; font-weight: 600; color: #1E3A8A; margin-bottom: 0.5rem;">
        © {oggi.year} Circolari ARGO Online - I.C.S. "Anna Frank"
    </div>
    <div style="color: #6B7280; margin-bottom: 0.5rem;">
        Visualizzate le circolari dal <strong>{trenta_giorni_fa.strftime('%d/%m/%Y')}</strong> al <strong>{oggi.strftime('%d/%m/%Y')}</strong>
    </div>
    <div style="color: #9CA3AF; font-size: 0.85rem;">
        Ultimo aggiornamento: {oggi.strftime('%d/%m/%Y %H:%M:%S')} • 
        Versione: 2.0 • 
        Sorgente: ARGO Scraping
    </div>
    </div>
    ''', unsafe_allow_html=True)

# ==============================================================================
# 🛑 AVVIO
# ==============================================================================

if __name__ == "__main__":
    main()
