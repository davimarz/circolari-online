#!/usr/bin/env python3
"""
Robot Circolari - Versione SIMULATA per GitHub Actions
Usa database SQLite locale per evitare costi Railway
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta

print("🤖 ROBOT CIRCOLARI - Avvio...")
print(f"Timestamp: {datetime.now().isoformat()}")
print("🔧 Modalità: SIMULAZIONE con SQLite locale")

# Configurazione
ARGO_USER = "davide.marziano.sc26953"
ARGO_PASS = "dvd2Frank."
DB_PATH = "circolari.db"  # Database SQLite locale

# ==============================================================================
# 🛑 DATABASE SQLITE LOCALE (GRATUITO)
# ==============================================================================

def init_sqlite_db():
    """Inizializza database SQLite locale"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Tabella circolari
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circolari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titolo TEXT NOT NULL,
                contenuto TEXT,
                categoria TEXT,
                data_pubblicazione DATE NOT NULL,
                data_scaricamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                allegati TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabella logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS robot_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                azione TEXT,
                circolari_processate INTEGER DEFAULT 0,
                circolari_scartate INTEGER DEFAULT 0,
                errore TEXT,
                dettagli TEXT DEFAULT '{}'
            )
        """)
        
        conn.commit()
        conn.close()
        print(f"✅ Database SQLite inizializzato: {DB_PATH}")
        return True
        
    except Exception as e:
        print(f"❌ Errore inizializzazione SQLite: {e}")
        return False

def salva_circolare_sqlite(titolo, contenuto, categoria, data_pub, allegati=None):
    """Salva una circolare in SQLite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        allegati_json = json.dumps(allegati) if allegati else '[]'
        
        # Controlla se esiste già
        cursor.execute("""
            SELECT id FROM circolari 
            WHERE titolo = ? AND data_pubblicazione = ?
        """, (titolo, data_pub))
        
        if cursor.fetchone():
            # Aggiorna
            cursor.execute("""
                UPDATE circolari 
                SET contenuto = ?, categoria = ?, allegati = ?
                WHERE titolo = ? AND data_pubblicazione = ?
            """, (contenuto, categoria, allegati_json, titolo, data_pub))
            print(f"   🔄 Aggiornata: {titolo[:50]}")
        else:
            # Inserisci nuova
            cursor.execute("""
                INSERT INTO circolari 
                (titolo, contenuto, categoria, data_pubblicazione, allegati)
                VALUES (?, ?, ?, ?, ?)
            """, (titolo, contenuto, categoria, data_pub, allegati_json))
            print(f"   ✅ Salvata: {titolo[:50]}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore salvataggio SQLite: {e}")
        return False

def elimina_circolari_vecchie_sqlite():
    """Elimina circolari vecchie da SQLite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        data_limite = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        cursor.execute("SELECT COUNT(*) FROM circolari WHERE data_pubblicazione < ?", 
                      (data_limite,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            cursor.execute("DELETE FROM circolari WHERE data_pubblicazione < ?", 
                          (data_limite,))
            conn.commit()
            print(f"🗑️  Eliminate {count} circolari vecchie")
        else:
            print("✅ Nessuna circolare vecchia da eliminare")
        
        conn.close()
        return count
        
    except Exception as e:
        print(f"⚠️ Errore eliminazione SQLite: {e}")
        return 0

def salva_log_sqlite(azione, processate=0, scartate=0, errore=None):
    """Salva log in SQLite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        dettagli = {
            "timestamp": datetime.now().isoformat(),
            "argo_user": ARGO_USER,
            "ambiente": "github_actions_sqlite",
            "note": "Database SQLite locale - Modalità simulazione"
        }
        
        cursor.execute("""
            INSERT INTO robot_logs 
            (azione, circolari_processate, circolari_scartate, errore, dettagli)
            VALUES (?, ?, ?, ?, ?)
        """, (azione, processate, scartate, errore, json.dumps(dettagli)))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"⚠️ Errore salvataggio log SQLite: {e}")
        return False

# ==============================================================================
# 🛑 SIMULAZIONE CIRCOLARI
# ==============================================================================

