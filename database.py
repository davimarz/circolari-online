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
        logger.info("Connessione al database stabilita")
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
            # Crea la tabella circolari se non esiste
            cur.execute("""
                CREATE TABLE IF NOT EXISTS circolari (
                    id SERIAL PRIMARY KEY,
                    numero VARCHAR(50),
                    titolo TEXT NOT NULL,
                    data_pubblicazione DATE NOT NULL,
                    allegati TEXT,
                    categoria VARCHAR(100),
                    autore VARCHAR(200),
                    contenuto TEXT,
                    url_originale TEXT,
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
    Recupera TUTTE le circolari dal database.
    Versione FLESSIBILE che funziona con qualsiasi schema.
    """
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            # Prova a selezionare tutte le colonne disponibili
            cur.execute("""
                SELECT 
                    COALESCE(numero, '') as numero,
                    titolo,
                    data_pubblicazione,
                    COALESCE(allegati, '') as allegati,
                    COALESCE(categoria, '') as categoria,
                    COALESCE(autore, '') as autore,
                    COALESCE(contenuto, '') as contenuto
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
