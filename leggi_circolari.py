#!/usr/bin/env python3
"""
Script per scaricare circolari da Argo e salvarle in PostgreSQL
Versione ottimizzata per Railway con PostgreSQL
"""

import os
import sys
import time
import requests
import psycopg2
from datetime import datetime, timedelta
import re
from urllib.parse import urlparse

# ==============================================================================
# 🛑 CONFIGURAZIONE DATABASE
# ==============================================================================
print("🔧 Configurazione database...")

# URL del database da Railway
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL non configurato!")
    print("   Configuralo su Railway: Variables → Add DATABASE_URL")
    print("   Il valore dovrebbe essere simile a: postgresql://postgres:password@host:port/database")
    sys.exit(1)

print(f"🔗 Database: {DATABASE_URL.split('@')[-1]}")

# Credenziali Argo
ARGO_USER = os.getenv("ARGO_USER", "davide.marziano.sc26953")
ARGO_PASS = os.getenv("ARGO_PASS", "dvd2Frank.")

# ==============================================================================
# 🛑 FUNZIONI DATABASE
# ==============================================================================

def get_db_connection():
    """Crea una connessione al database PostgreSQL"""
    try:
        # Parse dell'URL per psycopg2
        result = urlparse(DATABASE_URL)
        
        conn = psycopg2.connect(
            database=result.path[1:],  # Rimuove lo slash iniziale
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
                circolari_processate INTEGER DEFAULT 0,
                circolari_scartate INTEGER DEFAULT 0,
                errore TEXT,
                dettagli JSONB DEFAULT '{}'
            )
        """)
        
        # Indici per performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_circolari_data ON circolari(data_pubblicazione)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_circolari_titolo ON circolari(titolo)")
        
        conn.commit()
        print("✅ Database inizializzato correttamente")
        return True
        
    except Exception as e:
        print(f"❌ Errore inizializzazione database: {e}")
        return False
    finally:
        if conn:
            conn.close()

def salva_circolare(titolo, contenuto, categoria, data_pubblicazione, pdf_url=None, allegati=None):
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
        
        if cursor.fetchone():
            # Aggiorna
            cursor.execute("""
                UPDATE circolari 
                SET contenuto = %s, categoria = %s, pdf_url = %s, 
                    allegati = %s, updated_at = CURRENT_TIMESTAMP
                WHERE titolo = %s AND data_pubblicazione = %s
            """, (contenuto, categoria, pdf_url, allegati, titolo, data_pubblicazione))
            print(f"   🔄 Aggiornata circolare esistente")
        else:
            # Inserisci nuova
            cursor.execute("""
                INSERT INTO circolari 
                (titolo, contenuto, categoria, data_pubblicazione, pdf_url, allegati)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (titolo, contenuto, categoria, data_pubblicazione, pdf_url, allegati))
            print(f"   ✅ Nuova circolare salvata")
        
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
            print(f"🗑️  Eliminate {count} circolari vecchie (>30 giorni)")
        else:
            print("✅ Nessuna circolare vecchia da eliminare")
        
        return count
        
    except Exception as e:
        print(f"⚠️ Errore eliminazione circolari vecchie: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def salva_log(processate, scartate, errore=None, dettagli=None):
    """Salva un log dell'esecuzione"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO robot_logs 
            (circolari_processate, circolari_scartate, errore, dettagli)
            VALUES (%s, %s, %s, %s)
        """, (processate, scartate, errore, dettagli or {}))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"⚠️ Errore salvataggio log: {e}")
        return False
    finally:
        if conn:
            conn.close()

# ==============================================================================
# 🛑 FUNZIONI ARGO
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

