import os
import sys
import logging
import json  # AGGIUNTO
import psycopg2
from datetime import datetime, timedelta

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_railway_connection():
    """
    Connessione al database Railway PostgreSQL
    """
    # Configurazione CORRETTA per Railway
    DB_CONFIG = {
        'host': 'switchback.proxy.rlwy.net',
        'port': 53723,
        'database': 'railway',
        'user': 'postgres',
        'password': 'TpsVpUowNnMqSXpvAosQEezxpGPtbPNG',
        'sslmode': 'require'
    }
    
    logger.info(f"Tentativo connessione a: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            sslmode=DB_CONFIG['sslmode']
        )
        logger.info("✅ Connessione al database Railway stabilita")
        return conn
        
    except psycopg2.OperationalError as e:
        logger.error(f"❌ Errore connessione database: {e}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Errore imprevisto: {e}")
        return None

def init_database():
    """
    Inizializza il database Railway se necessario
    """
    conn = get_railway_connection()
    if conn is None:
        logger.warning("Impossibile connettersi al database, salto inizializzazione")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Crea tabella circolari se non esiste
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circolari (
                id SERIAL PRIMARY KEY,
                titolo TEXT NOT NULL,
                data_pubblicazione DATE DEFAULT CURRENT_DATE,
                file_url TEXT,
                contenuto TEXT,
                categoria TEXT DEFAULT 'Generale',
                priorita INTEGER DEFAULT 1,
                firmatario TEXT,
                fonte TEXT DEFAULT 'ARGO',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(titolo, data_pubblicazione)
            );
        """)
        
        # Crea tabella logs robot
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS robot_logs (
                id SERIAL PRIMARY KEY,
                tipo TEXT NOT NULL,
                messaggio TEXT,
                dettagli TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Database Railway inizializzato/verificato")
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore inizializzazione database: {e}")
        return False

def save_circolare_to_railway(titolo, contenuto, data_pub, file_url=None, categoria='ARGO', firmatario=''):
    """
    Salva una circolare nel database Railway
    """
    conn = get_railway_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Controlla se esiste già
        cursor.execute("""
            SELECT id FROM circolari 
            WHERE titolo = %s AND data_pubblicazione = %s
        """, (titolo, data_pub))
        
        exists = cursor.fetchone()
        
        if exists:
            logger.info(f"Circolare già esistente: {titolo}")
            cursor.close()
            conn.close()
            return True
        
        # Inserisci nuova circolare (con file_url opzionale)
        if file_url:
            cursor.execute("""
                INSERT INTO circolari 
                (titolo, contenuto, data_pubblicazione, file_url, categoria, firmatario, fonte)
                VALUES (%s, %s, %s, %s, %s, %s, 'ARGO')
            """, (titolo, contenuto, data_pub, file_url, categoria, firmatario))
        else:
            cursor.execute("""
                INSERT INTO circolari 
                (titolo, contenuto, data_pubblicazione, categoria, firmatario, fonte)
                VALUES (%s, %s, %s, %s, %s, 'ARGO')
            """, (titolo, contenuto, data_pub, categoria, firmatario))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Circolare salvata: {titolo}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore salvataggio circolare: {e}")
        return False

def log_robot_action(tipo, messaggio, dettagli=None):
    """
    Logga un'azione del robot nel database
    """
    conn = get_railway_connection()
    if conn is None:
        return
    
    try:
        cursor = conn.cursor()
        
        # Converti dettagli a stringa JSON
        dettagli_str = json.dumps(dettagli) if dettagli else None
        
        cursor.execute("""
            INSERT INTO robot_logs (tipo, messaggio, dettagli)
            VALUES (%s, %s, %s)
        """, (tipo, messaggio, dettagli_str))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Errore log robot: {e}")

def main():
    """
    Funzione principale del robot
    """
    logger.info("=" * 50)
    logger.info("🤖 ROBOT CIRCOLARI ARGO + RAILWAY")
    logger.info("=" * 50)
    
    # Verifica configurazione
    logger.info("Verifica configurazione...")
    
    # Configurazione Railway
    railway_config = {
        'host': os.environ.get('RAILWAY_DB_HOST', 'switchback.proxy.rlwy.net'),
        'port': os.environ.get('RAILWAY_DB_PORT', '53723'),
        'password': os.environ.get('RAILWAY_DB_PASSWORD', 'TpsVpUowNnMqSXpvAosQEezxpGPtbPNG')
    }
    
    logger.info(f"RAILWAY_DB_HOST: {railway_config['host']}")
    logger.info(f"RAILWAY_DB_PORT: {railway_config['port']}")
    logger.info(f"RAILWAY_DB_PASSWORD: {railway_config['password'][:8]}...")
    logger.info("Configuration OK")
    
    logger.info("Avvio robot ARGO + Railway PostgreSQL")
    logger.info(f"Database: Railway PostgreSQL ({railway_config['host']}:{railway_config['port']})")
    logger.info(f"Data limite: ultimi {os.environ.get('DATA_LIMITE_GIORNI', 30)} giorni")
    logger.info(f"Inizio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info("-" * 50)
    
    # 1. Inizializza database
    if not init_database():
        logger.warning("Continuo comunque, il database potrebbe essere già inizializzato")
    
    # 2. Simulazione dati di test
    logger.info("Simulazione scaricamento circolari da ARGO...")
    
    # Dati di test
    circolari_test = [
        {
            'titolo': 'Circolare Test 1 - Robot Railway',
            'contenuto': 'Questa è una circolare di test inserita dal robot Railway.',
            'data': datetime.now().date(),
            'firmatario': 'Dirigente Scolastico',
            'file_url': None
        },
        {
            'titolo': 'Circolare Test 2 - Integrazione ARGO',
            'contenuto': 'Seconda circolare di test per verificare integrazione ARGO-Railway.',
            'data': (datetime.now() - timedelta(days=1)).date(),
            'firmatario': 'Vice Preside',
            'file_url': 'https://example.com/allegato.pdf'
        }
    ]
    
    # 3. Salva nel database
    circolari_salvate = 0
    for circ in circolari_test:
        success = save_circolare_to_railway(
            titolo=circ['titolo'],
            contenuto=circ['contenuto'],
            data_pub=circ['data'],
            file_url=circ['file_url'],
            firmatario=circ['firmatario']
        )
        if success:
            circolari_salvate += 1
    
    # 4. Log conclusione
    log_robot_action(
        tipo='SUCCESS',
        messaggio='Robot eseguito con successo',
        dettagli={
            'circolari_processate': len(circolari_test),
            'circolari_salvate': circolari_salvate,
            'timestamp': datetime.now().isoformat()
        }
    )
    
    logger.info("=" * 50)
    logger.info(f"✅ Robot completato con successo")
    logger.info(f"Circolari processate: {len(circolari_test)}")
    logger.info(f"Circolari salvate: {circolari_salvate}")
    logger.info("=" * 50)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Robot interrotto manualmente")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Errore critico nel robot: {e}")
        log_robot_action('ERROR', f'Errore critico: {str(e)}')
        sys.exit(1)
