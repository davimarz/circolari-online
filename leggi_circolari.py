def main():
    """Funzione principale"""
    print("🚀 DEBUG - Verifica variabili d'ambiente")
    print(f"ARGO_USER presente: {'SI' if os.environ.get('ARGO_USER') else 'NO'}")
    print(f"ARGO_PASS presente: {'SI' if os.environ.get('ARGO_PASS') else 'NO'}")
    print(f"DATABASE_URL presente: {'SI' if os.environ.get('DATABASE_URL') else 'NO'}")
    
    if os.environ.get('DATABASE_URL'):
        db_url = os.environ.get('DATABASE_URL')
        print(f"DATABASE_URL inizia con: {db_url[:50]}...")
        print(f"Porta nella URL: {'5432' if ':5432' in db_url else 'ALTRA'}")
    
    print("=" * 60)
    # ... resto del codice ...





#!/usr/bin/env python3
"""
Robot per scaricare circolari dal portale ARGO e salvarle in PostgreSQL
Database: Railway PostgreSQL (connessione PRIVATA)
Eseguito automaticamente ogni ora via GitHub Actions
"""

import os
import sys
import time
import re
from datetime import datetime, timedelta

# Database PostgreSQL su Railway
import psycopg2
from psycopg2.extras import RealDictCursor

# Selenium per web scraping
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

print("=" * 60)
print("🤖 ROBOT CIRCOLARI ARGO - Railway PostgreSQL (PRIVATO)")
print("=" * 60)

# IMPORTANTE: Usare solo DATABASE_URL, NON DATABASE_PUBLIC_URL
config = {
    'ARGO_USER': os.environ.get('ARGO_USER'),
    'ARGO_PASS': os.environ.get('ARGO_PASS'),
    'DATABASE_URL': os.environ.get('DATABASE_URL')  # Solo questa!
}

# Verifica configurazione
print("🔍 Verifica configurazione...")
print(f"✅ ARGO_USER: {'***' + config['ARGO_USER'][-3:] if config['ARGO_USER'] else 'Mancante'}")
print(f"✅ ARGO_PASS: {'***' + config['ARGO_PASS'][-3:] if config['ARGO_PASS'] else 'Mancante'}")
print(f"✅ DATABASE_URL: {'Configurata' if config['DATABASE_URL'] else 'Mancante'}")

if not all([config['ARGO_USER'], config['ARGO_PASS'], config['DATABASE_URL']]):
    print("❌ ERRORE: Variabili mancanti!")
    sys.exit(1)

# Funzioni Database PostgreSQL su Railway (PRIVATO)
def get_db_connection():
    """Crea connessione PRIVATA al database PostgreSQL su Railway"""
    try:
        # Usa DATABASE_URL (connessione privata, zero costi)
        conn = psycopg2.connect(config['DATABASE_URL'], sslmode='require')
        print("✅ Connessione PRIVATA a Railway PostgreSQL stabilita")
        return conn
    except Exception as e:
        print(f"❌ Errore connessione database PRIVATO: {str(e)}")
        print("ℹ️  Verifica che DATABASE_URL sia la variabile PRIVATA di Railway")
        return None

# ... (il resto del file rimane uguale, usa get_db_connection() ovunque) ...

def init_database():
    """Inizializza il database se necessario"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Crea tabella se non esiste
        cur.execute("""
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
        
        # Crea indice
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_circolari_data 
            ON circolari(data_pubblicazione DESC)
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("✅ Database Railway PRIVATO inizializzato")
        return True
        
    except Exception as e:
        print(f"❌ Errore inizializzazione database: {str(e)}")
        return False

# ... (resto del codice invariato) ...
