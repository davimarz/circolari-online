import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Stabilisce una connessione al database PostgreSQL.
    """
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
        return conn
    except Exception as e:
        logger.error(f"Errore di connessione al database: {e}")
        return None

def init_db():
    """
    Inizializza il database creando la tabella se non esiste.
    """
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        with conn.cursor() as cur:
            # Tabella per circolari ARGO
            cur.execute("""
                CREATE TABLE IF NOT EXISTS circolari (
                    id SERIAL PRIMARY KEY,
                    titolo TEXT NOT NULL,
                    contenuto TEXT NOT NULL,
                    data_pubblicazione DATE NOT NULL,
                    allegati TEXT,
                    pdf_url TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Indice per ricerca per data
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_circolari_data 
                ON circolari(data_pubblicazione DESC)
            """)
            
            # Indice per titolo
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_circolari_titolo 
                ON circolari(titolo)
            """)
            
            conn.commit()
            logger.info("✅ Tabella circolari ARGO verificata/creata")
        
        return True
    except Exception as e:
        logger.error(f"Errore nell'inizializzazione del DB: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_circolari_ultimi_30_giorni():
    """
    Recupera le circolari degli ultimi 30 giorni in ordine decrescente di data.
    """
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    id,
                    titolo,
                    contenuto,
                    data_pubblicazione,
                    allegati,
                    pdf_url,
                    created_at,
                    TO_CHAR(data_pubblicazione, 'DD/MM/YYYY') as data_formattata,
                    EXTRACT(DAY FROM CURRENT_DATE - data_pubblicazione) as giorni_fa
                FROM circolari 
                WHERE data_pubblicazione >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY data_pubblicazione DESC, id DESC
            """)
            
            circolari = cur.fetchall()
            logger.info(f"Recuperate {len(circolari)} circolari (ultimi 30 giorni)")
            return circolari
    except Exception as e:
        logger.error(f"Errore nel recupero delle circolari: {e}")
        return []
    finally:
        conn.close()

def get_circolari_tutte():
    """
    Recupera TUTTE le circolari in ordine decrescente di data.
    """
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    id,
                    titolo,
                    contenuto,
                    data_pubblicazione,
                    allegati,
                    pdf_url,
                    created_at,
                    TO_CHAR(data_pubblicazione, 'DD/MM/YYYY') as data_formattata
                FROM circolari 
                ORDER BY data_pubblicazione DESC, id DESC
            """)
            
            circolari = cur.fetchall()
            logger.info(f"Recuperate {len(circolari)} circolari (tutte)")
            return circolari
    except Exception as e:
        logger.error(f"Errore nel recupero delle circolari: {e}")
        return []
    finally:
        conn.close()

# Alias per compatibilità con app.py
get_circolari = get_circolari_ultimi_30_giorni
get_circolari_recenti = get_circolari_ultimi_30_giorni
