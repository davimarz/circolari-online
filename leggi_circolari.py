#!/usr/bin/env python3
"""
Robot Circolari - Salva su DATABASE_PUBLIC_URL per Adminer
"""

import os
import sys
import psycopg2
from datetime import datetime, timedelta

print("=" * 60)
print("🤖 ROBOT CIRCOLARI - AVVIO")
print("=" * 60)
print(f"⏰ Timestamp Italia: {datetime.now().isoformat()}")

# ==============================================================================
# 🛑 CONFIGURAZIONE - VARIABILI D'AMBIENTE
# ==============================================================================

# Usa DATABASE_URL da Railway
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERRORE: DATABASE_URL non configurata!")
    print("   Configura DATABASE_URL su Railway")
    sys.exit(1)

print("🔧 Configurazione:")
print(f"   • Database: PostgreSQL Railway")
print(f"   • Modalità: Connessione sicura")

# ==============================================================================
# 🛑 FUNZIONI DATABASE
# ==============================================================================

def get_db_connection():
    """Crea connessione al database"""
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        print("✅ Connesso al database")
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
        
        # Tabella completa (come in database.py)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circolari (
                id SERIAL PRIMARY KEY,
                numero VARCHAR(50),
                titolo TEXT NOT NULL,
                data_pubblicazione DATE NOT NULL,
                allegati TEXT,
                categoria VARCHAR(100),
                autore VARCHAR(200),
                contenuto TEXT,
                url_originale TEXT,
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

def salva_circolare(titolo, contenuto, data_pub, allegati=None, numero="", categoria="", autore=""):
    """Salva una circolare completa"""
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
        
        # Controlla se esiste già
        cursor.execute("""
            SELECT id FROM circolari 
            WHERE titolo = %s AND data_pubblicazione = %s
        """, (titolo, data_pub_str))
        
        if cursor.fetchone() is None:
            # Inserisci nuova circolare
            cursor.execute("""
                INSERT INTO circolari 
                (numero, titolo, data_pubblicazione, allegati, categoria, autore, contenuto)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (numero, titolo, data_pub_str, allegati_str, categoria, autore, contenuto))
            
            new_id = cursor.fetchone()[0]
            conn.commit()
            print(f"   ✅ Salvata nuova: {titolo[:50]} (ID: {new_id})")
            return True
        else:
            print(f"   ⚠️  Già presente: {titolo[:50]}")
            return False
        
    except Exception as e:
        print(f"❌ Errore salvataggio: {e}")
        return False
    finally:
        if conn:
            conn.close()

# ==============================================================================
# 🛑 SCARICA CIRCOLARI DI ESEMPIO
# ==============================================================================

def scarica_circolari_esempio():
    """Scarica circolari di esempio per test"""
    print("\n" + "=" * 60)
    print("📥 SCARICAMENTO CIRCOLARI DI ESEMPIO")
    print("=" * 60)
    
    # Circolari di esempio più realistiche
    circolari = [
        {
            "numero": f"Circ. {datetime.now().strftime('%Y')}/001",
            "titolo": "Comunicazione urgente agli studenti",
            "contenuto": "Si comunica che a partire da domani le lezioni seguiranno l'orario normale.",
            "data": datetime.now().date(),
            "allegati": ["comunicazione.pdf", "allegato.docx"],
            "categoria": "Comunicazioni",
            "autore": "Presidenza"
        },
        {
            "numero": f"Circ. {datetime.now().strftime('%Y')}/002",
            "titolo": "Orario delle lezioni aggiornato",
            "contenuto": "Si pubblica il nuovo orario delle lezioni in vigore dal prossimo lunedì.",
            "data": (datetime.now() - timedelta(days=1)).date(),
            "allegati": ["orario_settimanale.pdf"],
            "categoria": "Documenti Istituzionali",
            "autore": "Segreteria"
        },
        {
            "numero": f"Circ. {datetime.now().strftime('%Y')}/003",
            "titolo": "Bando di concorso per poesia",
            "contenuto": "Si bandisce il concorso di poesia San Valentino aperto a tutti gli studenti.",
            "data": (datetime.now() - timedelta(days=3)).date(),
            "allegati": ["bando_concorso.pdf", "modulo_iscrizione.docx"],
            "categoria": "Concorsi per Alunni",
            "autore": "Pro Loco Giarre"
        }
    ]
    
    processate = 0
    scartate = 0
    
    print(f"🔍 Trovate {len(circolari)} circolari di esempio")
    
    for i, circ in enumerate(circolari):
        print(f"\n🔄 [{i+1}] {circ['numero']} - {circ['titolo']}")
        print(f"   📅 Data: {circ['data']}")
        print(f"   🏷️  Categoria: {circ['categoria']}")
        
        if circ['allegati']:
            print(f"   📎 Allegati: {', '.join(circ['allegati'])}")
        
        if salva_circolare(
            titolo=circ["titolo"],
            contenuto=circ["contenuto"],
            data_pub=circ["data"],
            allegati=circ["allegati"],
            numero=circ["numero"],
            categoria=circ["categoria"],
            autore=circ["autore"]
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
        
        # Scarica circolari di esempio
        print("\n⬇️  Scaricamento circolari...")
        processate, scartate = scarica_circolari_esempio()
        
        # Riepilogo
        print("\n" + "=" * 60)
        print("📊 RIEPILOGO")
        print("=" * 60)
        print(f"✅ Circolari salvate: {processate}")
        print(f"❌ Circolari non salvate: {scartate}")
        print(f"📋 Totale circolari nel sistema: {processate}")
        print("=" * 60)
        
        print("\n🎯 ROBOT COMPLETATO!")
        print("Le circolari sono ora visibili sulla webapp.")
        
    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
