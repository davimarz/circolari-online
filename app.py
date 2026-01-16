"""
app.py - Applicazione Streamlit completa per Circolari Online
Configurata per Railway con database PostgreSQL interno
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import database as db

# ==============================================================================
# 🛑 CONFIGURAZIONE PAGINA STREAMLIT
# ==============================================================================

st.set_page_config(
    page_title="Circolari Online - Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/tuo-repo/circolari-online',
        'Report a bug': 'https://github.com/tuo-repo/circolari-online/issues',
        'About': """
        # Circolari Online v2.0
        
        Dashboard per la gestione e visualizzazione delle circolari scolastiche.
        
        **Tecnologie:**
        - Frontend: Streamlit
        - Backend: PostgreSQL su Railway
        - Automazione: GitHub Actions
        
        **Sviluppato da:** Davide Marziano
        """
    }
)

# ==============================================================================
# 🛑 FUNZIONI UTILITY
# ==============================================================================

def init_session_state():
    """Inizializza lo stato della sessione"""
    if 'filtro_giorni' not in st.session_state:
        st.session_state.filtro_giorni = 30
    if 'filtro_categoria' not in st.session_state:
        st.session_state.filtro_categoria = "Tutte"
    if 'pagina_circolari' not in st.session_state:
        st.session_state.pagina_circolari = 1
    if 'circolari_per_pagina' not in st.session_state:
        st.session_state.circolari_per_pagina = 10

def apply_custom_css():
    """Applica CSS personalizzato"""
    st.markdown("""
    <style>
    /* Stili generali */
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-bottom: 1rem;
    }
    
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #1E88E5;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1E88E5, #0D47A1);
        color: white;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
    }
    
    .circolare-card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border-left: 4px solid #4CAF50;
    }
    
    .circolare-card-vecchia {
        border-left: 4px solid #FF9800;
    }
    
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .badge-amministrativa { background-color: #E3F2FD; color: #1565C0; }
    .badge-docenti { background-color: #F3E5F5; color: #7B1FA2; }
    .badge-studenti { background-color: #E8F5E9; color: #2E7D32; }
    .badge-genitori { background-color: #FFF3E0; color: #EF6C00; }
    .badge-orario { background-color: #E0F2F1; color: #00695C; }
    .badge-test { background-color: #F5F5F5; color: #616161; }
    .badge-formazione { background-color: #FFF8E1; color: #FF8F00; }
    .badge-comunicazioni { background-color: #FCE4EC; color: #C2185B; }
    
    /* Stili per le tabelle */
    .dataframe {
        width: 100%;
    }
    
    .dataframe th {
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
    }
    
    /* Stili per i bottoni */
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
    }
    
    .btn-sincronizza {
        background: linear-gradient(135deg, #FF9800, #F57C00);
        color: white;
        border: none;
    }
    
    .btn-sincronizza:hover {
        background: linear-gradient(135deg, #F57C00, #EF6C00);
    }
    
    /* Stili per gli expander */
    .streamlit-expanderHeader {
        font-weight: 600;
        background-color: #f1f8ff;
    }
    
    /* Alert personalizzati */
    .alert-success {
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    
    .alert-warning {
        background-color: #fff3cd;
        border-color: #ffeeba;
        color: #856404;
        padding: 1rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    
    .alert-info {
        background-color: #d1ecf1;
        border-color: #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def get_badge_color(categoria):
    """Restituisce il colore del badge in base alla categoria"""
    colori = {
        "Amministrativa": "badge-amministrativa",
        "Docenti": "badge-docenti",
        "Studenti": "badge-studenti",
        "Genitori": "badge-genitori",
        "Orario": "badge-orario",
        "Formazione": "badge-formazione",
        "Comunicazioni": "badge-comunicazioni",
        "Test": "badge-test",
        "Archivio": "badge-test",
    }
    return colori.get(categoria, "badge-test")

# ==============================================================================
# 🛑 HEADER E SIDEBAR
# ==============================================================================

def render_header():
    """Renderizza l'header della pagina"""
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown('<h1 class="main-header">📚 Circolari Online</h1>', unsafe_allow_html=True)
        st.markdown("**Dashboard completa per la gestione delle circolari scolastiche**")
    
    with col2:
        # Test connessione database
        test_result = db.test_connection()
        if test_result["status"] == "connected":
            st.success("✅ DB Connesso")
        else:
            st.error("❌ DB Offline")
    
    with col3:
        st.markdown(f"**Ultimo aggiornamento:**")
        st.caption(datetime.now().strftime("%d/%m/%Y %H:%M"))
    
    st.markdown("---")

def render_sidebar():
    """Renderizza la sidebar con filtri e statistiche"""
    with st.sidebar:
        st.markdown('<h2 class="sub-header">⚙️ Filtri</h2>', unsafe_allow_html=True)
        
        # Filtro per giorni
        giorni = st.slider(
            "Mostra ultimi giorni",
            min_value=7,
            max_value=365,
            value=st.session_state.filtro_giorni,
            help="Mostra circolari pubblicate negli ultimi N giorni"
        )
        st.session_state.filtro_giorni = giorni
        
        # Filtro per categoria
        categorie = db.get_categorie()
        categoria = st.selectbox(
            "Categoria",
            categorie,
            index=categorie.index(st.session_state.filtro_categoria) if st.session_state.filtro_categoria in categorie else 0
        )
        st.session_state.filtro_categoria = categoria
        
        # Ricerca testuale
        st.markdown("---")
        st.markdown('<h3 class="sub-header">🔍 Ricerca</h3>', unsafe_allow_html=True)
        ricerca_testo = st.text_input("Cerca nelle circolari", placeholder="Inserisci testo da cercare...")
        
        if ricerca_testo:
            if st.button("🔎 Cerca", use_container_width=True):
                st.session_state.ricerca_attiva = True
                st.session_state.testo_ricerca = ricerca_testo
        
        # Statistiche sidebar
        st.markdown("---")
        st.markdown('<h3 class="sub-header">📊 Statistiche</h3>', unsafe_allow_html=True)
        
        stats = db.get_statistiche()
        
        if stats:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Totale", stats["generali"]["totale_circolari"])
            with col2:
                st.metric("Ultimi 7gg", stats["generali"]["ultima_settimana"])
            
            st.metric("Aggiunte oggi", stats["generali"]["aggiunte_oggi"])
            
            if stats["generali"]["prima_circolare"] != "N/A":
                st.caption(f"Prima: {stats['generali']['prima_circolare']}")
            if stats["generali"]["ultima_circolare"] != "N/A":
                st.caption(f"Ultima: {stats['generali']['ultima_circolare']}")
        
        # Informazioni sistema
        st.markdown("---")
        with st.expander("ℹ️ Informazioni sistema"):
            st.write(f"**Database:** PostgreSQL")
            st.write(f"**Host:** postgres.railway.internal")
            st.write(f"**Porta:** 5432")
            st.write(f"**Modalità:** Produzione")
            st.write(f"**Costo:** Gratuito (interno Railway)")
            
            if stats and "robot" in stats:
                st.write(f"**Ultimo robot:** {stats['robot']['ultima_esecuzione']}")
                st.write(f"**Tasso successo:** {stats['robot']['tasso_successo']}")
            
            # Stato sincronizzazione
            st.markdown("---")
            st.markdown("**🔄 Stato Sincronizzazione:**")
            if stats and stats["generali"]["totale_circolari"] > 0:
                st.success(f"✅ {stats['generali']['totale_circolari']} circolari disponibili")
            else:
                st.warning("⚠️  Nessuna circolare nel database")
                st.info("Usa il pulsante 'Sincronizza da backup' nella tab Gestione")
        
        return ricerca_testo

# ==============================================================================
# 🛑 FUNZIONI PER LE TAB
# ==============================================================================

def render_tab_circolari():
    """Renderizza la tab Circolari"""
    st.markdown('<h2 class="sub-header">📋 Elenco Circolari</h2>', unsafe_allow_html=True)
    
    # Controlla se c'è una ricerca attiva
    if hasattr(st.session_state, 'ricerca_attiva') and st.session_state.ricerca_attiva:
        st.info(f"🔍 Risultati ricerca per: '{st.session_state.testo_ricerca}'")
        df_circolari = db.cerca_circolari(st.session_state.testo_ricerca, limit=50)
        
        if df_circolari.empty:
            st.warning("Nessuna circolare trovata con i criteri di ricerca.")
            if st.button("❌ Cancella ricerca"):
                del st.session_state.ricerca_attiva
                del st.session_state.testo_ricerca
                st.rerun()
        else:
            st.success(f"Trovate {len(df_circolari)} circolari")
    else:
        # Carica circolari normali
        df_circolari = db.get_circolari_recenti(
            limit=100,
            categoria=st.session_state.filtro_categoria if st.session_state.filtro_categoria != "Tutte" else None,
            giorni_indietro=st.session_state.filtro_giorni
        )
    
    if df_circolari.empty:
        st.markdown('<div class="alert-warning">📭 Nessuna circolare trovata con i filtri attuali.</div>', unsafe_allow_html=True)
        st.write("### 🔧 Possibili soluzioni:")
        
        col_sol1, col_sol2, col_sol3 = st.columns(3)
        
        with col_sol1:
            if st.button("🎯 Amplia filtro temporale", use_container_width=True):
                st.session_state.filtro_giorni = 365
                st.rerun()
        
        with col_sol2:
            if st.button("📂 Sincronizza da backup", use_container_width=True):
                st.session_state.mostra_sincronizza = True
                st.rerun()
        
        with col_sol3:
            if st.button("🔄 Aggiorna dati", use_container_width=True):
                st.rerun()
        
        st.info("""
        **Perché non vedo le circolari?**
        1. Il robot potrebbe non aver ancora salvato nel database PostgreSQL
        2. Le circolari potrebbero essere più vecchie del filtro temporale
        3. Potrebbe esserci un problema di connessione al database
        
        **Soluzione rapida:** Usa il pulsante "Sincronizza da backup" nella tab Gestione
        """)
        return
    
    # Mostra statistiche filtro
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Circolari trovate", len(df_circolari))
    with col2:
        categorie_uniche = df_circolari['categoria'].nunique()
        st.metric("Categorie", categorie_uniche)
    with col3:
        if 'data_pubblicazione' in df_circolari.columns:
            if not df_circolari.empty:
                data_min = df_circolari['data_pubblicazione'].min()
                data_max = df_circolari['data_pubblicazione'].max()
                if pd.notna(data_min) and pd.notna(data_max):
                    # Formatta le date
                    if isinstance(data_min, pd.Timestamp):
                        data_min_str = data_min.strftime('%d/%m/%Y')
                        data_max_str = data_max.strftime('%d/%m/%Y')
                        st.metric("Periodo", f"{data_min_str} - {data_max_str}")
    
    # Pulsanti di esportazione
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    with col_exp1:
        if st.button("📥 Esporta CSV", use_container_width=True):
            csv = df_circolari.to_csv(index=False)
            st.download_button(
                label="Scarica CSV",
                data=csv,
                file_name=f"circolari_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col_exp2:
        if st.button("📊 Esporta JSON", use_container_width=True):
            json_data = df_circolari.to_json(orient="records", indent=2)
            st.download_button(
                label="Scarica JSON",
                data=json_data,
                file_name=f"circolari_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    with col_exp3:
        if st.button("🔄 Aggiorna dati", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Visualizzazione circolari
    for idx, row in df_circolari.iterrows():
        with st.container():
            col_left, col_right = st.columns([4, 1])
            
            with col_left:
                # Titolo e categoria
                st.markdown(f"### {row['titolo']}")
                
                # Categoria con badge colorato
                categoria = row.get('categoria', 'N/A')
                badge_class = get_badge_color(categoria)
                st.markdown(f'<span class="badge {badge_class}">{categoria}</span>', unsafe_allow_html=True)
                
                # Data
                if 'data_formattata' in row:
                    st.caption(f"📅 Pubblicata: {row['data_formattata']}")
                if 'scaricata_il' in row:
                    st.caption(f"⬇️ Scaricata: {row['scaricata_il']}")
                
                # Contenuto (anteprima)
                contenuto = row.get('contenuto', '')
                if len(contenuto) > 300:
                    anteprima = contenuto[:300] + "..."
                    with st.expander("📝 Leggi contenuto completo"):
                        st.write(contenuto)
                    st.write(anteprima)
                else:
                    st.write(contenuto)
            
            with col_right:
                # Allegati
                allegati = row.get('allegati', [])
                if allegati and len(allegati) > 0:
                    st.markdown("**Allegati:**")
                    for allegato in allegati[:3]:  # Mostra max 3 allegati
                        st.write(f"📎 {allegato}")
                    if len(allegati) > 3:
                        st.caption(f"+ {len(allegati) - 3} altri")
                
                # Fonte
                fonte = row.get('fonte', 'N/A')
                if fonte:
                    st.caption(f"Fonte: {fonte}")
                
                # Pulsante dettagli
                if 'id' in row:
                    if st.button("🔍 Dettagli", key=f"dettagli_{row['id']}", use_container_width=True):
                        st.session_state.dettaglio_circolare = row['id']
                        st.rerun()
            
            st.markdown("---")

def render_tab_statistiche():
    """Renderizza la tab Statistiche"""
    st.markdown('<h2 class="sub-header">📈 Statistiche e Grafici</h2>', unsafe_allow_html=True)
    
    # Ottieni statistiche
    stats = db.get_statistiche()
    
    if not stats:
        st.warning("Impossibile recuperare le statistiche.")
        st.info("Il database potrebbe essere vuoto o non connesso.")
        return
    
    # Metriche principali
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Totale Circolari",
            stats["generali"]["totale_circolari"],
            f"{stats['generali']['ultima_settimana']} (ultimi 7gg)"
        )
    
    with col2:
        st.metric(
            "Categorie",
            stats["categorie"]["totali"],
            stats["categorie"]["top_categoria"]
        )
    
    with col3:
        st.metric(
            "Giorni coperti",
            stats["generali"]["giorni_coperti"]
        )
    
    with col4:
        st.metric(
            "Tasso successo robot",
            stats["robot"]["tasso_successo"]
        )
    
    st.markdown("---")
    
    # Grafici
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Grafico a torta categorie
        st.markdown("### 📊 Distribuzione per Categoria")
        
        if stats["categorie"]["distribuzione"]:
            df_categorie = pd.DataFrame(
                list(stats["categorie"]["distribuzione"].items()),
                columns=['Categoria', 'Numero']
            )
            
            fig_pie = px.pie(
                df_categorie,
                values='Numero',
                names='Categoria',
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.3
            )
            fig_pie.update_layout(
                height=400,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Nessun dato disponibile per le categorie")
    
    with col_chart2:
        # Grafico a barre temporale
        st.markdown("### 📅 Circolari per Mese")
        
        df_mesi = db.get_circolari_per_mese(limit_mesi=12)
        
        if not df_mesi.empty:
            fig_bar = px.bar(
                df_mesi,
                x='mese',
                y='numero_circolari',
                color='numero_circolari',
                color_continuous_scale='Blues',
                labels={'mese': 'Mese', 'numero_circolari': 'Numero Circolari'}
            )
            fig_bar.update_layout(
                height=400,
                xaxis_title="Mese",
                yaxis_title="Numero Circolari",
                coloraxis_showscale=False
            )
            fig_bar.update_xaxes(tickangle=45)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Nessun dato disponibile per l'analisi mensile")
    
    # Tabella dettagliata categorie
    st.markdown("---")
    st.markdown("### 📋 Dettaglio Categorie")
    
    if stats["categorie"]["distribuzione"]:
        df_cat_dettaglio = pd.DataFrame(
            list(stats["categorie"]["distribuzione"].items()),
            columns=['Categoria', 'Numero Circolari']
        )
        df_cat_dettaglio['Percentuale'] = (df_cat_dettaglio['Numero Circolari'] / 
                                          df_cat_dettaglio['Numero Circolari'].sum() * 100).round(1)
        df_cat_dettaglio = df_cat_dettaglio.sort_values('Numero Circolari', ascending=False)
        
        st.dataframe(
            df_cat_dettaglio,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Categoria": st.column_config.TextColumn("Categoria"),
                "Numero Circolari": st.column_config.NumberColumn("Numero", format="%d"),
                "Percentuale": st.column_config.ProgressColumn(
                    "Percentuale",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                )
            }
        )
    else:
        st.info("Nessuna categoria disponibile")

def render_tab_robot():
    """Renderizza la tab Log Robot"""
    st.markdown('<h2 class="sub-header">🤖 Log delle Esecuzioni Robot</h2>', unsafe_allow_html=True)
    
    # Filtri log
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        azioni = ["Tutte", "esecuzione_completata", "errore_critico", "scaricamento_simulato", "esecuzione_ibrida"]
        azione_selezionata = st.selectbox("Filtra per azione", azioni)
    
    with col_filtro2:
        limite_log = st.slider("Numero log", min_value=10, max_value=100, value=20)
    
    # Carica logs
    df_logs = db.get_logs_robot(limit=limite_log, azione=azione_selezionata if azione_selezionata != "Tutte" else None)
    
    if df_logs.empty:
        st.info("📭 Nessun log trovato con i filtri attuali.")
        return
    
    # Statistiche logs
    logs_totali = len(df_logs)
    logs_errori = df_logs['errore'].notna().sum()
    logs_successo = logs_totali - logs_errori
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("Log totali", logs_totali)
    with col_stat2:
        st.metric("Successi", logs_successo)
    with col_stat3:
        st.metric("Errori", logs_errori)
    
    # Tabella logs
    st.markdown("### 📋 Log Dettagliati")
    
    # Prepara colonne per visualizzazione
    if 'dettagli' in df_logs.columns:
        # Espandi i dettagli JSON
        try:
            dettagli_list = []
            for dettagli_json in df_logs['dettagli']:
                if dettagli_json and dettagli_json != '{}':
                    dettagli_list.append(json.loads(dettagli_json))
                else:
                    dettagli_list.append({})
            
            # Aggiungi colonne utili dai dettagli
            for i, dettagli in enumerate(dettagli_list):
                if 'ambiente' in dettagli:
                    df_logs.at[i, 'ambiente'] = dettagli['ambiente']
                if 'database' in dettagli:
                    df_logs.at[i, 'database_utilizzato'] = dettagli['database']
        except:
            pass
    
    # Mostra tabella
    colonne_da_mostrare = ['data_ora', 'azione', 'circolari_processate', 'circolari_scartate', 'circolari_eliminate', 'durata_secondi', 'errore']
    colonne_disponibili = [col for col in colonne_da_mostrare if col in df_logs.columns]
    
    st.dataframe(
        df_logs[colonne_disponibili],
        use_container_width=True,
        hide_index=True,
        column_config={
            "data_ora": st.column_config.TextColumn("Data/Ora"),
            "azione": st.column_config.TextColumn("Azione"),
            "circolari_processate": st.column_config.NumberColumn("Processate", format="%d"),
            "circolari_scartate": st.column_config.NumberColumn("Scartate", format="%d"),
            "circolari_eliminate": st.column_config.NumberColumn("Eliminate", format="%d"),
            "durata_secondi": st.column_config.NumberColumn("Durata (s)", format="%.2f"),
            "errore": st.column_config.TextColumn("Errore", width="large")
        }
    )
    
    # Grafico timeline esecuzioni
    st.markdown("---")
    st.markdown("### ⏱️ Timeline Esecuzioni")
    
    if 'data_ora' in df_logs.columns:
        try:
            # Converti la colonna data_ora in datetime
            df_logs['timestamp_dt'] = pd.to_datetime(df_logs['data_ora'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
            
            # Crea grafico timeline
            fig_timeline = go.Figure()
            
            # Aggiungi punti per successi
            successi = df_logs[df_logs['errore'].isna()]
            if not successi.empty:
                fig_timeline.add_trace(go.Scatter(
                    x=successi['timestamp_dt'],
                    y=[1] * len(successi),
                    mode='markers',
                    marker=dict(size=10, color='green'),
                    name='Successo',
                    hovertext=successi['azione']
                ))
            
            # Aggiungi punti per errori
            errori = df_logs[df_logs['errore'].notna()]
            if not errori.empty:
                fig_timeline.add_trace(go.Scatter(
                    x=errori['timestamp_dt'],
                    y=[0.5] * len(errori),
                    mode='markers',
                    marker=dict(size=10, color='red'),
                    name='Errore',
                    hovertext=errori['errore']
                ))
            
            fig_timeline.update_layout(
                height=200,
                showlegend=True,
                xaxis_title="Data/Ora",
                yaxis=dict(showticklabels=False, range=[0, 1.5]),
                hovermode='closest'
            )
            
            st.plotly_chart(fig_timeline, use_container_width=True)
        except Exception as e:
            st.warning(f"Impossibile creare timeline: {e}")

def render_tab_gestione():
    """Renderizza la tab Gestione"""
    st.markdown('<h2 class="sub-header">⚙️ Gestione Sistema</h2>', unsafe_allow_html=True)
    
    tab_gest1, tab_gest2, tab_gest3 = st.tabs(["🗃️ Database", "🔄 Manutenzione", "📤 Esportazione"])
    
    with tab_gest1:
        # Info database
        st.markdown("### Informazioni Database")
        
        test_result = db.test_connection()
        
        if test_result["status"] == "connected":
            st.success("✅ Database connesso")
            
            col_db1, col_db2 = st.columns(2)
            with col_db1:
                st.metric("PostgreSQL", test_result["postgres_version"].split()[1])
            with col_db2:
                st.metric("Database", test_result["database"])
            
            st.info("**Configurazione attuale:**")
            st.write(f"- **Host:** postgres.railway.internal")
            st.write(f"- **Porta:** 5432")
            st.write(f"- **Tipo:** PostgreSQL interno Railway")
            st.write(f"- **Costo:** Gratuito")
            st.write(f"- **Accesso:** Solo dall'interno Railway")
        else:
            st.error("❌ Database non connesso")
            st.write(test_result["message"])
        
        # Pulsante test connessione
        if st.button("🔍 Test connessione database", use_container_width=True):
            st.rerun()
    
    with tab_gest2:
        # Manutenzione
        st.markdown("### Operazioni di Manutenzione")
        
        col_maint1, col_maint2 = st.columns(2)
        
        with col_maint1:
            if st.button("🧹 Pulisci circolari vecchie", use_container_width=True):
                with st.spinner("Eliminazione circolari vecchie in corso..."):
                    eliminate = db.elimina_circolari_vecchie(giorni=30)
                    if eliminate > 0:
                        st.success(f"Eliminate {eliminate} circolari vecchie (>30 giorni)")
                    else:
                        st.info("Nessuna circolare vecchia da eliminare")
                    st.rerun()
        
        with col_maint2:
            if st.button("📊 Aggiorna statistiche", use_container_width=True):
                with st.spinner("Aggiornamento statistiche in corso..."):
                    st.info("Le statistiche vengono aggiornate automaticamente. Questa operazione forza l'aggiornamento.")
                    st.rerun()
        
        # Sincronizzazione da backup SQLite
        st.markdown("---")
        st.markdown("### 🔄 Sincronizzazione Emergenza")
        
        col_sync1, col_sync2 = st.columns([3, 1])
        
        with col_sync1:
            st.markdown("""
            **Quando usare questa funzione:**
            - Se le circolari non appaiono nell'app
            - Dopo un errore del robot
            - Per recuperare dati da backup SQLite
            
            **Nota:** Il file `circolari.db` deve essere stato scaricato dal robot GitHub Actions
            """)
        
        with col_sync2:
            if st.button("🔄 Sincronizza da backup", use_container_width=True, type="primary"):
                with st.spinner("Sincronizzazione in corso..."):
                    try:
                        sincronizzate = db.sincronizza_da_sqlite()
                        if sincronizzate > 0:
                            st.success(f"✅ Sincronizzate {sincronizzate} circolari da backup SQLite")
                            st.info("Le circolari saranno ora visibili nella tab 'Circolari'")
                        else:
                            st.info("ℹ️  Nessuna nuova circolare da sincronizzare")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Errore durante la sincronizzazione: {e}")
        
        # Informazioni sistema
        st.markdown("---")
        st.markdown("### Informazioni Sistema")
        
        stats = db.get_statistiche()
        if stats and "database" in stats:
            st.write(f"**Ultimo aggiornamento DB:** {stats['database']['ultimo_aggiornamento']}")
        
        st.write(f"**Ora server:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        st.write(f"**Fuso orario:** UTC+1 (Europa/Roma)")
        
        # Backup info
        st.markdown("---")
        st.markdown("### Backup")
        st.info("""
        **Backup automatici:**
        - Il robot GitHub Actions crea backup giornalieri
        - I backup sono disponibili nella sezione Artifacts di GitHub Actions
        - Database principale: PostgreSQL su Railway (backup automatico Railway)
        
        **📁 File backup:**
        - `circolari.db`: Database SQLite completo
        - `robot_report.json`: Report esecuzione robot
        - `circolari.json`: Statistiche circolari
        """)
        
        if st.button("📋 Mostra info backup GitHub", use_container_width=True):
            st.info("Vai su: GitHub → Repository → Actions → Robot Circolari → Artifacts")
    
    with tab_gest3:
        # Esportazione dati
        st.markdown("### Esportazione Dati")
        
        # Ottieni tutte le circolari
        df_tutte = db.get_circolari_recenti(limit=1000, giorni_indietro=365*5)  # 5 anni
        
        if not df_tutte.empty:
            st.success(f"Disponibili {len(df_tutte)} circolari per l'esportazione")
            
            # Formati esportazione
            formato = st.radio("Formato esportazione", ["CSV", "JSON", "Excel"])
            
            if st.button("📥 Genera file di esportazione", use_container_width=True):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                if formato == "CSV":
                    csv_data = df_tutte.to_csv(index=False)
                    st.download_button(
                        label="📥 Scarica CSV",
                        data=csv_data,
                        file_name=f"circolari_complete_{timestamp}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                elif formato == "JSON":
                    json_data = df_tutte.to_json(orient="records", indent=2)
                    st.download_button(
                        label="📥 Scarica JSON",
                        data=json_data,
                        file_name=f"circolari_complete_{timestamp}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                elif formato == "Excel":
                    # Per Excel serve BytesIO
                    import io
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_tutte.to_excel(writer, index=False, sheet_name='Circolari')
                        # Aggiungi foglio statistiche
                        stats_sheet = pd.DataFrame([{
                            'Data esportazione': datetime.now().strftime('%d/%m/%Y %H:%M'),
                            'Totale circolari': len(df_tutte),
                            'Categorie': df_tutte['categoria'].nunique(),
                            'Periodo da': df_tutte['data_pubblicazione'].min(),
                            'Periodo a': df_tutte['data_pubblicazione'].max()
                        }])
                        stats_sheet.to_excel(writer, index=False, sheet_name='Statistiche')
                    
                    st.download_button(
                        label="📥 Scarica Excel",
                        data=buffer.getvalue(),
                        file_name=f"circolari_complete_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
        else:
            st.warning("Nessuna circolare disponibile per l'esportazione")
            
            # Suggerimenti
            st.info("""
            **Per esportare dati:**
            1. Assicurati che il robot abbia eseguito correttamente
            2. Verifica che ci siano circolari nel database
            3. Usa il pulsante "Sincronizza da backup" se necessario
            4. Controlla i log del robot per eventuali errori
            """)

# ==============================================================================
# 🛑 PAGINA DETTAGLIO CIRCOLARE
# ==============================================================================

def render_dettaglio_circolare():
    """Renderizza la pagina di dettaglio di una circolare"""
    circolare_id = st.session_state.dettaglio_circolare
    circolare = db.get_circolare_by_id(circolare_id)
    
    if not circolare:
        st.error("Circolare non trovata")
        if st.button("← Torna all'elenco"):
            del st.session_state.dettaglio_circolare
            st.rerun()
        return
    
    # Header dettaglio
    col_back, col_title = st.columns([1, 4])
    
    with col_back:
        if st.button("← Torna all'elenco"):
            del st.session_state.dettaglio_circolare
            st.rerun()
    
    with col_title:
        st.markdown(f"# 📄 {circolare['titolo']}")
    
    st.markdown("---")
    
    # Informazioni circolare
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.markdown("**Categoria:**")
        categoria = circolare.get('categoria', 'N/A')
        badge_class = get_badge_color(categoria)
        st.markdown(f'<span class="badge {badge_class}">{categoria}</span>', unsafe_allow_html=True)
    
    with col_info2:
        st.markdown("**Data pubblicazione:**")
        st.markdown(f"`{circolare.get('data_formattata', 'N/A')}`")
    
    with col_info3:
        st.markdown("**Data scaricamento:**")
        st.markdown(f"`{circolare.get('scaricata_il', 'N/A')}`")
    
    # Fonte
    if circolare.get('fonte'):
        st.markdown(f"**Fonte:** {circolare['fonte']}")
    
    st.markdown("---")
    
    # Contenuto
    st.markdown("## 📝 Contenuto")
    st.markdown(circolare.get('contenuto', 'Nessun contenuto disponibile'))
    
    # Allegati
    allegati = circolare.get('allegati', [])
    if allegati:
        st.markdown("---")
        st.markdown(f"## 📎 Allegati ({len(allegati)})")
        
        for i, allegato in enumerate(allegati, 1):
            col_alleg1, col_alleg2 = st.columns([3, 1])
            with col_alleg1:
                st.write(f"**{i}. {allegato}**")
            with col_alleg2:
                # Simula download (in un sistema reale qui ci sarebbe il link al file)
                st.download_button(
                    label="⬇️ Scarica",
                    data=f"Simulazione file: {allegato}",
                    file_name=allegato,
                    key=f"download_{circolare_id}_{i}",
                    use_container_width=True
                )
    
    # Metadati
    st.markdown("---")
    with st.expander("🔍 Metadati tecnici"):
        col_meta1, col_meta2 = st.columns(2)
        
        with col_meta1:
            st.write(f"**ID:** {circolare['id']}")
            st.write(f"**Fonte:** {circolare.get('fonte', 'N/A')}")
        
        with col_meta2:
            st.write(f"**Database:** PostgreSQL Railway")
            st.write(f"**Host:** postgres.railway.internal")

# ==============================================================================
# 🛑 FUNZIONE SPECIALE: SINCRO SESSIONE
# ==============================================================================

def render_sincronizzazione():
    """Pagina speciale per sincronizzazione"""
    st.markdown('<h1 class="main-header">🔄 Sincronizzazione Circolari</h1>', unsafe_allow_html=True)
    
    st.info("""
    **Questa funzione sincronizza le circolari dal backup SQLite al database PostgreSQL.**
    
    **Quando usarla:**
    - Se le circolari scaricate dal robot non compaiono nell'app
    - Dopo un errore del robot
    - Per recuperare dati da backup precedenti
    
    **Nota:** Il robot GitHub Actions salva un backup SQLite (`circolari.db`) ad ogni esecuzione.
    """)
    
    col_info, col_action = st.columns([2, 1])
    
    with col_info:
        stats = db.get_statistiche()
        if stats:
            st.metric("Circolari attuali nel DB", stats["generali"]["totale_circolari"])
    
    with col_action:
        if st.button("🔄 Avvia Sincronizzazione", type="primary", use_container_width=True):
            with st.spinner("Sincronizzazione in corso..."):
                try:
                    sincronizzate = db.sincronizza_da_sqlite()
                    if sincronizzate > 0:
                        st.success(f"✅ Sincronizzate {sincronizzate} nuove circolari!")
                        st.info("Le circolari saranno ora visibili nella tab 'Circolari'")
                        
                        # Aggiorna statistiche
                        stats_aggiornate = db.get_statistiche()
                        if stats_aggiornate:
                            st.metric("Nuovo totale circolari", stats_aggiornate["generali"]["totale_circolari"])
                    else:
                        st.info("ℹ️  Nessuna nuova circolare da sincronizzare")
                    
                    # Pulsante per tornare
                    if st.button("📋 Vai all'elenco circolari", use_container_width=True):
                        del st.session_state.mostra_sincronizza
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Errore durante la sincronizzazione: {e}")
                    st.write("Dettagli errore:", str(e))
    
    st.markdown("---")
    st.markdown("### 📁 File backup disponibili")
    
    # Informazioni sui backup
    st.info("""
    **Per ottenere il file di backup (`circolari.db`):**
    1. Vai su GitHub → Repository → Actions
    2. Clicca sull'ultima esecuzione del robot
    3. Scorri fino alla sezione "Artifacts"
    4. Scarica il file `robot-output-XXX.zip`
    5. Estrai `circolari.db` dalla cartella
    6. Caricalo manualmente se necessario
    """)
    
    # Pulsante per tornare
    if st.button("← Torna alla dashboard", use_container_width=True):
        del st.session_state.mostra_sincronizza
        st.rerun()

# ==============================================================================
# 🛑 MAIN APP
# ==============================================================================

def main():
    """Funzione principale dell'applicazione"""
    # Inizializzazione
    init_session_state()
    apply_custom_css()
    
    # Controlla se mostrare pagina sincronizzazione
    if hasattr(st.session_state, 'mostra_sincronizza') and st.session_state.mostra_sincronizza:
        render_sincronizzazione()
        return
    
    # Controlla se siamo in modalità dettaglio
    if hasattr(st.session_state, 'dettaglio_circolare'):
        render_dettaglio_circolare()
        return
    
    # Render header e sidebar
    render_header()
    ricerca_testo = render_sidebar()
    
    # Tabs principali
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Circolari", 
        "📈 Statistiche", 
        "🤖 Log Robot", 
        "⚙️ Gestione"
    ])
    
    with tab1:
        render_tab_circolari()
    
    with tab2:
        render_tab_statistiche()
    
    with tab3:
        render_tab_robot()
    
    with tab4:
        render_tab_gestione()
    
    # Footer
    st.markdown("---")
    col_foot1, col_foot2, col_foot3 = st.columns([2, 1, 1])
    
    with col_foot1:
        st.caption(f"© {datetime.now().year} Circolari Online - Sistema di gestione circolari scolastiche")
    
    with col_foot2:
        st.caption(f"Versione: 2.0.0")
    
    with col_foot3:
        st.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ==============================================================================
# 🛑 AVVIO APPLICAZIONE
# ==============================================================================

if __name__ == "__main__":
    main()
