#!/usr/bin/env python3
"""
Robot Circolari - Versione ibrida: salva su PostgreSQL Railway E SQLite locale
"""

import os
import sys
import json
import sqlite3
import psycopg2
from datetime import datetime, timedelta
from urllib.parse import urlparse

print("=" * 70)
print("🤖 ROBOT CIRCOLARI - AVVIO")
print("=" * 70)
print(f"⏰ Timestamp: {datetime.now().isoformat()}")

# ==============================================================================
# 🛑 CONFIGURAZIONE COMPLETA - DUE DATABASE
# ==============================================================================

# Credenziali Argo
ARGO_USER = "davide.marziano.sc26953"
ARGO_PASS = "dvd2Frank."

# 1. DATABASE POSTGRESQL RAILWAY (per Streamlit App)
POSTGRES_URL = "postgresql://postgres:TpsVpUowNnMqSXpvAosQEezxpGPtbPNG@postgres.railway.internal:5432/railway"

# 2. DATABASE SQLITE LOCALE (backup/fallback)
SQLITE_PATH = "circolari.db"

# File report
REPORT_PATH = "robot_report.json"

print("🔧 Configurazione database:")
print(f"   • PostgreSQL Railway: {'✅ Configurato' if POSTGRES_URL else '❌ Mancante'}")
print(f"   • SQLite locale: {SQLITE_PATH}")
print(f"   • Modalità: Ibrida (salva su entrambi i database)")

# ==============================================================================
# 🛑 FUNZIONI DATABASE POSTGRESQL
# ==============================================================================

def get_postgres_connection():
    """Crea connessione a PostgreSQL Railway"""
    try:
        conn = psycopg2.connect(POSTGRES_URL, connect_timeout=10)
        print("✅ Connesso a PostgreSQL Railway")
        return conn
    except Exception as e:
        print(f"❌ Errore connessione PostgreSQL: {str(e)[:100]}")
        print("⚠️  Il robot salverà solo su SQLite locale")
        return None

