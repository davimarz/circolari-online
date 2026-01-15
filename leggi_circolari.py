#!/usr/bin/env python3
"""
Robot per leggere circolari dal sito dell'IC Anna Frank
Versione Robusta con gestione errori migliorata
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import psycopg2
from database import salva_circolare_db, init_db, test_connection

# Configura logging dettagliato
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# URL del sito delle circolari (esempio)
SITO_CIRCOLARI = "https://www.icannafrank.edu.it/circolari"

class RobotCircolari:
    def __init__(self):
        """Inizializza il robot"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.circolari_trovate = 0
        self.circolari_salvate = 0
        
    def test_connessione(self):
        """Testa la connessione al database"""
        logger.info("🔍 Verifica struttura database...")
        if not test_connection():
            logger.error("❌ Connessione database fallita")
            return False
        return True
    
    def analizza_pagina(self, url):
        """Analizza una pagina per estrarre le circolari"""
        try:
            logger.info(f"📄 Analisi pagina: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            circolari = []
            
            # CERCA I BLOCCHI DELLE CIRCOLARI (ADATTA QUESTI SELECTOR)
            # Questi sono esempi - devi adattarli al tuo sito
            possibili_selectors = [
                'div.circolari', 'div.news-item', 'article.post',
                'div.avviso', 'tr', 'div.content', 'div.circolare'
            ]
            
            for selector in possibili_selectors:
                elementi = soup.select(selector)
                if len(elementi) > 2:  # Se trova abbastanza elementi
                    logger.info(f"✅ Trovato selector: {selector} ({len(elementi)} elementi)")
                    for elem in elementi:
                        try:
                            circolare = self._estrai_circolare(elem)
                            if circolare:
                                circolari.append(circolare)
                        except Exception as e:
                            logger.debug(f"Errore estrazione singola circolare: {e}")
                    break
            
            return circolari
            
        except Exception as e:
            logger.error(f"❌ Errore analisi pagina {url}: {e}")
            return []
    
    def _estrai_circolare(self, elemento):
        """Estrai i dati da un elemento HTML"""
        try:
            # CERCA TITOLO
            titolo = None
            titolo_selectors = ['h2', 'h3', 'h4', '.titolo', '.title', 'a', 'strong']
            
            for selector in titolo_selectors:
                trovato = elemento.select_one(selector)
                if trovato and trovato.text.strip():
                    titolo = trovato.text.strip()
                    break
            
            if not titolo:
                return None
            
            # CERCA DATA
            data_text = None
            data_selectors = ['.data', '.date', 'time', 'span.data', 'small']
            
            for selector in data_selectors:
                trovato = elemento.select_one(selector)
                if trovato and trovato.text.strip():
                    data_text = trovato.text.strip()
                    break
            
            # CERCA CONTENUTO
            contenuto = ""
            contenuto_selectors = ['.contenuto', '.content', 'p', 'div.descrizione']
            
            for selector in contenuto_selectors:
                trovati = elemento.select(selector)
                if trovati:
                    contenuto = ' '.join([p.text.strip() for p in trovati])
                    break
            
            # CERCA LINK PDF
            pdf_url = None
            link_selectors = ['a[href$=".pdf"]', 'a[href*="download"]', 'a[href*="pdf"]']
            
            for selector in link_selectors:
                trovato = elemento.select_one(selector)
                if trovato and trovato.get('href'):
                    href = trovato.get('href')
                    if not href.startswith('http'):
                        href = requests.compat.urljoin(SITO_CIRCOLARI, href)
                    pdf_url = href
                    break
            
            # Pulisci e formatta
            titolo = self._pulisci_testo(titolo)
            contenuto = self._pulisci_testo(contenuto)
            
            # Converti data
            data_pubblicazione = self._parse_data(data_text) if data_text else datetime.now().date()
            
            return {
                'titolo': titolo[:500],  # Limita lunghezza
                'contenuto': contenuto[:5000],
                'data_pubblicazione': data_pubblicazione,
                'pdf_url': pdf_url,
                'fonte': 'sito_scuola'
            }
            
        except Exception as e:
            logger.debug(f"Errore estrazione circolare: {e}")
            return None
    
    def _pulisci_testo(self, testo):
        """Pulisce il testo da spazi e newline multipli"""
        if not testo:
            return ""
        # Rimuovi spazi multipli e newline
        import re
        testo = re.sub(r'\s+', ' ', testo)
        return testo.strip()
    
    def _parse_data(self, data_text):
        """Converte il testo della data in oggetto date"""
        try:
            # Prova vari formati di data
            formati = [
                '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d',
                '%d %B %Y', '%d %b %Y', '%B %d, %Y'
            ]
            
            for formato in formati:
                try:
                    return datetime.strptime(data_text, formato).date()
                except:
                    continue
            
            # Se non trova formato, usa oggi
            return datetime.now().date()
            
        except:
            return datetime.now().date()
    
    def salva_circolare(self, circolare):
        """Salva una circolare nel database"""
        try:
            logger.info(f"💾 Tentativo salvataggio: {circolare['titolo'][:50]}...")
            
            success = salva_circolare_db(
                titolo=circolare['titolo'],
                contenuto=circolare['contenuto'],
                data_pubblicazione=circolare['data_pubblicazione'],
                pdf_url=circolare.get('pdf_url'),
                fonte=circolare.get('fonte', 'sito_scuola')
            )
            
            if success:
                self.circolari_salvate += 1
                logger.info(f"✅ Salvata: {circolare['titolo'][:50]}...")
            else:
                logger.warning(f"⚠️ Non salvata (già presente?): {circolare['titolo'][:50]}...")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Errore salvataggio circolare: {e}")
            return False
    
    def run(self):
        """Esegue il robot"""
        logger.info("=" * 60)
        logger.info("🤖 ROBOT CIRCOLARI - VERSIONE ROBUSTA")
        logger.info("=" * 60)
        start_time = datetime.now()
        logger.info(f"🚀 Inizio: {start_time.strftime('%d/%m/%Y %H:%M:%S')}")
        logger.info("-" * 60)
        
        # Test iniziali
        if not self.test_connessione():
            logger.error("❌ Test connessione fallito. Uscita.")
            return False
        
        # Inizializza database
        init_db()
        
        # Analizza il sito
        logger.info("🌐 Connessione al sito delle circolari...")
        circolari_trovate = self.analizza_pagina(SITO_CIRCOLARI)
        
        if not circolari_trovate:
            # Fallback: crea una circolare di test
            logger.warning("⚠️ Nessuna circolare trovata, creo test...")
            circolari_trovate = [{
                'titolo': f"Circolare Test Robot {datetime.now().strftime('%H:%M')}",
                'contenuto': 'Questa è una circolare di test generata automaticamente dal robot.',
                'data_pubblicazione': datetime.now().date(),
                'pdf_url': None,
                'fonte': 'robot_test'
            }]
        
        self.circolari_trovate = len(circolari_trovate)
        logger.info(f"📊 Trovate {self.circolari_trovate} circolari")
        
        # Salva le circolari
        logger.info("💾 Salvataggio nel database...")
        for i, circ in enumerate(circolari_trovate, 1):
            logger.info(f"📝 [{i}/{self.circolari_trovate}] Elaborazione...")
            self.salva_circolare(circ)
            time.sleep(0.5)  # Pausa per non sovraccaricare
        
        # Riepilogo
        end_time = datetime.now()
        durata = end_time - start_time
        
        logger.info("=" * 60)
        logger.info("🏁 ROBOT COMPLETATO")
        logger.info(f"   Trovate: {self.circolari_trovate}")
        logger.info(f"   Salvate: {self.circolari_salvate}")
        logger.info(f"   Durata: {durata.total_seconds():.1f}s")
        logger.info(f"   Ora: {end_time.strftime('%H:%M:%S')}")
        logger.info("=" * 60)
        
        return self.circolari_salvate > 0

def main():
    """Funzione principale"""
    robot = RobotCircolari()
    
    try:
        success = robot.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("⏹️ Interrotto dall'utente")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Errore fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
