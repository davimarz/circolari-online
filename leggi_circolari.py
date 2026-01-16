#!/usr/bin/env python3
"""
Robot Circolari - Versione COMPLETA per GitHub Actions
Database SQLite locale - ZERO COSTI
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta

print("=" * 70)
print("🤖 ROBOT CIRCOLARI - AVVIO")
print("=" * 70)
print(f"⏰ Timestamp: {datetime.now().isoformat()}")
print("🔧 Modalità: SIMULAZIONE con SQLite locale")
print("💰 Costo: GRATUITO - Nessun database esterno")
print("=" * 70)

# ==============================================================================
# 🛑 CONFIGURAZIONE COMPLETA
# ==============================================================================

# Credenziali Argo (per simulazione)
ARGO_USER = "davide.marziano.sc26953"
ARGO_PASS = "dvd2Frank."

# Configurazione database
DB_PATH = "circolari.db"  # Database SQLite locale
REPORT_PATH = "robot_report.json"
STATS_PATH = "circolari.json"

# ==============================================================================
# 🛑 FUNZIONI DATABASE SQLITE
# ==============================================================================

def init_sqlite_db():
    """Inizializza database SQLite locale con tutte le tabelle"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print(f"📦 Creazione database SQLite: {DB_PATH}")
        
        # Tabella circolari (principale)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circolari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titolo TEXT NOT NULL,
                contenuto TEXT,
                categoria TEXT,
                data_pubblicazione DATE NOT NULL,
                data_scaricamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                allegati TEXT DEFAULT '[]',
                fonte TEXT DEFAULT 'simulazione',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabella logs del robot
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS robot_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                azione TEXT,
                circolari_processate INTEGER DEFAULT 0,
                circolari_scartate INTEGER DEFAULT 0,
                circolari_eliminate INTEGER DEFAULT 0,
                errore TEXT,
                dettagli TEXT DEFAULT '{}',
                durata_secondi REAL DEFAULT 0
            )
        """)
        
        # Tabella statistiche
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistiche (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data DATE NOT NULL,
                totale_circolari INTEGER DEFAULT 0,
                nuove_circolari INTEGER DEFAULT 0,
                categorie TEXT DEFAULT '{}'
            )
        """)
        
        # Indici per performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_circolari_data ON circolari(data_pubblicazione)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_circolari_categoria ON circolari(categoria)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON robot_logs(timestamp)")
        
        conn.commit()
        conn.close()
        
        print("✅ Database SQLite inizializzato correttamente")
        print(f"   • Tabelle: circolari, robot_logs, statistiche")
        print(f"   • Indici: ottimizzati per performance")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore inizializzazione database: {e}")
        return False

def salva_circolare_sqlite(titolo, contenuto, categoria, data_pub, allegati=None):
    """Salva una circolare nel database SQLite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Prepara dati
        data_pub_str = data_pub.strftime('%Y-%m-%d') if isinstance(data_pub, datetime) else data_pub
        allegati_json = json.dumps(allegati) if allegati else '[]'
        
        # Controlla se esiste già (per evitare duplicati)
        cursor.execute("""
            SELECT id FROM circolari 
            WHERE titolo = ? AND data_pubblicazione = ? AND categoria = ?
        """, (titolo, data_pub_str, categoria))
        
        existing = cursor.fetchone()
        
        if existing:
            # Aggiorna circolare esistente
            cursor.execute("""
                UPDATE circolari 
                SET contenuto = ?, allegati = ?, data_scaricamento = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (contenuto, allegati_json, existing[0]))
            
            print(f"   🔄 Aggiornata circolare esistente")
            print(f"      Titolo: {titolo[:60]}")
            
        else:
            # Inserisci nuova circolare
            cursor.execute("""
                INSERT INTO circolari 
                (titolo, contenuto, categoria, data_pubblicazione, allegati, fonte)
                VALUES (?, ?, ?, ?, ?, 'github_actions')
            """, (titolo, contenuto, categoria, data_pub_str, allegati_json))
            
            print(f"   ✅ Nuova circolare salvata")
            print(f"      Titolo: {titolo[:60]}")
            print(f"      Data: {data_pub_str}")
            print(f"      Categoria: {categoria}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Errore salvataggio circolare: {e}")
        return False

