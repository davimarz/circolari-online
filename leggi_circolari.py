#!/usr/bin/env python3
"""
Robot Circolari - Salva su DATABASE_PUBLIC_URL per Adminer
"""

import os
import sys
import json
import psycopg2
from datetime import datetime, timedelta

print("=" * 60)
print("🤖 ROBOT CIRCOLARI - AVVIO")
print("=" * 60)
print(f"⏰ Timestamp Italia: {datetime.now().isoformat()}")

# ==============================================================================
# 🛑 CONFIGURAZIONE - USO DATABASE_PUBLIC_URL PER ADMINER
# ==============================================================================

# URL DATABASE PUBBLICO (visibile in Adminer)
DATABASE_URL = "postgresql://postgres:TpsVpUowNnMqSXpvAosQEezxpGPtbPNG@switchback.proxy.rlwy.net:53723/railway"

print("🔧 Configurazione:")
print(f"   • Database: PostgreSQL Railway (PUBBLICO)")
print(f"   • Host: switchback.proxy.rlwy.net:53723")
print(f"   • Modalità: Diretta su database pubblico")

# ==============================================================================
# 🛑 FUNZIONI DATABASE
# ==============================================================================

def get_db_connection():
    """Crea connessione al database pubblico"""
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        print("✅ Connesso al database pubblico")
        return conn
    except Exception as e:
        print(f"❌ Errore connessione: {str(e)[:100]}")
        return None

def init_database():
    """Crea tabella se non esiste"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Tabella SEMPLIFICATA
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circolari (
                id SERIAL PRIMARY KEY,
                titolo TEXT NOT NULL,
                contenuto TEXT,
                data_pubblicazione DATE NOT NULL,
                allegati TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("✅ Tabella circolari pronta")
        return True
        
    except Exception as e:
        print(f"❌ Errore inizializzazione: {e}")
        return False
    finally:
        if conn:
            conn.close()

def salva_circolare(titolo, contenuto, data_pub, allegati=None):
    """Salva una circolare"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        data_pub_str = data_pub.strftime('%Y-%m-%d') if isinstance(data_pub, datetime) else data_pub
        
        # Converti allegati in stringa separata da virgole
        allegati_str = ""
        if allegati and len(allegati) > 0:
            allegati_str = ",".join(allegati)
        
        # Inserisci circolare
        cursor.execute("""
            INSERT INTO circolari (titolo, contenuto, data_pubblicazione, allegati)
            VALUES (%s, %s, %s, %s)
        """, (titolo, contenuto, data_pub_str, allegati_str))
        
        conn.commit()
        print(f"   ✅ Salvata: {titolo[:50]}")
        return True
        
    except Exception as e:
        print(f"❌ Errore salvataggio: {e}")
        return False
    finally:
        if conn:
            conn.close()

# ==============================================================================
# 🛑 SCARICA CIRCOLARI
# ==============================================================================

def scarica_circolari():
    """Scarica circolari di esempio"""
    print("\n" + "=" * 60)
    print("📥 SCARICAMENTO CIRCOLARI")
    print("=" * 60)
    
    data_limite = datetime.now() - timedelta(days=30)
    
    # Circolari di esempio
    circolari = [
        {
            "data": datetime.now().date(),
            "titolo": f"Circolare {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "contenuto": "Questa è una circolare di test generata automaticamente dal robot.",
            "allegati": ["documento.pdf", "allegato.docx"]
        },
        {
            "data": (datetime.now() - timedelta(days=1)).date(),
            "titolo": "Comunicazione importante",
            "contenuto": "Si ricorda a tutti gli studenti di controllare il registro elettronico.",
            "allegati": ["avviso.pdf"]
        },
        {
            "data": (datetime.now() - timedelta(days=3)).date(),
            "titolo": "Orario lezioni aggiornato",
            "contenuto": "Nuovo orario in vigore da lunedì prossimo.",
            "allegati": ["orario.pdf", "note.pdf"]
        }
    ]
    
    processate = 0
    scartate = 0
    
    print(f"🔍 Trovate {len(circolari)} circolari")
    
    for i, circ in enumerate(circolari):
        print(f"\n🔄 [{i+1}] {circ['data']} - {circ['titolo']}")
        
        if circ['allegati']:
            print(f"   📎 Allegati: {', '.join(circ['allegati'])}")
        
        if salva_circolare(
            titolo=circ["titolo"],
            contenuto=circ["contenuto"],
            data_pub=circ["data"],
            allegati=circ["allegati"]
        ):
            processate += 1
        else:
            scartate += 1
    
    return processate, scartate

# ==============================================================================
# 🛑 MAIN
# ==============================================================================

def main():
    """Funzione principale"""
    print("\n🚀 INIZIO ESECUZIONE")
    print("-" * 40)
    
    try:
        # Inizializza database
        print("📦 Inizializzazione database...")
        if not init_database():
            raise Exception("Database non inizializzato")
        
        # Scarica circolari
        print("\n⬇️  Scaricamento circolari...")
        processate, scartate = scarica_circolari()
        
        # Riepilogo
        print("\n" + "=" * 60)
        print("📊 RIEPILOGO")
        print("=" * 60)
        print(f"✅ Circolari salvate: {processate}")
        print(f"❌ Circolari non salvate: {scartate}")
        print(f"🌐 App Streamlit: https://circolari-online-production.up.railway.app")
        print("=" * 60)
        
        print("\n🎯 ROBOT COMPLETATO!")
        print("Le circolari sono ora visibili sulla webapp e in Adminer.")
        
    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
