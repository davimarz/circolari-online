#!/usr/bin/env python3
"""
Reset database - Elimina TUTTE le circolari
"""

import psycopg2

# DATABASE CONFIG
DATABASE_URL = "postgresql://postgres:TpsVpUowNnMqSXpvAosQEezxpGPtbPNG@postgres.railway.internal:5432/railway"

print("🗑️  RESET DATABASE")
print("=" * 40)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Conta prima
    cursor.execute("SELECT COUNT(*) FROM circolari")
    count_prima = cursor.fetchone()[0]
    
    # Elimina tutto
    cursor.execute("DELETE FROM circolari")
    conn.commit()
    
    # Conta dopo
    cursor.execute("SELECT COUNT(*) FROM circolari")
    count_dopo = cursor.fetchone()[0]
    
    print(f"✅ Eliminate {count_prima} circolari")
    print(f"📊 Rimangono {count_dopo} circolari")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Errore: {e}")
