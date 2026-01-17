import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    """Connessione al database"""
    try:
        return psycopg2.connect(
            os.environ.get("DATABASE_URL"),
            cursor_factory=RealDictCursor
        )
    except:
        return None

def init_db():
    """Crea tabella se non esiste"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS circolari (
                    id SERIAL PRIMARY KEY,
                    titolo TEXT NOT NULL,
                    contenuto TEXT NOT NULL,
                    data_pubblicazione DATE NOT NULL,
                    allegati TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(titolo, data_pubblicazione)
                )
            """)
            conn.commit()
        return True
    except Exception as e:
        print(f"DB Error: {e}")
        return False
    finally:
        conn.close()

def pulisci_vecchie():
    """Elimina circolari > 30 giorni"""
    conn = get_connection()
    if not conn:
        return 0
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM circolari 
                WHERE data_pubblicazione < CURRENT_DATE - INTERVAL '30 days'
            """)
            eliminate = cur.rowcount
            conn.commit()
            return eliminate
    except:
        return 0
    finally:
        conn.close()

def get_circolari_ultimi_30_giorni():
    """Recupera circolari degli ultimi 30 giorni"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    titolo,
                    contenuto,
                    data_pubblicazione,
                    allegati,
                    TO_CHAR(data_pubblicazione, 'DD/MM/YYYY') as data_formattata,
                    EXTRACT(DAY FROM CURRENT_DATE - data_pubblicazione)::integer as giorni_fa
                FROM circolari 
                WHERE data_pubblicazione >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY data_pubblicazione DESC, id DESC
            """)
            return cur.fetchall()
    except:
        return []
    finally:
        conn.close()

def salva_circolare(titolo, contenuto, data_pubblicazione, allegati=""):
    """Salva una nuova circolare"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO circolari (titolo, contenuto, data_pubblicazione, allegati)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (titolo, data_pubblicazione) DO NOTHING
                RETURNING id
            """, (titolo, contenuto, data_pubblicazione, allegati))
            conn.commit()
            return cur.fetchone() is not None
    except:
        return False
    finally:
        conn.close()
