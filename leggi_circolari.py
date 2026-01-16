#!/usr/bin/env python3
"""
Script per scaricare circolari da Argo e salvarle in PostgreSQL
Versione per GitHub Actions e Railway
"""

import os
import sys
import time
import json
import psycopg2
from datetime import datetime, timedelta
import re
from urllib.parse import urlparse

# ==============================================================================
# 🛑 CONFIGURAZIONE
# ==============================================================================
print("🔧 Configurazione ambiente...")

# Database da GitHub Secrets
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL non configurato!")
    print("   Configuralo in GitHub Secrets")
    sys.exit(1)

# Credenziali Argo da Secrets
ARGO_USER = os.getenv("ARGO_USER")
ARGO_PASS = os.getenv("ARGO_PASS")

if not ARGO_USER or not ARGO_PASS:
    print("⚠️ Credenziali Argo non configurate, uso valori di default")
    ARGO_USER = os.getenv("ARGO_USER", "test_user")
    ARGO_PASS = os.getenv("ARGO_PASS", "test_pass")

print(f"🔗 Database configurato")
print(f"👤 Utente Argo: {ARGO_USER}")

# ==============================================================================
# 🛑 FUNZIONI DATABASE
# ==============================================================================

def get_db_connection():
    """Crea una connessione al database PostgreSQL"""
    try:
        # Parse dell'URL
        result = urlparse(DATABASE_URL)
        
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        return conn
    except Exception as e:
        print(f"❌ Errore connessione database: {e}")
        return None

def init_database():
    """Inizializza le tabelle del database se non esistono"""
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
                pdf_url TEXT,
                allegati JSONB DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                dettagli JSONB DEFAULT '{}',
                errore TEXT
            )
        """)
        
        # Indici
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_circolari_data 
            ON circolari(data_pubblicazione)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_circolari_titolo 
            ON circolari(titolo)
        """)
        
        conn.commit()
        print("✅ Database inizializzato")
        return True
        
    except Exception as e:
        print(f"❌ Errore inizializzazione database: {e}")
        return False
    finally:
        if conn:
            conn.close()

def salva_circolare(titolo, contenuto, categoria, data_pubblicazione, allegati=None):
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
        """, (titolo, data_pubblicazione))
        
        allegati_json = json.dumps(allegati) if allegati else None
        
        if cursor.fetchone():
            # Aggiorna
            cursor.execute("""
                UPDATE circolari 
                SET contenuto = %s, categoria = %s, 
                    allegati = %s, updated_at = CURRENT_TIMESTAMP
                WHERE titolo = %s AND data_pubblicazione = %s
                RETURNING id
            """, (contenuto, categoria, allegati_json, titolo, data_pubblicazione))
            
            circ_id = cursor.fetchone()[0]
            print(f"   🔄 Aggiornata circolare ID: {circ_id}")
        else:
            # Inserisci nuova
            cursor.execute("""
                INSERT INTO circolari 
                (titolo, contenuto, categoria, data_pubblicazione, allegati)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (titolo, contenuto, categoria, data_pubblicazione, allegati_json))
            
            circ_id = cursor.fetchone()[0]
            print(f"   ✅ Nuova circolare ID: {circ_id}")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Errore salvataggio circolare: {e}")
        return False
    finally:
        if conn:
            conn.close()

def elimina_circolari_vecchie():
    """Elimina le circolari più vecchie di 30 giorni"""
    conn = get_db_connection()
    if not conn:
        return 0
    
    try:
        cursor = conn.cursor()
        data_limite = datetime.now() - timedelta(days=30)
        
        # Conta quante verranno eliminate
        cursor.execute("""
            SELECT COUNT(*) FROM circolari 
            WHERE data_pubblicazione < %s
        """, (data_limite,))
        
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Elimina
            cursor.execute("""
                DELETE FROM circolari 
                WHERE data_pubblicazione < %s
            """, (data_limite,))
            
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

def salva_log(azione, processate=0, scartate=0, eliminate=0, errore=None, dettagli=None):
    """Salva un log dell'esecuzione"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        dettagli_json = json.dumps(dettagli) if dettagli else '{}'
        
        cursor.execute("""
            INSERT INTO robot_logs 
            (azione, circolari_processate, circolari_scartate, 
             circolari_eliminate, dettagli, errore)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (azione, processate, scartate, eliminate, dettagli_json, errore))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"⚠️ Errore salvataggio log: {e}")
        return False
    finally:
        if conn:
            conn.close()

# ==============================================================================
# 🛑 FUNZIONI CIRCOLARI
# ==============================================================================

