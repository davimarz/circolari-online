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
        # Usa DATABASE_URL se disponibile (Railway/GitHub Actions)
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        else:
            # Altrimenti usa parametri separati (locale)
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
            # Tabella ottimizzata per ARGO
            cur.execute("""
                CREATE TABLE IF NOT EXISTS circolari (
                    id SERIAL PRIMARY KEY,
                    titolo TEXT NOT NULL,
                    contenuto TEXT,
                    data_pubblicazione DATE NOT NULL,
                    allegati TEXT,
                    pdf_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Indici per performance
                    CONSTRAINT unique_circolare UNIQUE(titolo, data_pubblicazione)
                )
            """)
            
            # Crea indice per ricerca veloce
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_circolari_data 
                ON circolari(data_pubblicazione DESC)
            """)
            
            conn.commit()
            logger.info("✅ Tabella circolari verificata/creata")
        
        return True
    except Exception as e:
        logger.error(f"Errore nell'inizializzazione del DB: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_circolari(limite=None):
    """
    Recupera le circolari dal database.
    """
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            if limite:
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
                    ORDER BY data_pubblicazione DESC
                    LIMIT %s
                """, (limite,))
            else:
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

def get_circolari_recenti(limite=50):
    """
    Recupera le circolari più recenti.
    """
    return get_circolari(limite=limite)
