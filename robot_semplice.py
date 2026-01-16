#!/usr/bin/env python3
import os
import sys
import psycopg2
from datetime import datetime

print("🤖 ROBOT SEMPLICISSIMO")

DATABASE_URL = os.environ.get('DATABASE_URL')

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Query semplicissima
    cur.execute("""
        INSERT INTO circolari (titolo, contenuto, data_pubblicazione)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (
        "Test " + datetime.now().strftime("%H:%M"),
        "Test funzionante",
        datetime.now().date()
    ))
    
    id_salvato = cur.fetchone()[0]
    conn.commit()
    
    print(f"✅ SUCCESSO! ID: {id_salvato}")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ ERRORE: {e}")
    sys.exit(1)
