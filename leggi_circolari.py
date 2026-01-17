#!/usr/bin/env python3
"""
Robot Circolari ARGO - Scraping REALE che legge ESATTAMENTE le circolari da ARGO
SENZA inventare o aggiungere dati fittizi
"""

import os
import sys
import re
import psycopg2
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

print("=" * 60)
print("🤖 ROBOT CIRCOLARI ARGO - SCRAPING REALE")
print("=" * 60)
print(f"⏰ Timestamp Italia: {datetime.now().isoformat()}")

# ==============================================================================
# 🛑 CONFIGURAZIONE
# ==============================================================================

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERRORE: DATABASE_URL non configurata!")
    sys.exit(1)

# Credenziali ARGO (obbligatorie)
ARGO_USERNAME = os.environ.get('ARGO_USERNAME', '')
ARGO_PASSWORD = os.environ.get('ARGO_PASSWORD', '')

if not ARGO_USERNAME or not ARGO_PASSWORD:
    print("❌ ERRORE: Credenziali ARGO non configurate!")
    print("   Configura ARGO_USERNAME e ARGO_PASSWORD in GitHub Secrets")
    sys.exit(1)

ARGO_BASE_URL = "https://www.portaleargo.it"
ARGO_LOGIN_URL = f"{ARGO_BASE_URL}/auth/sso/login"
ARGO_BACHECA_URL = f"{ARGO_BASE_URL}/famiglia/bacheca"

print(f"✅ DATABASE_URL configurata")
print(f"✅ Credenziali ARGO configurate")
print(f"🌐 URL ARGO: {ARGO_BASE_URL}")

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

def salva_circolare_reale(data_str, categoria, messaggio, allegati_info, autore=""):
    """
    Salva una circolare REALE da ARGO.
    NON inventa dati, usa solo quello che trova.
    """
    conn = get_db_connection()
    if not conn:
        return False, 0
    
    try:
        cursor = conn.cursor()
        
        # 1. Converti data da dd/mm/yyyy
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
        
        # 3. Crea titolo dal messaggio (SOLO dati reali)
        titolo = "Circolare"
        
        # Cerca "Oggetto:" nel messaggio
        oggetto_match = re.search(r'Oggetto:\s*(.+?)(?:\n|$)', messaggio, re.IGNORECASE)
        if oggetto_match:
            titolo = oggetto_match.group(1).strip()
        else:
            # Prendi prime righe non vuote
            righe = [r.strip() for r in messaggio.split('\n') if r.strip()]
            if righe:
                # Rimuovi "Da:" se presente
                prima_riga = righe[0]
                if prima_riga.startswith('Da:'):
                    if len(righe) > 1:
                        titolo = righe[1][:150]
                    else:
                        titolo = categoria if categoria else "Circolare"
                else:
                    titolo = prima_riga[:150]
        
        titolo = titolo.strip()
        if not titolo:
            titolo = "Circolare senza titolo"
        
        # 4. Processa allegati (SOLO se ci sono informazioni reali)
        allegati_str = ""
        if allegati_info:
            allegati_str = allegati_info.strip()
        
        # 5. Pulisci i dati
        messaggio = messaggio.strip()
        categoria = categoria.strip() if categoria else ""
        autore = autore.strip() if autore else ""
        
        # 6. Controlla se esiste già (per evitare duplicati)
        cursor.execute("""
            SELECT id FROM circolari 
            WHERE data_pubblicazione = %s AND titolo = %s
        """, (data_pub, titolo))
        
        if cursor.fetchone() is None:
            # 7. Inserisci nuova circolare
            cursor.execute("""
                INSERT INTO circolari 
                (titolo, contenuto, data_pubblicazione, allegati)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
                titolo[:200],
                messaggio,
                data_pub,
                allegati_str
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
# 🛑 SCRAPING REALE ARGO
# ==============================================================================

def crea_sessione_argo():
    """Crea una sessione requests per ARGO"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
    })
    return session

