#!/usr/bin/env python3
"""
Script per scaricare circolari da Argo e salvarle in Supabase
Filtra solo le circolari degli ultimi 30 giorni
"""

import sys
import subprocess
import importlib.util
import time
import os
import glob
import shutil
from datetime import datetime, timedelta

# ==============================================================================
# 🛑 CONTROLLO E INSTALLAZIONE DIPENDENZE
# ==============================================================================
def verifica_installazione(pacchetto, nome_import=None):
    """Verifica se un pacchetto è installato"""
    if nome_import is None:
        nome_import = pacchetto
    
    if importlib.util.find_spec(nome_import) is None:
        print(f"⚠️ Pacchetto '{pacchetto}' non trovato. Installo...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pacchetto])
            print(f"✅ '{pacchetto}' installato correttamente")
            return True
        except subprocess.CalledProcessError:
            print(f"❌ Errore durante l'installazione di '{pacchetto}'")
            return False
    return True

# Lista delle dipendenze necessarie
dipendenze = [
    ("selenium", "selenium"),
    ("webdriver-manager", "webdriver_manager"),
    ("supabase", "supabase"),
]

print("🔍 Verifico dipendenze...")
for pacchetto, nome_import in dipendenze:
    if not verifica_installazione(pacchetto, nome_import):
        print(f"\n❌ Impossibile procedere senza '{pacchetto}'")
        print("   Installa manualmente con: pip install", pacchetto)
        sys.exit(1)

print("✅ Tutte le dipendenze sono installate\n")

# ==============================================================================
# 🛑 CONFIGURAZIONE
# ==============================================================================
ARGO_USER = "davide.marziano.sc26953"
ARGO_PASS = "dvd2Frank." 

SUPABASE_URL = "https://ojnofjebrlwrlowovvjd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9qbm9mamVicmx3cmxvd292dmpkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc2NzgzMTcsImV4cCI6MjA4MzI1NDMxN30._LVpGUOyq-HJQsZO7YLDf7Fu7N5Kk_BxDBhKsFSGE_U"

# Configurazione Storage
STORAGE_BUCKET = "documenti"

# ==============================================================================
# 🛑 IMPORT DOPO VERIFICA DIPENDENZE
# ==============================================================================
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from supabase import create_client
import re

# ==============================================================================
# 🛑 INIZIALIZZAZIONE
# ==============================================================================

# --- DATA LIMITE: SOLO CIRCOLARI DEGLI ULTIMI 30 GIORNI ---
data_limite = datetime.now() - timedelta(days=30)
print(f"📅 Data limite: circolari dopo il {data_limite.strftime('%d/%m/%Y')}")

# --- PULIZIA CARTELLA DOWNLOAD ---
cartella_download = os.path.join(os.getcwd(), "scaricati")
if os.path.exists(cartella_download):
    shutil.rmtree(cartella_download) 
os.makedirs(cartella_download)

# --- CHROME OPTIONS ---
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--headless')  # Modalità headless per server

prefs = {
    "download.default_directory": cartella_download,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True,
    "profile.default_content_settings.popups": 0
}
chrome_options.add_experimental_option("prefs", prefs)

print("📡 Mi collego a Supabase...")
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connesso a Supabase")
except Exception as e:
    print(f"❌ Errore connessione Supabase: {e}")
    sys.exit(1)

print("🤖 Configuro Chrome...")
try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 30)
    print("✅ Browser Chrome configurato")
except Exception as e:
    print(f"❌ Errore configurazione Chrome: {e}")
    print("⚠️ Provo senza webdriver-manager...")
    try:
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 30)
        print("✅ Browser Chrome avviato (senza webdriver-manager)")
    except Exception as e2:
        print(f"❌ Impossibile avviare Chrome: {e2}")
        sys.exit(1)

# ==============================================================================
# 🛑 FUNZIONI UTILITY
# ==============================================================================

def attendi_e_trova_file():
    """Attende che un file sia completamente scaricato"""
    tempo_max = 30
    timer = 0
    while timer < tempo_max:
        files = glob.glob(os.path.join(cartella_download, "*.*"))
        files_completi = [f for f in files if not f.endswith('.crdownload') and not f.endswith('.tmp')]
        if files_completi:
            return max(files_completi, key=os.path.getctime)
        time.sleep(1)
        timer += 1
    return None

