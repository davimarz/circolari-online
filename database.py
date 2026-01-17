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

def save_circolari(circolari_list):
    """
    Salva una lista di circolari nel database.
    """
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        with conn.cursor() as cur:
            for circolare in circolari_list:
                # Controlla se la circolare esiste già
                cur.execute("""
                    SELECT id FROM circolari 
                    WHERE numero = %s AND data_pubblicazione = %s
                """, (circolare.get('numero'), circolare.get('data_pubblicazione')))
                
                if cur.fetchone() is None:
                    # Inserisce nuova circolare
                    cur.execute("""
                        INSERT INTO circolari 
                        (numero, titolo, data_pubblicazione, allegati, categoria, autore, contenuto, url_originale)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        circolare.get('numero'),
                        circolare.get('titolo'),
                        circolare.get('data_pubblicazione'),
                        circolare.get('allegati'),
                        circolare.get('categoria'),
                        circolare.get('autore'),
                        circolare.get('contenuto'),
                        circolare.get('url_originale')
                    ))
        
        conn.commit()
        logger.info(f"Salvate {len(circolari_list)} circolari nel database")
        return True
    except Exception as e:
        logger.error(f"Errore nel salvataggio delle circolari: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_circolari(filtro_categoria=None):
    """
    Recupera le circolari dal database con eventuale filtro per categoria.
    """
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            if filtro_categoria:
                cur.execute("""
                    SELECT numero, titolo, data_pubblicazione, allegati, categoria, autore, contenuto
                    FROM circolari 
                    WHERE categoria = %s
                    ORDER BY data_pubblicazione DESC
                """, (filtro_categoria,))
            else:
                cur.execute("""
                    SELECT numero, titolo, data_pubblicazione, allegati, categoria, autore, contenuto
                    FROM circolari 
                    ORDER BY data_pubblicazione DESC
                """)
            
            circolari = cur.fetchall()
            return circolari
    except Exception as e:
        logger.error(f"Errore nel recupero delle circolari: {e}")
        return []
    finally:
        conn.close()
