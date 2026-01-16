"""
database.py - Versione SEMPLIFICATA
Gestione database PostgreSQL per Streamlit App
"""

import psycopg2
import pandas as pd
from datetime import datetime, timedelta

# ==============================================================================
# 🛑 CONFIGURAZIONE
# ==============================================================================

DATABASE_URL = "postgresql://postgres:TpsVpUowNnMqSXpvAosQEezxpGPtbPNG@postgres.railway.internal:5432/railway"

# ==============================================================================
# 🛑 FUNZIONI DATABASE
# ==============================================================================

def get_connection():
    """Crea connessione al database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Errore connessione: {e}")
        return None

def init_database():
    """Inizializza tabella se non esiste"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circolari (
                id SERIAL PRIMARY KEY,
                titolo TEXT NOT NULL,
                contenuto TEXT,
                data_pubblicazione DATE NOT NULL,
                allegati TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("✅ Tabella circolari pronta")
        return True
        
    except Exception as e:
        print(f"Errore inizializzazione: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_circolari_recenti(limite=50):
    """
    Ottiene le circolari più recenti.
    
    Returns:
        Lista di dizionari con le circolari
    """
    conn = get_connection()
    if not conn:
        return []
    
    try:
        query = """
            SELECT 
                id, titolo, contenuto, 
                data_pubblicazione, allegati,
                TO_CHAR(data_pubblicazione, 'DD/MM/YYYY') as data_formattata
            FROM circolari 
            ORDER BY data_pubblicazione DESC, created_at DESC
            LIMIT %s
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (limite,))
        
        # Converti risultati in lista di dizionari
        circolari = []
        for row in cursor.fetchall():
            circolare = {
                'id': row[0],
                'titolo': row[1],
                'contenuto': row[2],
                'data_pubblicazione': row[3],
                'allegati': row[4].split(',') if row[4] else [],
                'data_formattata': row[5]
            }
            circolari.append(circolare)
        
        return circolari
        
    except Exception as e:
        print(f"Errore query circolari: {e}")
        return []
    finally:
        if conn:
            conn.close()

def test_connection():
    """Testa connessione database"""
    conn = get_connection()
    if conn:
        conn.close()
        return {"status": "connected", "timestamp": datetime.now().isoformat()}
    else:
        return {"status": "disconnected", "message": "Impossibile connettersi"}

# Inizializza al primo import
init_database()
