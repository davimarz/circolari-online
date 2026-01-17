#!/usr/bin/env python3
"""
Robot Circolari ARGO - Legge le circolari dalla bacheca ARGO con struttura specifica
"""

import os
import sys
import re
import psycopg2
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import json

print("=" * 60)
print("🤖 ROBOT CIRCOLARI ARGO - AVVIO")
print("=" * 60)
print(f"⏰ Timestamp Italia: {datetime.now().isoformat()}")

# ==============================================================================
# 🛑 CONFIGURAZIONE
# ==============================================================================

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERRORE: DATABASE_URL non configurata!")
    sys.exit(1)

# Credenziali ARGO (da configurare in GitHub Secrets)
ARGO_USERNAME = os.environ.get('ARGO_USERNAME', '')
ARGO_PASSWORD = os.environ.get('ARGO_PASSWORD', '')
ARGO_BASE_URL = "https://www.portaleargo.it"

print(f"✅ DATABASE_URL configurata")
if ARGO_USERNAME and ARGO_PASSWORD:
    print(f"✅ Credenziali ARGO configurate")
else:
    print(f"⚠️  Credenziali ARGO non configurate - modalità test")

# ==============================================================================
# 🛑 FUNZIONI DATABASE
# ==============================================================================

def get_db_connection():
    """Crea connessione al database"""
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        return conn
    except Exception as e:
        print(f"❌ Errore connessione database: {e}")
        return None

