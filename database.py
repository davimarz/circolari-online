import os
import psycopg2

def salva_circolare_db(titolo, contenuto, data_pubblicazione, pdf_url=None):
    """Versione SEMPLICE che funziona"""
    try:
        DATABASE_URL = os.environ.get('DATABASE_URL')
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Query SEMPLICE - SENZA 'fonte'
        cur.execute("""
            INSERT INTO circolari (titolo, contenuto, data_pubblicazione, pdf_url)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (titolo, contenuto, data_pubblicazione, pdf_url))
        
        risultato = cur.fetchone()
        if risultato:
            conn.commit()
            return True
        else:
            conn.rollback()
            return False
            
    except Exception as e:
        print(f"Errore database: {e}")
        return False
