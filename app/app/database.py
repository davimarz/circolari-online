import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

class DatabaseManager:
    """Gestore database PostgreSQL online"""
    
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
    
    def get_connection(self):
        """Ottieni connessione al database"""
        try:
            conn = psycopg2.connect(self.database_url, sslmode='require')
            return conn
        except Exception as e:
            print(f"❌ Errore connessione database: {e}")
            return None
    
    def init_database(self):
        """Inizializza le tabelle nel database"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Tabella circolari
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS circolari (
                    id SERIAL PRIMARY KEY,
                    titolo TEXT NOT NULL,
                    contenuto TEXT,
                    data_pubblicazione TIMESTAMP NOT NULL,
                    pdf_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(titolo, data_pubblicazione)
                )
            """)
            
            # Indici per performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_circolari_data 
                ON circolari(data_pubblicazione DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_circolari_created 
                ON circolari(created_at DESC)
            """)
            
            # Tabella log robot
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS robot_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT,
                    nuove_circolari INTEGER DEFAULT 0,
                    errore TEXT
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("✅ Database inizializzato su Neon.tech")
            return True
            
        except Exception as e:
            print(f"❌ Errore inizializzazione database: {e}")
            return False
    
    def salva_circolare(self, circolare):
        """Salva una circolare nel database"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Verifica se esiste già
            cursor.execute("""
                SELECT id FROM circolari 
                WHERE titolo = %s AND data_pubblicazione = %s
            """, (circolare['titolo'], circolare['data_pubblicazione']))
            
            if cursor.fetchone():
                print(f"⏭️ Già presente: {circolare['titolo'][:50]}...")
                cursor.close()
                conn.close()
                return True
            
            # Inserisci nuova
            cursor.execute("""
                INSERT INTO circolari (titolo, contenuto, data_pubblicazione, pdf_url)
                VALUES (%s, %s, %s, %s)
            """, (
                circolare['titolo'],
                circolare['contenuto'],
                circolare['data_pubblicazione'],
                circolare.get('pdf_url', '')
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"✅ Salvata online: {circolare['titolo'][:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Errore salvataggio circolare: {e}")
            return False
    
    def log_robot(self, status, nuove_circolari=0, errore=None):
        """Registra log esecuzione robot"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO robot_logs (status, nuove_circolari, errore)
                VALUES (%s, %s, %s)
            """, (status, nuove_circolari, errore))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"📝 Log robot salvato: {status}")
            return True
            
        except Exception as e:
            print(f"❌ Errore salvataggio log: {e}")
            return False

# Istanza globale
db_manager = DatabaseManager()
