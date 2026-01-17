#!/usr/bin/env python3
"""
Robot Circolari ARGO - Scraping REALE
Versione migliorata e minimalista
"""

import os
import sys
import re
import psycopg2
from datetime import datetime
import requests
from bs4 import BeautifulSoup

print("=" * 60)
print("🤖 SCRAPER ARGO REALE")
print("=" * 60)

# ==============================================================================
# 🛑 CONFIGURAZIONE
# ==============================================================================

DATABASE_URL = os.environ.get('DATABASE_URL')
ARGO_USERNAME = os.environ.get('ARGO_USERNAME', '')
ARGO_PASSWORD = os.environ.get('ARGO_PASSWORD', '')

if not DATABASE_URL:
    print("❌ DATABASE_URL mancante")
    sys.exit(1)

if not ARGO_USERNAME or not ARGO_PASSWORD:
    print("❌ Credenziali ARGO mancanti")
    sys.exit(1)

# ==============================================================================
# 🛑 FUNZIONI DATABASE (semplificate)
# ==============================================================================

def get_db_connection():
    """Connessione database"""
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"❌ Errore DB: {e}")
        return None

def salva_circolare(titolo, contenuto, data_pubblicazione, allegati=""):
    """
    Salva una circolare nel database.
    Restituisce True se salvata, False se duplicata o errore.
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Pulisci dati
        titolo = titolo.strip()[:200]
        contenuto = contenuto.strip()[:5000]
        allegati = allegati.strip()[:500]
        
        # Converti data
        try:
            data_obj = datetime.strptime(data_pubblicazione, '%d/%m/%Y').date()
        except:
            print(f"❌ Data non valida: {data_pubblicazione}")
            return False
        
        # Scarta se > 30 giorni
        oggi = datetime.now().date()
        if (oggi - data_obj).days > 30:
            print(f"⏳ Scartata: {data_pubblicazione} (>30 giorni)")
            return False
        
        # Inserisci
        cursor.execute("""
            INSERT INTO circolari (titolo, contenuto, data_pubblicazione, allegati)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (titolo, data_pubblicazione) DO NOTHING
            RETURNING id
        """, (titolo, contenuto, data_obj, allegati))
        
        if cursor.fetchone():
            conn.commit()
            return True
        else:
            return False  # Duplicato
            
    except Exception as e:
        print(f"❌ Errore salvataggio: {e}")
        return False
    finally:
        conn.close()

def pulisci_circolari_vecchie():
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
            print(f"🧹 Eliminate {eliminate} circolari vecchie")
        return eliminate
    except:
        return 0
    finally:
        conn.close()

# ==============================================================================
# 🛑 SCRAPING ARGO
# ==============================================================================

def crea_sessione():
    """Crea sessione HTTP"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    return session

def login_argo(session):
    """Login ad ARGO"""
    try:
        # URL comuni ARGO
        login_url = "https://www.portaleargo.it/auth/sso/login"
        bacheca_url = "https://www.portaleargo.it/famiglia/bacheca"
        
        # 1. Ottieni pagina login
        resp = session.get(login_url, timeout=30)
        
        # 2. Cerca token
        soup = BeautifulSoup(resp.text, 'html.parser')
        token_input = soup.find('input', {'name': '_token'})
        token = token_input.get('value', '') if token_input else ''
        
        # 3. Login
        payload = {
            '_token': token,
            'username': ARGO_USERNAME,
            'password': ARGO_PASSWORD
        }
        
        resp = session.post(login_url, data=payload, allow_redirects=True)
        
        # 4. Verifica successo
        if "login" in resp.url or "password errata" in resp.text.lower():
            print("❌ Login fallito - Credenziali errate")
            return False
        
        print("✅ Login effettuato")
        return True
        
    except Exception as e:
        print(f"❌ Errore login: {e}")
        return False

