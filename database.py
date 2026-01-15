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
    Connessione al database PostgreSQL su Railway
    """
    # Configurazione FISSA per Railway
    HOST = "switchback.proxy.rlwy.net"
    PORT = "53723"
    USER = "postgres"
    PASSWORD = "TpsVpUowNnMqSXpvAosQEezxpGPtbPNG"
    DATABASE = "railway"
    
    # Costruisci URL
    DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?sslmode=require"
    
    logger.info("=" * 60)
    logger.info("🔗 Connessione database Railway")
    logger.info(f"Host: {HOST}:{PORT}")
    logger.info("=" * 60)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("✅ Connessione RIUSCITA")
        return conn
    except Exception as e:
        logger.error(f"❌ Errore connessione: {e}")
        st.error(f"❌ Errore database: {str(e)}")
        return None

def init_database():
    """
    INIZIALIZZAZIONE COMPLETA DEL DATABASE
    Crea/Aggiorna tutte le tabelle e colonne
    """
    logger.info("🔄 INIZIALIZZAZIONE DATABASE COMPLETA")
    
    conn = get_database_connection()
    if conn is None:
        return "❌ Connessione fallita"
    
    try:
        cursor = conn.cursor()
        
        # 1. Crea tabella circolari COMPLETA
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
        logger.info("✅ Tabella 'circolari' creata/verificata")
        
        # 2. AGGIUNGI COLONNE MANCANTI (se la tabella esisteva già)
        columns_to_add = [
            ('firmatario', 'TEXT'),
            ('fonte', 'TEXT DEFAULT ''ARGO'''),
            ('file_url', 'TEXT'),
            ('categoria', 'TEXT DEFAULT ''Generale'''),
            ('priorita', 'INTEGER DEFAULT 1')
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                cursor.execute(f"""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name='circolari' AND column_name='{col_name}'
                        ) THEN
                            EXECUTE 'ALTER TABLE circolari ADD COLUMN {col_name} {col_type}';
                            RAISE NOTICE 'Colonna {col_name} aggiunta';
                        END IF;
                    END $$;
                """)
                logger.info(f"   → Colonna '{col_name}' verificata")
            except Exception as e:
                logger.warning(f"   → Colonna '{col_name}': {e}")
        
        # 3. Tabella utenti
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
        logger.info("✅ Tabella 'utenti' creata/verificata")
        
        # 4. Tabella logs robot
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS robot_logs (
                id SERIAL PRIMARY KEY,
                tipo TEXT NOT NULL,
                messaggio TEXT,
                dettagli TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("✅ Tabella 'robot_logs' creata/verificata")
        
        # 5. Admin default
        cursor.execute("""
            INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo)
            VALUES ('admin', 'admin@annafrank.edu.it', 
                    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 
                    'Admin', 'Sistema', 'amministratore')
            ON CONFLICT (username) DO NOTHING;
        """)
        
        # 6. Verifica finale
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
        table_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'circolari';")
        columns = [row[0] for row in cursor.fetchall()]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("=" * 60)
        logger.info(f"✅ DATABASE INIZIALIZZATO CON SUCCESSO")
        logger.info(f"   Tabelle: {table_count}")
        logger.info(f"   Colonne 'circolari': {', '.join(columns)}")
        logger.info("=" * 60)
        
        return f"✅ Database OK! Tabelle: {table_count}, Colonne circolari: {len(columns)}"
            
    except Exception as e:
        logger.error(f"❌ Errore inizializzazione: {e}")
        return f"❌ Errore: {str(e)}"

def test_connection_simple():
    """
    Test semplice connessione
    """
    conn = get_database_connection()
    if conn is None:
        return False, "Connessione fallita"
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test, current_timestamp as time;")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return True, f"✅ Connesso! Ora server: {result[1]}"
    except Exception as e:
        return False, f"❌ Errore: {str(e)}"

def get_circolari(limit=100):
    """
    Recupera circolari
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
        logger.error(f"Errore: {e}")
        return pd.DataFrame()