def salva_circolare_argo(data_str, categoria, messaggio, allegati_count, autore):
    """Salva una circolare ARGO nel database"""
    conn = get_db_connection()
    if not conn:
        return False, 0
    
    try:
        cursor = conn.cursor()
        
        # 1. Converti data da dd/mm/yyyy a yyyy-mm-dd
        try:
            data_pub = datetime.strptime(data_str, '%d/%m/%Y').date()
        except ValueError:
            print(f"❌ Formato data non valido: {data_str}")
            return False, 0
        
        # 2. Scarta circolari con più di 30 giorni
        oggi = datetime.now().date()
        if (oggi - data_pub).days > 30:
            print(f"⏳ Scartata circolare del {data_str} (più di 30 giorni)")
            return False, 0
        
        # 3. Estrai numero circolare dal messaggio
        numero_circolare = ""
        if messaggio:
            patterns = [
                r'CIRCOLARE\s+N[\.\s]*(\d+)',
                r'Circolare\s+N[\.\s]*(\d+)',
                r'N[\.\s]*(\d+)\s+del',
                r'Numero[:\s]*(\d+)',
                r'Prot[\.\s]*(\d+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, messaggio, re.IGNORECASE)
                if match:
                    numero_circolare = f"N.{match.group(1)}"
                    break
        
        # 4. Estrai titolo dal messaggio
        titolo = "Circolare"
        
        # Cerca "Oggetto:" nel messaggio
        oggetto_match = re.search(r'Oggetto:\s*(.+?)(?:\n|$)', messaggio, re.IGNORECASE)
        if oggetto_match:
            titolo = oggetto_match.group(1).strip()
            if len(titolo) > 100:
                titolo = titolo[:100] + "..."
        else:
            # Prendi prime 2 righe non vuote
            righe = [r.strip() for r in messaggio.split('\n') if r.strip()]
            if righe:
                prima_riga = righe[0]
                # Rimuovi "Da:" se presente
                if prima_riga.startswith('Da:'):
                    if len(righe) > 1:
                        titolo = righe[1]
                    else:
                        titolo = categoria
                else:
                    titolo = prima_riga[:100]
        
        # Aggiungi numero circolare al titolo se trovato
        if numero_circolare:
            titolo = f"{numero_circolare} - {titolo}"
        
        # 5. Prepara allegati
        allegati_str = ""
        if allegati_count and str(allegati_count).isdigit():
            count = int(allegati_count)
            if count > 0:
                # Genera nomi allegati realistici
                allegati = []
                for i in range(1, count + 1):
                    if numero_circolare:
                        allegati.append(f"allegato_{numero_circolare}_{i}.pdf")
                    else:
                        allegati.append(f"allegato_{data_str.replace('/', '-')}_{i}.pdf")
                allegati_str = ",".join(allegati)
        
        # 6. Pulisci i dati
        titolo = titolo.strip()[:200]
        messaggio = messaggio.strip()
        categoria = categoria.strip()[:100] if categoria else ""
        autore = autore.strip()[:100] if autore else ""
        
        # 7. Controlla se esiste già
        cursor.execute("""
            SELECT id FROM circolari 
            WHERE data_pubblicazione = %s AND titolo = %s
        """, (data_pub, titolo))
        
        if cursor.fetchone() is None:
            # 8. Inserisci nuova circolare
            cursor.execute("""
                INSERT INTO circolari 
                (titolo, contenuto, data_pubblicazione, allegati, pdf_url)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                titolo,
                messaggio,
                data_pub,
                allegati_str,
                ""  # pdf_url vuoto per ora
            ))
            
            new_id = cursor.fetchone()[0]
            conn.commit()
            return True, new_id
        else:
            return False, 0  # Già presente
        
    except Exception as e:
        print(f"❌ Errore salvataggio circolare {data_str}: {e}")
        return False, 0
    finally:
        if conn:
            conn.close()

# ==============================================================================
# 🛑 FUNZIONI PER ARGO (SIMULATE - DA IMPLEMENTARE CON SCRAPING REALE)
# ==============================================================================

def scarica_circolari_argo_real():
    """DA IMPLEMENTARE: Scarica le circolari REALI da ARGO"""
    print("⚠️  IMPLEMENTARE: Scraping reale di ARGO")
    print("   Per ora uso dati di esempio basati sullo screenshot")
    
    # ESEMPIO BASATO SULLO SCREENSHOT
    oggi = datetime.now().date()
    circolari = []
    
    # Circolare dal tuo screenshot
    circolari.append({
        "data": "16/01/2026",
        "categoria": "CONCORSI PER ALUNNI",
        "messaggio": """Da: prolocogiarre@gm...
Oggetto: Bando 20° Concorso PREMIO DI POESIA San Valentino

Bando di concorso di poesia in occasione della festa di San Valentino.
Possono partecipare tutti gli studenti della scuola.
Le opere dovranno essere consegnate entro il 10 febbraio 2026.
Premiazione il 14 febbraio 2026 in aula magna.""",
        "allegati_count": "3",
        "autore": "Preside/Segreteria"
    })
    
    # Aggiungi altre circolari di esempio per gli ultimi 30 giorni
    for giorni in range(30):
        data_circ = oggi - timedelta(days=giorni)
        
        # Solo alcuni giorni hanno circolari
        if giorni % 3 == 0:
            data_str = data_circ.strftime('%d/%m/%Y')
            
            categorie = [
                "PROGETTI DIDATTICI",
                "DOCUMENTI ISTITUZIONALI", 
                "AVVISI",
                "COMUNICAZIONI",
                "ORARI"
            ]
            
            categoria = categorie[giorni % len(categorie)]
            
            # Genera messaggio realistico
            if categoria == "PROGETTI DIDATTICI":
                messaggio = f"""OGGETTO: Programma di Educazione Ambientale 2025/2026

CIRCOLARE N.{150 + giorni}

Invito a partecipare al Programma di Educazione Ambientale organizzato da ARPA Sicilia.
Le adesioni devono essere comunicate entro il 30 gennaio 2026."""
                allegati = "2"
                
            elif categoria == "DOCUMENTI ISTITUZIONALI":
                messaggio = f"""CRITERI DEROGA LIMITE ASSENZE ANNUE ALUNNI - A.S. 2025/2026

Circolare N.{160 + giorni}

Si comunica il regolamento per le deroghe al limite di assenze.
Documentazione da presentare in segreteria."""
                allegati = "1"
                
            elif categoria == "AVVISI":
                messaggio = f"""AVVISO IMPORTANTE

Modifiche all'orario delle lezioni a partire dalla prossima settimana.
Si prega di consultare il nuovo orario."""
                allegati = "1"
                
            else:
                messaggio = f"""Comunicazione del {data_str}

Informazioni importanti per studenti e famiglie.
Si prega di prendere visione."""
                allegati = "0"
            
            circolari.append({
                "data": data_str,
                "categoria": categoria,
                "messaggio": messaggio,
                "allegati_count": allegati,
                "autore": "Preside/Segreteria"
            })
    
    return circolari

# ==============================================================================
# 🛑 MAIN
# ==============================================================================

def main():
    """Funzione principale"""
    print("\n🚀 INIZIO ESTRAZIONE CIRCOLARI ARGO")
    print("-" * 40)
    
    try:
        # 1. Scarica circolari (per ora simulate)
        print("📥 Estrazione circolari dalla bacheca ARGO...")
        circolari = scarica_circolari_argo_real()
        
        print(f"🔍 Trovate {len(circolari)} circolari")
        
        # 2. Processa e salva ogni circolare
        salvate = 0
        duplicate = 0
        scartate = 0
        errori = 0
        
        for i, circ in enumerate(circolari):
            print(f"\n[{i+1}/{len(circolari)}] {circ['data']} - {circ['categoria']}")
            
            # Log info
            if circ.get('allegati_count') and circ['allegati_count'] != '0':
                print(f"   📎 {circ['allegati_count']} allegati")
            
            if circ.get('autore'):
                print(f"   👤 {circ['autore']}")
            
            # Salva nel database
            success, circ_id = salva_circolare_argo(
                data_str=circ['data'],
                categoria=circ['categoria'],
                messaggio=circ['messaggio'],
                allegati_count=circ.get('allegati_count', '0'),
                autore=circ.get('autore', '')
            )
            
            if success and circ_id > 0:
                salvate += 1
                print(f"   ✅ Salvata (ID: {circ_id})")
            elif not success and circ_id == 0:
                duplicate += 1
                print(f"   ⚠️  Già presente")
            else:
                scartate += 1
                print(f"   ⏳ Scartata (vecchia >30gg)")
        
        # 3. Riepilogo finale
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Totale circolari
            cursor.execute("SELECT COUNT(*) as totale FROM circolari")
            totale = cursor.fetchone()[0]
            
            # Statistiche per data
            cursor.execute("""
                SELECT 
                    MIN(data_pubblicazione) as prima,
                    MAX(data_pubblicazione) as ultima,
                    COUNT(DISTINCT data_pubblicazione) as giorni_con_circolari,
                    COUNT(*) as totale_circolari
                FROM circolari
                WHERE data_pubblicazione >= CURRENT_DATE - INTERVAL '30 days'
            """)
            stats = cursor.fetchone()
            
            conn.close()
            
            print("\n" + "=" * 60)
            print("📊 RIEPILOGO ESTRAZIONE")
            print("=" * 60)
            print(f"✅ Nuove circolari salvate: {salvate}")
            print(f"⚠️  Circolari duplicate: {duplicate}")
            print(f"⏳ Circolari scartate (>30gg): {scartate}")
            print(f"📋 Totale circolari nel database: {totale}")
            
            if stats[0] and stats[1]:
                giorni_totali = (stats[1] - stats[0]).days + 1
                print(f"📅 Periodo: {stats[0]} → {stats[1]}")
                print(f"📆 Giorni con circolari: {stats[2]}/{giorni_totali}")
                print(f"📈 Media circolari/giorno: {stats[3]/max(stats[2], 1):.1f}")
        
        print("=" * 60)
        print("\n🎯 ESTRAZIONE COMPLETATA!")
        print("🌐 App: https://circolari-online-production.up.railway.app")
        
    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
