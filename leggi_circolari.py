#!/usr/bin/env python3
"""
Scraper ARGO REALE - Versione Funzionante
Accesso a https://www.portaleargo.it/voti/?classic
Menu: Bacheca → Messaggi da leggere
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
print("🤖 SCRAPER ARGO REALE")
print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print("=" * 60)

# ==============================================================================
# 🛑 CONFIGURAZIONE REALE
# ==============================================================================

DATABASE_URL = os.environ.get('DATABASE_URL')
ARGO_USERNAME = os.environ.get('ARGO_USERNAME', 'davide.marziano.sc26953')
ARGO_PASSWORD = os.environ.get('ARGO_PASSWORD', 'dvd2Frank.')

# URL REALE del tuo ARGO
ARGO_BASE_URL = "https://www.portaleargo.it"
ARGO_LOGIN_URL = f"{ARGO_BASE_URL}/voti/?classic"
ARGO_BACHECA_URL = f"{ARGO_BASE_URL}/voti/famiglia/genitori/bacheca.php"

if not DATABASE_URL:
    print("❌ DATABASE_URL mancante")
    sys.exit(1)

print(f"🔗 URL ARGO: {ARGO_LOGIN_URL}")
print(f"👤 Username: {ARGO_USERNAME}")

# ==============================================================================
# 🛑 FUNZIONI DATABASE
# ==============================================================================

def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"❌ Errore DB: {e}")
        return None

def salva_circolare(titolo, contenuto, data_pubblicazione, allegati=""):
    """Salva una circolare reale"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Pulisci dati
        titolo = titolo.strip()[:250]
        contenuto = contenuto.strip()[:10000]
        allegati = allegati.strip()[:500]
        
        # Converti data da dd/mm/yyyy a date
        try:
            data_obj = datetime.strptime(data_pubblicazione, '%d/%m/%Y').date()
        except:
            # Prova altri formati
            try:
                data_obj = datetime.strptime(data_pubblicazione, '%d/%m/%y').date()
            except:
                print(f"❌ Formato data non valido: {data_pubblicazione}")
                return False
        
        # Scarta se > 30 giorni
        oggi = datetime.now().date()
        if (oggi - data_obj).days > 30:
            print(f"⏳ Scartata: {data_pubblicazione} (>30 giorni)")
            return False
        
        # Controlla se esiste già
        cursor.execute("""
            SELECT id FROM circolari 
            WHERE titolo = %s AND data_pubblicazione = %s
        """, (titolo, data_obj))
        
        if cursor.fetchone():
            print(f"⚠️  Già presente: {titolo[:50]}...")
            return False
        
        # Inserisci
        cursor.execute("""
            INSERT INTO circolari (titolo, contenuto, data_pubblicazione, allegati)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (titolo, contenuto, data_obj, allegati))
        
        circ_id = cursor.fetchone()[0]
        conn.commit()
        print(f"✅ Salvata: {titolo[:50]}... (ID: {circ_id})")
        return True
        
    except Exception as e:
        print(f"❌ Errore salvataggio: {e}")
        return False
    finally:
        conn.close()

def pulisci_vecchie():
    """Elimina circolari > 30 giorni"""
    conn = get_db_connection()
    if not conn:
        return 0
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM circolari 
            WHERE data_pubblicazione < CURRENT_DATE - INTERVAL '30 days'
        """)
        eliminate = cursor.rowcount
        conn.commit()
        if eliminate > 0:
            print(f"🧹 Eliminate {eliminate} circolari >30 giorni")
        return eliminate
    except:
        return 0
    finally:
        conn.close()

# ==============================================================================
# 🛑 SCRAPING REALE ARGO
# ==============================================================================

