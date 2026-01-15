import os
import psycopg2
import streamlit as st

def get_database_connection():
    """
    Crea una connessione usando variabili separate
    """
    # Leggi dalle variabili separate
    host = os.environ.get('PGHOST')
    port = os.environ.get('PGPORT')
    user = os.environ.get('PGUSER')
    password = os.environ.get('PGPASSWORD')
    database = os.environ.get('PGDATABASE')
    
    # Verifica che tutte le variabili ci siano
    missing = []
    if not host: missing.append('PGHOST')
    if not port: missing.append('PGPORT')
    if not user: missing.append('PGUSER')
    if not password: missing.append('PGPASSWORD')
    if not database: missing.append('PGDATABASE')
    
    if missing:
        st.error(f"❌ Variabili mancanti: {', '.join(missing)}")
        return None
    
    # Costruisci URL CORRETTA
    DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode=require"
    
    # DEBUG - mostra in console (non nella UI per sicurezza)
    print("=" * 60)
    print(f"CONNESSIONE DATABASE:")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"User: {user}")
    print(f"Password: {'*' * len(password)}")
    print(f"Database: {database}")
    print(f"URL completa (password nascosta): postgresql://{user}:{'*' * len(password)}@{host}:{port}/{database}?sslmode=require")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Connessione al database stabilita")
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Errore operazionale: {e}")
        st.error(f"❌ Errore connessione: {str(e)}")
        
        # Mostra suggerimenti specifici
        if "password authentication failed" in str(e):
            st.info("🔑 **Problema password:**")
            st.info("1. Verifica che la password sia esatta")
            st.info("2. Controlla che non ci siano spazi alla fine")
            st.info("3. La password è: " + "*" * len(password) + f" ({len(password)} caratteri)")
            
        elif "could not translate host name" in str(e):
            st.info("🌐 **Problema hostname:**")
            st.info(f"Host cercato: {host}")
            st.info("Verifica che l'host sia: switchback.proxy.rlwy.net")
            
        return None
    except Exception as e:
        print(f"❌ Errore generico: {e}")
        st.error(f"❌ Errore imprevisto: {str(e)}")
        return None
