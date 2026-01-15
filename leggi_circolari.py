def save_circolare(titolo, contenuto, data_pub, file_url=None, firmatario=''):
    """
    Salva una circolare nel database
    """
    conn = get_railway_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Controlla se esiste già
        cursor.execute("SELECT id FROM circolari WHERE titolo = %s AND data_pubblicazione = %s", (titolo, data_pub))
        if cursor.fetchone():
            logger.info(f"Circolare già presente: {titolo}")
            cursor.close()
            conn.close()
            return True
        
        # VERSIONE SICURA: controlla quali colonne esistono
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'circolari' 
            AND column_name IN ('firmatario', 'file_url');
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        # Costruisci query dinamica in base alle colonne disponibili
        if 'firmatario' in columns and 'file_url' in columns:
            cursor.execute("""
                INSERT INTO circolari (titolo, contenuto, data_pubblicazione, file_url, firmatario, fonte)
                VALUES (%s, %s, %s, %s, %s, 'ARGO')
            """, (titolo, contenuto, data_pub, file_url, firmatario))
        elif 'firmatario' in columns:
            cursor.execute("""
                INSERT INTO circolari (titolo, contenuto, data_pubblicazione, firmatario, fonte)
                VALUES (%s, %s, %s, %s, 'ARGO')
            """, (titolo, contenuto, data_pub, firmatario))
        else:
            cursor.execute("""
                INSERT INTO circolari (titolo, contenuto, data_pubblicazione, fonte)
                VALUES (%s, %s, %s, 'ARGO')
            """, (titolo, contenuto, data_pub))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Circolare salvata: {titolo}")
        return True
    except Exception as e:
        logger.error(f"❌ Errore salvataggio: {e}")
        return False