def elimina_circolari_vecchie_sqlite():
    """Elimina circolari più vecchie di 30 giorni"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Calcola data limite (30 giorni fa)
        data_limite = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Conta quante saranno eliminate
        cursor.execute("SELECT COUNT(*) FROM circolari WHERE data_pubblicazione < ?", 
                      (data_limite,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Salva backup delle vecchie circolari (opzionale)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS circolari_archivio AS 
                SELECT * FROM circolari WHERE data_pubblicazione < ?
            """, (data_limite,))
            
            # Elimina le vecchie
            cursor.execute("DELETE FROM circolari WHERE data_pubblicazione < ?", 
                          (data_limite,))
            
            conn.commit()
            print(f"🗑️  Eliminate {count} circolari vecchie (prima del {data_limite})")
            print(f"📦 Backup salvato in tabella: circolari_archivio")
        else:
            print("✅ Nessuna circolare vecchia da eliminare")
        
        conn.close()
        return count
        
    except Exception as e:
        print(f"⚠️ Errore eliminazione circolari vecchie: {e}")
        return 0

def salva_log_sqlite(azione, processate=0, scartate=0, eliminate=0, errore=None, durata=0):
    """Salva log dettagliato dell'esecuzione"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Dettagli completi del log
        dettagli = {
            "timestamp": datetime.now().isoformat(),
            "argo_user": ARGO_USER,
            "ambiente": "github_actions",
            "modalita": "simulazione_sqlite",
            "python_version": sys.version.split()[0],
            "sistema": sys.platform,
            "parametri": {
                "db_path": DB_PATH,
                "filtro_giorni": 30
            }
        }
        
        cursor.execute("""
            INSERT INTO robot_logs 
            (azione, circolari_processate, circolari_scartate, 
             circolari_eliminate, errore, dettagli, durata_secondi)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (azione, processate, scartate, eliminate, errore, json.dumps(dettagli), durata))
        
        conn.commit()
        conn.close()
        
        print(f"📝 Log salvato: {azione}")
        return True
        
    except Exception as e:
        print(f"⚠️ Errore salvataggio log: {e}")
        return False

def aggiorna_statistiche():
    """Aggiorna le statistiche giornaliere"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        data_oggi = datetime.now().strftime('%Y-%m-%d')
        
        # Totale circolari
        cursor.execute("SELECT COUNT(*) FROM circolari")
        totale = cursor.fetchone()[0]
        
        # Nuove oggi
        cursor.execute("SELECT COUNT(*) FROM circolari WHERE DATE(created_at) = DATE('now')")
        nuove_oggi = cursor.fetchone()[0]
        
        # Distribuzione categorie
        cursor.execute("SELECT categoria, COUNT(*) FROM circolari GROUP BY categoria")
        categorie_data = cursor.fetchall()
        categorie_dict = {cat: count for cat, count in categorie_data}
        
        # Inserisci/aggiorna statistiche
        cursor.execute("""
            INSERT OR REPLACE INTO statistiche 
            (data, totale_circolari, nuove_circolari, categorie)
            VALUES (?, ?, ?, ?)
        """, (data_oggi, totale, nuove_oggi, json.dumps(categorie_dict)))
        
        conn.commit()
        conn.close()
        
        print(f"📊 Statistiche aggiornate per {data_oggi}")
        print(f"   • Totale circolari: {totale}")
        print(f"   • Nuove oggi: {nuove_oggi}")
        print(f"   • Categorie: {len(categorie_dict)}")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Errore aggiornamento statistiche: {e}")
        return False

# ==============================================================================
# 🛑 SIMULAZIONE CIRCOLARI REALISTICHE
# ==============================================================================

def scarica_circolari_simulate():
    """Simula lo scaricamento di circolari reali da Argo"""
    print("\n" + "=" * 70)
    print("🎭 SIMULAZIONE SCARICAMENTO CIRCOLARI ARGO")
    print("=" * 70)
    print("ℹ️  Modalità: Simulazione realistica con dati di esempio")
    print("📅 Filtro: Solo ultimi 30 giorni")
    print("=" * 70)
    
    data_limite = datetime.now() - timedelta(days=30)
    
    # Circolari di esempio (simulate ma realistiche)
    circolari = [
        {
            "data": datetime.now().date(),
            "titolo": f"Circolare ufficiale {datetime.now().strftime('%d/%m/%Y')} - Test sistema",
            "contenuto": """Si comunica a tutto il personale docente e agli studenti che il sistema di gestione circolari è ora attivo.

FUNZIONALITÀ PRINCIPALI:
1. Ricezione automatica delle circolari
2. Archiviazione digitale
3. Ricerca avanzata per data e categoria
4. Notifiche automatiche

Per problemi tecnici contattare l'ufficio informatico.

