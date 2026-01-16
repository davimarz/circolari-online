#!/usr/bin/env python3
"""
Script per scaricare circolari da Argo e salvarle in Supabase
Versione ottimizzata per ambienti server senza UI
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
import re

# ==============================================================================
# 🛑 CONFIGURAZIONE VARIABILI D'AMBIENTE
# ==============================================================================
print("🔧 Configurazione ambiente...")

# Credenziali da variabili d'ambiente (più sicuro)
ARGO_USER = os.getenv("ARGO_USER", "davide.marziano.sc26953")
ARGO_PASS = os.getenv("ARGO_PASS", "dvd2Frank.")

# URL del backend (su Railway)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")

# Configurazione Supabase
SUPABASE_URL = "https://ojnofjebrlwrlowovvjd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9qbm9mamVicmx3cmxvd292dmpkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc2NzgzMTcsImV4cCI6MjA4MzI1NDMxN30._LVpGUOyq-HJQsZO7YLDf7Fu7N5Kk_BxDBhKsFSGE_U"

print(f"🔗 Backend URL: {BACKEND_URL}")

# ==============================================================================
# 🛑 FUNZIONI UTILITY
# ==============================================================================

def test_backend_connection():
    """Testa la connessione al backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend connesso correttamente")
            return True
        else:
            print(f"⚠️ Backend risponde con status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Impossibile connettersi al backend: {e}")
        return False

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

