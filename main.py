import streamlit as st
import pandas as pd
from datetime import datetime
import database
import logging

# Configurazione pagina
st.set_page_config(
    page_title="Circolari Online",
    page_icon="📚",
    layout="wide"
)

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Header
    st.title("📚 Circolari Online")
    st.markdown("---")
    
    # Inizializzazione database
    if database.init_db():
        st.sidebar.success("✅ Database connesso")
    else:
        st.sidebar.error("❌ Errore di connessione al database")
        st.stop()
    
    # Sidebar per filtri
    with st.sidebar:
        st.header("Filtri")
        
        # Filtro per categoria
        categorie = st.multiselect(
            "Seleziona categorie",
            ["Tutte", "Documenti Istituzionali", "Progetti Didattici", "Concorsi per Alunni", "Comunicazioni"]
        )
        
        # Filtro per data
        date_range = st.date_input(
            "Intervallo date",
            value=(datetime.now().replace(day=1), datetime.now()),
            max_value=datetime.now()
        )
        
        st.markdown("---")
        st.markdown("### Statistiche")
    
    # Carica circolari
    try:
        if "Tutte" in categorie or not categorie:
            circolari = database.get_circolari()
        else:
            circolari = database.get_circolari(filtro_categoria=categorie[0])
        
        if circolari:
            # Converti in DataFrame per visualizzazione
            df = pd.DataFrame(circolari)
            
            # Filtra per data
            if len(date_range) == 2:
                start_date, end_date = date_range
                df['data_pubblicazione'] = pd.to_datetime(df['data_pubblicazione'])
                df = df[(df['data_pubblicazione'] >= pd.Timestamp(start_date)) & 
                       (df['data_pubblicazione'] <= pd.Timestamp(end_date))]
            
            # Mostra statistiche
            st.sidebar.metric("Circolari totali", len(df))
            if 'categoria' in df.columns:
                st.sidebar.metric("Categorie", df['categoria'].nunique())
            
            # Visualizzazione circolari
            st.subheader(f"📋 Circolari ({len(df)} trovati)")
            
            for _, row in df.iterrows():
                with st.expander(f"{row['numero']} - {row['titolo']} - {row['data_pubblicazione'].strftime('%d/%m/%Y')}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Categoria:** {row.get('categoria', 'N/A')}")
                        st.markdown(f"**Autore:** {row.get('autore', 'N/A')}")
                        st.markdown("**Contenuto:**")
                        st.markdown(row.get('contenuto', 'Nessun contenuto disponibile'))
                    
                    with col2:
                        if row.get('allegati'):
                            st.markdown("**Allegati:**")
                            allegati = row['allegati'].split(',') if isinstance(row['allegati'], str) else row['allegati']
                            for allegato in allegati:
                                st.markdown(f"📎 {allegato.strip()}")
            
            # Tabella riassuntiva
            st.markdown("---")
            st.subheader("Tabella riassuntiva")
            st.dataframe(
                df[['numero', 'titolo', 'data_pubblicazione', 'categoria']],
                use_container_width=True
            )
        else:
            st.info("📭 Al momento non ci sono circolari disponibili.")
            
    except Exception as e:
        logger.error(f"Errore nel caricamento delle circolari: {e}")
        st.error(f"Errore nel caricamento delle circolari: {str(e)}")
        st.info("📭 Al momento non ci sono circolari disponibili.")

if __name__ == "__main__":
    main()
