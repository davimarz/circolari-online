def init_database():
    """
    Inizializza/verifica il database e crea le tabelle
    """
    logger.info("Inizializzazione database...")
    
    conn = get_database_connection()
    if conn is None:
        return "❌ Impossibile connettersi al database"
    
    try:
        cursor = conn.cursor()
        
        # Verifica versione
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        # 1. Crea tabella circolari con TUTTE le colonne
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circolari (
                id SERIAL PRIMARY KEY,
                titolo TEXT NOT NULL,
                data_pubblicazione DATE DEFAULT CURRENT_DATE,
                file_url TEXT,
                contenuto TEXT,
                categoria TEXT DEFAULT 'Generale',
                priorita INTEGER DEFAULT 1,
                firmatario TEXT,  -- COLONNA MANCANTE
                fonte TEXT DEFAULT 'ARGO',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(titolo, data_pubblicazione)
            );
        """)
        logger.info("Tabella 'circolari' creata/verificata")
        
        # 2. AGGIUNGI COLONNE MANCANTI SE LA TABELLA ESISTE GIA'
        try:
            cursor.execute("ALTER TABLE circolari ADD COLUMN IF NOT EXISTS firmatario TEXT;")
            logger.info("Colonna 'firmatario' aggiunta/verificata")
        except Exception as e:
            logger.warning(f"Colonna firmatario: {e}")
            
        try:
            cursor.execute("ALTER TABLE circolari ADD COLUMN IF NOT EXISTS fonte TEXT DEFAULT 'ARGO';")
            logger.info("Colonna 'fonte' aggiunta/verificata")
        except Exception as e:
            logger.warning(f"Colonna fonte: {e}")
        
        # 3. Tabella utenti
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utenti (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                nome TEXT,
                cognome TEXT,
                ruolo TEXT DEFAULT 'lettore',
                attivo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );
        """)
        
        # 4. Tabella logs robot
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS robot_logs (
                id SERIAL PRIMARY KEY,
                tipo TEXT NOT NULL,
                messaggio TEXT,
                dettagli TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 5. Inserisci admin
        cursor.execute("""
            INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo)
            VALUES ('admin', 'admin@annafrank.edu.it', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Admin', 'Sistema', 'amministratore')
            ON CONFLICT (username) DO NOTHING;
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return f"✅ Database OK! PostgreSQL: {version.split(',')[0]}"
            
    except Exception as e:
        logger.error(f"Errore inizializzazione: {e}")
        return f"❌ Errore inizializzazione: {str(e)}"