def upload_pdf_supabase(file_path, nome_file):
    """Upload PDF a Supabase Storage con gestione errori"""
    try:
        with open(file_path, "rb") as f:
            print(f"      ⬆️ Upload come: {nome_file}")
            
            # Usa direttamente la funzione di upload
            response = supabase.storage.from_(STORAGE_BUCKET).upload(
                path=nome_file,
                file=f,
                file_options={"content-type": "application/pdf"}
            )
            
            # Ottieni URL pubblico
            url_pubblico = supabase.storage.from_(STORAGE_BUCKET).get_public_url(nome_file)
            print(f"      ✅ Upload completato")
            
            return url_pubblico
            
    except Exception as e:
        print(f"      ❌ Errore upload: {e}")
        return None

def verifica_colonne_tabella():
    """Verifica che la tabella abbia le colonne necessarie"""
    try:
        # Prova a vedere la struttura
        result = supabase.table('circolari').select("titolo").limit(1).execute()
        print("✅ Tabella circolari esiste")
        
        # Prova a inserire una riga di test con pdf_url
        try:
            test_data = {
                "titolo": "TEST_COLUMN_CHECK",
                "contenuto": "Test per verificare colonne",
                "pdf_url": "http://test.com",
                "data_pubblicazione": datetime.now().isoformat()
            }
            supabase.table('circolari').insert(test_data).execute()
            supabase.table('circolari').delete().eq("titolo", "TEST_COLUMN_CHECK").execute()
            print("✅ Colonna pdf_url esiste e funziona")
        except Exception as e:
            if "pdf_url" in str(e):
                print("❌ La colonna 'pdf_url' non esiste nella tabella!")
                print("   Esegui questo SQL in Supabase:")
                print("   ALTER TABLE circolari ADD COLUMN pdf_url TEXT;")
                return False
        return True
        
    except Exception as e:
        print(f"❌ Errore verifica tabella: {e}")
        return False

def parse_data_argo(data_str):
    """Converte la data da formato Argo a datetime object"""
    try:
        # Rimuovi spazi extra e newline
        data_str = data_str.strip()
        
        # Se la stringa è vuota
        if not data_str:
            return None
        
        # Prova formato GG/MM/AAAA
        if '/' in data_str:
            parts = data_str.split('/')
            if len(parts) == 3:
                giorno, mese, anno = parts
                # Gestisci anno corto
                if len(anno) == 2:
                    anno = '20' + anno
                return datetime(int(anno), int(mese), int(giorno))
        
        # Prova formato GG-MM-AAAA
        elif '-' in data_str:
            parts = data_str.split('-')
            if len(parts) == 3:
                giorno, mese, anno = parts
                if len(anno) == 2:
                    anno = '20' + anno
                return datetime(int(anno), int(mese), int(giorno))
        
        # Prova estrarre data con regex
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', data_str)
        if match:
            giorno, mese, anno = match.groups()
            if len(anno) == 2:
                anno = '20' + anno
            return datetime(int(anno), int(mese), int(giorno))
        
        print(f"⚠️ Formato data non riconosciuto: '{data_str}'")
        return None
        
    except Exception as e:
        print(f"⚠️ Errore parsing data '{data_str}': {e}")
        return None

