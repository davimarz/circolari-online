#!/usr/bin/env python3
"""
ROBOT SEMPLICE E FUNZIONANTE - SENZA 'fonte'
"""

import os
import sys
import psycopg2
from datetime import datetime

print("🤖 ROBOT SEMPLICE - INIZIO")

try:
    # Connessione al database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ ERRORE: DATABASE_URL non trovata")
        sys.exit(1)
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("✅ Connesso al database")
    
    # Query SEMPLICE - SENZA 'fonte'
    query = """
        INSERT INTO circolari (titolo, contenuto, data_pubblicazione)
        VALUES (%s, %s, %s)
        RETURNING id
    """
    
    # Dati di test
    oggi = datetime.now()
    titolo = f"Test Robot {oggi.strftime('%H:%M')}"
    contenuto = "Circolare di test generata automaticamente"
    data = oggi.date()
    
    print(f"💾 Salvataggio: {titolo}")
    
    # Esegui
    cur.execute(query, (titolo, contenuto, data))
    risultato = cur.fetchone()
    
    if risultato:
        id_salvato = risultato[0]
        conn.commit()
        print(f"✅ SUCCESSO! Circolare salvata con ID: {id_salvato}")
        sys.exit(0)
    else:
        conn.rollback()
        print("⚠️ Nessun ID restituito")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ ERRORE: {str(e)}")
    sys.exit(1)