Il Dirigente Scolastico""",
            "categoria": "Amministrativa",
            "allegati": ["regolamento_uso_sistema.pdf", "faq_tecniche.pdf"]
        },
        {
            "data": (datetime.now() - timedelta(days=2)).date(),
            "titolo": "Assemblea generale dei genitori - Convocatione ufficiale",
            "contenuto": """Si convoca l'assemblea generale dei genitori per il giorno 25 Gennaio 2026 alle ore 18:30 presso l'Aula Magna.

ORDINE DEL GIORNO:
1. Presentazione bilancio attività 2025
2. Piano didattico 2026
3. Interventi di miglioramento strutture
4. Varie ed eventuali

La partecipazione è caldamente raccomandata.

Cordiali saluti,
Il Consiglio di Istituto""",
            "categoria": "Genitori",
            "allegati": ["convocatione_assemblea.pdf", "ordine_del_giorno.pdf", "modulo_presenza.pdf"]
        },
        {
            "data": (datetime.now() - timedelta(days=7)).date(),
            "titolo": "Calendario esami di recupero - Primo quadrimestre",
            "contenuto": """Si pubblica il calendario degli esami di recupero del primo quadrimestre.

CALENDARIO:
- MATEMATICA: 28 Gennaio 2026, ore 9:00
- ITALIANO: 29 Gennaio 2026, ore 9:00  
- INGLESE: 30 Gennaio 2026, ore 9:00
- SCIENZE: 31 Gennaio 2026, ore 9:00

Si ricorda di portare:
1. Documento di identità
2. Materiale per scrivere
3. Eventuale calcolatrice (solo per matematica)

I risultati saranno pubblicati entro 5 giorni lavorativi.

Il Coordinatore Didattico""",
            "categoria": "Studenti",
            "allegati": ["calendario_esami.pdf", "regolamento_esami.pdf", "aula_assegnazione.pdf"]
        },
        {
            "data": (datetime.now() - timedelta(days=15)).date(),
            "titolo": "Modifiche orario lezioni - Secondo quadrimestre",
            "contenuto": """A partire da Lunedì 2 Febbraio 2026 entrerà in vigore il nuovo orario delle lezioni per il secondo quadrimestre.

PRINCIPALI MODIFICHE:
1. Anticipazione ingresso: ore 8:00 (anziché 8:15)
2. Nuova pausa pranzo: 13:00-14:00
3. Aggiunta rientro pomeridiano per classi quinte: mercoledì

L'orario completo è disponibile in allegato.

Il Dirigente Scolastico""",
            "categoria": "Orario",
            "allegati": ["orario_definitivo.pdf", "note_modifiche.pdf"]
        },
        {
            "data": (datetime.now() - timedelta(days=35)).date(),  # Vecchia (>30 giorni)
            "titolo": "Comunicazione vecchia - Evento passato",
            "contenuto": "Questa circolare è più vecchia di 30 giorni e verrà automaticamente scartata dal sistema.",
            "categoria": "Archivio",
            "allegati": []
        },
        {
            "data": (datetime.now() - timedelta(days=10)).date(),
            "titolo": "Corso di formazione docenti - Nuove tecnologie didattiche",
            "contenuto": """Si organizza un corso di formazione sulle nuove tecnologie didattiche.

DETTAGLI CORSO:
- Data: 20-21 Gennaio 2026
- Orario: 9:00-13:00 / 14:00-17:00
- Relatore: Prof. Marco Rossi
- Sede: Laboratorio Informatico A

Argomenti trattati:
1. Piattaforme e-learning
2. Strumenti di valutazione digitale
3. Risorse didattiche online

Iscrizioni entro il 15 Gennaio.