def estrai_circolari_da_bacheca(session):
    """Estrai circolari dalla bacheca"""
    print("📥 Estrazione circolari...")
    
    circolari = []
    
    try:
        # URL bacheca
        bacheca_url = "https://www.portaleargo.it/famiglia/bacheca"
        resp = session.get(bacheca_url, timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Cerca tutte le tabelle
        tabelle = soup.find_all('table')
        
        for tabella in tabelle:
            righe = tabella.find_all('tr')
            
            # Deve avere almeno intestazione e dati
            if len(righe) < 2:
                continue
            
            # Analizza intestazione per colonne
            intestazione = righe[0]
            th_elements = intestazione.find_all(['th', 'td'])
            
            # Cerca indici colonne
            indici = {}
            for idx, th in enumerate(th_elements):
                testo = th.get_text(strip=True).upper()
                if 'DATA' in testo:
                    indici['data'] = idx
                elif 'OGGETTO' in testo or 'TITOLO' in testo:
                    indici['titolo'] = idx
                elif 'MESSAGGIO' in testo or 'CONTENUTO' in testo:
                    indici['contenuto'] = idx
                elif 'ALLEGAT' in testo or 'FILE' in testo:
                    indici['allegati'] = idx
            
            # Se non trovato, usa default
            if not indici:
                indici = {'data': 0, 'titolo': 1, 'contenuto': 2, 'allegati': 3}
            
            # Processa righe dati
            for riga in righe[1:]:
                celle = riga.find_all('td')
                if len(celle) < 2:
                    continue
                
                try:
                    # Estrai dati
                    data_str = ""
                    titolo = ""
                    contenuto = ""
                    allegati = ""
                    
                    if 'data' in indici and indici['data'] < len(celle):
                        data_cell = celle[indici['data']]
                        data_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', data_cell.get_text())
                        if data_match:
                            data_str = data_match.group(1)
                    
                    if 'titolo' in indici and indici['titolo'] < len(celle):
                        titolo_cell = celle[indici['titolo']]
                        titolo = titolo_cell.get_text(strip=True)
                    
                    if 'contenuto' in indici and indici['contenuto'] < len(celle):
                        contenuto_cell = celle[indici['contenuto']]
                        contenuto = contenuto_cell.get_text(strip=True, separator='\n')
                    
                    if 'allegati' in indici and indici['allegati'] < len(celle):
                        allegati_cell = celle[indici['allegati']]
                        allegati = allegati_cell.get_text(strip=True)
                    
                    # Se abbiamo data e titolo/contenuto, aggiungi
                    if data_str and (titolo or contenuto):
                        # Se non c'è titolo, crea dal contenuto
                        if not titolo and contenuto:
                            titolo = contenuto.split('\n')[0][:100]
                        
                        if not titolo:
                            titolo = "Circolare"
                        
                        circolari.append({
                            'data': data_str,
                            'titolo': titolo,
                            'contenuto': contenuto or titolo,
                            'allegati': allegati
                        })
                        
                except Exception as e:
                    continue
        
        # Se non trovato in tabelle, cerca in div
        if not circolari:
            circolari = estrai_circolari_da_div(soup)
        
        print(f"✅ Trovate {len(circolari)} circolari")
        return circolari
        
    except Exception as e:
        print(f"❌ Errore estrazione: {e}")
        return []

def estrai_circolari_da_div(soup):
    """Cerca circolari in elementi div"""
    circolari = []
    
    # Cerca elementi che potrebbero contenere circolari
    possibili_circolari = soup.find_all(['div', 'section', 'article'], 
                                       class_=re.compile(r'comunicazione|avviso|circolare|news|bacheca', re.I))
    
    for elem in possibili_circolari:
        try:
            testo = elem.get_text(strip=False, separator='\n')
            
            # Cerca data
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', testo)
            if not date_match:
                continue
            
            data_str = date_match.group(1)
            
            # Estrai titolo (prima riga dopo la data)
            lines = [l.strip() for l in testo.split('\n') if l.strip()]
            titolo = ""
            
            for i, line in enumerate(lines):
                if data_str in line:
                    if i + 1 < len(lines):
                        titolo = lines[i + 1][:150]
                    break
            
            if not titolo and lines:
                titolo = lines[0][:150]
            
            if not titolo:
                titolo = "Circolare"
            
            # Contenuto completo
            contenuto = testo[:3000]
            
            # Cerca allegati
            allegati = []
            for link in elem.find_all('a', href=True):
                href = link.get('href', '').lower()
                if '.pdf' in href or '.doc' in href or '.zip' in href:
                    allegati.append(link.get_text(strip=True) or "Documento")
            
            allegati_str = ", ".join(allegati[:3])
            
            circolari.append({
                'data': data_str,
                'titolo': titolo,
                'contenuto': contenuto,
                'allegati': allegati_str
            })
            
        except:
            continue
    
    return circolari

# ==============================================================================
# 🛑 MAIN
# ==============================================================================

def main():
    """Funzione principale"""
    print("\n🚀 AVVIO SCRAPING ARGO")
    print("-" * 40)
    
    # Pulisci vecchie circolari
    pulisci_circolari_vecchie()
    
    # Crea sessione e login
    session = crea_sessione()
    
    if not login_argo(session):
        print("❌ Impossibile procedere senza login")
        sys.exit(1)
    
    # Estrai circolari
    circolari = estrai_circolari_da_bacheca(session)
    
    if not circolari:
        print("⚠️ Nessuna circolare trovata")
        print("\n💡 Suggerimenti:")
        print("   1. Verifica che ci siano circolari nella bacheca ARGO")
        print("   2. Controlla la struttura della pagina")
        print("   3. Salva la pagina HTML per debug")
        sys.exit(0)
    
    # Salva circolari
    salvate = 0
    duplicate = 0
    
    for i, circ in enumerate(circolari):
        print(f"\n[{i+1}/{len(circolari)}] {circ['data']} - {circ['titolo'][:50]}...")
        
        success = salva_circolare(
            titolo=circ['titolo'],
            contenuto=circ['contenuto'],
            data_pubblicazione=circ['data'],
            allegati=circ['allegati']
        )
        
        if success:
            salvate += 1
            print(f"   ✅ Salvata")
        else:
            duplicate += 1
            print(f"   ⚠️  Già presente")
    
    # Riepilogo
    print("\n" + "=" * 60)
    print("📊 RIEPILOGO")
    print("=" * 60)
    print(f"✅ Salvate: {salvate}")
    print(f"⚠️  Duplicate: {duplicate}")
    print(f"📋 Totali nel DB: {salvate}")
    print("=" * 60)
    
    if salvate > 0:
        print("🎯 SCRAPING COMPLETATO CON SUCCESSO!")
    else:
        print("ℹ️  Nessuna nuova circolare trovata")

if __name__ == "__main__":
    main()
