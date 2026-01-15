import os
import psycopg2
import pandas as pd
from psycopg2 import sql
import streamlit as st

def get_database_connection():
    """
    Crea una connessione al database PostgreSQL su Railway
    """
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        st.error("⚠️ DATABASE_URL non configurata su Railway")
        return None
    
    try:
        # Assicurati che ci sia sslmode=require
        if 'sslmode=' not in DATABASE_URL:
            DATABASE_URL += "?sslmode=require"
        elif 'sslmode=require' not in DATABASE_URL:
            # Sostituisci qualsiasi altro sslmode con require
            DATABASE_URL = DATABASE_URL.replace('sslmode=', 'sslmode=require')
        
        conn = psycopg2.connect(DATABASE_URL)
        return conn
        
    except Exception as e:
        st.error(f"❌ Errore connessione al database: {str(e)}")
        return None

def init_database():
    """
    Inizializza/verifica il database
    """
    conn = get_database_connection()
    if conn is None:
        return "❌ Impossibile connettersi al database"
    
    try:
        cursor = conn.cursor()
        
        # 1. Verifica connessione
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        # 2. Crea tabella circolari se non esiste
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circolari (
                id SERIAL PRIMARY KEY,
                titolo TEXT NOT NULL,
                data_pubblicazione DATE,
                file_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 3. Verifica che la tabella esista
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'circolari';")
        table_exists = cursor.fetchone()[0]
        
        # 4. Crea tabella utenti se non esiste
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utenti (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                ruolo TEXT DEFAULT 'lettore',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if table_exists > 0:
            return f"✅ Database pronto! PostgreSQL: {version[0]}"
        else:
            return f"⚠️ Database connesso ma tabelle potrebbero non essere create: {version[0]}"
            
    except Exception as e:
        return f"❌ Errore durante inizializzazione: {str(e)}"

def test_database_connection():
    """
    Funzione di test semplice per la connessione
    """
    conn = get_database_connection()
    if conn is None:
        return False, "Nessuna connessione"
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result[0] == 1:
            return True, "Connessione OK"
        else:
            return False, "Risposta inattesa dal database"
    except Exception as e:
        return False, f"Errore query: {str(e)}"
