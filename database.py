import os
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Configurazione database Railway
DATABASE_URL = "postgresql://postgres:TpsVpUowNnMqSXpvAosQEezxpGPtbPNG@postgres.railway.internal:5432/railway"

def get_connection():
    """Crea connessione al database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Errore connessione database: {e}")
        return None

def get_circolari_recenti(limit=50):
    """Ottiene le circolari più recenti"""
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = """
            SELECT 
                id, titolo, contenuto, categoria, 
                data_pubblicazione, data_scaricamento,
                allegati
            FROM circolari 
            ORDER BY data_pubblicazione DESC, data_scaricamento DESC
            LIMIT %s
        """
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        return df
    except Exception as e:
        print(f"Errore query circolari: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_statistiche():
    """Ottiene statistiche delle circolari"""
    conn = get_connection()
    if not conn:
        return {}
    
    try:
        cursor = conn.cursor()
        
        # Totale circolari
        cursor.execute("SELECT COUNT(*) FROM circolari")
        totale = cursor.fetchone()[0]
        
        # Ultimi 7 giorni
        cursor.execute("""
            SELECT COUNT(*) FROM circolari 
            WHERE data_pubblicazione >= CURRENT_DATE - INTERVAL '7 days'
        """)
        ultima_settimana = cursor.fetchone()[0]
        
        # Per categoria
        cursor.execute("""
            SELECT categoria, COUNT(*) as count 
            FROM circolari 
            GROUP BY categoria 
            ORDER BY count DESC
        """)
        categorie = dict(cursor.fetchall())
        
        # Ultima circolare
        cursor.execute("""
            SELECT MAX(data_pubblicazione) FROM circolari
        """)
        ultima_data = cursor.fetchone()[0]
        
        return {
            "totale": totale,
            "ultima_settimana": ultima_settimana,
            "categorie": categorie,
            "ultima_data": ultima_data
        }
        
    except Exception as e:
        print(f"Errore statistiche: {e}")
        return {}
    finally:
        conn.close()

def get_logs_robot(limit=20):
    """Ottiene i log del robot"""
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = """
            SELECT 
                timestamp, azione, 
                circolari_processate, circolari_scartate,
                errore
            FROM robot_logs 
            ORDER BY timestamp DESC
            LIMIT %s
        """
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        return df
    except Exception as e:
        print(f"Errore query logs: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def inizializza_database():
    """Inizializza il database se non esiste"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Tabella circolari
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circolari (
                id SERIAL PRIMARY KEY,
                titolo VARCHAR(500) NOT NULL,
                contenuto TEXT,
                categoria VARCHAR(100),
                data_pubblicazione DATE NOT NULL,
                data_scaricamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                allegati JSONB DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabella logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS robot_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                azione VARCHAR(100),
                circolari_processate INTEGER DEFAULT 0,
                circolari_scartate INTEGER DEFAULT 0,
                errore TEXT,
                dettagli JSONB DEFAULT '{}'
            )
        """)
        
        conn.commit()
        print("✅ Database inizializzato")
        return True
        
    except Exception as e:
        print(f"❌ Errore inizializzazione: {e}")
        return False
    finally:
        conn.close()

# Inizializza al primo import
if __name__ != "__main__":
    inizializza_database()
