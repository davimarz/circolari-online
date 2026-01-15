import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_all_circolari, salva_circolare_db, init_db, test_connection
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inizializza database all'avvio
init_db()

# Configurazione pagina Streamlit
st.set_page_config(
    page_title="Bacheca Circolari IC Anna Frank",
    page_icon="📢",
    layout="wide"
)

# Titolo e descrizione
st.title("📢 Bacheca Circolari - IC Anna Frank")
st.markdown("---")

# Sidebar per informazioni
with st.sidebar:
    st.header("ℹ️ Informazioni")
    
    # Test connessione database
    if test_connection():
        st.success("✅ Database connesso")
    else:
        st.error("❌ Errore database")
    
    st.markdown("""
    ### Come usare:
    1. Le circolari sono visualizzate in ordine di data
    2. Clicca su una circolare per espandere il contenuto
    3. Usa la ricerca per filtrare
    """)
    
    # Bottone per refresh manuale
    if st.button("🔄 Aggiorna circolari"):
        st.rerun()

# Funzione principale
def main():
    # Header con statistiche
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Ultimo aggiornamento", datetime.now().strftime("%H:%M"))
    
    # Ottieni circolari dal database
    try:
        circolari = get_all_circolari()
        
        with col2:
            st.metric("Circolari totali", len(circolari))
        
        if circolari:
            # Converti in DataFrame per visualizzazione
            df_data = []
            for circ in circolari:
                df_data.append({
                    'ID': circ['id'],
                    'Data': circ['data_pubblicazione'],
                    'Titolo': circ['titolo'],
                    'Fonte': circ.get('fonte', 'sito_scuola'),
                    'PDF': '📄' if circ['pdf_url'] else ''
                })
            
            df = pd.DataFrame(df_data)
            
            # Barra di ricerca
            search_term = st.text_input("🔍 Cerca nelle circolari...", "")
            
            if search_term:
                df = df[df['Titolo'].str.contains(search_term, case=False, na=False)]
            
            # Visualizza circolari
            st.subheader(f"📋 Elenco Circolari ({len(df)} trovate)")
            
            for idx, row in df.iterrows():
                circ_id = row['ID']
                circolare_originale = next((c for c in circolari if c['id'] == circ_id), None)
                
                if circolare_originale:
                    with st.expander(f"{row['Data']} - {row['Titolo']} {row['PDF']}"):
                        st.markdown(f"**Fonte:** {row['Fonte']}")
                        st.markdown("---")
                        st.markdown(circolare_originale['contenuto'])
                        
                        if circolare_originale['pdf_url']:
                            st.markdown(f"📄 [Scarica PDF]({circolare_originale['pdf_url']})")
            
            # Mostra DataFrame compatto
            st.markdown("### 📊 Tabella riepilogativa")
            st.dataframe(
                df[['Data', 'Titolo', 'Fonte', 'PDF']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("📭 Nessuna circolare disponibile nel database")
            
    except Exception as e:
        st.error(f"❌ Errore nel caricamento delle circolari: {str(e)}")
        logger.error(f"Errore in app.py: {e}")

if __name__ == "__main__":
    main()
