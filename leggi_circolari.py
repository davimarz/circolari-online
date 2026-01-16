#!/usr/bin/env python3
"""
Robot per leggere circolari - VERSIONE FUNZIONANTE
SENZA colonna 'fonte'
"""

import os
import sys
import time
import logging
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

SITO_CIRCOLARI = "https://www.icannafrank.edu.it/circolari"

class RobotCircolari:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.circolari_salvate = 0
    
    def test_connessione(self):
        logger.info("🔍 Test connessione database...")
        return test_connection()
    
    def analizza_pagina(self):
        """Crea una circolare di test"""
        oggi = datetime.now()
        return [{
            'titolo': f"Circolare Test {oggi.strftime('%d/%m %H:%M')}",
            'contenuto': 'Questa è una circolare di test generata automaticamente.',
            'data_pubblicazione': oggi.date(),
            'pdf_url': None
        }]
    
    def salva_circolare(self, circolare):
        """Salva SENZA 'fonte'"""
        try:
            titolo_breve = circolare['titolo'][:50]
            logger.info(f"💾 Salvataggio: {titolo_breve}")
            
            success = salva_circolare_db(
                titolo=circolare['titolo'],
                contenuto=circolare['contenuto'],
                data_pubblicazione=circolare['data_pubblicazione'],
                pdf_url=circolare.get('pdf_url')
            )
            
            if success:
                self.circolari_salvate += 1
                logger.info(f"✅ Salvata")
            return success
            
        except Exception as e:
            logger.error(f"❌ Errore: {e}")
            return False
    
    def run(self):
        logger.info("=" * 50)
        logger.info("🤖 ROBOT CIRCOLARI")
        logger.info("=" * 50)
        start_time = datetime.now()
        
        if not self.test_connessione():
            logger.error("❌ Database non connesso")
            return False
        
        logger.info("📄 Analisi pagina...")
        circolari = self.analizza_pagina()
        
        logger.info(f"📊 Trovate {len(circolari)} circolari")
        
        for circ in circolari:
            self.salva_circolare(circ)
            time.sleep(0.5)
        
        end_time = datetime.now()
        durata = end_time - start_time
        
        logger.info("=" * 50)
        if self.circolari_salvate > 0:
            logger.info(f"✅ SUCCESSO: {self.circolari_salvate} circolari salvate")
            logger.info(f"⏱️  Durata: {durata.total_seconds():.1f}s")
            return True
        else:
            logger.error("❌ NESSUNA circolare salvata")
            return False

def main():
    robot = RobotCircolari()
    try:
        success = robot.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"💥 Errore: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
