#!/usr/bin/env python3
"""
Robot Circolari - Legge le circolari dalla bacheca ARGO
"""

import os
import sys
import re
import psycopg2
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time

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
if ARGO_USERNAME:
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

def pulisci_database():
    """Pulisce il database dalle vecchie circolari"""
    print("\n🧹 Pulizia database dalle vecchie circolari...")
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Elimina solo le circolari vecchie (più di 60 giorni)
        cursor.execute("""
            DELETE FROM circolari 
            WHERE data_pubblicazione < CURRENT_DATE - INTERVAL '60 days'
        """)
        
        deleted = cursor.rowcount
        conn.commit()
        
        if deleted > 0:
            print(f"🗑️  Eliminate {deleted} circolari vecchie (>60 giorni)")
        else:
            print("✅ Nessuna circolare vecchia da eliminare")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Errore nella pulizia: {e}")
        return True  # Continua comunque
    finally:
        if conn:
            conn.close()

def salva_circolare(titolo, contenuto, data_pubblicazione, allegati=None, categoria="", autore=""):
    """Salva una circolare nel database"""
    conn = get_db_connection()
    if not conn:
        return False, 0
    
    try:
        cursor = conn.cursor()
        
        # Pulisci i dati
        titolo = titolo.strip()[:200] if titolo else "Circolare senza titolo"
        contenuto = contenuto.strip() if contenuto else ""
        categoria = categoria.strip()[:100] if categoria else ""
        autore = autore.strip()[:200] if autore else ""
        
        # Processa allegati
        allegati_str = ""
        if allegati:
            if isinstance(allegati, str):
                # Se è una stringa, splitta per virgole
                allegati_list = [a.strip() for a in allegati.split(',') if a.strip()]
            else:
                # Se è una lista
                allegati_list = [str(a).strip() for a in allegati if str(a).strip()]
            
            allegati_str = ",".join(allegati_list)
        
        # Estrai numero circolare dal titolo o contenuto
        numero_circolare = ""
        search_text = f"{titolo} {contenuto}"
        patterns = [
            r'CIRCOLARE\s+N[\.\s]*(\d+)',
            r'Circolare\s+N[\.\s]*(\d+)',
            r'N[\.\s]*(\d+)\s+-',
            r'Circ\.\s*(\d+)',
            r'Prot\.\s*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                numero_circolare = match.group(1)
                break
        
        # Controlla se esiste già
        cursor.execute("""
            SELECT id FROM circolari 
            WHERE data_pubblicazione = %s 
            AND (titolo = %s OR contenuto LIKE %s)
        """, (data_pubblicazione, titolo, f"%{titolo[:50]}%"))
        
        if cursor.fetchone() is None:
            # Inserisci nuova circolare
            cursor.execute("""
                INSERT INTO circolari 
                (titolo, contenuto, data_pubblicazione, allegati, pdf_url)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                titolo,
                contenuto,
                data_pubblicazione,
                allegati_str,
                ""  # pdf_url vuoto per ora
            ))
            
            new_id = cursor.fetchone()[0]
            conn.commit()
            return True, new_id
        else:
            return False, 0  # Già presente
        
    except Exception as e:
        print(f"❌ Errore salvataggio circolare '{titolo[:50]}...': {e}")
        return False, 0
    finally:
        if conn:
            conn.close()

# ==============================================================================
# 🛑 FUNZIONI PER ARGO (GENERICHE)
# ==============================================================================

def login_argo(session):
    """Effettua login ad ARGO"""
    if not ARGO_USERNAME or not ARGO_PASSWORD:
        print("⚠️  Credenziali ARGO non configurate - salto login")
        return True  # Continua in modalità test
    
    try:
        print("🔐 Accesso ad ARGO...")
        
        # 1. Ottieni la pagina di login
        login_url = f"{ARGO_BASE_URL}/auth/sso/login"
        response = session.get(login_url)
        
        if response.status_code != 200:
            print(f"❌ Impossibile raggiungere la pagina di login: {response.status_code}")
            return False
        
        # 2. Estrai token CSRF (se presente)
        soup = BeautifulSoup(response.content, 'html.parser')
        token = ""
        
        token_input = soup.find('input', {'name': '_token'})
        if token_input:
            token = token_input.get('value', '')
        
        # 3. Prepara dati login
        login_data = {
            '_token': token,
            'username': ARGO_USERNAME,
            'password': ARGO_PASSWORD
        }
        
        # 4. Effettua login
        response = session.post(login_url, data=login_data)
        
        # 5. Verifica login
        if "Benvenuto" in response.text or "Dashboard" in response.text:
            print("✅ Login ARGO effettuato")
            return True
        else:
            print("❌ Login ARGO fallito")
            return False
            
    except Exception as e:
        print(f"❌ Errore durante il login ARGO: {e}")
        return False

def estrai_circolari_da_bacheca(session):
    """Estrae le circolari dalla bacheca ARGO"""
    print("📋 Estrazione circolari dalla bacheca ARGO...")
    
    circolari_trovate = []
    
    try:
        # URL della bacheca (da verificare su ARGO)
        bacheca_url = f"{ARGO_BASE_URL}/famiglia/bacheca"
        
        response = session.get(bacheca_url)
        if response.status_code != 200:
            print(f"⚠️  Impossibile accedere alla bacheca: {response.status_code}")
            return circolari_trovate
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Cerca la tabella delle circolari
        # Questi selettori sono da ADATTARE alla struttura reale di ARGO
        tabelle = soup.find_all('table')
        
        for i, tabella in enumerate(tabelle):
            print(f"🔍 Analisi tabella {i+1}...")
            
            # Cerca righe della tabella
            righe = tabella.find_all('tr')
            
            for riga in righe[1:]:  # Salta l'header
                celle = riga.find_all('td')
                
                if len(celle) >= 5:  # Dovrebbero essere: Data, Categoria, Num.Doc., Messaggio, File
                    try:
                        # Estrai dati dalle celle
                        data_str = celle[0].get_text(strip=True)
                        categoria = celle[1].get_text(strip=True)
                        num_doc = celle[2].get_text(strip=True)
                        messaggio = celle[3].get_text(strip=True)
                        file_allegati = celle[4].get_text(strip=True)
                        
                        # Converti data
                        try:
                            data_pub = datetime.strptime(data_str, '%d/%m/%Y').date()
                        except:
                            # Prova altri formati
                            try:
                                data_pub = datetime.strptime(data_str, '%Y-%m-%d').date()
                            except:
                                print(f"⚠️  Data non riconosciuta: {data_str}")
                                continue
                        
                        # Processa allegati
                        allegati = []
                        if file_allegati:
                            allegati = [f.strip() for f in file_allegati.split(',') if f.strip()]
                        
                        # Crea titolo dal messaggio
                        titolo = messaggio[:100]
                        if num_doc:
                            titolo = f"{num_doc} - {titolo}"
                        
                        circolari_trovate.append({
                            'data': data_pub,
                            'categoria': categoria,
                            'titolo': titolo,
                            'messaggio': messaggio,
                            'allegati': allegati
                        })
                        
                    except Exception as e:
                        print(f"⚠️  Errore parsing riga: {e}")
                        continue
        
        print(f"✅ Trovate {len(circolari_trovate)} circolari nella bacheca")
        return circolari_trovate
        
    except Exception as e:
        print(f"❌ Errore durante l'estrazione: {e}")
        return circolari_trovate

def scarica_circolari_test():
    """Funzione di test quando ARGO non è disponibile"""
    print("🔧 Modalità TEST - generazione circolari di esempio...")
    
    oggi = datetime.now().date()
    circolari_test = []
    
    # Genera alcune circolari di esempio per test
    for i in range(7):
        data = oggi - timedelta(days=i*2)
        
        circolari_test.append({
            'data': data,
            'categoria': ['AVVISI', 'COMUNICAZIONI', 'PROGETTI DIDATTICI'][i % 3],
            'titolo': f'Circolare di test {data.strftime("%d/%m/%Y")}',
            'messaggio': f'Messaggio della circolare di test del {data.strftime("%d/%m/%Y")}. Questo è un contenuto di esempio.',
            'allegati': ['documento.pdf'] if i % 2 == 0 else []
        })
    
    return circolari_test

# ==============================================================================
# 🛑 MAIN
# ==============================================================================

def main():
    """Funzione principale"""
    print("\n🚀 INIZIO PROCESSO CIRCOLARI")
    print("-" * 40)
    
    try:
        # 1. Pulizia database
        pulisci_database()
        
        # 2. Preparazione sessione ARGO
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 3. Login ad ARGO
        logged_in = login_argo(session)
        
        # 4. Estrazione circolari
        if logged_in and ARGO_USERNAME:
            circolari = estrai_circolari_da_bacheca(session)
        else:
            print("⚠️  Modalità test attivata")
            circolari = scarica_circolari_test()
        
        if not circolari:
            print("❌ Nessuna circolare trovata")
            sys.exit(1)
        
        # 5. Salvataggio nel database
        print(f"\n💾 Salvataggio {len(circolari)} circolari nel database...")
        
        salvate = 0
        duplicate = 0
        errori = 0
        
        for i, circ in enumerate(circolari):
            print(f"\n[{i+1}/{len(circolari)}] {circ['data']} - {circ['categoria']}")
            print(f"   📄 {circ['titolo'][:60]}...")
            
            if circ.get('allegati'):
                print(f"   📎 Allegati: {', '.join(circ['allegati'])}")
            
            # Salva nel database
            success, circ_id = salva_circolare(
                titolo=circ['titolo'],
                contenuto=circ['messaggio'],
                data_pubblicazione=circ['data'],
                allegati=circ.get('allegati', []),
                categoria=circ.get('categoria', '')
            )
            
            if success and circ_id > 0:
                salvate += 1
                print(f"   ✅ Salvata (ID: {circ_id})")
            elif not success and circ_id == 0:
                duplicate += 1
                print(f"   ⚠️  Già presente")
            else:
                errori += 1
                print(f"   ❌ Errore nel salvataggio")
        
        # 6. Riepilogo finale
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as totale FROM circolari")
            totale = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT MIN(data_pubblicazione) as prima, 
                       MAX(data_pubblicazione) as ultima
                FROM circolari
            """)
            dates = cursor.fetchone()
            conn.close()
            
            print("\n" + "=" * 60)
            print("📊 RIEPILOGO")
            print("=" * 60)
            print(f"✅ Nuove circolari salvate: {salvate}")
            print(f"⚠️  Circolari duplicate: {duplicate}")
            print(f"❌ Errori: {errori}")
            print(f"📋 Totale circolari nel database: {totale}")
            
            if dates[0] and dates[1]:
                giorni = (dates[1] - dates[0]).days + 1
                print(f"📅 Periodo: {dates[0]} → {dates[1]} ({giorni} giorni)")
        
        print("=" * 60)
        print("\n🎯 PROCESSO COMPLETATO!")
        print("🌐 App: https://circolari-online-production.up.railway.app")
        
    except Exception as e:
        print(f"\n❌ ERRORE CRITICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
