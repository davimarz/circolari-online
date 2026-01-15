import os
import psycopg2
import pandas as pd
from psycopg2 import sql
import streamlit as st
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_connection():
    """
    Crea una connessione al database PostgreSQL su Railway
    """
    # LEGGI dalla variabile d'ambiente - OBBLIGATORIO per Railway
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # DEBUG logging
    if DATABASE_URL:
        logger.info(f"DATABASE_URL trovata (primi 60 caratteri): {DATABASE_URL[:60]}...")
        if 'railway.internal' in DATABASE_URL:
            logger.warning("ATTENZIONE: URL interno rilevato!")
    else:
        logger.error("DATABASE_URL NON TROVATA nelle variabili d'ambiente")
        st.error("❌ ERRORE CRITICO: DATABASE_URL non configurata su Railway")
        st.info("Vai su Railway → circolari-online → Variables → imposta DATABASE_URL")
        return None
    
    try:
        # CORREZIONE: Se è l'URL interno, convertilo in pubblico
        if 'postgres.railway.internal:5432' in DATABASE_URL:
            logger.info("Convertendo URL interno in pubblico...")
            # Conserva username, password e database
            parts = DATABASE_URL.split('@')
            if len(parts) == 2:
                credentials = parts[0]  # postgresql://postgres:password
                # Sostituisci host:port
                new_url = f"{credentials}@switchback.proxy.rlwy.net:53723/railway"
                DATABASE_URL = new_url
                logger.info(f"URL convertito: {DATABASE_URL[:60]}...")
        
        # Assicurati che ci sia sslmode=require per connessioni esterne
        if 'sslmode=' not in DATABASE_URL:
            DATABASE_URL += "?sslmode=require"
            logger.info("Aggiunto sslmode=require")
        
        # Connessione
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("✅ Connessione al database stabilita con successo")
        return conn
        
    except psycopg2.OperationalError as e:
        logger.error(f"Errore operazionale DB: {e}")
        st.error(f"❌ Errore connessione al database: {str(e)}")
        st.info("Controlla che:")
        st.info("1. Il database PostgreSQL sia ONLINE su Railway")
        st.info("2. L'URL pubblico sia corretto: switchback.proxy.rlwy.net:53723")
        st.info("3. La password sia corretta")
        return None
    except Exception as e:
        logger.error(f"Errore generico DB: {e}")
        st.error(f"❌ Errore imprevisto: {str(e)}")
        return None

def init_database():
    """
    Inizializza/verifica il database - versione semplificata per debug
    """
    logger.info("Inizializzazione database iniziata...")
    
    conn = get_database_connection()
    if conn is None:
        return "❌ Impossibile connettersi al database"
    
    try:
        cursor = conn.cursor()
        
        # 1. Verifica connessione semplice
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"PostgreSQL versione: {version[0]}")
        
        # 2. Lista tabelle esistenti
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        # 3. Crea tabella circolari se non esiste
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circolari (
                id SERIAL PRIMARY KEY,
                titolo TEXT NOT NULL,
                data_pubblicazione DATE,
                file_url TEXT,
                contenuto TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Tabella 'circolari' verificata/creata")
        
        # 4. Crea tabella utenti se non esiste
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utenti (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT,
                ruolo TEXT DEFAULT 'lettore',
                attivo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );
        """)
        logger.info("Tabella 'utenti' verificata/creata")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        table_list = ", ".join([t[0] for t in tables]) if tables else "nessuna"
        return f"✅ Database OK! Trovate {len(tables)} tabelle: {table_list}"
            
    except Exception as e:
        logger.error(f"Errore inizializzazione: {e}")
        return f"❌ Errore durante inizializzazione: {str(e)}"

def test_database_connection():
    """
    Test rapido della connessione
    """
    logger.info("Test connessione database...")
    conn = get_database_connection()
    if conn is None:
        return False, "Nessuna connessione"
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test_value, current_timestamp as server_time;")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result[0] == 1:
            logger.info("Test connessione PASSATO")
            return True, f"Connessione OK - Server time: {result[1]}"
        else:
            logger.warning("Test connessione FALLITO - risposta inattesa")
            return False, "Risposta inattesa dal database"
    except Exception as e:
        logger.error(f"Test connessione ERRORE: {e}")
        return False, f"Errore query: {str(e)}"

def get_circolari(limit=50):
    """
    Recupera le circolari dal database
    """
    conn = get_database_connection()
    if conn is None:
        return pd.DataFrame()
    
    try:
        query = "SELECT * FROM circolari ORDER BY data_pubblicazione DESC LIMIT %s;"
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    except Exception as e:
        logger.error(f"Errore recupero circolari: {e}")
        return pd.DataFrame()
