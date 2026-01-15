import os
import psycopg2
import pandas as pd
from psycopg2 import sql
import streamlit as st
import logging
import subprocess

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_connection():
    """
    Crea una connessione al database PostgreSQL su Railway
    Versione CON PASSWORD FISSA CORRETTA: TpsVpUowNnMqSXpvAosQEezxpGPtbPNG
    """
    # Configurazione FISSA per Railway
    HOST = "switchback.proxy.rlwy.net"
    PORT = "53723"
    USER = "postgres"
    PASSWORD = "TpsVpUowNnMqSXpvAosQEezxpGPtbPNG"  # PASSWORD CORRETTA
    DATABASE = "railway"
    
    # Costruisci URL di connessione
    DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?sslmode=require"
    
    # Log di debug (SICURO - solo in console)
    logger.info("=" * 70)
    logger.info("🔗 Tentativo connessione database Railway")
    logger.info(f"Host: {HOST}")
    logger.info(f"Port: {PORT}")
    logger.info(f"User: {USER}")
    logger.info(f"Password (iniziata con): {PASSWORD[:6]}...")
    logger.info(f"Password lunghezza: {len(PASSWORD)} caratteri")
    logger.info(f"Database: {DATABASE}")
    logger.info("=" * 70)
    
    try:
        # Tentativo di connessione
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("✅ CONNESSIONE DATABASE RIUSCITA!")
        return conn
        
    except psycopg2.OperationalError as e:
        logger.error(f"❌ Errore connessione database: {e}")
        
        # Analisi dettagliata dell'errore
        error_msg = str(e)
        
        if "password authentication failed" in error_msg:
            st.error("🔑 **ERRORE: Password non valida**")
            st.error(f"La password ({len(PASSWORD)} caratteri) viene rifiutata dal server")
            st.info(f"**Password usata:** `{PASSWORD[:8]}...{PASSWORD[-8:]}`")
            st.info("**Controlla:**")
            st.info("1. La password è stata copiata ESATTAMENTE")
            st.info("2. Non ci sono spazi all'inizio o alla fine")
            st.info("3. Il database è ONLINE su Railway")
            
        elif "could not translate host name" in error_msg:
            st.error("🌐 **ERRORE: Host non raggiungibile**")
            st.error(f"Impossibile connettersi a: {HOST}")
            st.info("Verifica che:")
            st.info(f"1. {HOST} sia l'host corretto")
            st.info("2. Il database sia esposto pubblicamente su Railway")
            
        elif "Connection refused" in error_msg:
            st.error("🚫 **ERRORE: Connessione rifiutata**")
            st.error(f"Porta {PORT} non accetta connessioni")
            st.info("Verifica che la porta sia corretta")
            
        else:
            st.error(f"❌ Errore di connessione: {error_msg}")
            
        return None
        
    except Exception as e:
        logger.error(f"❌ Errore imprevisto: {e}")
        st.error(f"❌ Errore imprevisto: {str(e)}")
        return None

def init_database():
    """
    Inizializza/verifica il database e crea le tabelle necessarie
    """
    logger.info("Inizializzazione database iniziata...")
    
    conn = get_database_connection()
    if conn is None:
        return "❌ Impossibile connettersi al database"
    
    try:
        cursor = conn.cursor()
        
        # 1. Verifica versione PostgreSQL
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"PostgreSQL versione: {version}")
        
        # 2. Crea tabella circolari
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circolari (
                id SERIAL PRIMARY KEY,
                titolo TEXT NOT NULL,
                data_pubblicazione DATE DEFAULT CURRENT_DATE,
                file_url TEXT,
                contenuto TEXT,
                categoria TEXT DEFAULT 'Generale',
                priorita INTEGER DEFAULT 1,
                firmatario TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Tabella 'circolari' creata/verificata")
        
        # 3. Crea tabella utenti
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utenti (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                nome TEXT,
                cognome TEXT,
                ruolo TEXT DEFAULT 'lettore' CHECK (ruolo IN ('amministratore', 'editore', 'lettore')),
                attivo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                reset_token TEXT,
                reset_expires TIMESTAMP
            );
        """)
        logger.info("Tabella 'utenti' creata/verificata")
        
        # 4. Crea tabella logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                azione TEXT NOT NULL,
                tabella TEXT,
                record_id INTEGER,
                utente_id INTEGER,
                dettagli JSONB,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Tabella 'logs' creata/verificata")
        
        # 5. Inserisci utente admin di default (password: admin123)
        cursor.execute("""
            INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo)
            VALUES ('admin', 'admin@annafrank.edu.it', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Admin', 'Sistema', 'amministratore')
            ON CONFLICT (username) DO NOTHING;
        """)
        
        # 6. Conta tabelle create
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        table_count = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Inizializzazione completata. Tabelle create: {table_count}")
        
        return f"✅ Database inizializzato! PostgreSQL: {version.split(',')[0]} | Tabelle: {table_count}"
            
    except Exception as e:
        logger.error(f"Errore inizializzazione database: {e}")
        return f"❌ Errore durante inizializzazione: {str(e)}"

def test_connection_simple():
    """
    Test semplice della connessione
    """
    conn = get_database_connection()
    if conn is None:
        return False, "Connessione fallita"
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test, current_timestamp as server_time, version() as pg_version;")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return True, f"✅ Connesso! PostgreSQL {result[2].split(' ')[1]} | Ora server: {result[1]}"
    except Exception as e:
        return False, f"❌ Errore query: {str(e)}"

def get_circolari(limit=100):
    """
    Recupera le circolari dal database
    """
    conn = get_database_connection()
    if conn is None:
        return pd.DataFrame()
    
    try:
        query = """
            SELECT id, titolo, data_pubblicazione, file_url, contenuto, 
                   categoria, priorita, firmatario, created_at
            FROM circolari 
            ORDER BY data_pubblicazione DESC, priorita DESC
            LIMIT %s;
        """
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    except Exception as e:
        logger.error(f"Errore recupero circolari: {e}")
        return pd.DataFrame()

def insert_circolare(titolo, contenuto, file_url=None, categoria='Generale', priorita=1, firmatario=''):
    """
    Inserisce una nuova circolare
    """
    conn = get_database_connection()
    if conn is None:
        return False, "Errore connessione"
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO circolari (titolo, contenuto, file_url, categoria, priorita, firmatario)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (titolo, contenuto, file_url, categoria, priorita, firmatario))
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, f"Circolare inserita con ID: {new_id}"
    except Exception as e:
        return False, f"Errore inserimento: {str(e)}"