def elimina_circolari_vecchie():
    """Elimina le circolari più vecchie di 30 giorni dal database"""
    try:
        # Calcola data limite per l'eliminazione
        data_limite_eliminazione = data_limite.strftime('%Y-%m-%d')
        
        print(f"🗑️  Cerco circolari più vecchie di {data_limite_eliminazione}...")
        
        # Prima otteniamo tutte le circolari per verificare
        result = supabase.table('circolari').select("*").execute()
        
        if result.data:
            vecchie_da_eliminare = []
            for circolare in result.data:
                # Controlla se ha una data di pubblicazione
                if circolare.get('data_pubblicazione'):
                    try:
                        # Parse della data
                        data_str = circolare['data_pubblicazione']
                        if 'T' in data_str:
                            data_str = data_str.split('T')[0]
                        
                        data_pub = datetime.strptime(data_str, '%Y-%m-%d')
                        
                        # Se è più vecchia di 30 giorni, la elimino
                        if data_pub < data_limite:
                            vecchie_da_eliminare.append(circolare['id'])
                    except Exception as e:
                        print(f"⚠️ Errore parsing data circolare {circolare.get('id')}: {e}")
            
            if vecchie_da_eliminare:
                print(f"📋 Trovate {len(vecchie_da_eliminare)} circolari vecchie da eliminare")
                for circ_id in vecchie_da_eliminare:
                    supabase.table('circolari').delete().eq('id', circ_id).execute()
                
                print(f"✅ Eliminate {len(vecchie_da_eliminare)} circolari vecchie")
            else:
                print("✅ Nessuna circolare vecchia da eliminare")
        else:
            print("ℹ️ Nessuna circolare nel database")
        
    except Exception as e:
        print(f"⚠️ Errore eliminazione circolari vecchie: {e}")

