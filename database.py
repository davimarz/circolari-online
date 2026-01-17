import psycopg2
from psycopg2.extras import RealDictCursor

# DATABASE CONFIG
DATABASE_URL = "postgresql://postgres:TpsVpUowNnMqSXpvAosQEezxpGPtbPNG@postgres.railway.internal:5432/railway"

def get_db_connection():
    """Connessione al database"""
    try:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"❌ Errore DB: {e}")
        return None

def init_db():
    """Inizializza database"""
    conn = get_db_connection()
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
        print(f"❌ Errore init DB: {e}")
        return False
    finally:
        conn.close()

def get_circolari_ultimi_30_giorni():
    """Recupera circolari ultimi 30 giorni"""
    conn = get_db_connection()
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
    except Exception as e:
        print(f"❌ Errore query: {e}")
        return []
    finally:
        conn.close()

# Alias
get_circolari = get_circolari_ultimi_30_giorni