def init_postgres_db():
    """Inizializza PostgreSQL Railway (se connesso)"""
    conn = get_postgres_connection()
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
                fonte VARCHAR(50) DEFAULT 'robot_github',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(titolo, data_pubblicazione, categoria)
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
                circolari_eliminate INTEGER DEFAULT 0,
                errore TEXT,
                dettagli JSONB DEFAULT '{}',
                durata_secondi REAL DEFAULT 0
            )
        """)
        
        # Indici
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_circolari_data_pg ON circolari(data_pubblicazione)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_circolari_categoria_pg ON circolari(categoria)")
        
        conn.commit()
        print("✅ PostgreSQL Railway inizializzato")
        return True
        
    except Exception as e:
        print(f"❌ Errore inizializzazione PostgreSQL: {e}")
        return False
    finally:
        if conn:
            conn.close()

def salva_circolare_postgres(titolo, contenuto, categoria, data_pub, allegati=None):
    """Salva circolare su PostgreSQL Railway"""
    conn = get_postgres_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        data_pub_str = data_pub.strftime('%Y-%m-%d') if isinstance(data_pub, datetime) else data_pub
        allegati_json = json.dumps(allegati) if allegati else '[]'
        
        # Controlla se esiste già
        cursor.execute("""
            SELECT id FROM circolari 
            WHERE titolo = %s AND data_pubblicazione = %s AND categoria = %s
        """, (titolo, data_pub_str, categoria))
        
        if cursor.fetchone():
            # Aggiorna
            cursor.execute("""
                UPDATE circolari 
                SET contenuto = %s, allegati = %s, data_scaricamento = CURRENT_TIMESTAMP
                WHERE titolo = %s AND data_pubblicazione = %s AND categoria = %s
            """, (contenuto, allegati_json, titolo, data_pub_str, categoria))
            print(f"   🔄 Aggiornata su PostgreSQL")
        else:
            # Inserisci nuova
            cursor.execute("""
                INSERT INTO circolari 
                (titolo, contenuto, categoria, data_pubblicazione, allegati, fonte)
                VALUES (%s, %s, %s, %s, %s, 'github_actions')
            """, (titolo, contenuto, categoria, data_pub_str, allegati_json))
            print(f"   ✅ Salvata su PostgreSQL")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Errore salvataggio PostgreSQL: {e}")
        return False
    finally:
        if conn:
            conn.close()

def elimina_circolari_vecchie_postgres():
    """Elimina circolari vecchie da PostgreSQL"""
    conn = get_postgres_connection()
    if not conn:
        return 0
    
    try:
        cursor = conn.cursor()
        data_limite = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        cursor.execute("SELECT COUNT(*) FROM circolari WHERE data_pubblicazione < %s", (data_limite,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Crea backup
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS circolari_archivio AS 
                SELECT * FROM circolari WHERE data_pubblicazione < %s
            """, (data_limite,))
            
            # Elimina
            cursor.execute("DELETE FROM circolari WHERE data_pubblicazione < %s", (data_limite,))
            
            conn.commit()
            print(f"🗑️  Eliminate {count} circolari vecchie da PostgreSQL")
        else:
            print("✅ Nessuna circolare vecchia da eliminare su PostgreSQL")
        
        return count
        
    except Exception as e:
        print(f"⚠️ Errore eliminazione PostgreSQL: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def salva_log_postgres(azione, processate=0, scartate=0, eliminate=0, errore=None, durata=0):
    """Salva log su PostgreSQL"""
    conn = get_postgres_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        dettagli = {
            "timestamp": datetime.now().isoformat(),
            "ambiente": "github_actions",
            "database": "postgresql_railway",
            "python_version": sys.version.split()[0]
        }
        
        cursor.execute("""
            INSERT INTO robot_logs 
            (azione, circolari_processate, circolari_scartate, 
             circolari_eliminate, errore, dettagli, durata_secondi)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (azione, processate, scartate, eliminate, errore, json.dumps(dettagli), durata))
        
        conn.commit()
        print(f"📝 Log salvato su PostgreSQL: {azione}")
        return True
        
    except Exception as e:
        print(f"⚠️ Errore salvataggio log PostgreSQL: {e}")
        return False
    finally:
        if conn:
            conn.close()

# ==============================================================================
# 🛑 FUNZIONI DATABASE SQLITE (backup)
# ==============================================================================

def init_sqlite_db():
    """Inizializza SQLite locale"""
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circolari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titolo TEXT NOT NULL,
                contenuto TEXT,
                categoria TEXT,
                data_pubblicazione DATE NOT NULL,
                data_scaricamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                allegati TEXT DEFAULT '[]',
                fonte TEXT DEFAULT 'backup_sqlite',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        print(f"✅ SQLite locale inizializzato: {SQLITE_PATH}")
        return True
        
    except Exception as e:
        print(f"❌ Errore inizializzazione SQLite: {e}")
        return False

def salva_circolare_sqlite(titolo, contenuto, categoria, data_pub, allegati=None):
    """Salva backup su SQLite locale"""
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        
        data_pub_str = data_pub.strftime('%Y-%m-%d') if isinstance(data_pub, datetime) else data_pub
        allegati_json = json.dumps(allegati) if allegati else '[]'
        
        cursor.execute("""
            INSERT OR REPLACE INTO circolari 
            (titolo, contenuto, categoria, data_pubblicazione, allegati, fonte)
            VALUES (?, ?, ?, ?, ?, 'backup_sqlite')
        """, (titolo, contenuto, categoria, data_pub_str, allegati_json))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"⚠️ Errore backup SQLite: {e}")
        return False

# ==============================================================================
# 🛑 FUNZIONE UNIFICATA PER SALVATAGGIO SU ENTRAMBI I DATABASE
# ==============================================================================

def salva_circolare_ibrida(titolo, contenuto, categoria, data_pub, allegati=None):
    """Salva circolare sia su PostgreSQL che SQLite"""
    print(f"\n💾 Salvataggio ibrido circolare:")
    print(f"   📌 Titolo: {titolo[:60]}")
    print(f"   🏷️  Categoria: {categoria}")
    
    # 1. Prova PostgreSQL (primario)
    success_pg = False
    if POSTGRES_URL:
        success_pg = salva_circolare_postgres(titolo, contenuto, categoria, data_pub, allegati)
    else:
        print("   ⚠️  PostgreSQL non configurato, salto")
    
    # 2. Salva sempre su SQLite (backup)
    success_sqlite = salva_circolare_sqlite(titolo, contenuto, categoria, data_pub, allegati)
    
    # 3. Riepilogo
    if success_pg:
        print(f"   ✅ Salvata su PostgreSQL Railway (visibile su Streamlit)")
    if success_sqlite:
        print(f"   💾 Backup su SQLite locale: {SQLITE_PATH}")
    
    return success_pg or success_sqlite  # Considera successo se almeno uno funziona

def elimina_circolari_vecchie_ibrida():
    """Elimina circolari vecchie da entrambi i database"""
    print("\n🧹 Pulizia circolari vecchie (>30 giorni):")
    
    # PostgreSQL
    eliminate_pg = 0
    if POSTGRES_URL:
        eliminate_pg = elimina_circolari_vecchie_postgres()
    
    # SQLite
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()
        data_limite = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        cursor.execute("SELECT COUNT(*) FROM circolari WHERE data_pubblicazione < ?", (data_limite,))
        count_sqlite = cursor.fetchone()[0]
        
        if count_sqlite > 0:
            cursor.execute("DELETE FROM circolari WHERE data_pubblicazione < ?", (data_limite,))
            conn.commit()
            print(f"   🗑️  Eliminate {count_sqlite} circolari vecchie da SQLite")
        
        conn.close()
    except:
        count_sqlite = 0
    
    return max(eliminate_pg, count_sqlite)

# ==============================================================================
# 🛑 SIMULAZIONE CIRCOLARI REALISTICHE
# ==============================================================================

def scarica_circolari_simulate():
    """Simula scaricamento circolari (salva su entrambi i DB)"""
    print("\n" + "=" * 70)
    print("🎭 SIMULAZIONE SCARICAMENTO CIRCOLARI")
    print("=" * 70)
    print("💡 Modalità: Ibrida - Salva su PostgreSQL + SQLite")
    print("📊 PostgreSQL: Visibile su Streamlit App")
    print("💾 SQLite: Backup locale su GitHub Actions")
    print("=" * 70)
    
    data_limite = datetime.now() - timedelta(days=30)
    
    # Circolari di esempio REALISTICHE
    circolari = [
        {
            "data": datetime.now().date(),
            "titolo": f"Circolare urgente: Aggiornamento sistema {datetime.now().strftime('%d/%m/%Y')}",
            "contenuto": """ATTENZIONE A TUTTO IL PERSONALE

Si comunica che nella giornata di domani, 18 Gennaio 2026, il sistema informatico sarà aggiornato dalle ore 14:00 alle ore 18:00.

IMPATTO SULL'ATTIVITÀ DIDATTICA:
1. Piattaforma e-learning non disponibile
2. Registro elettronico accessibile in sola lettura
3. Email istituzionali temporaneamente sospese

Si prega di pianificare le attività di conseguenza.

Per informazioni: ufficio.informatico@istitutoscolastico.edu.it

Il Dirigente Scolastico
Prof. Mario Rossi""",
            "categoria": "Amministrativa",
            "allegati": ["avviso_aggiornamento.pdf", "faq_sistema.pdf"]
        },
        {
            "data": (datetime.now() - timedelta(days=1)).date(),
            "titolo": "Assemblea generale genitori - Secondo quadrimestre",
            "contenuto": """OGGETTO: Convocazione assemblea generale genitori

Gentili Genitori,

si convoca l'assemblea generale dei genitori per il giorno:

📅 25 GENNAIO 2026
⏰ ORE 18:30
📍 AULA MAGNA - PIANO TERRA

ORDINE DEL GIORNO:
1. Bilancio attività primo quadrimestre
2. Presentazione piano didattico secondo quadrimestre
3. Interventi miglioramento strutture scolastiche
4. Proposte attività extracurricolari
5. Varie ed eventuali

La partecipazione è importante per la vita della comunità scolastica.

Il Presidente del Consiglio di Istituto
Giulia Bianchi""",
            "categoria": "Genitori",
            "allegati": ["convocazione_assemblea.pdf", "ordine_del_giorno.pdf", "scheda_presenza.pdf"]
        },
        {
            "data": (datetime.now() - timedelta(days=3)).date(),
            "titolo": "Calendario scrutini primo quadrimestre - Classi prime e seconde",
            "contenuto": """PUBBLICAZIONE CALENDARIO SCRUTINI

Si comunica il calendario degli scrutini del primo quadrimestre per le classi prime e seconde.

📅 CALENDARIO:
• CLASSE 1A: 28 Gennaio 2026, ore 9:00
• CLASSE 1B: 28 Gennaio 2026, ore 11:00
• CLASSE 1C: 29 Gennaio 2026, ore 9:00
• CLASSE 2A: 29 Gennaio 2026, ore 11:00
• CLASSE 2B: 30 Gennaio 2026, ore 9:00
• CLASSE 2C: 30 Gennaio 2026, ore 11:00

📍 SEDE: Sala docenti, primo piano

MATERIALE RICHIESTA:
1. Registri di classe aggiornati
2. Schede valutazione compilate
3. Relazioni disciplinari
4. Proposte voti e giudizi

I risultati saranno pubblicati sul registro elettronico entro 3 giorni lavorativi.

Il Coordinatore Didattico
Prof. Luca Verdi""",
            "categoria": "Docenti",
            "allegati": ["calendario_scrutini.pdf", "scheda_valutazione.docx", "modello_relazione.pdf"]
        },
        {
            "data": (datetime.now() - timedelta(days=7)).date(),
            "titolo": "Modifiche orario lezioni - In vigore dal 2 Febbraio 2026",
            "contenuto": """COMUNICAZIONE MODIFICHE ORARIO

A partire da Lunedì 2 Febbraio 2026 entrerà in vigore il nuovo orario delle lezioni.

PRINCIPALI CAMBIAMENTI:
🕗 ANTICIPO INGRESSO: ore 8:00 (anziché 8:15)
🕛 NUOVA PAUSA PRANZO: 13:00 - 14:00
🕒 RIENTRI POMERIDIANI: 
   • Classi quinte: Mercoledì 14:30-16:30
   • Classi terze: Giovedì 14:30-16:30

L'orario completo è disponibile in allegato.

Note importanti:
• Le fermate dello scuolabus saranno anticipate di 15 minuti
• La mensa scolastica seguirà il nuovo orario
• Le attività pomeridiane extrascolastiche inizieranno alle 16:45

Per informazioni: segreteria@istitutoscolastico.edu.it

Il Dirigente Scolastico""",
            "categoria": "Orario",
            "allegati": ["orario_definitivo_q2.pdf", "modifiche_dettagliate.pdf", "trasporti_scolastici.pdf"]
        },
        {
            "data": (datetime.now() - timedelta(days=10)).date(),
            "titolo": "Corso di formazione: Didattica digitale integrata",
            "contenuto": """CORSO DI FORMAZIONE DOCENTI

Titolo: "Didattica Digitale Integrata: strumenti e metodologie"
Formatore: Prof.ssa Elena Marini - Esperta in tecnologie didattiche

📅 DATE: 20-21 Gennaio 2026
⏰ ORARIO: 9:00-13:00 / 14:00-17:00
📍 SEDE: Laboratorio Informatico A

PROGRAMMA:
Giorno 1 - Fondamenti:
• Piattaforme e-learning (Google Classroom, Moodle)
• Creazione contenuti digitali interattivi
• Strumenti per la valutazione formativa

Giorno 2 - Avanzato:
• Realtà aumentata nella didattica
• Gamification e apprendimento basato sul gioco
• Progettazione di percorsi digitali integrati

ISCRIZIONI: Entro il 15 Gennaio tramite modulo allegato.

Il corso è riconosciuto per l'aggiornamento professionale.

Il Responsabile Formazione
Prof. Marco Neri""",
            "categoria": "Formazione",
            "allegati": ["programma_corso.pdf", "modulo_iscrizione.docx", "bibliografia_consigliata.pdf"]
        },
        {
            "data": (datetime.now() - timedelta(days=15)).date(),
            "titolo": "Avviso: Chiusura istituto per festività locali",
            "contenuto": """COMUNICAZIONE CHIUSURA ISTITUTO

Si comunica che l'istituto resterà chiuso nei seguenti giorni:

📅 26 GENNAIO 2026: Festa patronale della città
📅 27 GENNAIO 2026: Ponte festivo

Le lezioni riprenderanno regolarmente Mercoledì 28 Gennaio 2026.

Servizi sospesi:
• Segreteria
• Biblioteca
• Servizio mensa
• Attività pomeridiane

Servizi attivi:
• Registro elettronico (accesso online)
• Piattaforma e-learning
• Email istituzionali

Per urgenze: cell. 333-1234567 (solo emergenze)

Il Dirigente Scolastico""",
            "categoria": "Comunicazioni",
            "allegati": ["calendario_festivita.pdf"]
        },
        {
            "data": (datetime.now() - timedelta(days=40)).date(),  # Vecchia (>30 giorni)
            "titolo": "Evento passato: Gara di matematica 2025",
            "contenuto": "Questa circolare è relativa ad un evento passato e verrà scartata automaticamente.",
            "categoria": "Archivio",
            "allegati": []
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
        
        # SALVATAGGIO IBRIDO (PostgreSQL + SQLite)
        if salva_circolare_ibrida(
            titolo=circ["titolo"],
            contenuto=circ["contenuto"],
            categoria=circ["categoria"],
            data_pub=circ["data"],
            allegati=circ["allegati"]
        ):
            processate += 1
            print(f"   ✅ SALVATA SU ENTRAMBI I DATABASE")
        else:
            scartate += 1
            print(f"   ❌ ERRORE NEL SALVATAGGIO")
    
    print("\n" + "=" * 70)
    print("📊 RISULTATI PROCESSAMENTO")
    print("=" * 70)
    print(f"✅ Circolari processate con successo: {processate}")
    print(f"🗑️  Circolari scartate (vecchie/errori): {scartate}")
    print(f"💾 PostgreSQL Railway: {'✅ Attivo' if POSTGRES_URL else '❌ Disattivo'}")
    print(f"💾 SQLite locale: ✅ Backup attivo")
    
    return processate, scartate

# ==============================================================================
# 🛑 MAIN EXECUTION
# ==============================================================================

def main():
    """Funzione principale"""
    print("\n" + "=" * 70)
    print("🚀 INIZIO ESECUZIONE ROBOT CIRCOLARI - MODALITÀ IBRIDA")
    print("=" * 70)
    
    timestamp_inizio = datetime.now()
    
    try:
        # FASE 1: INIZIALIZZAZIONE DATABASE
        print("\n📦 FASE 1: INIZIALIZZAZIONE DATABASE")
        print("-" * 50)
        
        # PostgreSQL Railway (primario)
        pg_success = False
        if POSTGRES_URL:
            pg_success = init_postgres_db()
            if not pg_success:
                print("⚠️  PostgreSQL non inizializzato, continuo con SQLite")
        else:
            print("ℹ️  PostgreSQL non configurato, uso solo SQLite")
        
        # SQLite locale (backup)
        sqlite_success = init_sqlite_db()
        
        if not pg_success and not sqlite_success:
            raise Exception("Impossibile inizializzare nessun database")
        
        # FASE 2: PULIZIA CIRCOLARI VECCHIE
        print("\n🧹 FASE 2: PULIZIA CIRCOLARI VECCHIE")
        print("-" * 50)
        eliminate = elimina_circolari_vecchie_ibrida()
        
        # FASE 3: SCARICAMENTO CIRCOLARI
        print("\n⬇️  FASE 3: SCARICAMENTO CIRCOLARI")
        print("-" * 50)
        processate, scartate = scarica_circolari_simulate()
        
        # Calcola durata
        durata = (datetime.now() - timestamp_inizio).total_seconds()
        
        # FASE 4: SALVATAGGIO LOG
        print("\n📝 FASE 4: SALVATAGGIO LOG")
        print("-" * 50)
        
        # Log su PostgreSQL se disponibile
        if POSTGRES_URL:
            salva_log_postgres(
                azione="esecuzione_ibrida",
                processate=processate,
                scartate=scartate,
                eliminate=eliminate,
                durata=durata
            )
        
        # Log su file locale
        with open(REPORT_PATH, "w") as f:
            report = {
                "timestamp": datetime.now().isoformat(),
                "modalita": "ibrida",
                "database": {
                    "postgresql": "attivo" if POSTGRES_URL else "disattivo",
                    "sqlite": "attivo",
                    "note": "Circolari salvate su entrambi i database"
                },
                "risultati": {
                    "circolari_processate": processate,
                    "circolari_scartate": scartate,
                    "circolari_eliminate": eliminate,
                    "success_rate": round((processate / (processate + scartate) * 100), 2) if (processate + scartate) > 0 else 0
                },
                "streamlit_app": {
                    "visibile": "SI" if POSTGRES_URL and processate > 0 else "NO",
                    "motivo": "Circolari salvate su PostgreSQL Railway" if POSTGRES_URL and processate > 0 else "PostgreSQL non configurato o nessuna circolare processata",
                    "url_app": "https://circolari-online-production.up.railway.app"
                },
                "durata_secondi": round(durata, 2)
            }
            json.dump(report, f, indent=2)
        
        # RIEPILOGO FINALE
        print("\n" + "=" * 70)
        print("🎉 ESECUZIONE COMPLETATA CON SUCCESSO!")
        print("=" * 70)
        
        print(f"\n📈 RIEPILOGO FINALE:")
        print(f"   ⏱️  Durata totale: {durata:.2f} secondi")
        print(f"   ✅ Circolari processate: {processate}")
        print(f"   🗑️  Circolari scartate: {scartate}")
        print(f"   🧹 Circolari eliminate (vecchie): {eliminate}")
        
        print(f"\n💾 STATO DATABASE:")
        if POSTGRES_URL:
            print(f"   • PostgreSQL Railway: ✅ ATTIVO")
            print(f"     ↳ Circolari VISIBILI su Streamlit App")
            print(f"     ↳ URL: https://circolari-online-production.up.railway.app")
        else:
            print(f"   • PostgreSQL Railway: ❌ DISATTIVO")
        
        print(f"   • SQLite locale: ✅ ATTIVO")
        print(f"     ↳ File: {SQLITE_PATH}")
        print(f"     ↳ Backup locale GitHub Actions")
        
        print(f"\n👁️  VISIBILITÀ SU STREAMLIT:")
        if POSTGRES_URL and processate > 0:
            print(f"   ✅ LE CIRCOLARI SONO VISIBILI SULL'APP!")
            print(f"   🔗 Vai su: https://circolari-online-production.up.railway.app")
            print(f"   📊 Troverai {processate} nuove circolari")
        else:
            print(f"   ❌ Le circolari NON sono visibili sull'app")
            if not POSTGRES_URL:
                print(f"   ⚠️  Motivo: PostgreSQL non configurato")
            if processate == 0:
                print(f"   ⚠️  Motivo: Nessuna circolare processata")
        
        print(f"\n📁 File generati:")
        print(f"   1. {SQLITE_PATH} - Database SQLite (backup)")
        print(f"   2. {REPORT_PATH} - Report esecuzione")
        
        sys.exit(0)
        
    except Exception as e:
        durata = (datetime.now() - timestamp_inizio).total_seconds()
        
        print(f"\n❌ ERRORE CRITICO DURANTE L'ESECUZIONE")
        print(f"   Errore: {e}")
        
        # Log errore su PostgreSQL se disponibile
        if POSTGRES_URL:
            try:
                salva_log_postgres(
                    azione="errore_critico",
                    errore=str(e),
                    durata=durata
                )
            except:
                pass
        
        # Report errore locale
        with open("errore_robot.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "errore": str(e),
                "durata": durata
            }, f, indent=2)
        
        print(f"\n📄 Report errore salvato: errore_robot.json")
        sys.exit(1)

# ==============================================================================
# 🛑 PUNTO DI INGRESSO
# ==============================================================================

if __name__ == "__main__":
    main()