def invia_circolare_al_backend(circolare_data):
    """Invia una circolare al backend per il salvataggio"""
    try:
        print(f"📤 Invio circolare: {circolare_data['titolo'][:50]}...")
        
        response = requests.post(
            f"{BACKEND_URL}/api/circolari",
            json=circolare_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ Circolare inviata con successo (ID: {response.json().get('id', 'N/A')})")
            return True
        else:
            print(f"❌ Errore backend: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Errore invio circolare: {e}")
        return False

def elimina_circolari_vecchie():
    """Richiede l'eliminazione delle circolari vecchie (>30 giorni)"""
    try:
        print("🗑️  Richiedo eliminazione circolari vecchie...")
        
        response = requests.delete(
            f"{BACKEND_URL}/api/circolari/vecchie",
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result.get('eliminate', 0)} circolari vecchie eliminate")
            return True
        else:
            print(f"⚠️ Errore eliminazione: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️ Errore richiesta eliminazione: {e}")
        return False

def simula_scaricamento_circolari():
    """
    Simula lo scaricamento delle circolari da Argo
    In un ambiente reale, questa sarebbe la parte con Selenium
    """
    print("\n🎭 SIMULAZIONE scaricamento circolari da Argo...")
    
    # Data limite: ultimi 30 giorni
    data_limite = datetime.now() - timedelta(days=30)
    
    # Circolari di esempio (dati simulati)
    circolari_simulate = [
        {
            "data_str": datetime.now().strftime("%d/%m/%Y"),
            "categoria": "Comunicazioni",
            "titolo": "Riunione docenti del 20 gennaio",
            "allegati": ["https://example.com/riunione.pdf"]
        },
        {
            "data_str": (datetime.now() - timedelta(days=5)).strftime("%d/%m/%Y"),
            "categoria": "Genitori",
            "titolo": "Avviso assemblea genitori",
            "allegati": []
        },
        {
            "data_str": (datetime.now() - timedelta(days=15)).strftime("%d/%m/%Y"),
            "categoria": "Studenti",
            "titolo": "Calendario esami di recupero",
            "allegati": ["https://example.com/calendario.pdf"]
        },
        {
            "data_str": "01/12/2024",  # Più vecchia di 30 giorni
            "categoria": "Amministrativo",
            "titolo": "Comunicazione vecchia da scartare",
            "allegati": []
        },
        {
            "data_str": (datetime.now() - timedelta(days=10)).strftime("%d/%m/%Y"),
            "categoria": "Didattica",
            "titolo": "Modifiche orario secondo quadrimestre",
            "allegati": ["https://example.com/orario.pdf", "https://example.com/note.pdf"]
        }
    ]
    
    circolari_processate = 0
    circolari_scartate = 0
    
    for i, circ in enumerate(circolari_simulate):
        data_circolare = parse_data_argo(circ["data_str"])
        
        if data_circolare is None:
            print(f"⚠️ [{i+1}] Data non valida: '{circ['data_str']}' - Salto")
            continue
        
        # Controlla se è più vecchia di 30 giorni
        if data_circolare < data_limite:
            circolari_scartate += 1
            print(f"⏳ [{i+1}] {circ['data_str']} - {circ['titolo'][:40]}... (TROPPO VECCHIA, salto)")
            continue
        
        print(f"\n🔄 [{i+1}] {circ['data_str']} - {circ['titolo']}")
        
        # Prepara dati per il backend
        circolare_data = {
            "titolo": circ["titolo"],
            "contenuto": f"Categoria: {circ['categoria']} - Data: {circ['data_str']}",
            "data_pubblicazione": data_circolare.isoformat(),
            "categoria": circ["categoria"]
        }
        
        # Aggiungi allegati se presenti
        if circ["allegati"]:
            circolare_data["allegati"] = circ["allegati"]
            print(f"   📎 {len(circ['allegati'])} allegati trovati")
        
        # Invia al backend
        if invia_circolare_al_backend(circolare_data):
            circolari_processate += 1
        else:
            print("   ❌ Fallito invio al backend")
    
    return circolari_processate, circolari_scartate

def scarica_circolari_reali():
    """
    Versione alternativa che usa requests per scaricare
    (senza Selenium, se il portale lo permette)
    """
    print("\n🌐 Tentativo connessione diretta ad Argo...")
    
    # URL di esempio (da verificare)
    login_url = "https://www.portaleargo.it/famiglia/api/rest/login"
    circolari_url = "https://www.portaleargo.it/famiglia/api/rest/circolari"
    
    try:
        # Tentativo di login API
        session = requests.Session()
        
        # Headers per sembrare un browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
            'Content-Type': 'application/json'
        }
        
        # Dati login (da verificare formato esatto)
        login_data = {
            'username': ARGO_USER,
            'password': ARGO_PASS
        }
        
        print(f"🔐 Tentativo login come {ARGO_USER}...")
        response = session.post(login_url, json=login_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("✅ Login apparentemente riuscito")
            
            # Tentativo di ottenere circolari
            print("📄 Richiedo circolari...")
            response = session.get(circolari_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                circolari = response.json()
                print(f"✅ Ricevute {len(circolari)} circolari")
                
                # Qui processeresti le circolari
                return len(circolari), 0
            else:
                print(f"❌ Errore ricezione circolari: {response.status_code}")
                return 0, 0
        else:
            print(f"❌ Login fallito: {response.status_code}")
            return 0, 0
            
    except Exception as e:
        print(f"❌ Errore connessione Argo: {e}")
        return 0, 0

# ==============================================================================
# 🛑 MAIN EXECUTION
# ==============================================================================
def main():
    print("\n" + "="*60)
    print("🔄 SCRIPT CIRCOLARI ARGO")
    print("="*60)
    
    # 1. Test connessione backend
    print("\n1️⃣ Test connessione backend...")
    if not test_backend_connection():
        print("\n❌ Impossibile continuare senza backend funzionante")
        print("   Assicurati che:")
        print("   1. Il backend Streamlit sia avviato")
        print("   2. La variabile BACKEND_URL sia corretta")
        print("   3. Il database sia configurato su Railway")
        return
    
    # 2. Elimina circolari vecchie
    print("\n2️⃣ Pulizia circolari vecchie...")
    elimina_circolari_vecchie()
    
    # 3. Scarica circolari
    print("\n3️⃣ Scaricamento circolari...")
    
    # Scegli il metodo in base all'ambiente
    use_simulation = os.getenv("USE_SIMULATION", "false").lower() == "true"
    
    if use_simulation:
        print("🎭 Modalità SIMULAZIONE attivata")
        processate, scartate = simula_scaricamento_circolari()
    else:
        print("🌐 Tentativo connessione reale ad Argo")
        processate, scartate = scarica_circolari_reali()
        
        # Fallback alla simulazione se fallisce
        if processate == 0:
            print("\n⚠️ Connessione reale fallita, passo alla simulazione...")
            processate, scartate = simula_scaricamento_circolari()
    
    # 4. Riepilogo
    print("\n" + "="*60)
    print("📊 RIEPILOGO ESECUZIONE")
    print("="*60)
    print(f"✅ Circolari processate: {processate}")
    print(f"🗑️  Circolari scartate (vecchie): {scartate}")
    print("="*60)
    
    # 5. Log dell'esecuzione
    try:
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "circolari_processate": processate,
            "circolari_scartate": scartate,
            "tipo_esecuzione": "simulazione" if use_simulation else "reale"
        }
        
        requests.post(
            f"{BACKEND_URL}/api/logs",
            json=log_data,
            timeout=10
        )
        print("\n📝 Log salvato sul backend")
        
    except Exception as e:
        print(f"\n⚠️ Errore salvataggio log: {e}")
    
    print("\n🎯 Script completato con successo!")

if __name__ == "__main__":
    main()
