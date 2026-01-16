#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

ARGO_URL = "https://www.portaleargo.it/voti/?classic"
USERNAME = "davide.marziano.sc26953"
PASSWORD = "dvd2Frank."

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

print("=== TEST LOGIN ARGO ===")

# 1. Prima pagina
print("1. Carico pagina login...")
response = session.get(ARGO_URL)
soup = BeautifulSoup(response.content, 'html.parser')

# Cerca form login
forms = soup.find_all('form')
print(f"   Form trovati: {len(forms)}")

for form in forms:
    print(f"   Form action: {form.get('action', 'Nessuno')}")
    inputs = form.find_all('input')
    for inp in inputs:
        print(f"     Input: name='{inp.get('name')}', type='{inp.get('type')}'")

print("\n2. Provo login...")

# Cerca token
token = ""
token_input = soup.find('input', {'name': '_token'})
if token_input:
    token = token_input.get('value', '')
    print(f"   Token CSRF trovato: {token[:20]}...")

# Dati login
login_data = {
    '_token': token,
    'username': USERNAME,
    'password': PASSWORD
}

# URL login (potrebbe essere diverso)
login_url = "https://www.portaleargo.it/login"
response = session.post(login_url, data=login_data)

print(f"3. Risposta login: {response.status_code}")
print(f"   Lunghezza pagina: {len(response.text)} caratteri")

# Controlla se login riuscito
if "Benvenuto" in response.text or "Dashboard" in response.text or "menu" in response.text:
    print("✅ LOGIN RIUSCITO!")
    
    # Salva pagina per analisi
    with open('argo_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("   Pagina salvata in argo_dashboard.html")
    
    # Cerca link a circolari
    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a')
    print("\n4. Link trovati nella dashboard:")
    
    circolari_links = []
    for link in links[:20]:  # Prime 20
        href = link.get('href', '')
        text = link.text.strip()
        if any(term in text.lower() or term in href.lower() for term in ['circolare', 'avviso', 'comunicazione']):
            print(f"   🔗 {text[:50]} -> {href}")
            circolari_links.append((text, href))
    
    if circolari_links:
        print(f"\n✅ Trovati {len(circolari_links)} link a circolari/avvisi")
    else:
        print("\n⚠️ Nessun link a circolari trovato")
        
else:
    print("❌ LOGIN FALLITO")
    # Salva per debug
    with open('argo_login_failed.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("   Pagina salvata in argo_login_failed.html")
