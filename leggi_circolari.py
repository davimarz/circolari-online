#!/usr/bin/env python3
"""
Robot Circolari - Versione completa per GitHub Actions
Connessione diretta al database Railway
"""

import os
import sys
import json
import psycopg2
from datetime import datetime, timedelta
from urllib.parse import urlparse

print("🤖 ROBOT CIRCOLARI - Avvio...")
print(f"Timestamp: {datetime.now().isoformat()}")

# ==============================================================================
# 🛑 CONFIGURAZIONE DATABASE RAILWAY
# ==============================================================================
DATABASE_URL = "postgresql://postgres:TpsVpUowNnMqSXpvAosQEezxpGPtbPNG@postgres.railway.internal:5432/railway"
ARGO_USER = "davide.marziano.sc26953"
ARGO_PASS = "dvd2Frank."

print(f"🔧 Configurazione:")
print(f"   • Database: Railway PostgreSQL ✓")
print(f"   • Utente Argo: {ARGO_USER} ✓")
print(f"   • Host: postgres.railway.internal:5432 ✓")

# ==============================================================================
# 🛑 FUNZIONI DATABASE
# ==============================================================================

def get_db_connection():
    """Crea una connessione al database PostgreSQL di Railway"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Connessione database riuscita")
        return conn
    except Exception as e:
        print(f"❌ Errore connessione database: {str(e)[:100]}")
        return None

def init_database():
    """Inizializza le tabelle se non esistono"""
    conn = get_db_connection()
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
        
        # Indici
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_circolari_data 
            ON circolari(data_pubblicazione)
        """)
        
        conn.commit()
        print("✅ Database inizializzato")
        return True
        
    except Exception as e:
        print(f"❌ Errore inizializzazione: {e}")
        return False
    finally:
        if conn:
            conn.close()

def salva_circolare(titolo, contenuto, categoria, data_pub, allegati=None):
    """Salva una circolare nel database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Controlla se esiste già
        cursor.execute("""
            SELECT id FROM circolari 
            WHERE titolo = %s AND data_pubblicazione = %s
        """, (titolo, data_pub))
        
        allegati_json = json.dumps(allegati) if allegati else '[]'
        
        if cursor.fetchone():
            # Aggiorna
            cursor.execute("""
                UPDATE circolari 
                SET contenuto = %s, categoria = %s, allegati = %s
                WHERE titolo = %s AND data_pubblicazione = %s
            """, (contenuto, categoria, allegati_json, titolo, data_pub))
            print(f"   🔄 Aggiornata: {titolo[:50]}")
        else:
            # Inserisci nuova
            cursor.execute("""
                INSERT INTO circolari 
                (titolo, contenuto, categoria, data_pubblicazione, allegati)
                VALUES (%s, %s, %s, %s, %s)
            """, (titolo, contenuto, categoria, data_pub, allegati_json))
            print(f"   ✅ Salvata: {titolo[:50]}")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Errore salvataggio: {e}")
        return False
    finally:
        if conn:
            conn.close()

def elimina_circolari_vecchie():
    """Elimina circolari più vecchie di 30 giorni"""
    conn = get_db_connection()
    if not conn:
        return 0
    
    try:
        cursor = conn.cursor()
        data_limite = datetime.now() - timedelta(days=30)
        
        cursor.execute("SELECT COUNT(*) FROM circolari WHERE data_pubblicazione < %s", 
                      (data_limite,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            cursor.execute("DELETE FROM circolari WHERE data_pubblicazione < %s", 
                          (data_limite,))
            conn.commit()
            print(f"🗑️  Eliminate {count} circolari vecchie")
        else:
            print("✅ Nessuna circolare vecchia da eliminare")
        
        return count
        
    except Exception as e:
        print(f"⚠️ Errore eliminazione: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def salva_log(azione, processate=0, scartate=0, errore=None):
    """Salva log dell'esecuzione"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        dettagli = {
            "timestamp": datetime.now().isoformat(),
            "argo_user": ARGO_USER,
            "ambiente": "github_actions"
        }
        
        cursor.execute("""
            INSERT INTO robot_logs 
            (azione, circolari_processate, circolari_scartate, errore, dettagli)
            VALUES (%s, %s, %s, %s, %s)
        """, (azione, processate, scartate, errore, json.dumps(dettagli)))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"⚠️ Errore salvataggio log: {e}")
        return False
    finally:
        if conn:
            conn.close()

