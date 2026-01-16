"""
database.py - Gestione database PostgreSQL per Streamlit App
Configurato per Railway con DATABASE_URL interno
"""

import os
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import json

# ==============================================================================
# 🛑 CONFIGURAZIONE DATABASE RAILWAY
# ==============================================================================

# URL DATABASE RAILWAY (INTERNO - GRATUITO)
DATABASE_URL = "postgresql://postgres:TpsVpUowNnMqSXpvAosQEezxpGPtbPNG@postgres.railway.internal:5432/railway"

# ==============================================================================
# 🛑 FUNZIONI DI CONNESSIONE
# ==============================================================================

def get_connection():
    """
    Crea una connessione al database PostgreSQL di Railway.
    Funziona SOLO dentro l'ambiente Railway.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        print(f"✅ Connesso al database Railway: postgres.railway.internal:5432")
        return conn
    except Exception as e:
        print(f"❌ Errore connessione database Railway: {e}")
        print("ℹ️  Nota: Questa connessione funziona solo dentro Railway")
        return None

def init_database():
    """
    Inizializza il database con le tabelle necessarie.
    Viene eseguito automaticamente all'avvio dell'app.
    """
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        print("📦 Inizializzazione tabelle database...")
        
        # Tabella circolari
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circolari (
                id SERIAL PRIMARY KEY,
                titolo VARCHAR(500) NOT NULL,
                contenuto TEXT,
                categoria VARCHAR(100),
                data_pubblicazione DATE NOT NULL,
                data_scaricamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                allegati JSONB DEFAULT '[]',
                fonte VARCHAR(50) DEFAULT 'railway_app',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(titolo, data_pubblicazione, categoria)
            )
        """)
        
        # Tabella logs del robot
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS robot_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                azione VARCHAR(100),
                circolari_processate INTEGER DEFAULT 0,
                circolari_scartate INTEGER DEFAULT 0,
                circolari_eliminate INTEGER DEFAULT 0,
                errore TEXT,
                dettagli JSONB DEFAULT '{}',
                durata_secondi REAL DEFAULT 0
            )
        """)
        
        # Tabella statistiche giornaliere
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistiche (
                id SERIAL PRIMARY KEY,
                data DATE NOT NULL UNIQUE,
                totale_circolari INTEGER DEFAULT 0,
                nuove_circolari INTEGER DEFAULT 0,
                categorie JSONB DEFAULT '{}',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabella utenti (per futuri sviluppi)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utenti (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255),
                ruolo VARCHAR(50) DEFAULT 'visitatore',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        
        # Inserisci utente admin di default
        cursor.execute("""
            INSERT INTO utenti (username, email, ruolo) 
            VALUES ('admin', 'admin@circolarionline.it', 'amministratore')
            ON CONFLICT (username) DO NOTHING
        """)
        
        # Crea indici per performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_circolari_data ON circolari(data_pubblicazione)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_circolari_categoria ON circolari(categoria)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_circolari_titolo ON circolari(titolo)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON robot_logs(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_statistiche_data ON statistiche(data)")
        
        conn.commit()
        
        print("✅ Database inizializzato con successo")
        print("   • Tabelle: circolari, robot_logs, statistiche, utenti")
        print("   • Indicizzazioni: ottimizzate per performance")
        print("   • Utente default: admin/admin@circolarionline.it")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore inizializzazione database: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# ==============================================================================
# 🛑 FUNZIONI PER CIRCOLARI
# ==============================================================================

def get_circolari_recenti(limit=50, categoria=None, giorni_indietro=30):
    """
    Ottiene le circolari più recenti con filtri opzionali.
    
    Args:
        limit: Numero massimo di circolari da restituire
        categoria: Filtra per categoria (opzionale)
        giorni_indietro: Considera solo ultimi N giorni
    
    Returns:
        DataFrame pandas con le circolari
    """
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        data_limite = (datetime.now() - timedelta(days=giorni_indietro)).strftime('%Y-%m-%d')
        
        if categoria and categoria != "Tutte":
            query = """
                SELECT 
                    id, titolo, contenuto, categoria, 
                    data_pubblicazione, data_scaricamento,
                    allegati, fonte,
                    TO_CHAR(data_pubblicazione, 'DD/MM/YYYY') as data_formattata,
                    TO_CHAR(data_scaricamento, 'DD/MM/YYYY HH24:MI') as scaricata_il
                FROM circolari 
                WHERE data_pubblicazione >= %s AND categoria = %s
                ORDER BY data_pubblicazione DESC, data_scaricamento DESC
                LIMIT %s
            """
            params = (data_limite, categoria, limit)
        else:
            query = """
                SELECT 
                    id, titolo, contenuto, categoria, 
                    data_pubblicazione, data_scaricamento,
                    allegati, fonte,
                    TO_CHAR(data_pubblicazione, 'DD/MM/YYYY') as data_formattata,
                    TO_CHAR(data_scaricamento, 'DD/MM/YYYY HH24:MI') as scaricata_il
                FROM circolari 
                WHERE data_pubblicazione >= %s
                ORDER BY data_pubblicazione DESC, data_scaricamento DESC
                LIMIT %s
            """
            params = (data_limite, limit)
        
        df = pd.read_sql_query(query, conn, params=params)
        
        # Converti allegati da JSON a lista Python
        if 'allegati' in df.columns:
            df['allegati'] = df['allegati'].apply(lambda x: json.loads(x) if x else [])
        
        print(f"📋 Query circolari: {len(df)} risultati")
        return df
        
    except Exception as e:
        print(f"❌ Errore query circolari: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def get_circolare_by_id(circolare_id):
    """
    Ottiene una circolare specifica per ID.
    """
    conn = get_connection()
    if not conn:
        return None
    
    try:
        query = """
            SELECT 
                id, titolo, contenuto, categoria, 
                data_pubblicazione, data_scaricamento,
                allegati, fonte,
                TO_CHAR(data_pubblicazione, 'DD/MM/YYYY') as data_formattata,
                TO_CHAR(data_scaricamento, 'DD/MM/YYYY HH24:MI') as scaricata_il
            FROM circolari 
            WHERE id = %s
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (circolare_id,))
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        
        if row:
            circolare = dict(zip(columns, row))
            # Converti allegati
            if 'allegati' in circolare and circolare['allegati']:
                circolare['allegati'] = json.loads(circolare['allegati'])
            return circolare
        return None
        
    except Exception as e:
        print(f"❌ Errore query circolare ID {circolare_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def salva_circolare(titolo, contenuto, categoria, data_pubblicazione, allegati=None, fonte="streamlit_app"):
    """
    Salva una nuova circolare nel database.
    """
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        allegati_json = json.dumps(allegati) if allegati else '[]'
        data_pub = data_pubblicazione.strftime('%Y-%m-%d') if isinstance(data_pubblicazione, datetime) else data_pubblicazione
        
        cursor.execute("""
            INSERT INTO circolari 
            (titolo, contenuto, categoria, data_pubblicazione, allegati, fonte)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (titolo, data_pubblicazione, categoria) 
            DO UPDATE SET 
                contenuto = EXCLUDED.contenuto,
                allegati = EXCLUDED.allegati,
                data_scaricamento = CURRENT_TIMESTAMP
            RETURNING id
        """, (titolo, contenuto, categoria, data_pub, allegati_json, fonte))
        
        circolare_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"✅ Circolare salvata: ID {circolare_id} - {titolo[:50]}")
        return circolare_id
        
    except Exception as e:
        print(f"❌ Errore salvataggio circolare: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def elimina_circolari_vecchie(giorni=30):
    """
    Elimina circolari più vecchie del numero di giorni specificato.
    """
    conn = get_connection()
    if not conn:
        return 0
    
    try:
        cursor = conn.cursor()
        data_limite = (datetime.now() - timedelta(days=giorni)).strftime('%Y-%m-%d')
        
        # Conta quante saranno eliminate
        cursor.execute("SELECT COUNT(*) FROM circolari WHERE data_pubblicazione < %s", (data_limite,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Crea backup in tabella archivio
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS circolari_archivio AS 
                SELECT * FROM circolari WHERE data_pubblicazione < %s
            """, (data_limite,))
            
            # Elimina le vecchie
            cursor.execute("DELETE FROM circolari WHERE data_pubblicazione < %s", (data_limite,))
            
            conn.commit()
            print(f"🗑️  Eliminate {count} circolari vecchie (prima del {data_limite})")
        else:
            print("✅ Nessuna circolare vecchia da eliminare")
        
        return count
        
    except Exception as e:
        print(f"⚠️ Errore eliminazione circolari vecchie: {e}")
        conn.rollback()
        return 0
    finally:
        if conn:
            conn.close()

# ==============================================================================
# 🛑 FUNZIONI PER STATISTICHE
# ==============================================================================

def get_statistiche():
    """
    Ottiene statistiche complete del database.
    """
    conn = get_connection()
    if not conn:
        return {}
    
    try:
        cursor = conn.cursor()
        
        # Statistiche generali
        cursor.execute("SELECT COUNT(*) FROM circolari")
        totale = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM circolari WHERE data_pubblicazione >= CURRENT_DATE - INTERVAL '7 days'")
        ultima_settimana = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM circolari WHERE DATE(created_at) = CURRENT_DATE")
        oggi = cursor.fetchone()[0]
        
        # Distribuzione categorie
        cursor.execute("""
            SELECT categoria, COUNT(*) as count 
            FROM circolari 
            GROUP BY categoria 
            ORDER BY count DESC
            LIMIT 10
        """)
        categorie = dict(cursor.fetchall())
        
        # Date estreme
        cursor.execute("SELECT MIN(data_pubblicazione), MAX(data_pubblicazione) FROM circolari")
        date_range = cursor.fetchone()
        
        # Statistiche robot
        cursor.execute("SELECT COUNT(*) FROM robot_logs")
        total_logs = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(timestamp) FROM robot_logs")
        ultimo_log = cursor.fetchone()[0]
        
        # Calcola tasso di successo
        cursor.execute("""
            SELECT 
                SUM(circolari_processate) as total_processate,
                SUM(circolari_scartate) as total_scartate
            FROM robot_logs 
            WHERE azione = 'esecuzione_completata'
        """)
        robot_stats = cursor.fetchone()
        
        success_rate = 0
        if robot_stats and robot_stats[0] and robot_stats[1]:
            total = robot_stats[0] + robot_stats[1]
            if total > 0:
                success_rate = round((robot_stats[0] / total) * 100, 2)
        
        return {
            "generali": {
                "totale_circolari": totale,
                "ultima_settimana": ultima_settimana,
                "aggiunte_oggi": oggi,
                "prima_circolare": date_range[0].strftime('%d/%m/%Y') if date_range[0] else "N/A",
                "ultima_circolare": date_range[1].strftime('%d/%m/%Y') if date_range[1] else "N/A",
                "giorni_coperti": (date_range[1] - date_range[0]).days if date_range[0] and date_range[1] else 0
            },
            "categorie": {
                "totali": len(categorie),
                "distribuzione": categorie,
                "top_categoria": max(categorie.items(), key=lambda x: x[1])[0] if categorie else "N/A"
            },
            "robot": {
                "total_logs": total_logs,
                "ultima_esecuzione": ultimo_log.strftime('%d/%m/%Y %H:%M') if ultimo_log else "N/A",
                "tasso_successo": f"{success_rate}%",
                "processate_totali": robot_stats[0] if robot_stats[0] else 0,
                "scartate_totali": robot_stats[1] if robot_stats[1] else 0
            },
            "database": {
                "tipo": "PostgreSQL",
                "host": "postgres.railway.internal",
                "porta": 5432,
                "nome": "railway",
                "ultimo_aggiornamento": datetime.now().strftime('%d/%m/%Y %H:%M')
            }
        }
        
    except Exception as e:
        print(f"❌ Errore statistiche: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def get_circolari_per_mese(limit_mesi=12):
    """
    Ottiene il numero di circolari per mese.
    """
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = """
            SELECT 
                TO_CHAR(data_pubblicazione, 'YYYY-MM') as mese,
                COUNT(*) as numero_circolari
            FROM circolari
            GROUP BY TO_CHAR(data_pubblicazione, 'YYYY-MM')
            ORDER BY mese DESC
            LIMIT %s
        """
        
        df = pd.read_sql_query(query, conn, params=(limit_mesi,))
        return df
        
    except Exception as e:
        print(f"❌ Errore query circolari per mese: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

# ==============================================================================
# 🛑 FUNZIONI PER LOGS ROBOT
# ==============================================================================

def get_logs_robot(limit=20, azione=None):
    """
    Ottiene i log delle esecuzioni del robot.
    """
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        if azione and azione != "Tutte":
            query = """
                SELECT 
                    id,
                    TO_CHAR(timestamp, 'DD/MM/YYYY HH24:MI:SS') as data_ora,
                    azione,
                    circolari_processate,
                    circolari_scartate,
                    circolari_eliminate,
                    errore,
                    durata_secondi,
                    dettagli
                FROM robot_logs 
                WHERE azione = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """
            params = (azione, limit)
        else:
            query = """
                SELECT 
                    id,
                    TO_CHAR(timestamp, 'DD/MM/YYYY HH24:MI:SS') as data_ora,
                    azione,
                    circolari_processate,
                    circolari_scartate,
                    circolari_eliminate,
                    errore,
                    durata_secondi,
                    dettagli
                FROM robot_logs 
                ORDER BY timestamp DESC
                LIMIT %s
            """
            params = (limit,)
        
        df = pd.read_sql_query(query, conn, params=params)
        return df
        
    except Exception as e:
        print(f"❌ Errore query logs robot: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def salva_log_robot(azione, processate=0, scartate=0, eliminate=0, errore=None, durata=0, dettagli=None):
    """
    Salva un log dell'esecuzione del robot.
    """
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        dettagli_json = json.dumps(dettagli) if dettagli else '{}'
        
        cursor.execute("""
            INSERT INTO robot_logs 
            (azione, circolari_processate, circolari_scartate, 
             circolari_eliminate, errore, durata_secondi, dettagli)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (azione, processate, scartate, eliminate, errore, durata, dettagli_json))
        
        conn.commit()
        print(f"📝 Log salvato: {azione}")
        return True
        
    except Exception as e:
        print(f"❌ Errore salvataggio log: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# ==============================================================================
# 🛑 FUNZIONI UTILITY
# ==============================================================================

def get_categorie():
    """
    Ottiene l'elenco delle categorie disponibili.
    """
    conn = get_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT categoria FROM circolari ORDER BY categoria")
        categorie = [row[0] for row in cursor.fetchall()]
        return ["Tutte"] + categorie if categorie else ["Tutte"]
        
    except Exception as e:
        print(f"❌ Errore query categorie: {e}")
        return ["Tutte"]
    finally:
        if conn:
            conn.close()

def cerca_circolari(testo, limit=20):
    """
    Cerca circolari per testo nel titolo o contenuto.
    """
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        query = """
            SELECT 
                id, titolo, contenuto, categoria, 
                data_pubblicazione, data_scaricamento,
                TO_CHAR(data_pubblicazione, 'DD/MM/YYYY') as data_formattata
            FROM circolari 
            WHERE 
                titolo ILIKE %s OR 
                contenuto ILIKE %s OR
                categoria ILIKE %s
            ORDER BY data_pubblicazione DESC
            LIMIT %s
        """
        
        search_term = f"%{testo}%"
        df = pd.read_sql_query(query, conn, params=(search_term, search_term, search_term, limit))
        return df
        
    except Exception as e:
        print(f"❌ Errore ricerca circolari: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def test_connection():
    """
    Testa la connessione al database.
    """
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            cursor.execute("SELECT current_database()")
            db_name = cursor.fetchone()[0]
            conn.close()
            
            return {
                "status": "connected",
                "postgres_version": version.split(',')[0],
                "database": db_name,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    else:
        return {"status": "disconnected", "message": "Impossibile connettersi"}

# ==============================================================================
# 🛑 INIZIALIZZAZIONE AUTOMATICA
# ==============================================================================

# Inizializza il database quando il modulo viene importato
print("🔧 database.py - Caricamento modulo...")
print(f"📊 Configurazione database Railway: postgres.railway.internal:5432")
print(f"👤 Credenziali: integrate nel DATABASE_URL")
init_database()
