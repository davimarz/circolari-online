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
    Connessione ROBUSTA al database
    """
    DB_CONFIG = {
        'host': 'switchback.proxy.rlwy.net',
        'port': 53723,
        'database': 'railway',
        'user': 'postgres',
        'password': 'TpsVpUowNnMqSXpvAosQEezxpGPtbPNG',
        'sslmode': 'require'
    }
    
    logger.info(f"🔗 Connessione a: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    
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

def save_circolare_safe(titolo, contenuto, data_pub, file_url=None, firmatario=''):
    """
    Salvataggio SICURO - adatta alla struttura del database
    """
    conn = get_railway_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # 1. Controlla se esiste già
        cursor.execute("""
            SELECT id FROM circolari 
            WHERE titolo = %s AND data_pubblicazione = %s
        """, (titolo, data_pub))
        
        if cursor.fetchone():
            logger.info(f"📌 Circolare già presente: {titolo}")
            cursor.close()
            conn.close()
            return True
        
        # 2. Costruisci query dinamica in base alle colonne disponibili
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'circolari'
            ORDER BY column_name;
        """)
        
        available_columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"📊 Colonne disponibili: {available_columns}")
        
        # 3. Costruisci query in base alle colonne
        if 'firmatario' in available_columns and 'file_url' in available_columns:
            cursor.execute("""
                INSERT INTO circolari (titolo, contenuto, data_pubblicazione, file_url, firmatario, fonte)
                VALUES (%s, %s, %s, %s, %s, 'ROBOT')
                RETURNING id;
            """, (titolo, contenuto, data_pub, file_url, firmatario))
        elif 'firmatario' in available_columns:
            cursor.execute("""
                INSERT INTO circolari (titolo, contenuto, data_pubblicazione, firmatario, fonte)
                VALUES (%s, %s, %s, %s, 'ROBOT')
                RETURNING id;
            """, (titolo, contenuto, data_pub, firmatario))
        else:
            cursor.execute("""
                INSERT INTO circolari (titolo, contenuto, data_pubblicazione, fonte)
                VALUES (%s, %s, %s, 'ROBOT')
                RETURNING id;
            """, (titolo, contenuto, data_pub))
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Circolare salvata (ID: {new_id}): {titolo}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore salvataggio: {e}")
        
        # Tentativo di fix automatico
        try:
            logger.info("🛠️ Tentativo fix automatico...")
            cursor.execute("ALTER TABLE circolari ADD COLUMN IF NOT EXISTS firmatario TEXT;")
            conn.commit()
            logger.info("✅ Colonna 'firmatario' aggiunta")
            
            # Riprova inserimento
            cursor.execute("""
                INSERT INTO circolari (titolo, contenuto, data_pubblicazione, firmatario, fonte)
                VALUES (%s, %s, %s, %s, 'ROBOT')
            """, (titolo, contenuto, data_pub, firmatario))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"✅ Circolare salvata dopo fix: {titolo}")
            return True
            
        except Exception as fix_error:
            logger.error(f"❌ Fix fallito: {fix_error}")
            return False

def log_robot_action(tipo, messaggio, dettagli=None):
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

def check_database_structure():
    """
    Verifica struttura database
    """
    conn = get_railway_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Verifica tabella circolari
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'circolari'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'circolari';")
            columns = [row[0] for row in cursor.fetchall()]
            logger.info(f"✅ Tabella 'circolari' esiste. Colonne: {', '.join(columns)}")
        else:
            logger.warning("⚠️ Tabella 'circolari' non esiste")
        
        cursor.close()
        conn.close()
        return table_exists
        
    except Exception as e:
        logger.error(f"Errore verifica struttura: {e}")
        return False

def main():
    """
    Robot principale - VERSIONE ROBUSTA
    """
    logger.info("=" * 60)
    logger.info("🤖 ROBOT CIRCOLARI - VERSIONE ROBUSTA")
    logger.info("=" * 60)
    
    logger.info(f"🚀 Inizio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info("-" * 60)
    
    # 1. Verifica struttura database
    logger.info("🔍 Verifica struttura database...")
    if not check_database_structure():
        logger.warning("⚠️ Problema con il database, continuo comunque")
    
    # 2. Dati di test (sostituire con ARGO)
    circolari_test = [
        {
            'titolo': 'Circolare Test Robot ' + datetime.now().strftime('%H:%M'),
            'contenuto': f'Test automatico inserito dal robot alle {datetime.now().strftime("%H:%M")}.',
            'data': datetime.now().date(),
            'firmatario': 'Sistema Automatico',
            'file_url': None
        }
    ]
    
    # 3. Salva circolari
    salvate = 0
    for circ in circolari_test:
        logger.info(f"💾 Tentativo salvataggio: {circ['titolo']}")
        
        if save_circolare_safe(
            titolo=circ['titolo'],
            contenuto=circ['contenuto'],
            data_pub=circ['data'],
            file_url=circ['file_url'],
            firmatario=circ['firmatario']
        ):
            salvate += 1
            logger.info(f"   → ✅ Salvata")
        else:
            logger.info(f"   → ❌ Fallita")
    
    # 4. Log finale
    log_robot_action(
        tipo='SUCCESS',
        messaggio=f'Robot completato - {salvate}/{len(circolari_test)} salvate',
        dettagli={
            'circolari_totali': len(circolari_test),
            'circolari_salvate': salvate,
            'data': datetime.now().isoformat()
        }
    )
    
    logger.info("=" * 60)
    logger.info(f"🏁 ROBOT COMPLETATO")
    logger.info(f"   Successi: {salvate}/{len(circolari_test)}")
    logger.info(f"   Ora: {datetime.now().strftime('%H:%M:%S')}")
    logger.info("=" * 60)
    
    return salvate > 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("⏹️ Robot interrotto")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 ERRORE CRITICO: {e}")
        log_robot_action('ERROR', f'Errore critico: {str(e)}')
        sys.exit(1)
