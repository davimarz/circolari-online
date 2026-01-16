#!/usr/bin/env python3
print("=== TEST CONNESSIONE DATABASE ===")

import os

# Mostra se DATABASE_URL esiste
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("❌ ERRORE: DATABASE_URL non trovata nei Secrets di GitHub!")
    print("   Vai su: Repository → Settings → Secrets → Actions")
    print("   Aggiungi: DATABASE_URL con la tua connection string")
    exit(1)

print(f"✅ DATABASE_URL trovata (lunghezza: {len(db_url)} caratteri)")

# Controlla se è corretta
if 'rlwy.net' in db_url:
    print("✅ Hostname corretto: contiene 'rlwy.net'")
else:
    print("❌ Hostname ERRATO: non contiene 'rlwy.net'")
    if 'rlw.net' in db_url:
        print("   ⚠️  Contiene 'rlw.net' (manca la 'y')")
    exit(1)

# Test connessione
try:
    import psycopg2
    from datetime import datetime
    
    print("\n🔗 Tentativo connessione al database...")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    print("✅ Connessione riuscita!")
    
    # Test query semplice
    cur.execute("SELECT version()")
    version = cur.fetchone()[0]
    print(f"📊 Database: {version.split(',')[0]}")
    
    # Conta circolari
    cur.execute("SELECT COUNT(*) FROM circolari")
    count = cur.fetchone()[0]
    print(f"📋 Circolari nel database: {count}")
    
    # Prova a inserire una nuova
    print("\n💾 Test inserimento...")
    cur.execute("""
        INSERT INTO circolari (titolo, contenuto, data_pubblicazione)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (
        f"Test GitHub Actions {datetime.now().strftime('%H:%M:%S')}",
        "Test da GitHub Actions dopo fix DATABASE_URL",
        datetime.now().date()
    ))
    
    new_id = cur.fetchone()[0]
    conn.commit()
    print(f"🎉 SUCCESSO! Nuova circolare ID: {new_id}")
    
    conn.close()
    print("\n✅ TUTTO FUNZIONA!")
    exit(0)
    
except Exception as e:
    print(f"❌ ERRORE durante la connessione: {e}")
    exit(1)
