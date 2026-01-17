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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Vincolo unico per evitare duplicati
                    CONSTRAINT unique_circolare_titolo_data UNIQUE(titolo, data_pubblicazione)
                )
            """)
            
            # Indice per ricerca per data (ottimizzato per ordine decrescente)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_circolari_data_desc 
                ON circolari(data_pubblicazione DESC, id DESC)
            """)
            
            # Indice per pulizia automatica (>30 giorni)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_circolari_data_cleanup 
                ON circolari(data_pubblicazione)
                WHERE data_pubblicazione < CURRENT_DATE - INTERVAL '30 days'
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

def pulisci_circolari_vecchie():
    """
    Elimina automaticamente le circolari con più di 30 giorni.
    """
    conn = get_db_connection()
    if conn is None:
        return 0
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM circolari 
                WHERE data_pubblicazione < CURRENT_DATE - INTERVAL '30 days'
                RETURNING id
            """)
            
            eliminate = cur.rowcount
            conn.commit()
            
            if eliminate > 0:
                logger.info(f"🧹 Eliminate {eliminate} circolari vecchie (>30 giorni)")
            
            return eliminate
    except Exception as e:
        logger.error(f"Errore nella pulizia circolari vecchie: {e}")
        return 0
    finally:
        conn.close()

def get_circolari_ultimi_30_giorni(limite=None):
    """
    Recupera le circolari degli ultimi 30 giorni in ordine decrescente di data.
    """
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            query = """
                SELECT 
                    id,
                    titolo,
                    contenuto,
                    data_pubblicazione,
                    allegati,
                    pdf_url,
                    created_at,
                    TO_CHAR(data_pubblicazione, 'DD/MM/YYYY') as data_formattata,
                    EXTRACT(DAY FROM CURRENT_DATE - data_pubblicazione)::integer as giorni_fa,
                    CASE 
                        WHEN data_pubblicazione = CURRENT_DATE THEN 'Oggi'
                        WHEN data_pubblicazione = CURRENT_DATE - 1 THEN 'Ieri'
                        ELSE TO_CHAR(data_pubblicazione, 'DD/MM/YYYY')
                    END as data_visualizzazione
                FROM circolari 
                WHERE data_pubblicazione >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY data_pubblicazione DESC, id DESC
            """
            
            if limite:
                query += f" LIMIT {limite}"
            
            cur.execute(query)
            circolari = cur.fetchall()
            logger.info(f"Recuperate {len(circolari)} circolari (ultimi 30 giorni)")
            return circolari
    except Exception as e:
        logger.error(f"Errore nel recupero delle circolari: {e}")
        return []
    finally:
        conn.close()

def get_circolari_per_data(data_inizio=None, data_fine=None):
    """
    Recupera circolari per intervallo di date.
    """
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        with conn.cursor() as cur:
            if data_inizio and data_fine:
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
                    WHERE data_pubblicazione BETWEEN %s AND %s
                    ORDER BY data_pubblicazione DESC, id DESC
                """, (data_inizio, data_fine))
            elif data_inizio:
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
                    WHERE data_pubblicazione >= %s
                    ORDER BY data_pubblicazione DESC, id DESC
                """, (data_inizio,))
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
                    ORDER BY data_pubblicazione DESC, id DESC
                """)
            
            circolari = cur.fetchall()
            return circolari
    except Exception as e:
        logger.error(f"Errore nel recupero circolari per data: {e}")
        return []
    finally:
        conn.close()

def get_statistiche():
    """
    Restituisce statistiche sulle circolari.
    """
    conn = get_db_connection()
    if conn is None:
        return {}
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as totale,
                    COUNT(CASE WHEN data_pubblicazione >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as ultimi_30_giorni,
                    COUNT(CASE WHEN data_pubblicazione = CURRENT_DATE THEN 1 END) as oggi,
                    COUNT(CASE WHEN allegati IS NOT NULL AND allegati != '' THEN 1 END) as con_allegati,
                    MIN(data_pubblicazione) as data_prima,
                    MAX(data_pubblicazione) as data_ultima
                FROM circolari
            """)
            
            stats = cur.fetchone()
            return dict(stats) if stats else {}
    except Exception as e:
        logger.error(f"Errore nel recupero statistiche: {e}")
        return {}
    finally:
        conn.close()

# Alias per compatibilità
get_circolari = get_circolari_ultimi_30_giorni
get_circolari_recenti = get_circolari_ultimi_30_giorni