def login_argo():
    """Login reale ad ARGO"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
    })
    
    print("\n🔐 Login ARGO...")
    
    try:
        # 1. Visita pagina login
        print(f"   📍 Accesso a: {ARGO_LOGIN_URL}")
        resp = session.get(ARGO_LOGIN_URL, timeout=30)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 2. Cerca il form di login
        form = soup.find('form', {'id': 'loginform'})
        if not form:
            form = soup.find('form')
        
        if not form:
            print("❌ Form di login non trovato")
            return None
        
        # 3. Prepara dati login
        login_data = {}
        inputs = form.find_all('input')
        
        for inp in inputs:
            name = inp.get('name')
            value = inp.get('value', '')
            if name:
                if 'username' in name.lower() or 'user' in name:
                    login_data[name] = ARGO_USERNAME
                elif 'password' in name.lower() or 'pass' in name:
                    login_data[name] = ARGO_PASSWORD
                else:
                    login_data[name] = value
        
        print(f"   🔑 Invio credenziali...")
        
        # 4. Invia login (action potrebbe essere relativa o assoluta)
        action = form.get('action', '')
        if not action.startswith('http'):
            if action.startswith('/'):
                action = ARGO_BASE_URL + action
            else:
                action = ARGO_LOGIN_URL
        
        resp = session.post(action, data=login_data, timeout=30, allow_redirects=True)
        
        # 5. Verifica login
        if 'logout' in resp.text.lower() or 'benvenuto' in resp.text.lower():
            print("✅ Login effettuato con successo")
            return session
        else:
            print("❌ Login fallito")
            print(f"   Controlla credenziali e URL")
            return None
            
    except Exception as e:
        print(f"❌ Errore login: {e}")
        return None

def scarica_bacheca(session):
    """Scarica la pagina bacheca"""
    print("\n📋 Accesso alla bacheca...")
    
    try:
        resp = session.get(ARGO_BACHECA_URL, timeout=30)
        resp.raise_for_status()
        
        # Salva per debug
        with open('bacheca.html', 'w', encoding='utf-8') as f:
            f.write(resp.text)
        print("💾 Pagina bacheca salvata (bacheca.html)")
        
        return resp.text
        
    except Exception as e:
        print(f"❌ Errore accesso bacheca: {e}")
        return None

def estrai_circolari_da_bacheca(html):
    """Estrai circolari reali dalla bacheca ARGO"""
    print("\n🔍 Estrazione circolari...")
    
    circolari = []
    soup = BeautifulSoup(html, 'html.parser')
    
    # Cerca la tabella delle comunicazioni
    # ARGO di solito ha una tabella con le circolari
    tabelle = soup.find_all('table')
    
    for i, tabella in enumerate(tabelle):
        # Controlla se è una tabella di comunicazioni
        testo_tabella = tabella.get_text().lower()
        if any(keyword in testo_tabella for keyword in ['comunicazione', 'circolare', 'messaggio', 'avviso', 'data', 'oggetto']):
            print(f"📊 Tabella {i+1}: potenziali comunicazioni")
            
            righe = tabella.find_all('tr')
            if len(righe) < 2:
                continue
            
            # Analizza intestazione
            intestazione = righe[0]
            ths = intestazione.find_all(['th', 'td'])
            
            # Cerca colonne rilevanti
            col_indices = {}
            for idx, th in enumerate(ths):
                testo = th.get_text(strip=True).lower()
                if 'data' in testo:
                    col_indices['data'] = idx
                elif 'oggetto' in testo or 'titolo' in testo or 'comunicazione' in testo:
                    col_indices['titolo'] = idx
                elif 'allegat' in testo:
                    col_indices['allegati'] = idx
            
            # Se non trovati, prova indice per indice
            if not col_indices and len(ths) >= 2:
                col_indices = {'data': 0, 'titolo': 1}
            
            # Estrai dati dalle righe
            for riga in righe[1:]:
                celle = riga.find_all('td')
                if len(celle) < 2:
                    continue
                
                try:
                    data = ""
                    titolo = ""
                    allegati = ""
                    contenuto = ""
                    
                    # Data
                    if 'data' in col_indices and col_indices['data'] < len(celle):
                        data_cell = celle[col_indices['data']]
                        data = data_cell.get_text(strip=True)
                        # Estrai solo data dd/mm/yyyy
                        match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', data)
                        if match:
                            data = match.group(1)
                    
                    # Titolo
                    if 'titolo' in col_indices and col_indices['titolo'] < len(celle):
                        titolo_cell = celle[col_indices['titolo']]
                        titolo = titolo_cell.get_text(strip=True)
                        
                        # Cerca link per contenuto
                        link = titolo_cell.find('a')
                        if link and link.get('href'):
                            # Potrebbe essere il link al contenuto completo
                            pass
                    
                    # Allegati
                    if 'allegati' in col_indices and col_indices['allegati'] < len(celle):
                        allegati_cell = celle[col_indices['allegati']]
                        allegati = allegati_cell.get_text(strip=True)
                    
                    # Se abbiamo data e titolo, aggiungi
                    if data and titolo:
                        # Per ora usiamo il titolo come contenuto
                        contenuto = titolo
                        
                        circolari.append({
                            'data': data,
                            'titolo': titolo,
                            'contenuto': contenuto,
                            'allegati': allegati
                        })
                        
                except Exception as e:
                    continue
    
    # Se non trovato in tabelle, cerca in altri elementi
    if not circolari:
        circolari = estrai_circolari_da_div(soup)
    
    return circolari

def estrai_circolari_da_div(soup):
    """Cerca circolari in elementi div"""
    circolari = []
    
    # Cerca elementi che potrebbero contenere circolari
    elementi = soup.find_all(['div', 'li', 'p'], class_=re.compile(r'comun|avis|circ|msg|news', re.I))
    
    for elem in elementi:
        testo = elem.get_text(strip=False, separator='\n')
        
        # Cerca data
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', testo)
        if not date_match:
            continue
        
        data = date_match.group(1)
        
        # Estrai titolo (prima riga significativa)
        lines = [l.strip() for l in testo.split('\n') if l.strip()]
        titolo = ""
        
        for line in lines:
            if line and not line.startswith(data) and len(line) > 5:
                titolo = line[:200]
                break
        
        if not titolo and lines:
            titolo = lines[0][:200]
        
        # Contenuto (tutto il testo)
        contenuto = testo[:5000]
        
        # Cerca allegati
        allegati = []
        for link in elem.find_all('a', href=True):
            if any(ext in link['href'].lower() for ext in ['.pdf', '.doc', '.docx', '.zip', '.rar']):
                nome = link.get_text(strip=True) or "Documento"
                allegati.append(nome)
        
        allegati_str = ", ".join(allegati[:3])
        
        circolari.append({
            'data': data,
            'titolo': titolo or "Circolare",
            'contenuto': contenuto,
            'allegati': allegati_str
        })
    
    return circolari

# ==============================================================================
# 🛑 MAIN
# ==============================================================================

def main():
    """Script principale"""
    print("\n🚀 AVVIO SCRAPER ARGO REALE")
    print("-" * 40)
    
    # Pulisci vecchie circolari
    pulisci_vecchie()
    
    # Login
    session = login_argo()
    if not session:
        print("❌ Impossibile procedere senza login")
        sys.exit(1)
    
    # Scarica bacheca
    html = scarica_bacheca(session)
    if not html:
        print("❌ Impossibile accedere alla bacheca")
        sys.exit(1)
    
    # Estrai circolari
    circolari = estrai_circolari_da_bacheca(html)
    
    if not circolari:
        print("\n⚠️  Nessuna circolare trovata nella bacheca")
        print("   Controlla manualmente la pagina bacheca.html")
        sys.exit(0)
    
    print(f"\n📋 Trovate {len(circolari)} circolari")
    
    # Salva nel database
    salvate = 0
    for circ in circolari:
        print(f"\n📄 {circ['data']} - {circ['titolo'][:50]}...")
        
        success = salva_circolare(
            titolo=circ['titolo'],
            contenuto=circ['contenuto'],
            data_pubblicazione=circ['data'],
            allegati=circ['allegati']
        )
        
        if success:
            salvate += 1
    
    # Riepilogo
    print("\n" + "=" * 60)
    print("📊 RIEPILOGO")
    print("=" * 60)
    print(f"✅ Circolari salvate: {salvate}/{len(circolari)}")
    print(f"📅 Mantenute solo ultimi 30 giorni")
    print("=" * 60)
    
    if salvate > 0:
        print("🎯 SCRAPING COMPLETATO!")
        print(f"🌐 App: https://circolari-online-production.up.railway.app")
    else:
        print("ℹ️  Nessuna nuova circolare trovata")

if __name__ == "__main__":
    main()
