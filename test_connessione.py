import psycopg2
import sys

# Usa la tua DATABASE_URL ESATTA
DATABASE_URL = "postgresql://postgres:NESoahBqquyZobuAJbgJMVAXgoojwCs@switchback.proxy.rlw.net:5432/railway"

print("🧪 Test connessione database Railway")
print(f"URL: {DATABASE_URL[:50]}...")

try:
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    
    # Test 1: Versione PostgreSQL
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"✅ PostgreSQL: {version.split(',')[0]}")
    
    # Test 2: Lista tabelle
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    
    tables = cursor.fetchall()
    print(f"✅ Tabelle trovate: {len(tables)}")
    
    for table in tables:
        print(f"   - {table[0]}")
    
    cursor.close()
    conn.close()
    print("🎉 Test completato con successo!")
    
except Exception as e:
    print(f"❌ ERRORE: {e}")
    sys.exit(1)