# ==============================================================================
# 🛑 SIMULAZIONE CIRCOLARI (per test)
# ==============================================================================
def scarica_circolari_simulate():
    """Simula scaricamento circolari (in produzione sostituire con Argo)"""
    print("\n🎭 SIMULAZIONE scaricamento circolari Argo...")
    
    data_limite = datetime.now() - timedelta(days=30)
    
    circolari = [
        {
            "data": datetime.now().date(),
            "titolo": f"Circolare test {datetime.now().strftime('%d/%m/%Y')}",
            "contenuto": f"Circolare di test generata dal robot GitHub Actions il {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "categoria": "Comunicazioni",
            "allegati": ["test_documento.pdf"]
        },
        {
            "data": (datetime.now() - timedelta(days=5)).date(),
            "titolo": "Avviso assemblea genitori",
            "contenuto": "Si comunica l'assemblea generale dei genitori prevista per il giorno 25 gennaio 2026.",
            "categoria": "Genitori",
            "allegati": ["convocazione_assemblea.pdf", "ordine_del_giorno.pdf"]
        },
        {
            "data": (datetime.now() - timedelta(days=15)).date(),
            "titolo": "Calendario esami di recupero",
            "contenuto": "Si pubblica il calendario degli esami di recupero del primo quadrimestre.",
            "categoria": "Studenti",
            "allegati": ["calendario_esami.pdf"]
        },
        {
            "data": (datetime.now() - timedelta(days=40)).date(),  # Vecchia
            "titolo": "Comunicazione vecchia da scartare",
            "contenuto": "Questa circolare è vecchia e verrà scartata automaticamente.",
            "categoria": "Varie",
            "allegati": []
        }
    ]
    
    processate = 0
    scartate = 0
    
    for i, circ in enumerate(circolari):
        if circ["data"] < data_limite.date():
            print(f"⏳ [{i+1}] {circ['data']} - {circ['titolo'][:40]}... (VECCHIA)")
            scartate += 1
            continue
        
        print(f"\n🔄 [{i+1}] {circ['data']} - {circ['titolo']}")
        
        if circ['allegati']:
            print(f"   📎 Allegati: {', '.join(circ['allegati'])}")
        
        if salva_circolare(
            titolo=circ["titolo"],
            contenuto=circ["contenuto"],
            categoria=circ["categoria"],
            data_pub=circ["data"],
            allegati=circ["allegati"]
        ):
            processate += 1
        else:
            scartate += 1
    
    return processate, scartate

# ==============================================================================
# 🛑 MAIN EXECUTION
# ==============================================================================
def main():
    print("\n" + "="*60)
    print("🤖 ROBOT CIRCOLARI - Railway PostgreSQL")
    print("="*60)
    
    timestamp_inizio = datetime.now()
    
    try:
        # 1. Inizializza database
        print("\n1️⃣ Inizializzazione database...")
        if not init_database():
            raise Exception("Impossibile inizializzare database")
        
        # 2. Elimina circolari vecchie
        print("\n2️⃣ Pulizia circolari vecchie...")
        eliminate = elimina_circolari_vecchie()
        
        # 3. Scarica nuove circolari
        print("\n3️⃣ Scaricamento circolari...")
        processate, scartate = scarica_circolari_simulate()
        
        # 4. Riepilogo
        durata = (datetime.now() - timestamp_inizio).total_seconds()
        
        print("\n" + "="*60)
        print("📊 RIEPILOGO ESECUZIONE")
        print("="*60)
        print(f"✅ Circolari processate: {processate}")
        print(f"🗑️  Circolari scartate: {scartate}")
        print(f"🧹 Circolari eliminate (vecchie): {eliminate}")
        print(f"⏱️  Durata: {durata:.2f} secondi")
        print(f"📅 Data limite: {(datetime.now() - timedelta(days=30)).strftime('%d/%m/%Y')}")
        print("="*60)
        
        # 5. Salva log
        salva_log(
            azione="scaricamento_simulato",
            processate=processate,
            scartate=scartate
        )
        
        # 6. Report file
        report = {
            "timestamp": datetime.now().isoformat(),
            "database": "Railway PostgreSQL",
            "host": "postgres.railway.internal:5432",
            "circolari": {
                "processate": processate,
                "scartate": scartate,
                "eliminate": eliminate
            },
            "durata_secondi": durata,
            "status": "successo"
        }
        
        with open("robot_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📁 Report salvato: robot_report.json")
        print("\n🎯 ROBOT COMPLETATO CON SUCCESSO!")
        
    except Exception as e:
        print(f"\n❌ ERRORE CRITICO: {e}")
        salva_log(azione="errore", errore=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
