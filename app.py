import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# ============================================
# CONFIGURAZIONE PAGINA
# ============================================
st.set_page_config(
    page_title="Bacheca Circolari IC Anna Frank",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# CSS PERSONALIZZATO
# ============================================
st.markdown("""
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    
    .main-header {
        text-align: center;
        padding-bottom: 1.5rem;
        margin-bottom: 1.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1a365d;
        margin-bottom: 0.5rem;
    }
    
    .school-info {
        font-size: 1.5rem;
        color: #2c5282;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .author-info {
        font-size: 1rem;
        color: #718096;
        font-style: italic;
    }
    
    .update-info {
        font-size: 0.8rem;
        color: #a0aec0;
        text-align: right;
        margin-bottom: 1rem;
    }
    
    .pdf-button {
        background-color: #4299e1;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        text-decoration: none;
        display: inline-block;
        margin: 4px 4px 4px 0;
        font-size: 0.9rem;
        transition: all 0.3s;
        cursor: pointer;
    }
    
    .pdf-button:hover {
        background-color: #3182ce;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .info-box {
        background-color: #e6f7ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1890ff;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    
    .circolare-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin: 1rem 0;
        border-left: 4px solid #4299e1;
        transition: all 0.3s;
    }
    
    .circolare-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        transform: translateY(-2px);
    }
    
    .stats-box {
        display: flex;
        justify-content: space-around;
        background: #f7fafc;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #e2e8f0;
    }
    
    .stat-item {
        text-align: center;
    }
    
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2d3748;
    }
    
    .stat-label {
        font-size: 0.8rem;
        color: #718096;
    }
    
    .status-badge {
        display: inline-block;
        background: #c6f6d5;
        color: #22543d;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 10px;
    }
    
    .live-badge {
        display: inline-block;
        background: #fed7d7;
        color: #742a2a;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .last-update {
        font-size: 0.8rem;
        color: #4a5568;
        background: #edf2f7;
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
        margin-left: 10px;
    }
    
    .filter-box {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    
    .footer {
        text-align: center;
        color: #718096;
        font-size: 0.8rem;
        padding: 2rem 0;
        margin-top: 3rem;
        border-top: 1px solid #e2e8f0;
    }
    
    .railway-badge {
        display: inline-block;
        background: #0b0d0e;
        color: white;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================
# FUNZIONI DATABASE POSTGRESQL
# ============================================
def get_db_connection():
    """Crea connessione al database PostgreSQL su Railway"""
    try:
        # Railway fornisce DATABASE_URL automaticamente
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            st.error("❌ DATABASE_URL non configurato su Railway")
            st.info("Vai su Railway Dashboard → Variables → Aggiungi DATABASE_URL")
            return None
        
        # Connessione a PostgreSQL
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
        
    except Exception as e:
        st.error(f"❌ Errore connessione database: {str(e)}")
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
        
        # Crea indice per performance
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_circolari_data 
            ON circolari(data_pubblicazione DESC)
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        
        st.success("✅ Database inizializzato correttamente su Railway!")
        return True
        
    except Exception as e:
        st.error(f"❌ Errore inizializzazione database: {str(e)}")
        return False

@st.cache_data(ttl=300, show_spinner="Caricamento circolari...")
def fetch_circolari(giorni=30):
    """Recupera circolari dal database PostgreSQL su Railway"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame(), "Errore di connessione al database"
    
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
            return pd.DataFrame(), "Nessuna circolare trovata"
            
    except Exception as e:
        return pd.DataFrame(), f"Errore database: {str(e)}"

# ============================================
# HEADER
# ============================================
st.markdown("""
<div class="main-header">
    <div class="main-title">🏫 Bacheca Circolari IC Anna Frank <span class="status-badge">🟢 LIVE</span><span class="railway-badge">🚄 RAILWAY</span></div>
    <div class="school-info">Istituto Comprensivo Anna Frank - Agrigento</div>
    <div class="author-info">Sistema Automatico • Hosting su Railway • Realizzato da Prof. Davide Marziano</div>
</div>
""", unsafe_allow_html=True)

# ============================================
# INFORMAZIONI SISTEMA
# ============================================
st.markdown("""
<div class="info-box">
<strong>🚀 Sistema 100% Railway - Completamente Automatico</strong><br>
<small>
<strong>🚄 Hosting:</strong> Railway.app (WebApp + Database PostgreSQL)<br>
<strong>🤖 Robot:</strong> GitHub Actions - Esegue ogni ora<br>
<strong>⏰ Frequenza:</strong> 8:00-23:00 ora italiana<br>
<strong>🗄️ Database:</strong> PostgreSQL su Railway (1GB gratuito)<br>
<strong>⚡ Velocità:</strong> Server in Europa - HTTPS automatico<br>
<strong>🔄 Aggiornamento:</strong> Automatico ogni 5 minuti<br>
<br>
<small><em>🚄 Tutto su Railway • Zero configurazione • Always online</em></small>
</small>
</div>
""", unsafe_allow_html=True)

# ============================================
# INIZIALIZZAZIONE DATABASE
# ============================================
if st.button("🔄 Inizializza/Verifica Database Railway", type="secondary"):
    with st.spinner("Connessione a Railway PostgreSQL..."):
        if init_database():
            st.balloons()
        else:
            st.error("Verifica le variabili d'ambiente su Railway Dashboard")

# ============================================
# FILTRI
# ============================================
st.markdown('<div class="filter-box">', unsafe_allow_html=True)
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("<strong>🔍 Filtri di Visualizzazione</strong>", unsafe_allow_html=True)

with col2:
    giorni_filtro = st.selectbox(
        "Mostra ultimi:",
        [7, 14, 30, 60, 90],
        index=2,
        label_visibility="collapsed"
    )

st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# CARICAMENTO E VISUALIZZAZIONE CIRCOLARI
# ============================================
df, error = fetch_circolari(giorni_filtro)

if error:
    st.warning(f"⚠️ {error}")
    st.info("""
    **Prossimi passi:**
    1. Attendi la prima esecuzione del robot (ogni ora)
    2. Verifica i logs su GitHub Actions
    3. Controlla le variabili d'ambiente su Railway
    """)
else:
    if not df.empty:
        # STATISTICHE
        st.markdown("""
        <div class="stats-box">
            <div class="stat-item">
                <div class="stat-value">{}</div>
                <div class="stat-label">Circolari</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{}</div>
                <div class="stat-label">Con PDF</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">Railway</div>
                <div class="stat-label">Database</div>
            </div>
        </div>
        """.format(
            len(df),
            df['pdf_url'].notna().sum()
        ), unsafe_allow_html=True)
        
        # DATA ULTIMO AGGIORNAMENTO
        if 'data_pubblicazione' in df.columns and not df.empty:
            df['data_pubblicazione'] = pd.to_datetime(df['data_pubblicazione'], errors='coerce')
            latest = df['data_pubblicazione'].max()
            if pd.notna(latest):
                st.markdown(
                    f'<div class="update-info">📅 Ultima circolare: {latest.strftime("%d/%m/%Y alle %H:%M")} • 🚄 Database Railway</div>',
                    unsafe_allow_html=True
                )
        
        # LISTA CIRCOLARI
        for _, row in df.iterrows():
            st.markdown('<div class="circolare-card">', unsafe_allow_html=True)
            
            # TITOLO
            titolo = row.get('titolo', 'N/A')
            st.markdown(f"### {titolo}")
            
            # DATA
            if pd.notna(row.get('data_pubblicazione')):
                data_pub = row['data_pubblicazione']
                if isinstance(data_pub, str):
                    data_pub = pd.to_datetime(data_pub)
                data_str = data_pub.strftime("%d/%m/%Y")
                ora_str = data_pub.strftime("%H:%M")
                st.caption(f"📅 Pubblicata il {data_str} alle {ora_str} • 🗄️ Railway PostgreSQL")
            
            # CONTENUTO
            if 'contenuto' in row and pd.notna(row['contenuto']):
                contenuto = str(row['contenuto'])
                if len(contenuto) > 500:
                    contenuto = contenuto[:497] + "..."
                st.markdown(contenuto)
            
            # DOCUMENTI PDF
            if 'pdf_url' in row and pd.notna(row['pdf_url']):
                urls = str(row['pdf_url']).split(';;;')
                valid_urls = [url.strip() for url in urls if url.strip()]
                
                if valid_urls:
                    st.markdown("**📎 Documenti allegati:**")
                    for i, url in enumerate(valid_urls):
                        nome_file = url.split('/')[-1] if '/' in url else f"Documento_{i+1}.pdf"
                        st.markdown(
                            f'<a href="{url}" target="_blank" class="pdf-button">📄 {nome_file[:30]}</a>',
                            unsafe_allow_html=True
                        )
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("📭 **Nessuna circolare trovata nel periodo selezionato.**")
        st.markdown("""
        <div class="info-box">
        <strong>🚄 Sistema Railway - Pronto per l'uso</strong><br>
        • Il database PostgreSQL è attivo su Railway<br>
        • Il robot GitHub Actions si esegue automaticamente ogni ora<br>
        • Le circolari appariranno qui dopo la prima esecuzione<br>
        • Controlla lo stato su Railway Dashboard
        </div>
        """, unsafe_allow_html=True)

# ============================================
# FOOTER
# ============================================
st.markdown("""
<div class="footer">
<strong>🏫 Bacheca Circolari Automatica - IC Anna Frank Agrigento</strong><br>
Hosting su Railway.app • Database PostgreSQL • WebApp Streamlit<br>
<small>
🚄 Tutto su Railway • 🤖 Robot GitHub Actions • ⚡ Aggiornamenti automatici<br>
💯 Gratuito • 🌍 Always online • 🔒 HTTPS automatico
</small>
</div>
""", unsafe_allow_html=True)

# ============================================
# SCRIPT AUTO-REFRESH
# ============================================
st.markdown("""
<script>
// Auto-refresh ogni 5 minuti
setTimeout(function() {
    window.location.reload();
}, 300000);
</script>
""", unsafe_allow_html=True)
