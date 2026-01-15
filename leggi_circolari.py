import os
import sys
import logging
import json
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
    Connessione al database Railway
    """
    DB_CONFIG = {
        'host': 'switchback.proxy.rlwy.net',
        'port': 53723,
        'database': 'railway',
        'user': 'postgres',
        'password': 'TpsVpUowNnMqSXpvAosQEezxpGPtbPNG',
        'sslmode': 'require'
    }
    
    logger.info(f"Connessione a: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            sslmode=DB_CONFIG['sslmode']
        )
        logger.info("✅ Connessione database OK")
        return conn
    except Exception as e:
        logger.error(f"❌ Errore connessione: {e}")
        return None

def save_circolare(titolo, contenuto, data_pub, file_url=None, firmatario=''):
    """
    Salva una circolare nel database
    """
    conn = get_railway_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Controlla duplicati
        cursor.execute("SELECT id FROM circolari WHERE titolo = %s AND data_pubblicazione = %s", (titolo, data_pub))
        if cursor.fetchone():
            logger.info(f"Circolare già presente: {titolo}")
            cursor.close()
            conn.close()
            return True
        
        # Inserisci
        if file_url:
            cursor.execute("""
                INSERT INTO circolari (titolo, contenuto, data_pubblicazione, file_url, firmatario, fonte)
                VALUES (%s, %s, %s, %s, %s, 'ARGO')
            """, (titolo, contenuto, data_pub, file_url, firmatario))
        else:
            cursor.execute("""
                INSERT INTO circolari (titolo, contenuto, data_pubblicazione, firmatario, fonte)
                VALUES (%s, %s, %s, %s, 'ARGO')
            """, (titolo, contenuto, data_pub, firmatario))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Circolare salvata: {titolo}")
        return True
    except Exception as e:
        logger.error(f"❌ Errore salvataggio: {e}")
        return False

def log_robot(tipo, messaggio, dettagli=None):
    """
    Logga azione robot
    """
    conn = get_railway_connection()
    if conn is None:
        return
    
    try:
        cursor = conn.cursor()
        dettagli_str = json.dumps(dettagli) if dettagli else None
        
        cursor.execute("""
            INSERT INTO robot_logs (tipo, messaggio, dettagli)
            VALUES (%s, %s, %s)
        """, (tipo, messaggio, dettagli_str))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Errore log: {e}")

def main():
    """
    Robot principale
    """
    logger.info("=" * 50)
    logger.info("🤖 ROBOT CIRCOLARI")
    logger.info("=" * 50)
    
    logger.info(f"Inizio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info("-" * 50)
    
    # Simulazione dati (sostituire con ARGO)
    circolari_test = [
        {
            'titolo': 'Circolare Test Robot Railway',
            'contenuto': 'Test inserimento automatico da robot.',
            'data': datetime.now().date(),
            'firmatario': 'Sistema Robot',
            'file_url': None
        }
    ]
    
    # Salva circolari
    salvate = 0
    for circ in circolari_test:
        if save_circolare(
            titolo=circ['titolo'],
            contenuto=circ['contenuto'],
            data_pub=circ['data'],
            file_url=circ['file_url'],
            firmatario=circ['firmatario']
        ):
            salvate += 1
    
    # Log finale
    log_robot(
        tipo='SUCCESS',
        messaggio='Robot completato',
        dettagli={
            'circolari_salvate': salvate,
            'timestamp': datetime.now().isoformat()
        }
    )
    
    logger.info("=" * 50)
    logger.info(f"✅ Robot completato")
    logger.info(f"Circolari salvate: {salvate}")
    logger.info("=" * 50)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Errore critico: {e}")
        log_robot('ERROR', f'Errore critico: {str(e)}')
        sys.exit(1)