# ==============================================================================
# 🛑 MAIN EXECUTION
# ==============================================================================
try:
    # Verifica struttura tabella PRIMA di iniziare
    print("\n🔍 Verifico struttura database...")
    if not verifica_colonne_tabella():
        print("\n❌ PROBLEMA STRUTTURA DATABASE!")
        print("   Risolvi prima i problemi della tabella.")
        sys.exit(1)
    
    # --- ELIMINA CIRCOLARI VECCHIE PRIMA DI INIZIARE ---
    elimina_circolari_vecchie()
    
    # --- LOGIN ---
    print("\n🌍 Login su Argo...")
    driver.get("https://www.portaleargo.it/voti/?classic") 
    
    # Attendi e inserisci credenziali
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']")))
        driver.find_element(By.CSS_SELECTOR, "input[type='text']").send_keys(ARGO_USER)
        driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(ARGO_PASS)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        print("✅ Credenziali inserite")
    except Exception as e:
        print(f"❌ Errore login: {e}")
        # Prova a fare screenshot per debug
        driver.save_screenshot("login_error.png")
        print("📸 Screenshot salvato come login_error.png")
        sys.exit(1)
    
    print("⏳ Attendo Dashboard...")
    time.sleep(10)

    # --- NAVIGAZIONE ALLE CIRCOLARI ---
    print("👉 Navigazione alle circolari...")
    
    # Riporta alla pagina principale prima di cercare i menu
    driver.get("https://www.portaleargo.it/voti/?classic")
    time.sleep(5)
    
    # Cerca e clicca su "Bacheca" usando XPath flessibile
    print("🔍 Cerco menu Bacheca...")
    
    bacheca_trovata = False
    try:
        # Prova vari selettori per Bacheca
        selettori_bacheca = [
            "//*[contains(text(), 'Bacheca')]",
            "//a[contains(., 'Bacheca')]",
            "//span[contains(., 'Bacheca')]",
            "//button[contains(., 'Bacheca')]",
            "//div[contains(., 'Bacheca')]"
        ]
        
        for selettore in selettori_bacheca:
            try:
                elementi = driver.find_elements(By.XPATH, selettore)
                for elem in elementi:
                    if elem.is_displayed() and elem.is_enabled():
                        elem.click()
                        bacheca_trovata = True
                        print(f"✅ Cliccato Bacheca con selettore: {selettore}")
                        time.sleep(3)
                        break
                if bacheca_trovata:
                    break
            except:
                continue
        
        if not bacheca_trovata:
            # Prova con JavaScript
            driver.execute_script("""
                var elements = document.querySelectorAll('span, a, div, button, li');
                for (var i = 0; i < elements.length; i++) {
                    var text = elements[i].textContent || elements[i].innerText;
                    if (text.includes('Bacheca')) {
                        elements[i].click();
                        console.log('Cliccato Bacheca via JS');
                        break;
                    }
                }
            """)
            time.sleep(3)
            print("✅ Provato click JavaScript su Bacheca")
            bacheca_trovata = True
            
    except Exception as e:
        print(f"⚠️ Errore ricerca Bacheca: {e}")
    
    # Cerca sottomenu "Messaggi da leggere" o "Gestione Bacheca"
    time.sleep(2)
    try:
        selettori_sottomenu = [
            "//*[contains(text(), 'Messaggi da leggere')]",
            "//*[contains(text(), 'Gestione Bacheca')]",
            "//*[contains(text(), 'Circolari')]",
            "//*[contains(text(), 'Messaggi')]"
        ]
        
        for selettore in selettori_sottomenu:
            try:
                elementi = driver.find_elements(By.XPATH, selettore)
                for elem in elementi:
                    if elem.is_displayed():
                        driver.execute_script("arguments[0].click();", elem)
                        print(f"✅ Cliccato sottomenu: {selettore}")
                        time.sleep(5)
                        break
            except:
                continue
    except Exception as e:
        print(f"⚠️ Errore sottomenu: {e}")

    print("⏳ Caricamento tabella circolari...")
    time.sleep(10)

    # --- OTTIENI TUTTE LE CIRCOLARI ---
    try:
        righe_iniziali = driver.find_elements(By.CLASS_NAME, "x-grid-row")
        if not righe_iniziali:
            righe_iniziali = driver.find_elements(By.CSS_SELECTOR, "tr.x-grid-row")
        if not righe_iniziali:
            righe_iniziali = driver.find_elements(By.CSS_SELECTOR, "table tr")
        if not righe_iniziali:
            righe_iniziali = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
    except Exception as e:
        print(f"⚠️ Errore ricerca righe: {e}")
        righe_iniziali = []
    
    numero_totale = len(righe_iniziali)
    print(f"📊 Trovate {numero_totale} circolari totali")
    
    if numero_totale == 0:
        print("⚠️ Nessuna circolare trovata.")
        print("📸 Faccio screenshot per debug...")
        driver.save_screenshot("no_circolari.png")
        print("Screenshot salvato come no_circolari.png")
    
    # Contatori per statistiche
    circolari_processate = 0
    circolari_scartate_vecchie = 0
    circolari_con_allegati = 0
    
    for i in range(numero_totale):
        try:
            time.sleep(1)
            righe_fresche = driver.find_elements(By.CLASS_NAME, "x-grid-row")
            if not righe_fresche:
                righe_fresche = driver.find_elements(By.CSS_SELECTOR, "tr.x-grid-row")
            if not righe_fresche:
                righe_fresche = driver.find_elements(By.CSS_SELECTOR, "table tr")
            
            if i >= len(righe_fresche): 
                break
                
            riga_corrente = righe_fresche[i]
            colonne = riga_corrente.find_elements(By.TAG_NAME, "td")
            
            if len(colonne) < 3: 
                continue
            
            data_str = colonne[0].text if colonne[0].text else ""
            categoria = colonne[1].text if len(colonne) > 1 and colonne[1].text else ""
            titolo = colonne[2].text.replace("\n", " ").strip() if len(colonne) > 2 and colonne[2].text else ""
            
            if len(colonne) > 3:
                titolo = colonne[3].text.replace("\n", " ").strip() if colonne[3].text else titolo
            
            cella_file = colonne[4] if len(colonne) > 4 else None
            
            # Salta se mancano dati essenziali
            if not data_str or not titolo:
                continue
            
            # --- VERIFICA SE LA CIRCOLARE È RECENTE (ULTIMI 30 GIORNI) ---
            data_circolare = parse_data_argo(data_str)
            
            if data_circolare is None:
                print(f"⚠️ [{i+1}] Data non valida: '{data_str}' - Salto")
                continue
            
            if data_circolare < data_limite:
                circolari_scartate_vecchie += 1
                print(f"⏳ [{i+1}] {data_str} - {titolo[:40]}... (TROPPO VECCHIA, salto)")
                continue
            
            print(f"\n🔄 [{i+1}/{numero_totale}] {data_str} - {titolo[:50]}...")
            circolari_processate += 1

            # --- GESTIONE ALLEGATI ---
            public_links_string = ""
            ha_allegati = False
            
            if cella_file:
                ha_allegati = cella_file.text.strip() != "" or len(cella_file.find_elements(By.TAG_NAME, "div")) > 0

            if ha_allegati and cella_file:
                print("   📎 Scarico allegati...")
                circolari_con_allegati += 1
                try:
                    driver.execute_script("arguments[0].click();", cella_file)
                    time.sleep(2)
                    
                    # Cerca link PDF
                    try:
                        links_pdf_argo = driver.find_elements(By.PARTIAL_LINK_TEXT, ".pdf")
                        if not links_pdf_argo:
                            links_pdf_argo = driver.find_elements(By.CSS_SELECTOR, "a[href*='.pdf']")
                    except:
                        links_pdf_argo = []
                    
                    lista_url_pubblici = []

                    for index_file, link in enumerate(links_pdf_argo[:3]):  # Massimo 3 allegati
                        try:
                            print(f"      ⬇️ Download allegato {index_file+1}...")
                            link_url = link.get_attribute('href')
                            if link_url:
                                driver.execute_script(f"window.open('{link_url}', '_blank');")
                                time.sleep(3)
                                
                                file_scaricato = attendi_e_trova_file()
                                
                                if file_scaricato:
                                    ts = datetime.now().strftime('%Y%m%d%H%M%S')
                                    nome_sicuro = f"circolare_{data_circolare.strftime('%Y%m%d')}_{ts}_{index_file+1}.pdf"
                                    
                                    url_pubblico = upload_pdf_supabase(file_scaricato, nome_sicuro)
                                    if url_pubblico:
                                        lista_url_pubblici.append(url_pubblico)
                                    
                                    os.remove(file_scaricato)
                                else:
                                    print(f"      ⚠️ Download allegato {index_file+1} fallito")
                                    
                                # Chiudi la nuova tab
                                driver.switch_to.window(driver.window_handles[0])
                        except Exception as e:
                            print(f"      ❌ Errore allegato {index_file+1}: {e}")

                    if lista_url_pubblici:
                        public_links_string = ";;;".join(lista_url_pubblici)
                        print(f"   ✅ {len(lista_url_pubblici)} allegati processati")

                except Exception as e:
                    print(f"   ⚠️ Errore gestione allegati: {e}")

            # SALVATAGGIO NEL DATABASE
            try:
                # Formatta data per database
                data_per_db = data_circolare.isoformat()
                
                dati_circolare = {
                    "titolo": titolo,
                    "contenuto": f"Categoria: {categoria} - Data: {data_str}",
                    "data_pubblicazione": data_per_db,
                    "data_scaricamento": datetime.now().isoformat()
                }
                
                if public_links_string:
                    dati_circolare["pdf_url"] = public_links_string
                
                # Controlla se esiste già
                res = supabase.table('circolari').select("*").eq('titolo', titolo).execute()
                
                if not res.data:
                    supabase.table('circolari').insert(dati_circolare).execute()
                    print("   ✅ Salvata nel database (NUOVA).")
                else:
                    # Aggiorna solo se diversa
                    supabase.table('circolari').update(dati_circolare).eq('titolo', titolo).execute()
                    print("   🔄 Aggiornata nel database.")
                    
            except Exception as e:
                print(f"   ❌ Errore salvataggio database: {e}")

        except Exception as e:
            print(f"⚠️ Errore nella riga {i+1}: {e}")
            continue

except Exception as e:
    print(f"\n❌ ERRORE CRITICO: {e}")
    import traceback
    traceback.print_exc()

finally:
    print("\n" + "="*60)
    print("📊 RIEPILOGO ESECUZIONE")
    print("="*60)
    print(f"🔍 Circolari trovate totali: {numero_totale}")
    print(f"✅ Circolari processate (ultimi 30 giorni): {circolari_processate}")
    print(f"🗑️  Circolari scartate (troppo vecchie): {circolari_scartate_vecchie}")
    print(f"📎 Circolari con allegati: {circolari_con_allegati}")
    print("="*60)
    
    # Elimina nuovamente circolari vecchie per sicurezza
    try:
        elimina_circolari_vecchie()
    except:
        pass
    
    # Pulisci cartella download
    if os.path.exists(cartella_download):
        try:
            shutil.rmtree(cartella_download)
            print("🧹 Cartella download pulita.")
        except:
            pass
    
    print("\n🏁 Chiusura browser...")
    try:
        driver.quit()
    except:
        pass
    
    print("\n🎯 Script completato!")
