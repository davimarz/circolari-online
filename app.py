import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import database as db

# Configurazione pagina
st.set_page_config(
    page_title="Circolari Online",
    page_icon="📚",
    layout="wide"
)

# Titolo
st.title("📚 Circolari Online")
st.markdown("**Dashboard per la gestione delle circolari scolastiche**")

# Inizializza database
if db.inizializza_database():
    st.success("✅ Database connesso correttamente")
else:
    st.error("❌ Errore connessione database")

# Sidebar
with st.sidebar:
    st.header("Filtri")
    
    # Filtro data
    giorni_indietro = st.slider(
        "Ultimi giorni",
        min_value=7,
        max_value=90,
        value=30,
        help="Mostra circolari degli ultimi N giorni"
    )
    
    # Filtro categoria
    stats = db.get_statistiche()
    categorie = list(stats.get("categorie", {}).keys())
    
    if categorie:
        categoria_selezionata = st.selectbox(
            "Categoria",
            ["Tutte"] + categorie
        )
    else:
        categoria_selezionata = "Tutte"
    
    st.divider()
    
    # Statistiche sidebar
    st.subheader("📊 Statistiche")
    st.metric("Totale Circolari", stats.get("totale", 0))
    st.metric("Ultimi 7 giorni", stats.get("ultima_settimana", 0))
    
    if stats.get("ultima_data"):
        st.caption(f"Ultima circolare: {stats['ultima_data'].strftime('%d/%m/%Y')}")

# Layout principale
tab1, tab2, tab3 = st.tabs(["📋 Circolari", "📈 Statistiche", "🤖 Log Robot"])

with tab1:
    st.header("Elenco Circolari")
    
    # Ottieni circolari
    df_circolari = db.get_circolari_recenti(limit=100)
    
    if not df_circolari.empty:
        # Applica filtri
        data_limite = datetime.now() - timedelta(days=giorni_indietro)
        
        if 'data_pubblicazione' in df_circolari.columns:
            df_circolari['data_pubblicazione'] = pd.to_datetime(df_circolari['data_pubblicazione'])
            df_filtrato = df_circolari[df_circolari['data_pubblicazione'] >= data_limite]
        else:
            df_filtrato = df_circolari
        
        if categoria_selezionata != "Tutte" and 'categoria' in df_filtrato.columns:
            df_filtrato = df_filtrato[df_filtrato['categoria'] == categoria_selezionata]
        
        # Mostra risultati
        st.write(f"**{len(df_filtrato)} circolari trovate**")
        
        for idx, row in df_filtrato.iterrows():
            with st.expander(f"{row['data_pubblicazione'].strftime('%d/%m/%Y')} - {row['titolo']}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Categoria:** {row.get('categoria', 'N/A')}")
                    st.markdown(f"**Data:** {row['data_pubblicazione'].strftime('%d/%m/%Y')}")
                    st.markdown("**Contenuto:**")
                    st.write(row.get('contenuto', 'Nessun contenuto'))
                
                with col2:
                    # Allegati
                    allegati = row.get('allegati')
                    if allegati and allegati != '[]':
                        st.markdown("**Allegati:**")
                        for allegato in allegati:
                            st.write(f"📎 {allegato}")
                    
                    # Data scaricamento
                    if 'data_scaricamento' in row:
                        st.caption(f"Scaricata: {row['data_scaricamento'].strftime('%d/%m/%Y %H:%M')}")
    else:
        st.info("📭 Nessuna circolare trovata nel database")

with tab2:
    st.header("Statistiche")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Grafico per categoria
        if stats.get("categorie"):
            df_cat = pd.DataFrame({
                'Categoria': list(stats['categorie'].keys()),
                'Numero': list(stats['categorie'].values())
            })
            
            fig = px.pie(
                df_cat, 
                values='Numero', 
                names='Categoria',
                title="Distribuzione per categoria"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Circolari nel tempo
        df_circolari = db.get_circolari_recenti(limit=500)
        if not df_circolari.empty and 'data_pubblicazione' in df_circolari.columns:
            df_circolari['data_pubblicazione'] = pd.to_datetime(df_circolari['data_pubblicazione'])
            df_circolari['mese'] = df_circolari['data_pubblicazione'].dt.strftime('%Y-%m')
            
            conteggio_mensile = df_circolari.groupby('mese').size().reset_index(name='count')
            
            fig2 = px.bar(
                conteggio_mensile,
                x='mese',
                y='count',
                title="Circolari per mese",
                labels={'mese': 'Mese', 'count': 'Numero circolari'}
            )
            st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.header("Log del Robot")
    
    df_logs = db.get_logs_robot(limit=50)
    
    if not df_logs.empty:
        # Formatta timestamp
        if 'timestamp' in df_logs.columns:
            df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
            df_logs['data_ora'] = df_logs['timestamp'].dt.strftime('%d/%m/%Y %H:%M')
        
        # Mostra tabella
        st.dataframe(
            df_logs[['data_ora', 'azione', 'circolari_processate', 'circolari_scartate', 'errore']],
            use_container_width=True
        )
        
        # Statistiche robot
        if not df_logs.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                ultima_esecuzione = df_logs['timestamp'].max()
                st.metric("Ultima esecuzione", ultima_esecuzione.strftime('%d/%m/%Y %H:%M'))
            
            with col2:
                totali_processate = df_logs['circolari_processate'].sum()
                st.metric("Totali processate", totali_processate)
            
            with col3:
                errori = df_logs['errore'].notna().sum()
                st.metric("Errori", errori)
    else:
        st.info("📭 Nessun log trovato")

# Footer
st.divider()
st.caption(f"© {datetime.now().year} Circolari Online - Database: Railway PostgreSQL - Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
