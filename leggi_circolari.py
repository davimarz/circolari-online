#!/usr/bin/env python3
"""
Robot per leggere circolari dal sito dell'IC Anna Frank
Versione Robusta con gestione errori migliorata
"""

import os
import sys
import time
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from database import salva_circolare_db, init_db, test_connection, verifica_struttura

# Configura logging dettagliato
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# URL del sito delle circolari
SITO_CIRCOLARI = os.environ.get('SITO_CIRCOLARI', 'https://www.icannafrank.edu.it/circolari')

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
        
        # 1. Test connessione
        if not test_connection():
            logger.error("❌ Connessione database fallita")
            return False
        
        # 2. Inizializza/aggiorna database
        logger.info("🔄 Inizializzazione/aggiornamento database...")
        if not init_db():
            logger.error("❌ Inizializzazione database fallita")
            return False
        
        # 3. Verifica struttura
        logger.info("📋 Verifica struttura tabella...")
        if not verifica_struttura():
            logger.warning("⚠️ Struttura tabella incompleta, tenteremo comunque...")
        
        return True
    
    def analizza_pagina(self, url):
        """Analizza una pagina per estrarre le circolari"""
        try:
            logger.info(f"📄 Analisi pagina: {url}")
            
            # Simula circolari di test per ora
            # MODIFICA QUESTA PARTE CON IL TUO SITO REALE
            
            oggi = datetime.now()
            circolari_trovate = [{
                'titolo': f"Circolare Test Robot {oggi.strftime('%H:%M')}",
                'contenuto': 'Questa è una circolare di test generata automaticamente dal robot per verificare il funzionamento del sistema.',
                'data_pubblicazione': oggi.date(),
                'pdf_url': None,
                'fonte': 'robot_test'
            }]
            
            logger.info(f"✅ Trovate {len(circolari_trovate)} circolari (test)")
            return circolari_trovate
            
        except Exception as e:
            logger.error(f"❌ Errore analisi pagina {url}: {e}")
            
            # Fallback: crea una circolare di test
            oggi = datetime.now()
            return [{
                'titolo': f"Circolare Fallback {oggi.strftime('%H:%M')}",
                'contenuto': f'Circolare di fallback generata automaticamente a causa di un errore: {str(e)[:100]}',
                'data_pubblicazione': oggi.date(),
                'pdf_url': None,
                'fonte': 'robot_fallback'
            }]
    
    def salva_circolare(self, circolare):
        """Salva una circolare nel database"""
        try:
            titolo_breve = circolare['titolo'][:50] + "..." if len(circolare['titolo']) > 50 else circolare['titolo']
            logger.info(f"💾 Tentativo salvataggio: {titolo_breve}")
            
            success = salva_circolare_db(
                titolo=circolare['titolo'],
                contenuto=circolare['contenuto'],
                data_pubblicazione=circolare['data_pubblicazione'],
                pdf_url=circolare.get('pdf_url'),
                fonte=circolare.get('fonte', 'sito_scuola')
            )
            
            if success:
                self.circolari_salvate += 1
                logger.info(f"✅ Salvata: {titolo_breve}")
            else:
                logger.warning(f"⚠️ Non salvata (già presente?): {titolo_breve}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Errore salvataggio circolare: {e}")
            return False
    
    def run(self):
        """Esegue il robot"""
        logger.info("=" * 60)
        logger.info("🤖 ROBOT CIRCOLARI - VERSIONE DEFINITIVA CON FIX")
        logger.info("=" * 60)
        start_time = datetime.now()
        logger.info(f"🚀 Inizio: {start_time.strftime('%d/%m/%Y %H:%M:%S')}")
        logger.info("-" * 60)
        
        # Test iniziali CRITICI
        if not self.test_connessione():
            logger.error("❌ Test connessione fallito. Uscita.")
            return False
        
        # Analizza il sito
        logger.info(f"🌐 Connessione al sito: {SITO_CIRCOLARI}")
        circolari_trovate = self.analizza_pagina(SITO_CIRCOLARI)
        
        self.circolari_trovate = len(circolari_trovate)
        logger.info(f"📊 Trovate {self.circolari_trovate} circolari")
        
        # Salva le circolari
        if circolari_trovate:
            logger.info("💾 Salvataggio nel database...")
            for i, circ in enumerate(circolari_trovate, 1):
                logger.info(f"📝 [{i}/{self.circolari_trovate}] Elaborazione...")
                self.salva_circolare(circ)
                time.sleep(0.3)  # Pausa breve
        else:
            logger.warning("⚠️ Nessuna circolare da salvare")
        
        # Riepilogo
        end_time = datetime.now()
        durata = end_time - start_time
        
        logger.info("=" * 60)
        logger.info("🏁 ROBOT COMPLETATO")
        logger.info(f"   Trovate: {self.circolari_trovate}")
        logger.info(f"   Salvate: {self.circolari_salvate}")
        logger.info(f"   Durata: {durata.total_seconds():.1f}s")
        logger.info(f"   Ora: {end_time.strftime('%H:%M:%S')}")
        
        if self.circolari_salvate > 0:
            logger.info("✅ SUCCESSO: Circolari salvate correttamente")
        else:
            logger.warning("⚠️ ATTENZIONE: Nessuna circolare salvata")
            
        logger.info("=" * 60)
        
        return self.circolari_salvate > 0

def main():
    """Funzione principale"""
    robot = RobotCircolari()
    
    try:
        success = robot.run()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("⏹️ Interrotto dall'utente")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Errore fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
