import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_all_circolari

st.set_page_config(
    page_title="Bacheca Circolari IC Anna Frank",
    page_icon="📢",
    layout="wide"
)

st.title("📢 Bacheca Circolari - IC Anna Frank")
st.markdown("---")

with st.sidebar:
    st.header("ℹ️ Informazioni")
    st.info(f"Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    if st.button("🔄 Aggiorna circolari"):
        st.rerun()

def main():
    try:
        # Recupera le circolari
        circolari = get_all_circolari()
        
        # Statistiche
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Circolari totali", len(circolari))
        with col2:
            st.metric("Ultimo aggiornamento", datetime.now().strftime("%H:%M:%S"))
        
        if circolari:
            # Barra di ricerca
            search_term = st.text_input("🔍 Cerca nelle circolari...", "")
            
            # Mostra circolari
            for circ in circolari:
                if search_term.lower() in circ['titolo'].lower() or not search_term:
                    with st.expander(f"{circ['data_pubblicazione']} - {circ['titolo']}"):
                        st.write(circ['contenuto'])
                        if circ['pdf_url']:
                            st.markdown(f"📄 [Scarica PDF]({circ['pdf_url']})")
        else:
            st.info("📭 Nessuna circolare disponibile. Il robot le aggiungerà automaticamente.")
            
    except Exception as e:
        st.error(f"❌ Errore nel caricamento delle circolari: {str(e)}")
        st.info("⚠️ Assicurati che il database sia configurato correttamente.")

if __name__ == "__main__":
    main()
