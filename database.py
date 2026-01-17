import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        else:
            conn = psycopg2.connect(
                host=os.environ.get("DB_HOST"),
                port=os.environ.get("DB_PORT"),
                database=os.environ.get("DB_NAME"),
                user=os.environ.get("DB_USER"),
                password=os.environ.get("DB_PASSWORD"),
                cursor_factory=RealDictCursor
            )
        logger.info("Connessione al database stabilita")
        return conn
    except Exception as e:
        logger.error(f"Errore di connessione al database: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        with conn.cursor() as cur:
            # Tabella FLESSIBILE - si adatta allo schema esistente
            cur.execute("""
                CREATE TABLE IF NOT EXISTS circolari (
                    id SERIAL PRIMARY KEY,
                    titolo TEXT NOT NULL,
                    contenuto TEXT,
                    data_pubblicazione DATE NOT NULL,
                    allegati TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info("Tabella circolari verificata/creata")
        return True
    except Exception as e:
        logger.error(f"Errore nell'inizializzazione del DB: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_circolari():
    """
    Recupera circolari in modo FLESSIBILE.
    """
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            # Prova prima con tutte le colonne, poi con meno colonne
            try:
                cur.execute("""
                    SELECT * FROM circolari 
                    ORDER BY data_pubblicazione DESC
                """)
            except:
                # Se fallisce, prova con colonne base
                cur.execute("""
                    SELECT titolo, contenuto, data_pubblicazione, allegati, created_at
                    FROM circolari 
                    ORDER BY data_pubblicazione DESC
                """)
            
            circolari = cur.fetchall()
            logger.info(f"Recuperate {len(circolari)} circolari")
            return circolari
    except Exception as e:
        logger.error(f"Errore nel recupero delle circolari: {e}")
        return []
    finally:
        conn.close()
