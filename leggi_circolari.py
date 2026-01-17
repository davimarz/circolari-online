#!/usr/bin/env python3
"""
Robot Circolari ARGO - Scraping reale della bacheca ARGO
"""

import os
import sys
import re
import time
import psycopg2
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import json

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

# Credenziali ARGO (obbligatorie per scraping reale)
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

def salva_circolare_argo(data_str, categoria, messaggio, allegati_count, autore="", url=""):
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
            # Prova altro formato
            try:
                data_pub = datetime.strptime(data_str, '%Y-%m-%d').date()
            except:
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
                r'Prot[\.\s]*(\d+\/\d+)',
                r'Prot\.\s*(\d+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, messaggio, re.IGNORECASE)
                if match:
                    numero_circolare = f"{match.group(1)}"
                    break
        
        # 4. Estrai titolo dal messaggio
        titolo = "Circolare"
        
        # Cerca "Oggetto:" nel messaggio
        oggetto_match = re.search(r'Oggetto:\s*(.+?)(?:\n|$)', messaggio, re.IGNORECASE)
        if oggetto_match:
            titolo = oggetto_match.group(1).strip()
        else:
            # Cerca "Da:" e prendi dopo
            da_match = re.search(r'Da:\s*.+?\n(.+)', messaggio, re.IGNORECASE)
            if da_match:
                titolo = da_match.group(1).strip()
            else:
                # Prendi prime 2 righe non vuote
                righe = [r.strip() for r in messaggio.split('\n') if r.strip()]
                if righe:
                    titolo = righe[0][:120]
        
        # Pulisci titolo
        titolo = titolo.strip()
        if len(titolo) > 200:
            titolo = titolo[:200] + "..."
        
        # Aggiungi numero circolare al titolo se trovato
        if numero_circolare:
            titolo = f"{numero_circolare} - {titolo}"
        elif categoria:
            titolo = f"{categoria} - {titolo}"
        
        # 5. Prepara allegati
        allegati_str = ""
        if allegati_count and str(allegati_count).isdigit():
            count = int(allegati_count)
            if count > 0:
                # Crea nomi allegati generici
                allegati = []
                base_nome = re.sub(r'[^\w\s-]', '', titolo[:50]).strip().replace(' ', '_')
                for i in range(1, count + 1):
                    allegati.append(f"{base_nome}_allegato_{i}.pdf")
                allegati_str = ",".join(allegati)
        
        # 6. Pulisci i dati
        messaggio = messaggio.strip()
        categoria = categoria.strip()[:100] if categoria else ""
        autore = autore.strip()[:200] if autore else ""
        url = url.strip()[:500] if url else ""
        
        # 7. Controlla se esiste già (per titolo e data)
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
                url  # Usiamo pdf_url per memorizzare l'URL originale
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
# 🛑 FUNZIONI SCRAPING ARGO
# ==============================================================================

