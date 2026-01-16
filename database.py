import os
import psycopg2
from psycopg2 import pool
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

connection_pool = None

def init_connection_pool():
    global connection_pool
    try:
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL non configurato")
            return None
        
        connection_pool = psycopg2.pool.SimpleConnectionPool(1, 20, DATABASE_URL)
        logger.info("✅ Pool di connessioni inizializzato")
        return connection_pool
    except Exception as e:
        logger.error(f"❌ Errore inizializzazione pool: {e}")
        return None

def get_connection():
    global connection_pool
    if connection_pool is None:
        connection_pool = init_connection_pool()
    
    try:
        return connection_pool.getconn()
    except Exception as e:
        logger.error(f"❌ Errore ottenimento connessione: {e}")
        DATABASE_URL = os.environ.get('DATABASE_URL')
        return psycopg2.connect(DATABASE_URL)

def release_connection(conn):
    global connection_pool
    if connection_pool and conn:
        try:
            connection_pool.putconn(conn)
        except:
            conn.close()

def init_db():
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS circolari (
                id SERIAL PRIMARY KEY,
                data_pubblicazione DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                titolo TEXT NOT NULL,
                contenuto TEXT,
                pdf_url TEXT
            )
        ''')
        
        conn.commit()
        logger.info("✅ Database inizializzato")
        
    except Exception as e:
        logger.error(f"❌ Errore inizializzazione database: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)

def test_connection():
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        cur.close()
        logger.info("✅ Connessione database OK")
        return True
    except Exception as e:
        logger.error(f"❌ Errore connessione database: {e}")
        return False
    finally:
        if conn:
            release_connection(conn)

def salva_circolare_db(titolo, contenuto, data_pubblicazione, pdf_url=None):
    """Salva una circolare SENZA colonna 'fonte'"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Query SEMPLICE senza 'fonte'
        query = """
            INSERT INTO circolari (titolo, contenuto, data_pubblicazione, pdf_url)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        
        cur.execute(query, (titolo, contenuto, data_pubblicazione, pdf_url))
        circolare_id = cur.fetchone()[0]
        conn.commit()
        
        logger.info(f"✅ Circolare salvata con ID: {circolare_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore salvataggio circolare: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            release_connection(conn)

def get_all_circolari():
    """Recupera tutte le circolari - FUNZIONE MANCANTE!"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT id, titolo, contenuto, data_pubblicazione, pdf_url
            FROM circolari 
            ORDER BY data_pubblicazione DESC
        ''')
        circolari = cur.fetchall()
        cur.close()
        
        # Converti in lista di dizionari
        result = []
        for circ in circolari:
            result.append({
                'id': circ[0],
                'titolo': circ[1],
                'contenuto': circ[2],
                'data_pubblicazione': circ[3],
                'pdf_url': circ[4]
            })
        return result
    except Exception as e:
        logger.error(f"❌ Errore recupero circolari: {e}")
        return []
    finally:
        if conn:
            release_connection(conn)

def elimina_circolare_db(circolare_id):
    """Elimina una circolare"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM circolari WHERE id = %s', (circolare_id,))
        conn.commit()
        logger.info(f"✅ Circolare {circolare_id} eliminata")
        return True
    except Exception as e:
        logger.error(f"❌ Errore eliminazione circolare: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            release_connection(conn)

# Inizializza il database all'importazione
init_db()
