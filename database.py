import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        # Usa DATABASE_URL
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        else:
            # Fallback a parametri separati
            conn = psycopg2.connect(
                host=os.environ.get("DB_HOST"),
                port=os.environ.get("DB_PORT"),
                database=os.environ.get("DB_NAME"),
                user=os.environ.get("DB_USER"),
                password=os.environ.get("DB_PASSWORD"),
                cursor_factory=RealDictCursor
            )
        return conn
    except Exception as e:
        logger.error(f"Errore di connessione al database: {e}")
        return None

def get_circolari():
    """
    Recupera TUTTE le circolari dal database.
    Versione per schema SEMPLICE del database.
    """
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            # Query per lo schema SEMPLICE (senza numero, categoria, autore)
            cur.execute("""
                SELECT 
                    id,
                    titolo,
                    contenuto,
                    data_pubblicazione,
                    allegati,
                    created_at
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
