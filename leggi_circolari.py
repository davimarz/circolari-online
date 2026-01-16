#!/usr/bin/env python3
"""
Robot per leggere circolari dal Portale Argo IC Anna Frank
"""

import os
import sys
import time
import logging
import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from database import salva_circolare_db, test_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ⚠️ CONFIGURA QUESTI DATI
ARGO_URL = "https://www.portaleargo.it/voti/?classic"
ARGO_USERNAME = "davide.marziano.sc26953"
ARGO_PASSWORD = "dvd2Frank."

class RobotArgoCircolari:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.circolari_salvate = 0
        self.is_logged_in = False
    
    def test_connessione(self):
        return test_connection()
    
    def login_argo(self):
        """Effettua login su Portale Argo"""
        logger.info(f"🔐 Login Argo come: {ARGO_USERNAME}")
        
        try:
            # 1. Prima richiesta per ottenere cookie e token
            response = self.session.get(ARGO_URL, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Cerca token CSRF (se presente)
            token = ""
            token_input = soup.find('input', {'name': '_token'})
            if token_input:
                token = token_input.get('value', '')
            
            # 2. Prepara dati login
            login_data = {
                '_token': token,
                'username': ARGO_USERNAME,
                'password': ARGO_PASSWORD,
                'remember': 'on'
            }
            
            # 3. Invia login
            login_url = "https://www.portaleargo.it/login"
            response = self.session.post(login_url, data=login_data, timeout=30)
            
            # 4. Verifica login
            if "Dashboard" in response.text or "Benvenuto" in response.text or "menu" in response.text:
                logger.info("✅ Login Argo riuscito")
                self.is_logged_in = True
                return True
            else:
                logger.error("❌ Login Argo fallito")
                # Salva pagina per debug
                with open('debug_login.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.info("📄 Pagina di risposta salvata in debug_login.html")
                return False
                
        except Exception as e:
            logger.error(f"❌ Errore login Argo: {e}")
            return False
    
    def cerca_circolari_argo(self):
        """Cerca le circolari nell'area genitori/alunni di Argo"""
        logger.info("🔍 Cerca circolari in Argo...")
        
        if not self.is_logged_in:
            logger.error("❌ Non autenticato su Argo")
            return []
        
        try:
            # URL comuni per le circolari in Argo
            urls_da_provare = [
                "https://www.portaleargo.it/famiglia/genitore/circolari",
                "https://www.portaleargo.it/alunno/circolari",
                "https://www.portaleargo.it/circolari",
                "https://www.portaleargo.it/avvisi",
                "https://www.portaleargo.it/comunicazioni"
            ]
            
            circolari_trovate = []
            
            for url in urls_da_provare:
                try:
                    logger.info(f"📄 Provo URL: {url}")
                    response = self.session.get(url, timeout=30)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Cerca elementi che potrebbero essere circolari
                        # Argo spesso usa classi specifiche
                        possibili_elementi = soup.find_all(['tr', 'div', 'li', 'article'])
                        
                        for elem in possibili_elementi:
                            testo = elem.text.strip().lower()
                            if any(term in testo for term in ['circolare', 'avviso', 'comunicazione', 'notizia']):
                                # Prova ad estrarre dati
                                circolare = self._estrai_da_elemento_argo(elem)
                                if circolare:
                                    circolari_trovate.append(circolare)
                        
                        if circolari_trovate:
                            logger.info(f"✅ Trovate {len(circolari_trovate)} circolari in {url}")
                            break
                            
                except Exception as e:
                    logger.debug(f"Errore URL {url}: {e}")
                    continue
            
            return circolari_trovate
            
        except Exception as e:
            logger.error(f"❌ Errore ricerca circolari: {e}")
            return []
    
    def _estrai_da_elemento_argo(self, elemento):
        """Estrai dati da un elemento di Argo"""
        try:
            # Cerca titolo
            titolo_elem = elemento.find(['a', 'strong', 'h3', 'h4', 'td'])
            if not titolo_elem:
                return None
            
            titolo = titolo_elem.text.strip()
            if len(titolo) < 5:  # Titolo troppo corto
                return None
            
            # Cerca data (Argo spesso mette date in span o piccoli)
            data_elem = elemento.find(['span', 'small', 'time', 'font'])
            data_text = ""
            if data_elem:
                data_text = data_elem.text.strip()
                # Cerca pattern data italiano
                import re
                date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', data_text)
                if date_match:
                    data_text = date_match.group(1)
            
            # Cerca link PDF
            pdf_url = None
            link_elem = elemento.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                if '.pdf' in href.lower():
                    if href.startswith('http'):
                        pdf_url = href
                    elif href.startswith('/'):
                        pdf_url = 'https://www.portaleargo.it' + href
                    else:
                        pdf_url = 'https://www.portaleargo.it/' + href
            
            # Crea contenuto
            contenuto = f"Circolare: {titolo}"
            if data_text:
                contenuto += f"\nData: {data_text}"
            
            return {
                'titolo': titolo[:200],
                'contenuto': contenuto,
                'data_pubblicazione': self._parse_data(data_text) if data_text else datetime.now().date(),
                'pdf_url': pdf_url
            }
            
        except Exception as e:
            logger.debug(f"Errore estrazione elemento: {e}")
            return None
    
    def _parse_data(self, testo_data):
        """Converte testo data"""
        try:
            testo_data = testo_data.strip()
            if not testo_data:
                return datetime.now().date()
            
            # Rimuovi parole
            import re
            testo_data = re.sub(r'[a-zA-Z]', '', testo_data).strip()
            
            formati = ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']
            for fmt in formati:
                try:
                    return datetime.strptime(testo_data, fmt).date()
                except:
                    continue
            
            return datetime.now().date()
        except:
            return datetime.now().date()
    
    def salva_circolare(self, circolare):
        """Salva una circolare"""
        try:
            success = salva_circolare_db(
                titolo=circolare['titolo'],
                contenuto=circolare['contenuto'],
                data_pubblicazione=circolare['data_pubblicazione'],
                pdf_url=circolare.get('pdf_url')
            )
            
            if success:
                self.circolari_salvate += 1
                logger.info(f"✅ Salvata: {circolare['titolo'][:50]}...")
            return success
            
        except Exception as e:
            logger.error(f"❌ Errore salvataggio: {e}")
            return False
    
    def run(self):
        """Esegue il robot per Argo"""
        logger.info("=" * 60)
        logger.info("🤖 ROBOT ARGO CIRCOLARI")
        logger.info(f"   Utente: {ARGO_USERNAME}")
        logger.info("=" * 60)
        
        # Test database
        if not self.test_connessione():
            logger.error("❌ Database non connesso")
            return False
        
        # Login Argo
        if not self.login_argo():
            logger.warning("⚠️ Login Argo fallito, uso dati di test")
            # Fallback a circolari di test
            oggi = datetime.now()
            circolari = [{
                'titolo': f"Test (Argo non accessibile) {oggi.strftime('%H:%M')}",
                'contenuto': f"Login Argo fallito per {ARGO_USERNAME}. Controlla credenziali.",
                'data_pubblicazione': oggi.date(),
                'pdf_url': None
            }]
        else:
            # Cerca circolari reali
            circolari = self.cerca_circolari_argo()
            
            if not circolari:
                logger.warning("⚠️ Nessuna circolare trovata in Argo")
                oggi = datetime.now()
                circolari = [{
                    'titolo': f"Test (nessuna circolare trovata) {oggi.strftime('%H:%M')}",
                    'contenuto': "Il robot ha effettuato il login ma non ha trovato circolari.",
                    'data_pubblicazione': oggi.date(),
                    'pdf_url': None
                }]
        
        # Salva
        logger.info(f"💾 Trovate {len(circolari)} circolari, salvataggio...")
        for circ in circolari:
            self.salva_circolare(circ)
            time.sleep(1)  # Pausa per non sovraccaricare
        
        logger.info("=" * 60)
        logger.info(f"🏁 COMPLETATO: {self.circolari_salvate} circolari salvate")
        logger.info("=" * 60)
        
        return self.circolari_salvate > 0

def main():
    robot = RobotArgoCircolari()
    try:
        success = robot.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"💥 Errore: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