def simula_scaricamento_circolari():
    """
    Simula lo scaricamento delle circolari da Argo
    In produzione, questa parte sarà sostituita con Selenium/API reali
    """
    print("\n🎭 SIMULAZIONE scaricamento circolari...")
    
    # Data limite: ultimi 30 giorni
    data_limite = datetime.now() - timedelta(days=30)
    
    # Circolari di esempio (simulate)
    circolari_simulate = [
        {
            "data_str": datetime.now().strftime("%d/%m/%Y"),
            "categoria": "Comunicazioni",
            "titolo": "Riunione docenti - gennaio 2026",
            "contenuto": "Si comunica che giorno 20 gennaio 2026 si terrà la riunione di dipartimento.",
            "allegati": ["https://example.com/riunione_2026.pdf"]
        },
        {
            "data_str": (datetime.now() - timedelta(days=3)).strftime("%d/%m/%Y"),
            "categoria": "Genitori",
            "titolo": "Assemblea generale genitori",
            "contenuto": "Invito all'assemblea generale dei genitori prevista per il 25 gennaio.",
            "allegati": ["https://example.com/assemblea.pdf", "https://example.com/ordine_giorno.pdf"]
        },
        {
            "data_str": (datetime.now() - timedelta(days=10)).strftime("%d/%m/%Y"),
            "categoria": "Studenti",
            "titolo": "Calendario scrutini primo quadrimestre",
            "contenuto": "Si pubblica il calendario degli scrutini del primo quadrimestre.",
            "allegati": ["https://example.com/calendario_scrutini.pdf"]
        },
        {
            "data_str": "15/12/2024",  # Più vecchia di 30 giorni
            "categoria": "Amministrativo",
            "titolo": "Comunicazione vecchia",
            "contenuto": "Vecchia comunicazione da scartare.",
            "allegati": []
        },
        {
            "data_str": (datetime.now() - timedelta(days=20)).strftime("%d/%m/%Y"),
            "categoria": "Didattica",
            "titolo": "Modifiche orario secondo quadrimestre",
            "contenuto": "Si comunicano le modifiche all'orario per il secondo quadrimestre.",
            "allegati": ["https://example.com/orario_modifiche.pdf"]
        }
    ]
    
    processate = 0
    scartate = 0
    
    for i, circ in enumerate(circolari_simulate):
        data_circolare = parse_data_argo(circ["data_str"])
        
        if data_circolare is None:
            print(f"⚠️ [{i+1}] Data non valida: '{circ['data_str']}' - Salto")
            continue
        
        # Controlla se è più vecchia di 30 giorni
        if datetime.combine(data_circolare, datetime.min.time()) < data_limite:
            scartate += 1
            print(f"⏳ [{i+1}] {circ['data_str']} - {circ['titolo'][:40]}... (TROPPO VECCHIA)")
            continue
        
        print(f"\n🔄 [{i+1}] {circ['data_str']} - {circ['titolo']}")
        
        # Prepara allegati
        allegati_json = None
        if circ["allegati"]:
            print(f"   📎 {len(circ['allegati'])} allegati")
            allegati_json = circ["allegati"]
        
        # Salva nel database
        if salva_circolare(
            titolo=circ["titolo"],
            contenuto=circ["contenuto"],
            categoria=circ["categoria"],
            data_pubblicazione=data_circolare,
            allegati=allegati_json
        ):
            processate += 1
    
    return processate, scartate

# ==============================================================================
# 🛑 MAIN EXECUTION
# ==============================================================================
def main():
    print("\n" + "="*60)
    print("🔄 SCRIPT CIRCOLARI ARGO - PostgreSQL Edition")
    print("="*60)
    
    # 1. Inizializza database
    print("\n1️⃣ Inizializzazione database...")
    if not init_database():
        print("❌ Impossibile inizializzare il database")
        return
    
    # 2. Elimina circolari vecchie
    print("\n2️⃣ Pulizia circolari vecchie...")
    eliminate = elimina_circolari_vecchie()
    
    # 3. Scarica circolari
    print("\n3️⃣ Scaricamento circolari...")
    processate, scartate = simula_scaricamento_circolari()
    
    # 4. Riepilogo
    print("\n" + "="*60)
    print("📊 RIEPILOGO ESECUZIONE")
    print("="*60)
    print(f"✅ Circolari processate: {processate}")
    print(f"🗑️  Circolari scartate (vecchie): {scartate}")
    print(f"🧹 Circolari eliminate (vecchie): {eliminate}")
    print("="*60)
    
    # 5. Salva log
    try:
        salva_log(
            processate=processate,
            scartate=scartate,
            dettagli={
                "timestamp": datetime.now().isoformat(),
                "tipo": "simulazione",
                "eliminate_vecchie": eliminate
            }
        )
        print("\n📝 Log salvato nel database")
    except Exception as e:
        print(f"\n⚠️ Errore salvataggio log: {e}")
    
    print("\n🎯 Script completato con successo!")

if __name__ == "__main__":
    main()
