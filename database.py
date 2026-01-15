def init_database():
    """
    Inizializza/verifica il database e crea le tabelle necessarie
    """
    logger.info("Inizializzazione database iniziata...")
    
    conn = get_database_connection()
    if conn is None:
        return "❌ Impossibile connettersi al database"
    
    try:
        cursor = conn.cursor()
        
        # 1. Verifica versione PostgreSQL
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"PostgreSQL versione: {version}")
        
        # 2. Crea tabella circolari CON TUTTE LE COLONNE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circolari (
                id SERIAL PRIMARY KEY,
                titolo TEXT NOT NULL,
                data_pubblicazione DATE DEFAULT CURRENT_DATE,
                file_url TEXT,  -- COLONNA AGGIUNTA
                contenuto TEXT,
                categoria TEXT DEFAULT 'Generale',
                priorita INTEGER DEFAULT 1,
                firmatario TEXT,
                fonte TEXT DEFAULT 'ARGO',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(titolo, data_pubblicazione)
            );
        """)
        logger.info("Tabella 'circolari' creata/verificata")
        
        # 3. AGGIUNGI COLONNA SE MANCA (per database esistenti)
        try:
            cursor.execute("ALTER TABLE circolari ADD COLUMN IF NOT EXISTS file_url TEXT;")
            logger.info("Colonna 'file_url' verificata/aggiunta")
        except Exception as e:
            logger.warning(f"Colonna file_url già presente: {e}")
        
        # 4. Crea tabella utenti
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utenti (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                nome TEXT,
                cognome TEXT,
                ruolo TEXT DEFAULT 'lettore' CHECK (ruolo IN ('amministratore', 'editore', 'lettore')),
                attivo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                reset_token TEXT,
                reset_expires TIMESTAMP
            );
        """)
        logger.info("Tabella 'utenti' creata/verificata")
        
        # 5. Crea tabella logs robot
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS robot_logs (
                id SERIAL PRIMARY KEY,
                tipo TEXT NOT NULL,
                messaggio TEXT,
                dettagli TEXT,  -- CAMBIATO DA JSONB A TEXT
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Tabella 'robot_logs' creata/verificata")
        
        # 6. Inserisci utente admin di default (password: admin123)
        cursor.execute("""
            INSERT INTO utenti (username, email, password_hash, nome, cognome, ruolo)
            VALUES ('admin', 'admin@annafrank.edu.it', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Admin', 'Sistema', 'amministratore')
            ON CONFLICT (username) DO NOTHING;
        """)
        
        # 7. Conta tabelle create
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        table_count = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Inizializzazione completata. Tabelle create: {table_count}")
        
        return f"✅ Database inizializzato! PostgreSQL: {version.split(',')[0]} | Tabelle: {table_count}"
            
    except Exception as e:
        logger.error(f"Errore inizializzazione database: {e}")
        return f"❌ Errore durante inizializzazione: {str(e)}"