def crea_sessione_argo():
    """Crea una sessione requests per ARGO"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session

def login_argo(session):
    """Effettua login ad ARGO"""
    try:
        print("🔐 Accesso ad ARGO...")
        
        # 1. Ottieni la pagina di login per estrarre il token CSRF
        response = session.get(ARGO_LOGIN_URL, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 2. Cerca il token CSRF
        token = ""
        token_input = soup.find('input', {'name': '_token'})
        if token_input:
            token = token_input.get('value', '')
            print(f"   ✅ Token CSRF trovato: {token[:20]}...")
        else:
            # Prova a cercare in altri modi
            meta_token = soup.find('meta', {'name': 'csrf-token'})
            if meta_token:
                token = meta_token.get('content', '')
                print(f"   ✅ Token CSRF (meta): {token[:20]}...")
        
        if not token:
            print("   ⚠️  Token CSRF non trovato, provo comunque...")
        
        # 3. Prepara dati login
        login_data = {
            '_token': token,
            'username': ARGO_USERNAME,
            'password': ARGO_PASSWORD,
            'remember': 'on'
        }
        
        # 4. Effettua login POST
        print("   📤 Invio credenziali...")
        response = session.post(ARGO_LOGIN_URL, data=login_data, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # 5. Verifica login
        if "Benvenuto" in response.text or "Dashboard" in response.text or "menu" in response.text.lower():
            print("✅ Login ARGO effettuato con successo")
            return True
        elif "password errata" in response.text.lower() or "credenziali non valide" in response.text.lower():
            print("❌ Login fallito: credenziali errate")
            return False
        else:
            print("⚠️  Login: stato incerto, controllo accesso bacheca...")
            return True  # Prova comunque
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore di connessione durante il login: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore durante il login ARGO: {e}")
        return False

def estrai_circolari_da_bacheca(session):
    """Estrae le circolari dalla bacheca ARGO"""
    print("\n📋 Accesso alla bacheca ARGO...")
    
    circolari_trovate = []
    
    try:
        # 1. Accedi alla pagina bacheca
        response = session.get(ARGO_BACHECA_URL, timeout=30)
        response.raise_for_status()
        
        # Salva per debug (opzionale)
        with open('debug_bacheca.html', 'w', encoding='utf-8') as f:
            f.write(response.text[:50000])
        print("   💾 Pagina bacheca salvata per debug (debug_bacheca.html)")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 2. Cerca la tabella delle circolari
        # ARGO usa diverse classi per le tabelle
        tabelle = soup.find_all('table')
        
        if not tabelle:
            print("   ❌ Nessuna tabella trovata nella bacheca")
            # Cerca div con classe table
            div_tables = soup.find_all('div', class_=re.compile(r'table'))
            if div_tables:
                print(f"   🔍 Trovati {len(div_tables)} div con classe table")
                # Tratta come tabelle
                for div in div_tables:
                    # Crea una tabella fittizia dal div
                    fake_table = BeautifulSoup(str(div), 'html.parser')
                    tabelle.append(fake_table)
        
        print(f"   🔍 Trovate {len(tabelle)} tabelle/div")
        
        # 3. Analizza ogni tabella
        for table_idx, tabella in enumerate(tabelle):
            print(f"\n   📊 Analisi tabella {table_idx + 1}...")
            
            # Cerca tutte le righe
            righe = tabella.find_all(['tr', 'div'])
            
            if not righe:
                # Prova a cercare righe in altri modi
                righe = tabella.find_all(True, recursive=False)
            
            print(f"   📄 Righe trovate: {len(righe)}")
            
            # Cerca l'header per capire la struttura
            header_trovato = False
            colonne_indici = {}  # Mappa nome_colonna -> indice
            
            for riga_idx, riga in enumerate(righe[:10]):  # Controlla prime 10 righe
                # Cerca celle (td/th/div con classe cell)
                celle = riga.find_all(['td', 'th', 'div'])
                
                if len(celle) >= 4:  # Almeno 4 colonne (Data, Categoria, Messaggio, File)
                    # Controlla se è un header (cerca testo come "DATA", "CATEGORIA")
                    testo_celle = [c.get_text(strip=True).upper() for c in celle]
                    
                    if "DATA" in str(testo_celle) or "CATEGORIA" in str(testo_celle):
                        print(f"   ✅ Header trovato alla riga {riga_idx + 1}")
                        header_trovato = True
                        
                        # Mappa indici colonne
                        for idx, cell in enumerate(celle):
                            testo = cell.get_text(strip=True).upper()
                            if "DATA" in testo:
                                colonne_indici['data'] = idx
                            elif "CATEGORIA" in testo:
                                colonne_indici['categoria'] = idx
                            elif "MESSAGGIO" in testo or "OGGETTO" in testo:
                                colonne_indici['messaggio'] = idx
                            elif "FILE" in testo or "ALLEGATI" in testo or "DOCUMENTO" in testo:
                                colonne_indici['file'] = idx
                            elif "AUTORE" in testo:
                                colonne_indici['autore'] = idx
                        
                        print(f"   📋 Struttura colonne: {colonne_indici}")
                        break
            
            # Se non ho trovato header, suppongo una struttura standard
            if not header_trovato:
                print("   ⚠️  Header non trovato, uso struttura predefinita")
                colonne_indici = {
                    'data': 0,
                    'categoria': 1,
                    'messaggio': 3,
                    'file': 4,
                    'autore': 6 if len(celle) > 6 else None
                }
            
            # 4. Estrai dati dalle righe successive
            righe_dati = righe[riga_idx + 1:] if header_trovato else righe
            
            for riga_dati in righe_dati:
                celle = riga_dati.find_all(['td', 'div'])
                
                if len(celle) >= 4:  # Almeno Data, Categoria, Messaggio
                    try:
                        # Estrai dati in base agli indici
                        data = ""
                        categoria = ""
                        messaggio = ""
                        file_count = "0"
                        autore = ""
                        
                        # Data
                        if 'data' in colonne_indici and colonne_indici['data'] < len(celle):
                            data_cell = celle[colonne_indici['data']]
                            data = data_cell.get_text(strip=True)
                            # Pulisci data (rimuovi eventuali icone/extra)
                            data = re.sub(r'[^\d\/\-\.]', '', data)[:10]
                        
                        # Categoria
                        if 'categoria' in colonne_indici and colonne_indici['categoria'] < len(celle):
                            cat_cell = celle[colonne_indici['categoria']]
                            categoria = cat_cell.get_text(strip=True)
                        
                        # Messaggio
                        if 'messaggio' in colonne_indici and colonne_indici['messaggio'] < len(celle):
                            msg_cell = celle[colonne_indici['messaggio']]
                            messaggio = msg_cell.get_text(strip=True, separator='\n')
                            
                            # Se il messaggio è troncato, cerca link per dettagli
                            if '...' in messaggio or len(messaggio) < 20:
                                link = msg_cell.find('a')
                                if link and link.get('href'):
                                    # Potremmo seguire il link per il messaggio completo
                                    pass
                        
                        # File/Allegati
                        if 'file' in colonne_indici and colonne_indici['file'] < len(celle):
                            file_cell = celle[colonne_indici['file']]
                            file_text = file_cell.get_text(strip=True)
                            # Conta numeri nel testo dei file
                            numeri = re.findall(r'\d+', file_text)
                            if numeri:
                                file_count = numeri[0]
                        
                        # Autore
                        if 'autore' in colonne_indici and colonne_indici['autore'] is not None and colonne_indici['autore'] < len(celle):
                            auth_cell = celle[colonne_indici['autore']]
                            autore = auth_cell.get_text(strip=True)
                        
                        # Valida dati minimi
                        if data and re.match(r'\d{1,2}/\d{1,2}/\d{4}', data) and messaggio:
                            circolari_trovate.append({
                                'data': data,
                                'categoria': categoria,
                                'messaggio': messaggio,
                                'allegati_count': file_count,
                                'autore': autore
                            })
                            
                    except Exception as e:
                        print(f"   ⚠️  Errore parsing riga: {e}")
                        continue
        
        print(f"\n✅ Estrazione completata: {len(circolari_trovate)} circolari trovate")
        
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
        # Cerca tutti i contenitori che potrebbero essere circolari
        contenitori = soup.find_all(['div', 'tr'], class_=re.compile(r'news|comunica|avviso|circolare|bacheca', re.I))
        
        for cont in contenitori:
            try:
                # Cerca data
                data_elem = cont.find(class_=re.compile(r'data|date|giorno', re.I))
                data = data_elem.get_text(strip=True) if data_elem else ""
                
                # Cerca titolo/messaggio
                titolo_elem = cont.find(class_=re.compile(r'titolo|oggetto|messaggio|testo', re.I))
                messaggio = titolo_elem.get_text(strip=True, separator='\n') if titolo_elem else ""
                
                # Cerca categoria
                cat_elem = cont.find(class_=re.compile(r'categoria|tipo|tag', re.I))
                categoria = cat_elem.get_text(strip=True) if cat_elem else ""
                
                if data and messaggio:
                    circolari.append({
                        'data': data[:10],
                        'categoria': categoria,
                        'messaggio': messaggio,
                        'allegati_count': "0",
                        'autore': ""
                    })
                    
            except:
                continue
        
        print(f"   🔍 Approccio alternativo: {len(circolari)} circolari trovate")
        
    except Exception as e:
        print(f"   ❌ Errore approccio alternativo: {e}")
    
    return circolari

# ==============================================================================
# 🛑 MAIN
# ==============================================================================

def main():
    """Funzione principale"""
    print("\n🚀 INIZIO SCRAPING CIRCOLARI ARGO")
    print("-" * 40)
    
    try:
        # 1. Crea sessione
        session = crea_sessione_argo()
        
        # 2. Login ad ARGO
        if not login_argo(session):
            print("❌ Impossibile procedere senza login ARGO")
            sys.exit(1)
        
        # 3. Estrai circolari dalla bacheca
        print("\n📥 Estrazione circolari dalla bacheca ARGO...")
        circolari = estrai_circolari_da_bacheca(session)
        
        if not circolari:
            print("❌ Nessuna circolare trovata nella bacheca")
            sys.exit(1)
        
        print(f"🔍 {len(circolari)} circolari estratte dalla bacheca")
        
        # 4. Processa e salva ogni circolare
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
            
            if circ.get('messaggio'):
                # Mostra anteprima messaggio
                msg_preview = circ['messaggio'][:80].replace('\n', ' ')
                if len(circ['messaggio']) > 80:
                    msg_preview += "..."
                print(f"   📝 {msg_preview}")
            
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
                print(f"   ⏳ Scartata")
        
        # 5. Riepilogo finale
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Totale circolari
            cursor.execute("SELECT COUNT(*) as totale FROM circolari")
            totale = cursor.fetchone()[0]
            
            # Circolari ultimi 30 giorni
            cursor.execute("""
                SELECT COUNT(*) as recenti
                FROM circolari
                WHERE data_pubblicazione >= CURRENT_DATE - INTERVAL '30 days'
            """)
            recenti = cursor.fetchone()[0]
            
            # Statistiche date
            cursor.execute("""
                SELECT 
                    MIN(data_pubblicazione) as prima,
                    MAX(data_pubblicazione) as ultima
                FROM circolari
                WHERE data_pubblicazione >= CURRENT_DATE - INTERVAL '30 days'
            """)
            stats = cursor.fetchone()
            
            conn.close()
            
            print("\n" + "=" * 60)
            print("📊 RIEPILOGO SCRAPING ARGO")
            print("=" * 60)
            print(f"✅ Nuove circolari salvate: {salvate}")
            print(f"⚠️  Circolari duplicate: {duplicate}")
            print(f"⏳ Circolari scartate: {scartate}")
            print(f"📋 Totale circolari nel database: {totale}")
            print(f"📅 Circolari ultimi 30 giorni: {recenti}")
            
            if stats[0] and stats[1]:
                giorni = (stats[1] - stats[0]).days + 1
                print(f"📆 Periodo: {stats[0]} → {stats[1]} ({giorni} giorni)")
        
        print("=" * 60)
        print("\n🎯 SCRAPING ARGO COMPLETATO!")
        print("🌐 App: https://circolari-online-production.up.railway.app")
        print("⏰ Prossimo aggiornamento: tra 1 ora")
        
    except Exception as e:
        print(f"\n❌ ERRORE CRITICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
