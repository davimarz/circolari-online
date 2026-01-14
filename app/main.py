import os
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Configurazione database PostgreSQL online (Neon.tech)
def get_db_connection():
    """Connessione al database PostgreSQL online su Neon.tech"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        # URL di fallback per sviluppo
        database_url = "postgresql://neondb_owner:password@ep-fancy-water-a5xyzxyz.neon.tech/neondb?sslmode=require"
    
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
    except Exception as e:
        app.logger.error(f"Errore connessione database: {e}")
        return None

@app.route('/')
def index():
    """Pagina principale con template HTML"""
    return render_template('index.html')

@app.route('/api/circolari')
def get_circolari():
    """API: Ottieni tutte le circolari"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database non disponibile'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Recupera circolari (ultime 100)
        cursor.execute("""
            SELECT id, titolo, contenuto, data_pubblicazione, pdf_url, 
                   created_at, 
                   EXTRACT(EPOCH FROM created_at) as timestamp
            FROM circolari 
            ORDER BY data_pubblicazione DESC 
            LIMIT 100
        """)
        
        circolari = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Converti date in formato ISO
        for circ in circolari:
            if circ['data_pubblicazione']:
                circ['data_pubblicazione'] = circ['data_pubblicazione'].isoformat()
            if circ['created_at']:
                circ['created_at'] = circ['created_at'].isoformat()
        
        return jsonify({
            'success': True,
            'data': circolari,
            'count': len(circolari),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistiche')
def get_statistiche():
    """API: Statistiche in tempo reale"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database non disponibile'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Totale circolari
        cursor.execute("SELECT COUNT(*) FROM circolari")
        totali = cursor.fetchone()[0]
        
        # Ultime 24 ore
        cursor.execute("""
            SELECT COUNT(*) FROM circolari 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        ultime_24h = cursor.fetchone()[0]
        
        # Ultimi 7 giorni
        cursor.execute("""
            SELECT COUNT(*) FROM circolari 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
        ultimi_7gg = cursor.fetchone()[0]
        
        # Con PDF
        cursor.execute("""
            SELECT COUNT(*) FROM circolari 
            WHERE pdf_url IS NOT NULL AND pdf_url != ''
        """)
        con_pdf = cursor.fetchone()[0]
        
        # Ultima circolare
        cursor.execute("""
            SELECT MAX(data_pubblicazione) as ultima 
            FROM circolari
        """)
        ultima_data = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'statistiche': {
                'totali': totali,
                'ultime_24h': ultime_24h,
                'ultimi_7gg': ultimi_7gg,
                'con_pdf': con_pdf,
                'ultima_circolare': ultima_data.isoformat() if ultima_data else None
            },
            'server_time': datetime.now().isoformat(),
            'status': 'online'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """API: Verifica stato sistema"""
    conn = get_db_connection()
    db_status = 'online' if conn else 'offline'
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            db_status = 'online'
        except:
            db_status = 'error'
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'timestamp': datetime.now().isoformat(),
        'service': 'Bacheca Circolari IC Anna Frank',
        'version': '2.0.0'
    })

@app.route('/api/robot/logs')
def get_robot_logs():
    """API: Log ultime esecuzioni robot"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database non disponibile'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, timestamp, status, nuove_circolari, errore
            FROM robot_logs 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        
        logs = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Converti timestamp
        for log in logs:
            if log['timestamp']:
                log['timestamp'] = log['timestamp'].isoformat()
        
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
