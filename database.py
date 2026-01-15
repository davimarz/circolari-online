import os
import psycopg2
import pandas as pd
from psycopg2 import sql
import streamlit as st
import logging
import json

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_connection():
    """
    Crea una connessione al database PostgreSQL su Railway
    Versione CON PASSWORD FISSA: TpsVpUowNnMqSXpvAosQEezxpGPtbPNG
    """
    # Configurazione FISSA per Railway
    HOST = "switchback.proxy.rlwy.net"
    PORT = "53723"
    USER = "postgres"
    PASSWORD = "TpsVpUowNnMqSXpvAosQEezxpGPtbPNG"
    DATABASE = "railway"
    
    # Costruisci URL di connessione
    DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?sslmode=require"
    
    # Log di debug
    logger.info("=" * 60)
    logger.info("🔗 Connessione database Railway")
    logger.info(f"Host: {HOST}")
    logger.info(f"Port: {PORT}")
    logger.info(f"User: {USER}")
    logger.info(f"Database: {DATABASE}")
    logger.info("=" * 60)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("✅ Connessione database RIUSCITA")
        return conn
        
    except psycopg2.OperationalError as e:
        logger.error(f"❌ Errore connessione: {e}")
        st.error(f"❌ Errore connessione database: {str(e)}")
        
        if "password authentication failed" in str(e):
            st.info("🔑 **Problema password:**")
            st.info("1. Verifica che la password sia corretta")
            st.info("2. Controlla che non ci siano spazi")
            
        return None
        
    except Exception as e:
        logger.error(f"❌ Errore imprevisto: {e}")
        st.error(f"❌ Errore imprevisto: {str(e)}")
        return None

def init_database():
    """
    Inizializza/verifica il database e crea le tabelle
    """
    logger.info("Inizializzazione database...")
    
    conn = get_database_connection()
    if conn is None:
        return "❌ Impossibile connettersi al database"
    
    try:
        cursor = conn.cursor()
        
        # Verifica versione
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        # 1. Tabella circolari
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
                fonte TEXT DEFAULT 'ARGO',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(titolo, data_pubblicazione)
            );
        """)
        logger.info("Tabella 'circolari' creata/verificata")
        
        # 2. Tabella utenti
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utenti (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                nome TEXT,
                cognome TEXT,
                ruolo TEXT DEFAULT 'lettore',
                attivo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );
        """)
        logger.info("Tabella 'utenti' creata/verificata")
        
        # 3. Tabella logs robot
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS robot_logs (
                id SERIAL PRIMARY KEY,
                tipo TEXT NOT NULL,
                messaggio TEXT,
                dettagli TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Tabella 'robot_logs' creata/verificata")
        
        # 4. Inserisci admin default (password: admin123)
        cursor.execute("""
            INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo)
            VALUES ('admin', 'admin@annafrank.edu.it', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Admin', 'Sistema', 'amministratore')
            ON CONFLICT (username) DO NOTHING;
        """)
        
        # Conta tabelle
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
        table_count = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return f"✅ Database OK! PostgreSQL: {version.split(',')[0]} | Tabelle: {table_count}"
            
    except Exception as e:
        logger.error(f"Errore inizializzazione: {e}")
        return f"❌ Errore inizializzazione: {str(e)}"

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
                   categoria, priorita, firmatario, fonte, created_at
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
        
        # Controlla duplicati
        cursor.execute("SELECT id FROM circolari WHERE titolo = %s AND data_pubblicazione = CURRENT_DATE", (titolo,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return False, "Circolare già esistente oggi"
        
        # Inserisci
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

def get_robot_logs(limit=20):
    """
    Recupera i log del robot
    """
    conn = get_database_connection()
    if conn is None:
        return pd.DataFrame()
    
    try:
        query = "SELECT * FROM robot_logs ORDER BY created_at DESC LIMIT %s;"
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    except Exception as e:
        logger.error(f"Errore recupero log: {e}")
        return pd.DataFrame()