def parse_data_argo(data_str):
    """Converte la data da formato Argo a datetime object"""
    try:
        data_str = data_str.strip()
        
        if not data_str:
            return None
        
        # Rimuovi eventuali ore/minuti
        data_str = data_str.split()[0]
        
        # Prova formato GG/MM/AAAA
        if '/' in data_str:
            parts = data_str.split('/')
            if len(parts) == 3:
                giorno, mese, anno = parts
                if len(anno) == 2:
                    anno = '20' + anno
                return datetime(int(anno), int(mese), int(giorno)).date()
        
        # Prova formato GG-MM-AAAA
        elif '-' in data_str:
            parts = data_str.split('-')
            if len(parts) == 3:
                giorno, mese, anno = parts
                if len(anno) == 2:
                    anno = '20' + anno
                return datetime(int(anno), int(mese), int(giorno)).date()
        
        # Prova estrarre data con regex
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', data_str)
        if match:
            giorno, mese, anno = match.groups()
            if len(anno) == 2:
                anno = '20' + anno
            return datetime(int(anno), int(mese), int(giorno)).date()
        
        print(f"⚠️ Formato data non riconosciuto: '{data_str}'")
        return None
        
    except Exception as e:
        print(f"⚠️ Errore parsing data '{data_str}': {e}")
        return None

def scarica_circolari_simulate():
    """
    Simula lo scaricamento delle circolari
    In produzione, integrare con API/Selenium reali
    """
    print("\n🎭 SIMULAZIONE scaricamento circolari...")
    
    data_limite = datetime.now() - timedelta(days=30)
    
    # Dati di esempio
    circolari = [
        {
            "data_str": datetime.now().strftime("%d/%m/%Y"),
            "categoria": "Comunicazioni",
            "titolo": f"Circolare test {datetime.now().strftime('%Y-%m-%d')}",
            "contenuto": f"Circolare di test generata automaticamente il {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "allegati": None
        },
        {
            "data_str": (datetime.now() - timedelta(days=5)).strftime("%d/%m/%Y"),
            "categoria": "Genitori",
            "titolo": "Avviso assemblea genitori",
            "contenuto": "Si comunica l'assemblea generale dei genitori prevista per il prossimo mese.",
            "allegati": ["avviso_assemblea.pdf"]
        },
        {
            "data_str": (datetime.now() - timedelta(days=15)).strftime("%d/%m/%Y"),
            "categoria": "Studenti",
            "titolo": "Calendario esami di recupero",
            "contenuto": "Si pubblica il calendario degli esami di recupero del primo quadrimestre.",
            "allegati": ["calendario_esami.pdf", "modalita_esame.pdf"]
        },
        {
            "data_str": "01/12/2024",  # Vecchia
            "categoria": "Amministrativo",
            "titolo": "Comunicazione vecchia",
            "contenuto": "Vecchia comunicazione che verrà scartata.",
            "allegati": []
        }
    ]
    
    processate = 0
    scartate = 0
    
    for i, circ in enumerate(circolari):
        data_circolare = parse_data_argo(circ["data_str"])
        
        if data_circolare is None:
            print(f"⚠️ [{i+1}] Data non valida: '{circ['data_str']}'")
            scartate += 1
            continue
        
        # Controlla se è più vecchia di 30 giorni
        if datetime.combine(data_circolare, datetime.min.time()) < data_limite:
            print(f"⏳ [{i+1}] {circ['data_str']} - {circ['titolo'][:40]}... (VECCHIA)")
            scartate += 1
            continue
        
        print(f"\n🔄 [{i+1}] {circ['data_str']} - {circ['titolo']}")
        
        if circ["allegati"]:
            print(f"   📎 Allegati: {', '.join(circ['allegati'])}")
        
        # Salva nel database
        if salva_circolare(
            titolo=circ["titolo"],
            contenuto=circ["contenuto"],
            categoria=circ["categoria"],
            data_pubblicazione=data_circolare,
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
    print("🤖 ROBOT CIRCOLARI - GitHub Actions")
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
        print(f"⏱️  Durata esecuzione: {durata:.2f} secondi")
        print("="*60)
        
        # 5. Salva log
        dettagli = {
            "inizio": timestamp_inizio.isoformat(),
            "fine": datetime.now().isoformat(),
            "durata_secondi": durata,
            "ambiente": "github_actions"
        }
        
        salva_log(
            azione="scaricamento",
            processate=processate,
            scartate=scartate,
            eliminate=eliminate,
            dettagli=dettagli
        )
        
        print("\n🎯 Robot completato con successo!")
        
    except Exception as e:
        print(f"\n❌ ERRORE CRITICO: {e}")
        
        # Salva log di errore
        salva_log(
            azione="errore",
            errore=str(e),
            dettagli={
                "timestamp": datetime.now().isoformat(),
                "errore": str(e)
            }
        )
        
        sys.exit(1)

if __name__ == "__main__":
    main()