Il Responsabile Formazione""",
            "categoria": "Docenti",
            "allegati": ["programma_corso.pdf", "modulo_iscrizione.pdf", "bibliografia.pdf"]
        }
    ]
    
    processate = 0
    scartate = 0
    
    print(f"🔍 Trovate {len(circolari)} circolari totali")
    print("📋 Filtro attivo: solo ultimi 30 giorni")
    print("-" * 70)
    
    for i, circ in enumerate(circolari):
        # Controlla se è più vecchia di 30 giorni
        if circ["data"] < data_limite.date():
            scartate += 1
            print(f"⏳ [{i+1}] {circ['data']} - {circ['titolo'][:50]}...")
            print(f"   ❌ SCARTATA (più vecchia di 30 giorni)")
            continue
        
        print(f"\n🔄 [{i+1}] PROCESSANDO CIRCOLARE")
        print(f"   📅 Data: {circ['data']}")
        print(f"   📌 Titolo: {circ['titolo']}")
        print(f"   🏷️  Categoria: {circ['categoria']}")
        
        if circ['allegati']:
            print(f"   📎 Allegati: {len(circ['allegati'])} file")
            for allegato in circ['allegati']:
                print(f"      • {allegato}")
        
        # Salva nel database
        if salva_circolare_sqlite(
            titolo=circ["titolo"],
            contenuto=circ["contenuto"],
            categoria=circ["categoria"],
            data_pub=circ["data"],
            allegati=circ["allegati"]
        ):
            processate += 1
            print(f"   ✅ SALVATA CORRETTAMENTE")
        else:
            scartate += 1
            print(f"   ❌ ERRORE NEL SALVATAGGIO")
    
    print("\n" + "=" * 70)
    print("📊 RISULTATI PROCESSAMENTO")
    print("=" * 70)
    print(f"✅ Circolari processate con successo: {processate}")
    print(f"🗑️  Circolari scartate (vecchie/errori): {scartate}")
    print(f"📅 Periodo considerato: ultimi 30 giorni")
    
    return processate, scartate

# ==============================================================================
# 🛑 GENERAZIONE REPORT
# ==============================================================================

def genera_report_completo(processate, scartate, eliminate, durata):
    """Genera report completo in JSON"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Statistiche database
        cursor.execute("SELECT COUNT(*) FROM circolari")
        totale_circolari = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT categoria) FROM circolari")
        categorie_totali = cursor.fetchone()[0]
        
        cursor.execute("SELECT categoria, COUNT(*) FROM circolari GROUP BY categoria ORDER BY COUNT(*) DESC")
        categorie_stats = cursor.fetchall()
        
        cursor.execute("SELECT MIN(data_pubblicazione), MAX(data_pubblicazione) FROM circolari")
        date_range = cursor.fetchone()
        
        conn.close()
        
        # Report completo
        report = {
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "script": "leggi_circolari.py",
                "versione": "2.0.0",
                "ambiente": "github_actions"
            },
            "esecuzione": {
                "inizio": (datetime.now() - timedelta(seconds=durata)).isoformat(),
                "fine": datetime.now().isoformat(),
                "durata_secondi": round(durata, 2),
                "durata_formattata": f"{int(durata // 60)}m {int(durata % 60)}s"
            },
            "risultati": {
                "circolari_totali_db": totale_circolari,
                "circolari_processate": processate,
                "circolari_scartate": scartate,
                "circolari_eliminate_vecchie": eliminate,
                "success_rate": round((processate / (processate + scartate) * 100), 2) if (processate + scartate) > 0 else 0
            },
            "database": {
                "tipo": "SQLite",
                "percorso": DB_PATH,
                "dimensioni_mb": round(os.path.getsize(DB_PATH) / (1024 * 1024), 2) if os.path.exists(DB_PATH) else 0,
                "date_range": {
                    "prima_circolare": date_range[0] if date_range[0] else "N/A",
                    "ultima_circolare": date_range[1] if date_range[1] else "N/A"
                },
                "categorie_totali": categorie_totali,
                "distribuzione_categorie": [
                    {"categoria": cat, "count": count} for cat, count in categorie_stats
                ]
            },
            "configurazione": {
                "argo_user": ARGO_USER,
                "filtro_giorni": 30,
                "modalita": "simulazione",
                "costo": "gratuito"
            },
            "file_generati": [
                DB_PATH,
                REPORT_PATH,
                STATS_PATH
            ]
        }
        
        # Salva report principale
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Salva statistiche separate
        stats_data = {
            "ultimo_aggiornamento": datetime.now().isoformat(),
            "circolari_totali": totale_circolari,
            "categorie": [
                {"nome": cat, "quantita": count, "percentuale": round((count / totale_circolari * 100), 1) if totale_circolari > 0 else 0}
                for cat, count in categorie_stats
            ],
            "ultime_10_circolari": []
        }
        
        # Aggiungi ultime circolari
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT titolo, categoria, data_pubblicazione 
            FROM circolari 
            ORDER BY data_pubblicazione DESC, created_at DESC 
            LIMIT 10
        """)
        
        ultime_circolari = cursor.fetchall()
        conn.close()
        
        for circ in ultime_circolari:
            stats_data["ultime_10_circolari"].append({
                "titolo": circ[0],
                "categoria": circ[1],
                "data": circ[2]
            })
        
        with open(STATS_PATH, "w", encoding="utf-8") as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Report generati:")
        print(f"   📋 {REPORT_PATH} (report completo)")
        print(f"   📊 {STATS_PATH} (statistiche)")
        
        return report
        
    except Exception as e:
        print(f"❌ Errore generazione report: {e}")
        return None

# ==============================================================================
# 🛑 MAIN EXECUTION
# ==============================================================================

def main():
    """Funzione principale di esecuzione"""
    print("\n" + "=" * 70)
    print("🚀 INIZIO ESECUZIONE ROBOT CIRCOLARI")
    print("=" * 70)
    
    timestamp_inizio = datetime.now()
    
    try:
        # FASE 1: INIZIALIZZAZIONE
        print("\n📦 FASE 1: INIZIALIZZAZIONE DATABASE")
        print("-" * 50)
        if not init_sqlite_db():
            raise Exception("Fallita inizializzazione database SQLite")
        
        # FASE 2: PULIZIA CIRCOLARI VECCHIE
        print("\n🧹 FASE 2: PULIZIA CIRCOLARI VECCHIE")
        print("-" * 50)
        eliminate = elimina_circolari_vecchie_sqlite()
        
        # FASE 3: SCARICAMENTO CIRCOLARI
        print("\n⬇️  FASE 3: SCARICAMENTO CIRCOLARI")
        print("-" * 50)
        processate, scartate = scarica_circolari_simulate()
        
        # FASE 4: AGGIORNAMENTO STATISTICHE
        print("\n📊 FASE 4: AGGIORNAMENTO STATISTICHE")
        print("-" * 50)
        aggiorna_statistiche()
        
        # Calcola durata
        durata = (datetime.now() - timestamp_inizio).total_seconds()
        
        # FASE 5: GENERAZIONE REPORT
        print("\n📄 FASE 5: GENERAZIONE REPORT")
        print("-" * 50)
        report = genera_report_completo(processate, scartate, eliminate, durata)
        
        # FASE 6: SALVATAGGIO LOG FINALE
        print("\n📝 FASE 6: SALVATAGGIO LOG")
        print("-" * 50)
        salva_log_sqlite(
            azione="esecuzione_completata",
            processate=processate,
            scartate=scartate,
            eliminate=eliminate,
            durata=durata
        )
        
        # RIEPILOGO FINALE
        print("\n" + "=" * 70)
        print("🎉 ESECUZIONE COMPLETATA CON SUCCESSO!")
        print("=" * 70)
        
        print(f"\n📈 RIEPILOGO FINALE:")
        print(f"   ⏱️  Durata totale: {durata:.2f} secondi")
        print(f"   ✅ Circolari processate: {processate}")
        print(f"   🗑️  Circolari scartate: {scartate}")
        print(f"   🧹 Circolari eliminate (vecchie): {eliminate}")
        print(f"   💾 Database: {DB_PATH}")
        print(f"   📊 Report: {REPORT_PATH}")
        print(f"   💰 Costo: GRATUITO")
        
        print(f"\n🔧 Configurazione utilizzata:")
        print(f"   • Utente Argo: {ARGO_USER}")
        print(f"   • Filtro giorni: 30")
        print(f"   • Modalità: Simulazione")
        print(f"   • Sistema: {sys.platform}")
        
        print(f"\n📁 File generati:")
        print(f"   1. {DB_PATH} - Database SQLite")
        print(f"   2. {REPORT_PATH} - Report esecuzione")
        print(f"   3. {STATS_PATH} - Statistiche circolari")
        
        print("\n" + "=" * 70)
        print("🤖 ROBOT TERMINATO - Tutte le operazioni completate")
        print("=" * 70)
        
        sys.exit(0)
        
    except Exception as e:
        # GESTIONE ERRORI
        durata = (datetime.now() - timestamp_inizio).total_seconds()
        
        print(f"\n❌ ERRORE CRITICO DURANTE L'ESECUZIONE")
        print(f"   Errore: {e}")
        print(f"   Durata prima dell'errore: {durata:.2f}s")
        
        # Salva log di errore
        salva_log_sqlite(
            azione="errore_critico",
            errore=str(e),
            durata=durata
        )
        
        # Crea report di errore
        errore_report = {
            "timestamp": datetime.now().isoformat(),
            "stato": "errore",
            "errore": str(e),
            "durata_secondi": durata,
            "configurazione": {
                "argo_user": ARGO_USER,
                "db_path": DB_PATH,
                "python_version": sys.version
            }
        }
        
        with open("errore_robot.json", "w") as f:
            json.dump(errore_report, f, indent=2)
        
        print(f"\n📄 Report errore salvato: errore_robot.json")
        print("⚠️  Controlla il file di log per i dettagli")
        
        sys.exit(1)

# ==============================================================================
# 🛑 PUNTO DI INGRESSO
# ==============================================================================

if __name__ == "__main__":
    main()