def login_argo(session):
    """Effettua login ad ARGO"""
    try:
        print("🔐 Accesso ad ARGO...")
        
        # 1. Ottieni la pagina di login
        response = session.get(ARGO_LOGIN_URL, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 2. Cerca il token CSRF
        token = ""
        token_input = soup.find('input', {'name': '_token'})
        if token_input:
            token = token_input.get('value', '')
        
        # 3. Prepara dati login
        login_data = {
            '_token': token,
            'username': ARGO_USERNAME,
            'password': ARGO_PASSWORD,
        }
        
        # 4. Effettua login
        response = session.post(ARGO_LOGIN_URL, data=login_data, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # 5. Verifica login
        if "password errata" in response.text.lower():
            print("❌ Login fallito: credenziali errate")
            return False
        
        print("✅ Login ARGO effettuato")
        return True
            
    except Exception as e:
        print(f"❌ Errore durante il login ARGO: {e}")
        return False

def estrai_circolari_reali_da_argo(session):
    """
    Estrae le circolari REALI dalla bacheca ARGO.
    Legge ESATTAMENTE quello che c'è nella tabella.
    """
    print("\n📋 Accesso alla bacheca ARGO...")
    
    circolari_trovate = []
    
    try:
        # 1. Accedi alla pagina bacheca
        response = session.get(ARGO_BACHECA_URL, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 2. Cerca la tabella delle circolari (struttura tipica ARGO)
        # La tabella dovrebbe avere queste colonne: DATA, CATEGORIA, MESSAGGIO, FILE, ecc.
        
        # Prima cerca per ID comune
        tabella = soup.find('table', id=re.compile(r'table|bacheca|comunicazioni', re.I))
        
        if not tabella:
            # Cerca per classe
            tabella = soup.find('table', class_=re.compile(r'table|bacheca|comunicazioni', re.I))
        
        if not tabella:
            # Prendi la prima tabella che sembra avere dati
            tabelle = soup.find_all('table')
            for t in tabelle:
                # Controlla se la tabella ha abbastanza righe e colonne
                righe = t.find_all('tr')
                if len(righe) > 1:
                    prima_riga = righe[0]
                    celle = prima_riga.find_all(['td', 'th'])
                    if len(celle) >= 4:  # Almeno 4 colonne
                        tabella = t
                        break
        
        if not tabella:
            print("❌ Tabella delle circolari non trovata")
            # Salva la pagina per debug
            with open('debug_argo.html', 'w', encoding='utf-8') as f:
                f.write(response.text[:20000])
            print("💾 Pagina salvata in debug_argo.html per analisi")
            return []
        
        print("✅ Tabella circolari trovata")
        
        # 3. Estrai dati dalla tabella
        righe = tabella.find_all('tr')
        
        if len(righe) < 2:
            print("⚠️  Tabella senza dati")
            return []
        
        # Analizza intestazione per capire la struttura
        intestazione = righe[0]
        celle_intestazione = intestazione.find_all(['th', 'td'])
        
        # Mappa indici colonne basandoci sui nomi tipici ARGO
        indici_colonne = {}
        for idx, cella in enumerate(celle_intestazione):
            testo = cella.get_text(strip=True).upper()
            if 'DATA' in testo:
                indici_colonne['data'] = idx
            elif 'CATEGORIA' in testo:
                indici_colonne['categoria'] = idx
            elif 'MESSAGGIO' in testo or 'OGGETTO' in testo:
                indici_colonne['messaggio'] = idx
            elif 'FILE' in testo or 'ALLEGATI' in testo or 'DOCUMENTO' in testo:
                indici_colonne['file'] = idx
            elif 'AUTORE' in testo:
                indici_colonne['autore'] = idx
        
        # Se non riusciamo a mappare, usiamo posizioni predefinite basate sullo screenshot
        if not indici_colonne:
            indici_colonne = {
                'data': 0,        # Prima colonna: DATA
                'categoria': 1,   # Seconda colonna: CATEGORIA
                'messaggio': 3,   # Quarta colonna: MESSAGGIO
                'file': 4,        # Quinta colonna: FILE
                'autore': 6       # Settima colonna: AUTORE
            }
        
        print(f"📊 Struttura tabella: {indici_colonne}")
        
        # 4. Estrai dati dalle righe (dalla seconda in poi)
        for riga in righe[1:]:
            celle = riga.find_all('td')
            
            if len(celle) >= 3:  # Almeno Data, Categoria, Messaggio
                try:
                    # Estrai dati in base agli indici
                    data = ""
                    categoria = ""
                    messaggio = ""
                    file_info = ""
                    autore = ""
                    
                    # Data
                    if 'data' in indici_colonne and indici_colonne['data'] < len(celle):
                        data_cell = celle[indici_colonne['data']]
                        data = data_cell.get_text(strip=True)
                        # Pulisci data (mantieni solo numeri e slash)
                        data = re.sub(r'[^\d/]', '', data)
                    
                    # Categoria
                    if 'categoria' in indici_colonne and indici_colonne['categoria'] < len(celle):
                        cat_cell = celle[indici_colonne['categoria']]
                        categoria = cat_cell.get_text(strip=True)
                    
                    # Messaggio
                    if 'messaggio' in indici_colonne and indici_colonne['messaggio'] < len(celle):
                        msg_cell = celle[indici_colonne['messaggio']]
                        messaggio = msg_cell.get_text(strip=True, separator='\n')
                    
                    # File/Allegati
                    if 'file' in indici_colonne and indici_colonne['file'] < len(celle):
                        file_cell = celle[indici_colonne['file']]
                        file_info = file_cell.get_text(strip=True)
                    
                    # Autore
                    if 'autore' in indici_colonne and indici_colonne['autore'] < len(celle):
                        auth_cell = celle[indici_colonne['autore']]
                        autore = auth_cell.get_text(strip=True)
                    
                    # Verifica dati minimi: data e messaggio
                    if data and re.match(r'\d{1,2}/\d{1,2}/\d{4}', data) and messaggio:
                        circolari_trovate.append({
                            'data': data,
                            'categoria': categoria,
                            'messaggio': messaggio,
                            'allegati_info': file_info,
                            'autore': autore
                        })
                        
                except Exception as e:
                    print(f"⚠️  Errore parsing riga: {e}")
                    continue
        
        print(f"✅ Trovate {len(circolari_trovate)} circolari reali")
        
        # 5. Se nessuna circolare trovata, prova approccio alternativo
        if not circolari_trovate:
            print("🔄 Tentativo approccio alternativo...")
            circolari_trovate = estrai_circolari_approccio_alternativo(soup)
        
        return circolari_trovate
        
    except Exception as e:
        print(f"❌ Errore durante l'estrazione bacheca: {e}")
        import traceback
        traceback.print_exc()
        return []

def estrai_circolari_approccio_alternativo(soup):
    """Approccio alternativo per estrarre circolari"""
    circolari = []
    
    try:
        # Cerca tutti i contenitori che potrebbero contenere circolari
        # Basato su pattern comuni in ARGO
        pattern_circolari = re.compile(r'comunicazione|avviso|circolare|notizia|news', re.I)
        
        # Cerca div con classi comuni
        divs = soup.find_all('div', class_=pattern_circolari)
        
        for div in divs:
            try:
                # Cerca data (pattern comune: dd/mm/yyyy)
                data_match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', div.get_text())
                data = data_match.group(0) if data_match else ""
                
                # Estrai testo
                testo = div.get_text(strip=True, separator='\n')
                
                if data and len(testo) > 20:
                    circolari.append({
                        'data': data,
                        'categoria': '',
                        'messaggio': testo,
                        'allegati_info': '',
                        'autore': ''
                    })
                    
            except:
                continue
        
        print(f"   🔍 Approccio alternativo: {len(circolari)} circolari trovate")
        
    except Exception as e:
        print(f"   ❌ Errore approccio alternativo: {e}")
    
    return circolari

# ==============================================================================
# 🛑 PULIZIA DATABASE (elimina TUTTE le circolari esistenti prima di scaricare)
# ==============================================================================

def pulisci_database_completamente():
    """Elimina TUTTE le circolari esistenti prima di scaricare quelle reali"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM circolari")
        count_prima = cursor.fetchone()[0]
        
        if count_prima > 0:
            cursor.execute("DELETE FROM circolari")
            conn.commit()
            print(f"🧹 Eliminate {count_prima} circolari esistenti (preparazione per dati reali)")
        else:
            print("✅ Database già pulito")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore nella pulizia database: {e}")
        return False
    finally:
        if conn:
            conn.close()

# ==============================================================================
# 🛑 MAIN
# ==============================================================================

def main():
    """Funzione principale"""
    print("\n🚀 INIZIO SCRAPING CIRCOLARI ARGO REALI")
    print("-" * 40)
    
    try:
        # 1. Pulisci TUTTO il database (per partire da zero con dati reali)
        print("🧹 Pulizia database per dati reali...")
        pulisci_database_completamente()
        
        # 2. Crea sessione e login
        session = crea_sessione_argo()
        
        if not login_argo(session):
            print("❌ Impossibile procedere senza login ARGO")
            sys.exit(1)
        
        # 3. Estrai circolari REALI dalla bacheca
        print("\n📥 Estrazione circolari REALI dalla bacheca ARGO...")
        circolari = estrai_circolari_reali_da_argo(session)
        
        if not circolari:
            print("❌ Nessuna circolare reale trovata nella bacheca ARGO")
            print("   Verifica che:")
            print("   1. Le credenziali ARGO siano corrette")
            print("   2. Ci siano circolari nella bacheca ARGO")
            print("   3. La struttura della pagina non sia cambiata")
            sys.exit(1)
        
        print(f"🔍 {len(circolari)} circolari REALI estratte dalla bacheca")
        
        # 4. Salva SOLO le circolari reali
        salvate = 0
        duplicate = 0
        
        for i, circ in enumerate(circolari):
            print(f"\n[{i+1}/{len(circolari)}] {circ['data']}")
            
            if circ['categoria']:
                print(f"   🏷️  {circ['categoria']}")
            
            if circ['allegati_info']:
                print(f"   📎 {circ['allegati_info']}")
            
            # Anteprima messaggio
            if circ['messaggio']:
                anteprima = circ['messaggio'][:80].replace('\n', ' ')
                if len(circ['messaggio']) > 80:
                    anteprima += "..."
                print(f"   📝 {anteprima}")
            
            # Salva nel database
            success, circ_id = salva_circolare_reale(
                data_str=circ['data'],
                categoria=circ['categoria'],
                messaggio=circ['messaggio'],
                allegati_info=circ['allegati_info'],
                autore=circ['autore']
            )
            
            if success and circ_id > 0:
                salvate += 1
                print(f"   ✅ Salvata (ID: {circ_id})")
            else:
                duplicate += 1
                print(f"   ⚠️  Già presente")
        
        # 5. Riepilogo
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as totale FROM circolari")
            totale = cursor.fetchone()[0]
            conn.close()
            
            print("\n" + "=" * 60)
            print("📊 RIEPILOGO SCRAPING REALE")
            print("=" * 60)
            print(f"✅ Circolari REALI salvate: {salvate}")
            print(f"⚠️  Duplicate: {duplicate}")
            print(f"📋 Totale circolari nel database: {totale}")
            
            # Verifica che corrispondano
            if salvate == len(circolari):
                print("🎯 TUTTE le circolari reali sono state salvate correttamente")
            else:
                print(f"⚠️  Attenzione: {len(circolari) - salvate} circolari non salvate")
        
        print("=" * 60)
        print("\n🎯 SCRAPING ARGO REALE COMPLETATO!")
        print("📌 NOTA: Solo circolari REALI da ARGO, nessun dato inventato")
        print("🌐 App: https://circolari-online-production.up.railway.app")
        
    except Exception as e:
        print(f"\n❌ ERRORE CRITICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