def scarica_circolari_simulate():
    """Simula scaricamento circolari"""
    print("\n🎭 SIMULAZIONE scaricamento circolari Argo...")
    
    data_limite = datetime.now() - timedelta(days=30)
    
    circolari = [
        {
            "data": datetime.now().date(),
            "titolo": f"Test Robot GitHub Actions {datetime.now().strftime('%d/%m')}",
            "contenuto": "Circolare di test generata automaticamente dal robot in modalità simulazione.",
            "categoria": "Test",
            "allegati": ["test_documento.pdf"]
        },
        {
            "data": (datetime.now() - timedelta(days=5)).date(),
            "titolo": "Comunicazione importante - Modalità simulazione",
            "contenuto": "Questa circolare dimostra il funzionamento del robot senza costi di database.",
            "categoria": "Comunicazioni",
            "allegati": []
        },
        {
            "data": (datetime.now() - timedelta(days=40)).date(),  # Vecchia
            "titolo": "Vecchia circolare da scartare",
            "contenuto": "Questa verrà scartata automaticamente (>30 giorni).",
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
        
        if salva_circolare_sqlite(
            titolo=circ["titolo"],
            contenuto=circ["contenuto"],
            categoria=circ["categoria"],
            data_pub=circ["data"].strftime('%Y-%m-%d'),
            allegati=circ["allegati"]
        ):
            processate += 1
    
    return processate, scartate

# ==============================================================================
# 🛑 MAIN EXECUTION
# ==============================================================================

def main():
    print("\n" + "="*60)
    print("🤖 ROBOT CIRCOLARI - Modalità SIMULAZIONE")
    print("="*60)
    print("📝 NOTA: Usa database SQLite locale per evitare costi Railway")
    print("        I dati sono salvati nel file 'circolari.db'")
    print("="*60)
    
    timestamp_inizio = datetime.now()
    
    try:
        # 1. Inizializza database SQLite
        print("\n1️⃣ Inizializzazione database SQLite...")
        if not init_sqlite_db():
            raise Exception("Impossibile inizializzare SQLite")
        
        # 2. Elimina circolari vecchie
        print("\n2️⃣ Pulizia circolari vecchie...")
        eliminate = elimina_circolari_vecchie_sqlite()
        
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
        print(f"💾 Database: SQLite locale (circolari.db)")
        print(f"💰 Costo: GRATUITO - Nessuna connessione a Railway")
        print("="*60)
        
        # 5. Salva log
        salva_log_sqlite(
            azione="scaricamento_simulato",
            processate=processate,
            scartate=scartate
        )
        
        # 6. Crea report
        report = {
            "timestamp": datetime.now().isoformat(),
            "modalita": "simulazione_sqlite",
            "database": "SQLite locale",
            "circolari": {
                "processate": processate,
                "scartate": scartate,
                "eliminate": eliminate
            },
            "durata_secondi": durata,
            "costo": "gratuito",
            "note": "Robot eseguito senza costi di database esterno"
        }
        
        with open("robot_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        with open("circolari.json", "w") as f:
            # Leggi le circolari dal database per il report
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count, categoria FROM circolari GROUP BY categoria")
                stats = cursor.fetchall()
                conn.close()
                
                json.dump({
                    "total_circolari": sum([row[0] for row in stats]),
                    "per_categoria": {row[1]: row[0] for row in stats},
                    "ultimo_aggiornamento": datetime.now().isoformat()
                }, f, indent=2)
            except:
                json.dump({"note": "Dati non disponibili"}, f, indent=2)
        
        print(f"\n📁 File generati:")
        print(f"   ✓ circolari.db (database SQLite)")
        print(f"   ✓ robot_report.json")
        print(f"   ✓ circolari.json (statistiche)")
        
        print("\n🎯 ROBOT COMPLETATO CON SUCCESSO!")
        print("💡 Modalità gratuita - Nessun costo Railway")
        
    except Exception as e:
        print(f"\n❌ ERRORE CRITICO: {e}")
        salva_log_sqlite(azione="errore", errore=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
