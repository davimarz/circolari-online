#!/usr/bin/env python3
"""
Robot Circolari - Versione per GitHub Actions senza Selenium
"""

import os
import sys
import json
from datetime import datetime, timedelta

print("🤖 ROBOT CIRCOLARI - Avvio...")
print(f"Timestamp: {datetime.now().isoformat()}")

# ==============================================================================
# 🛑 CHECK CONFIGURAZIONE
# ==============================================================================
DATABASE_URL = os.getenv("postgresql://postgres:TpsVpUowNnMqSXpvAosQEezxpGPtbPNG@postgres.railway.internal:5432/railway")
ARGO_USER = os.getenv("ARGO_USER", "davide.marziano.sc26953")
ARGO_PASS = os.getenv("ARGO_PASS", "dvd2Frank.")

print(f"🔍 Configurazione ambiente:")
print(f"   • DATABASE_URL: {'✅ Configurato' if DATABASE_URL else '❌ Mancante'}")
print(f"   • ARGO_USER: {'✅ Configurato' if ARGO_USER else '❌ Mancante'}")
print(f"   • ARGO_PASS: {'✅ Configurato' if ARGO_PASS else '❌ Mancante'}")

if not DATABASE_URL:
    print("\n❌ ERRORE: DATABASE_URL non configurato!")
    print("\n📋 Per configurare:")
    print("1. Vai su GitHub → Repository → Settings → Secrets → Actions")
    print("2. Aggiungi secret 'DATABASE_URL'")
    print("3. Valore: ottienilo da Railway → PostgreSQL → Connect")
    print("\n💡 Formato: postgresql://postgres:PASSWORD@HOST:PORT/DATABASE")
    
    # Salva log errore
    errore_log = {
        "timestamp": datetime.now().isoformat(),
        "errore": "DATABASE_URL non configurato",
        "configurazione": {
            "python_version": sys.version,
            "env_vars": [k for k in os.environ.keys() if 'DATABASE' in k or 'POSTGRES' in k]
        }
    }
    
    with open("errore_configurazione.json", "w") as f:
        json.dump(errore_log, f, indent=2)
    
    sys.exit(1)

print(f"\n✅ Ambiente configurato correttamente")

# ==============================================================================
# 🛑 SIMULAZIONE SCARICAMENTO
# ==============================================================================
print("\n" + "="*60)
print("🎭 SIMULAZIONE SCARICAMENTO CIRCOLARI")
print("="*60)

# Circolari di esempio (simulate per test)
circolari_simulate = [
    {
        "id": 1,
        "data": datetime.now().strftime("%d/%m/%Y"),
        "titolo": "Circolare test GitHub Actions",
        "categoria": "Test",
        "contenuto": "Questa è una circolare di test generata automaticamente dal robot.",
        "allegati": []
    },
    {
        "id": 2,
        "data": (datetime.now() - timedelta(days=5)).strftime("%d/%m/%Y"),
        "titolo": "Avviso riunione docenti",
        "categoria": "Docenti",
        "contenuto": "Si comunica la riunione di dipartimento prevista per il prossimo venerdì.",
        "allegati": ["convocatione_riunione.pdf"]
    },
    {
        "id": 3,
        "data": (datetime.now() - timedelta(days=15)).strftime("%d/%m/%Y"),
        "titolo": "Calendario scrutini",
        "categoria": "Studenti",
        "contenuto": "Pubblicazione calendario scrutini primo quadrimestre.",
        "allegati": ["calendario_scrutini.pdf", "modalita_valutazione.pdf"]
    }
]

# Filtra solo ultimi 30 giorni
data_limite = datetime.now() - timedelta(days=30)
circolari_recenti = []
circolari_scartate = []

for circ in circolari_simulate:
    try:
        data_circ = datetime.strptime(circ["data"], "%d/%m/%Y")
        if data_circ >= data_limite:
            circolari_recenti.append(circ)
        else:
            circolari_scartate.append(circ["id"])
    except:
        circolari_recenti.append(circ)  # Se errore parsing, includi comunque

# ==============================================================================
# 🛑 SIMULAZIONE SALVATAGGIO DATABASE
# ==============================================================================
print(f"\n📊 PROCESSAMENTO CIRCOLARI:")
print(f"   • Trovate: {len(circolari_simulate)}")
print(f"   • Recenti (<30gg): {len(circolari_recenti)}")
print(f"   • Scartate (vecchie): {len(circolari_scartate)}")

if circolari_scartate:
    print(f"   • ID scartati: {circolari_scartate}")

print(f"\n📝 CIRCOLARI PROCESSATE:")
for circ in circolari_recenti:
    print(f"   [{circ['id']}] {circ['data']} - {circ['titolo']}")
    if circ['allegati']:
        print(f"      📎 Allegati: {', '.join(circ['allegati'])}")

# ==============================================================================
# 🛑 SIMULAZIONE DATABASE CONNESSIONE
# ==============================================================================
print("\n" + "="*60)
print("🗄️  SIMULAZIONE CONNESSIONE DATABASE")
print("="*60)

# Test connessione "simulata"
try:
    # In una versione reale, qui ci sarebbe psycopg2.connect(DATABASE_URL)
    print(f"🔗 Connessione a: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL[:50]}")
    print("✅ Connessione simulata riuscita")
    
    # Simula creazione tabelle
    print("📋 Tabelle verificate:")
    print("   • circolari ✓")
    print("   • robot_logs ✓")
    
    # Simula salvataggio
    print(f"💾 Salvate {len(circolari_recenti)} circolari")
    
except Exception as e:
    print(f"❌ Errore connessione: {e}")

# ==============================================================================
# 🛑 GENERAZIONE REPORT
# ==============================================================================
print("\n" + "="*60)
print("📈 REPORT FINALE")
print("="*60)

report = {
    "timestamp": datetime.now().isoformat(),
    "ambiente": "github_actions",
    "database_url_configurato": bool(DATABASE_URL),
    "circolari": {
        "totali_trovate": len(circolari_simulate),
        "recenti_processate": len(circolari_recenti),
        "vecchie_scartate": len(circolari_scartate),
        "dettaglio_scartate": circolari_scartate
    },
    "configurazione": {
        "argo_user": ARGO_USER,
        "has_argo_pass": bool(ARGO_PASS)
    },
    "note": "SIMULAZIONE - Per la versione reale installa psycopg2-binary"
}

print(f"⏱️  Timestamp: {report['timestamp']}")
print(f"📊 Circolari: {report['circolari']['recenti_processate']} processate, {report['circolari']['vecchie_scartate']} scartate")
print(f"🔐 Configurazione: {'✅ Completa' if DATABASE_URL else '❌ Incompleta'}")
print(f"💡 Nota: {report['note']}")

# Salva report
with open("report_robot.json", "w") as f:
    json.dump(report, f, indent=2)

print(f"\n📁 File generati:")
print("   ✓ report_robot.json")
print("   ✓ errore_configurazione.json (se errore)")

print("\n" + "="*60)
print("🎯 ROBOT COMPLETATO CON SUCCESSO!")
print("="*60)
print("\nℹ️  Prossimi passi per la versione reale:")
print("   1. Installa: pip install psycopg2-binary")
print("   2. Importa psycopg2 nello script")
print("   3. Sostituisci simulazione con connessione reale")
print("   4. Configura DATABASE_URL nei GitHub Secrets")

sys.exit(0)
