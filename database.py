import os
import psycopg2
from psycopg2 import pool, errors
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
        conn.autocommit = True  # IMPORTANTE: permette DDL commands
        cur = conn.cursor()
        
        # 1. Crea tabella se non esiste
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
        
        # 2. VERIFICA e AGGIUNGI colonna 'fonte' se manca
        try:
            # Controlla se la colonna 'fonte' esiste
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'circolari' 
                AND column_name = 'fonte'
            """)
            
            if cur.fetchone() is None:
                # Colonna non esiste, aggiungila
                logger.info("➕ Aggiungo colonna 'fonte' alla tabella...")
                cur.execute('''
                    ALTER TABLE circolari 
                    ADD COLUMN fonte TEXT DEFAULT 'sito_scuola'
                ''')
                logger.info("✅ Colonna 'fonte' aggiunta con successo")
            else:
                logger.info("✅ Colonna 'fonte' già presente")
                
        except Exception as e:
            logger.error(f"⚠️ Errore verifica colonna fonte: {e}")
            # Riprova con metodo alternativo
            try:
                cur.execute("ALTER TABLE circolari ADD COLUMN IF NOT EXISTS fonte TEXT DEFAULT 'sito_scuola'")
                logger.info("✅ Colonna 'fonte' aggiunta (metodo alternativo)")
            except:
                pass
        
        # 3. Crea indice per ottimizzare
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_circolari_data 
            ON circolari(data_pubblicazione DESC)
        ''')
        
        # 4. Mostra struttura finale
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'circolari' 
            ORDER BY ordinal_position
        """)
        
        colonne = cur.fetchall()
        colonne_str = ", ".join([col[0] for col in colonne])
        logger.info(f"📊 Struttura finale tabella: {colonne_str}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore inizializzazione database: {e}")
        return False
    finally:
        if conn:
            release_connection(conn)

def test_connection():
    """Testa la connessione al database"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT version()")
        result = cur.fetchone()
        cur.close()
        logger.info(f"✅ Connessione database OK - {result[0].split(',')[0]}")
        return True
    except Exception as e:
        logger.error(f"❌ Errore connessione database: {e}")
        return False
    finally:
        if conn:
            release_connection(conn)

def verifica_struttura():
    """Verifica la struttura della tabella circolari"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Controlla se la tabella esiste
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'circolari'
            )
        """)
        
        if not cur.fetchone()[0]:
            logger.error("❌ Tabella 'circolari' non esiste")
            return False
        
        # Ottieni tutte le colonne
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'circolari' 
            ORDER BY ordinal_position
        """)
        
        colonne = cur.fetchall()
        logger.info(f"📋 Colonne disponibili: {[col[0] for col in colonne]}")
        
        # Verifica colonne necessarie
        colonne_necessarie = ['titolo', 'contenuto', 'data_pubblicazione', 'fonte']
        colonne_presenti = [col[0] for col in colonne]
        
        for col in colonne_necessarie:
            if col not in colonne_presenti:
                logger.warning(f"⚠️ Colonna mancante: {col}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore verifica struttura: {e}")
        return False
    finally:
        if conn:
            release_connection(conn)

def salva_circolare_db(titolo, contenuto, data_pubblicazione, pdf_url=None, fonte='sito_scuola'):
    """Salva una nuova circolare nel database"""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # PRIMA verifica la struttura
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'circolari'
        """)
        colonne_disponibili = [row[0] for row in cur.fetchall()]
        
        logger.info(f"📊 Colonne disponibili: {colonne_disponibili}")
        
        # Adatta la query in base alle colonne disponibili
        if 'fonte' in colonne_disponibili:
            query = '''
                INSERT INTO circolari (titolo, contenuto, data_pubblicazione, pdf_url, fonte)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            '''
            params = (titolo, contenuto, data_pubblicazione, pdf_url, fonte)
        else:
            # Fallback: senza colonna fonte
            query = '''
                INSERT INTO circolari (titolo, contenuto, data_pubblicazione, pdf_url)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            '''
            params = (titolo, contenuto, data_pubblicazione, pdf_url)
            logger.warning("⚠️ Usando query senza 'fonte' (colonna mancante)")
        
        # Controlla se esiste già
        cur.execute('''
            SELECT COUNT(*) FROM circolari 
            WHERE titolo = %s AND data_pubblicazione = %s
        ''', (titolo, data_pubblicazione))
        
        if cur.fetchone()[0] > 0:
            logger.info(f"⚠️ Circolare già esistente: {titolo}")
            return False
        
        # Esegui inserimento
        cur.execute(query, params)
        circolare_id = cur.fetchone()[0]
        conn.commit()
        
        logger.info(f"✅ Circolare salvata con ID: {circolare_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore salvataggio circolare: {e}")
        if conn:
            conn.rollback()
        
        # Tentativo di fix automatico
        if 'column "fonte" does not exist' in str(e):
            logger.info("🛠️ Tentativo fix automatico colonna 'fonte'...")
            try:
                fix_conn = get_connection()
                fix_conn.autocommit = True
                fix_cur = fix_conn.cursor()
                fix_cur.execute("ALTER TABLE circolari ADD COLUMN IF NOT EXISTS fonte TEXT DEFAULT 'sito_scuola'")
                logger.info("✅ Colonna 'fonte' aggiunta automaticamente")
                fix_cur.close()
                release_connection(fix_conn)
            except Exception as fix_error:
                logger.error(f"❌ Fix automatico fallito: {fix_error}")
        
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
        
        # Verifica colonne disponibili
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'circolari'
        """)
        colonne = [row[0] for row in cur.fetchall()]
        
        # Costruisci query dinamicamente
        if 'fonte' in colonne:
            cur.execute('''
                SELECT id, titolo, contenuto, data_pubblicazione, pdf_url, fonte
                FROM circolari 
                ORDER BY data_pubblicazione DESC
            ''')
        else:
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
            circ_dict = {
                'id': circ[0],
                'titolo': circ[1],
                'contenuto': circ[2],
                'data_pubblicazione': circ[3],
                'pdf_url': circ[4] if len(circ) > 4 else None
            }
            if len(circ) > 5:  # Se c'è la colonna fonte
                circ_dict['fonte'] = circ[5]
            
            result.append(circ_dict)
        
        return result
    except Exception as e:
        logger.error(f"❌ Errore recupero circolari: {e}")
        return []
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
