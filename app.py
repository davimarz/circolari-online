import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

# ============================================
# CONFIGURAZIONE PORTA RAILWAY
# ============================================
PORT = int(os.environ.get('PORT', 8501))

# ============================================
# CONFIGURAZIONE PAGINA STREAMLIT
# ============================================
st.set_page_config(
    page_title="Bacheca Circolari IC Anna Frank",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# CSS PERSONALIZZATO PER RAILWAY
# ============================================
st.markdown("""
    <style>
    /* Nascondi elementi default Streamlit */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Header principale */
    .main-header {
        text-align: center;
        padding: 2rem 1rem;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .main-title {
        font-size: 2.8rem;
        font-weight: 900;
        margin-bottom: 0.5rem;
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .school-info {
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #e2e8f0;
    }
    
    .author-info {
        font-size: 1rem;
        color: #cbd5e0;
        font-style: italic;
        margin-top: 1rem;
    }
    
    /* Badge di stato */
    .status-badge {
        display: inline-block;
        background: #48bb78;
        color: white;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 700;
        margin-left: 15px;
        animation: pulse 2s infinite;
    }
    
    .railway-badge {
        display: inline-block;
        background: linear-gradient(135deg, #0b0d0e 0%, #1a202c 100%);
        color: white;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 700;
        margin-left: 10px;
        border: 2px solid #4299e1;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
    
    /* Box informazioni sistema */
    .info-box {
        background: linear-gradient(135deg, #e6f7ff 0%, #ebf8ff 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 6px solid #1890ff;
        margin: 1.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* Card circolari */
    .circolare-card {
        background: white;
        padding: 1.8rem;
        border-radius: 12px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.08);
        margin: 1.2rem 0;
        border-left: 5px solid #4299e1;
        transition: all 0.3s ease;
        border: 1px solid #e2e8f0;
    }
    
    .circolare-card:hover {
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        transform: translateY(-4px);
        border-left: 5px solid #2b6cb0;
    }
    
    /* Pulsanti PDF */
    .pdf-button {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        text-decoration: none;
        display: inline-block;
        margin: 6px 8px 6px 0;
        font-size: 0.95rem;
        font-weight: 600;
        transition: all 0.3s;
        cursor: pointer;
        box-shadow: 0 2px 4px rgba(66, 153, 225, 0.3);
    }
    
    .pdf-button:hover {
        background: linear-gradient(135deg, #3182ce 0%, #2b6cb0 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(66, 153, 225, 0.4);
    }
    
    /* Statistiche */
    .stats-box {
        display: flex;
        justify-content: space-around;
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        border: 2px solid #e2e8f0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    
    .stat-item {
        text-align: center;
        padding: 0 1rem;
    }
    
    .stat-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #2d3748;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #718096;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Filtri */
    .filter-box {
        background: #f8fafc;
        padding: 1.2rem;
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #718096;
        font-size: 0.9rem;
        padding: 2.5rem 0;
        margin-top: 4rem;
        border-top: 2px solid #e2e8f0;
        background: #f7fafc;
        border-radius: 10px;
    }
    
    /* Messaggi di stato */
    .update-info {
        font-size: 0.85rem;
        color: #4a5568;
        background: #edf2f7;
        padding: 8px 16px;
        border-radius: 8px;
        display: inline-block;
        margin: 10px 0;
        border-left: 4px solid #48bb78;
    }
    
    /* Pulsante inizializzazione */
    .stButton button {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 700;
        font-size: 1rem;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(72, 187, 120, 0.3);
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-title { font-size: 2rem; }
        .school-info { font-size: 1.3rem; }
        .stats-box { flex-direction: column; gap: 1rem; }
    }
    </style>
""", unsafe_allow_html=True)

# ============================================
# FUNZIONI DATABASE RAILWAY
# ============================================
def get_db_connection():
    """Crea connessione al database PostgreSQL su Railway"""
    try:
        # Railway fornisce DATABASE_URL automaticamente
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            st.error("""
            ❌ **DATABASE_URL non configurata su Railway**
            
            **Per risolvere:**
            1. Vai su Railway Dashboard → Servizio WebApp
            2. Clicca su "Variables"
            3. Aggiungi variabile: DATABASE_URL
            4. Valore: copia dalla sezione Variables del database PostgreSQL
            """)
            return None
        
        # Debug info (solo in sviluppo)
        if os.environ.get('RAILWAY_ENVIRONMENT') != 'production':
            st.info(f"🔗 Connessione a: {database_url.split('@')[1].split(':')[0]}")
        
        # Connessione a PostgreSQL con SSL
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
        
    except Exception as e:
        st.error(f"❌ **Errore connessione database:** {str(e)}")
        st.info("""
        **Verifica:**
        1. Il database PostgreSQL è attivo su Railway
        2. La variabile DATABASE_URL è corretta
        3. Le credenziali sono valide
        """)
        return None

def init_database():
    """Inizializza il database con la tabella circolari"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Crea tabella se non esiste
        cur.execute("""
            CREATE TABLE IF NOT EXISTS circolari (
                id SERIAL PRIMARY KEY,
                titolo TEXT NOT NULL,
                contenuto TEXT,
                data_pubblicazione TIMESTAMP NOT NULL,
                pdf_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(titolo, data_pubblicazione)
            )
        """)
        
        # Crea indici per performance
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_circolari_data 
            ON circolari(data_pubblicazione DESC)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_circolari_titolo 
            ON circolari(titolo)
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        
        st.success("✅ **Database Railway inizializzato correttamente!**")
        st.balloons()
        return True
        
    except Exception as e:
        st.error(f"❌ **Errore inizializzazione database:** {str(e)}")
        return False

@st.cache_data(ttl=300, show_spinner="🔄 Caricamento circolari dal database...")
def fetch_circolari(giorni=30):
    """Recupera circolari dal database PostgreSQL su Railway"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame(), "Errore di connessione al database Railway"
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query per ultimi N giorni
        query = """
            SELECT id, titolo, contenuto, data_pubblicazione, pdf_url, created_at
            FROM circolari
            WHERE data_pubblicazione >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY data_pubblicazione DESC
        """
        
        cur.execute(query, (giorni,))
        data = cur.fetchall()
        
        cur.close()
        conn.close()
        
        if data:
            df = pd.DataFrame(data)
            return df, None
        else:
            return pd.DataFrame(), "Nessuna circolare trovata nel database"
            
    except Exception as e:
        return pd.DataFrame(), f"Errore database: {str(e)}"

# ============================================
# HEADER PRINCIPALE
# ============================================
st.markdown("""
<div class="main-header">
    <div class="main-title">🏫 Bacheca Circolari IC Anna Frank 
        <span class="status-badge">🟢 LIVE</span>
        <span class="railway-badge">🚄 RAILWAY</span>
    </div>
    <div class="school-info">Istituto Comprensivo Anna Frank - Agrigento</div>
    <div class="author-info">Sistema Automatico • Hosting su Railway • Realizzato da Prof. Davide Marziano</div>
</div>
""", unsafe_allow_html=True)

# ============================================
# INFORMAZIONI SISTEMA RAILWAY
# ============================================
st.markdown("""
<div class="info-box">
<strong>🚀 Sistema 100% Railway - Always Online</strong><br>
<small>
<strong>🚄 Piattaforma:</strong> Railway.app (WebApp + Database)<br>
<strong>🗄️ Database:</strong> PostgreSQL su Railway (1GB storage gratuito)<br>
<strong>🤖 Robot:</strong> GitHub Actions - Esegue ogni ora 8:00-23:00<br>
<strong>⚡ Velocità:</strong> Server in Europa - HTTPS automatico<br>
<strong>🔄 Aggiornamento:</strong> Auto-refresh ogni 5 minuti<br>
<strong>🔒 Sicurezza:</strong> SSL/TLS - Connessioni cifrate<br>
<br>
<small><em>🚄 Deploy automatico • Zero manutenzione • Always online</em></small>
</small>
</div>
""", unsafe_allow_html=True)

# ============================================
# INIZIALIZZAZIONE DATABASE
# ============================================
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔄 Inizializza/Verifica Database Railway", type="primary", use_container_width=True):
        with st.spinner("Connessione al database Railway in corso..."):
            if init_database():
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Verifica le variabili d'ambiente su Railway")

# ============================================
# FILTRI DI VISUALIZZAZIONE
# ============================================
st.markdown('<div class="filter-box">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    giorni_filtro = st.selectbox(
        "**📅 Mostra circolari degli ultimi:**",
        [("7 giorni", 7), ("14 giorni", 14), ("30 giorni", 30), ("60 giorni", 60), ("90 giorni", 90)],
        format_func=lambda x: x[0],
        index=2
    )
    giorni_filtro = giorni_filtro[1]  # Estrai il valore numerico
st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# CARICAMENTO E VISUALIZZAZIONE CIRCOLARI
# ============================================
df, error = fetch_circolari(giorni_filtro)

if error:
    st.warning(f"⚠️ **{error}**")
    
    st.info("""
    **Sistema pronto - In attesa dei dati**
    
    Il sistema è configurato correttamente su Railway. 
    **Prossimi passi:**
    1. Il robot GitHub Actions si eseguirà automaticamente ogni ora
    2. Le circolari compariranno qui dopo la prima esecuzione
    3. Controlla lo stato del robot su [GitHub Actions](https://github.com/davimarz/circolari-online/actions)
    
    **Stato attuale:**
    ✅ Database Railway: **Connesso**  
    ✅ WebApp: **Online**  
    ⏳ Robot: **In attesa prima esecuzione**
    """)
    
    # Mostra info di debug se in sviluppo
    if os.environ.get('RAILWAY_ENVIRONMENT') != 'production':
        with st.expander("🔧 Debug informazioni"):
            st.write(f"Porta: {PORT}")
            st.write(f"Database URL presente: {'✅' if os.environ.get('DATABASE_URL') else '❌'}")
            if os.environ.get('DATABASE_URL'):
                st.write(f"Host database: {os.environ.get('DATABASE_URL').split('@')[1].split(':')[0]}")
else:
    if not df.empty:
        # STATISTICHE
        st.markdown(f"""
        <div class="stats-box">
            <div class="stat-item">
                <div class="stat-value">{len(df)}</div>
                <div class="stat-label">Circolari</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{df['pdf_url'].notna().sum()}</div>
                <div class="stat-label">Con Allegati</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{df['data_pubblicazione'].min().strftime('%d/%m') if not df.empty else '-'}</div>
                <div class="stat-label">Dal</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # DATA ULTIMO AGGIORNAMENTO
        if 'data_pubblicazione' in df.columns and not df.empty:
            df['data_pubblicazione'] = pd.to_datetime(df['data_pubblicazione'], errors='coerce')
            latest = df['data_pubblicazione'].max()
            if pd.notna(latest):
                st.markdown(
                    f'<div class="update-info">📅 **Ultima circolare:** {latest.strftime("%d/%m/%Y alle %H:%M")} • 🗄️ **Database Railway** • 🔄 **Auto-refresh attivo**</div>',
                    unsafe_allow_html=True
                )
        
        # LISTA CIRCOLARI
        st.markdown("### 📋 Elenco Circolari")
        for _, row in df.iterrows():
            st.markdown('<div class="circolare-card">', unsafe_allow_html=True)
            
            # TITOLO
            titolo = row.get('titolo', 'N/A')
            st.markdown(f"#### 📄 {titolo}")
            
            # DATA
            if pd.notna(row.get('data_pubblicazione')):
                data_pub = row['data_pubblicazione']
                if isinstance(data_pub, str):
                    data_pub = pd.to_datetime(data_pub)
                data_str = data_pub.strftime("%d/%m/%Y")
                ora_str = data_pub.strftime("%H:%M")
                st.caption(f"📅 **Pubblicata:** {data_str} alle {ora_str} • 🚄 **Hosting Railway**")
            
            # CONTENUTO
            if 'contenuto' in row and pd.notna(row['contenuto']):
                contenuto = str(row['contenuto'])
                if len(contenuto) > 600:
                    contenuto = contenuto[:597] + "..."
                st.markdown(f"<div style='margin: 15px 0; line-height: 1.6;'>{contenuto}</div>", unsafe_allow_html=True)
            
            # DOCUMENTI PDF
            if 'pdf_url' in row and pd.notna(row['pdf_url']):
                urls = str(row['pdf_url']).split(';;;')
                valid_urls = [url.strip() for url in urls if url.strip()]
                
                if valid_urls:
                    st.markdown("**📎 Documenti allegati:**")
                    for i, url in enumerate(valid_urls):
                        nome_file = url.split('/')[-1] if '/' in url else f"Documento_{i+1}.pdf"
                        nome_file_display = nome_file[:40] + ("..." if len(nome_file) > 40 else "")
                        st.markdown(
                            f'<a href="{url}" target="_blank" class="pdf-button">📄 {nome_file_display}</a>',
                            unsafe_allow_html=True
                        )
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("""
        📭 **Nessuna circolare trovata nel periodo selezionato**
        
        **Il sistema è attivo e funzionante:**  
        ✅ Database Railway: **Connesso**  
        ✅ WebApp: **Online**  
        🤖 Robot: **Programmato ogni ora**
        
        Le circolari appariranno automaticamente dopo la prima esecuzione del robot.
        """)

# ============================================
# FOOTER CON INFORMAZIONI TECNICHE
# ============================================
st.markdown(f"""
<div class="footer">
<strong>🏫 Bacheca Circolari Automatica - IC Anna Frank Agrigento</strong><br>
<strong>🚄 Piattaforma:</strong> Railway.app • <strong>🗄️ Database:</strong> PostgreSQL • <strong>🌐 WebApp:</strong> Streamlit<br>
<small>
🤖 GitHub Actions → 🗄️ Railway PostgreSQL → 🌐 Railway WebApp<br>
⚡ Porta: {PORT} • 🔄 Auto-refresh: 5 min • 🔒 HTTPS: Automatico<br>
💯 Piano Gratuito • 🌍 Always Online • ⚙️ Zero Configurazione
</small>
</div>
""", unsafe_allow_html=True)

# ============================================
# SCRIPT AUTO-REFRESH PER BROWSER
# ============================================
st.markdown("""
<script>
// Auto-refresh ogni 5 minuti (300000 ms)
setTimeout(function() {
    window.location.reload();
}, 300000);

// Mostra timer di aggiornamento
function updateTimer() {
    const now = new Date();
    const nextUpdate = new Date(now.getTime() + 300000);
    const options = { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit',
        timeZone: 'Europe/Rome'
    };
    
    const nextUpdateTime = nextUpdate.toLocaleTimeString('it-IT', options);
    const element = document.getElementById('next-refresh');
    if (element) {
        element.textContent = `Prossimo aggiornamento: ${nextUpdateTime}`;
    }
}

// Aggiorna ogni secondo
setInterval(updateTimer, 1000);
updateTimer();

// Aggiungi elemento per il timer
const timerDiv = document.createElement('div');
timerDiv.id = 'next-refresh';
timerDiv.style.cssText = 'text-align: center; font-size: 0.8rem; color: #718096; margin-top: 10px;';
document.querySelector('.footer').appendChild(timerDiv);
</script>
""", unsafe_allow_html=True)
