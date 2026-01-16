import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_all_circolari, init_db

st.set_page_config(
    page_title="Bacheca Circolari IC Anna Frank",
    page_icon="📢",
    layout="wide"
)

st.title("📢 Bacheca Circolari - IC Anna Frank")
st.markdown("---")

with st.sidebar:
    st.header("ℹ️ Informazioni")
    st.info("Aggiornato: " + datetime.now().strftime("%d/%m/%Y %H:%M"))
    
    if st.button("🔄 Aggiorna"):
        st.rerun()

def main():
    try:
        circolari = get_all_circolari()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Circolari totali", len(circolari))
        with col2:
            st.metric("Ultimo aggiornamento", datetime.now().strftime("%H:%M"))
        
        if circolari:
            search = st.text_input("🔍 Cerca circolari...", "")
            
            for circ in circolari:
                with st.expander(f"{circ['data_pubblicazione']} - {circ['titolo']}"):
                    st.write(circ['contenuto'])
                    if circ['pdf_url']:
                        st.markdown(f"[📄 Scarica PDF]({circ['pdf_url']})")
        else:
            st.info("📭 Nessuna circolare disponibile")
            
    except Exception as e:
        st.error(f"Errore: {str(e)}")

if __name__ == "__main__":
    main()
