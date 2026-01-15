import os
import psycopg2
from psycopg2 import pool
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pool di connessioni
connection_pool = None

def init_connection_pool():
    """Inizializza il pool di connessioni al database"""
    global connection_pool
    try:
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL non configurato")
            return None
        
        # Crea pool di connessioni
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20, DATABASE_URL
        )
        logger.info("✅ Pool di connessioni inizializzato")
        return connection_pool
    except Exception as e:
        logger.error(f"❌ Errore inizializzazione pool: {e}")
        return None

def get_connection():
    """Ottiene una connessione dal pool"""
    global connection_pool
    if connection_pool is None:
        connection_pool = init_connection_pool()
    
    try:
        return connection_pool.getconn()
    except Exception as e:
        logger.error(f"❌ Errore ottenimento connessione: {e}")
        # Fallback a connessione diretta
        DATABASE_URL = os.environ.get('DATABASE_URL')
        return psycopg2.connect(DATABASE_URL)

def release_connection(conn):
    """Rilascia una connessione nel pool"""
    global connection_pool
    if connection_pool and conn:
        try:
            connection_pool.putconn(conn)
        except:
            conn.close()

def init_db():
    """Inizializza il database e crea le tabelle se non esistono"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Crea tabella circolari con tutte le colonne necessarie
        cur.execute('''
            CREATE TABLE IF NOT EXISTS circolari (
                id SERIAL PRIMARY KEY,
                data_pubblicazione DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                titolo TEXT NOT NULL,
                contenuto TEXT,
                pdf_url TEXT,
                fonte TEXT DEFAULT 'sito_scuola'
            )
        ''')
        
        # Se la tabella esiste già, aggiungi la colonna 'fonte' se manca
        try:
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name = 'circolari' 
                        AND column_name = 'fonte'
                    ) THEN
                        ALTER TABLE circolari ADD COLUMN fonte TEXT DEFAULT 'sito_scuola';
                        RAISE NOTICE 'Colonna fonte aggiunta';
                    END IF;
                END $$;
            """)
        except Exception as e:
            logger.info(f"Nota colonna fonte: {e}")
        
        # Crea indice per ottimizzare le ricerche
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_circolari_data 
            ON circolari(data_pubblicazione DESC)
        ''')
        
        conn.commit()
        logger.info("✅ Database inizializzato correttamente")
        
    except Exception as e:
        logger.error(f"❌ Errore inizializzazione database: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            release_connection(conn)

def test_connection():
    """Testa la connessione al database"""
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

def get_all_circolari():
    """Recupera tutte le circolari"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT id, titolo, contenuto, data_pubblicazione, pdf_url, fonte
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
                'pdf_url': circ[4],
                'fonte': circ[5] if circ[5] else 'sito_scuola'
            })
        return result
    except Exception as e:
        logger.error(f"❌ Errore recupero circolari: {e}")
        return []
    finally:
        if conn:
            release_connection(conn)

def salva_circolare_db(titolo, contenuto, data_pubblicazione, pdf_url=None, fonte='sito_scuola'):
    """Salva una nuova circolare nel database"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Controlla se esiste già una circolare con lo stesso titolo e data
        cur.execute('''
            SELECT COUNT(*) FROM circolari 
            WHERE titolo = %s AND data_pubblicazione = %s
        ''', (titolo, data_pubblicazione))
        
        if cur.fetchone()[0] > 0:
            logger.info(f"⚠️ Circolare già esistente: {titolo}")
            return False
        
        # Inserisci nuova circolare
        cur.execute('''
            INSERT INTO circolari 
            (titolo, contenuto, data_pubblicazione, pdf_url, fonte)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        ''', (titolo, contenuto, data_pubblicazione, pdf_url, fonte))
        
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

def elimina_circolare_db(circolare_id):
    """Elimina una circolare dal database"""
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
