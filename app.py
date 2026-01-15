import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# ============================================
# CONFIGURAZIONE FORZATA PER RAILWAY
# ============================================
# Forza le variabili d'ambiente per Railway
os.environ['STREAMLIT_SERVER_PORT'] = '8080'
os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'

# Debug info
print(f"🚀 Streamlit avviato su Railway", file=sys.stderr)
print(f"🔧 PORT: {os.environ.get('PORT', '8080')}", file=sys.stderr)
print(f"🔧 DATABASE_URL presente: {'✅' if os.environ.get('DATABASE_URL') else '❌'}", file=sys.stderr)

# ============================================
# CONFIGURAZIONE PAGINA STREAMLIT
# ============================================
st.set_page_config(
    page_title="Bacheca Circolari IC Anna Frank - Railway",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://github.com/davimarz/circolari-online',
        'Report a bug': 'https://github.com/davimarz/circolari-online/issues',
        'About': "Bacheca Circolari Automatica su Railway"
    }
)

# ============================================
# CSS PERSONALIZZATO PER RAILWAY
# ============================================
st.markdown("""
    <style>
    /* Nascondi elementi default Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Header principale Railway */
    .railway-header {
        text-align: center;
        padding: 2.5rem 1rem;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #0b0d0e 0%, #1a202c 100%);
        border-radius: 12px;
        color: white;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        border: 1px solid #2d3748;
    }
    
    .railway-title {
        font-size: 3rem;
        font-weight: 900;
        margin-bottom: 0.5rem;
        color: white;
        text-shadow: 2px 2px 6px rgba(0,0,0,0.3);
        background: linear-gradient(90deg, #4299e1, #38b2ac);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .railway-subtitle {
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #e2e8f0;
    }
    
    .railway-badge {
        display: inline-block;
        background: linear-gradient(135deg, #0b0d0e 0%, #2d3748 100%);
        color: white;
        padding: 8px 20px;
        border-radius: 25px;
        font-size: 1rem;
        font-weight: 700;
        margin: 10px 5px;
        border: 2px solid #4299e1;
        box-shadow: 0 3px 10px rgba(66, 153, 225, 0.3);
    }
    
    .online-badge {
        display: inline-block;
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        padding: 8px 20px;
        border-radius: 25px;
        font-size: 1rem;
        font-weight: 700;
        margin: 10px 5px;
        animation: pulse 2s infinite;
        box-shadow: 0 3px 10px rgba(72, 187, 120, 0.3);
    }
    
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.9; transform: scale(1.02); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    /* Box informazioni Railway */
    .railway-info {
        background: linear-gradient(135deg, #ebf8ff 0%, #e6fffa 100%);
        padding: 1.8rem;
        border-radius: 12px;
        border-left: 6px solid #4299e1;
        margin: 1.5rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 1px solid #c6f6d5;
    }
    
    /* Card circolari */
    .circolare-card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 1.5rem 0;
        border-left: 6px solid #4299e1;
        transition: all 0.3s ease;
        border: 1px solid #e2e8f0;
        position: relative;
        overflow: hidden;
    }
    
    .circolare-card:hover {
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        transform: translateY(-5px);
        border-left: 6px solid #2b6cb0;
    }
    
    .circolare-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #4299e1, #38b2ac);
    }
    
    /* Pulsanti PDF */
    .pdf-button {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        margin: 8px 10px 8px 0;
        font-size: 1rem;
        font-weight: 600;
        transition: all 0.3s;
        cursor: pointer;
        box-shadow: 0 3px 8px rgba(66, 153, 225, 0.3);
    }
    
    .pdf-button:hover {
        background: linear-gradient(135deg, #3182ce 0%, #2b6cb0 100%);
        transform: translateY(-3px);
        box-shadow: 0 6px 15px rgba(66, 153, 225, 0.4);
    }
    
    .pdf-button::before {
        content: '📄';
        margin-right: 8px;
        font-size: 1.2rem;
    }
    
    /* Statistiche */
    .stats-box {
        display: flex;
        justify-content: space-around;
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        border: 2px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    
    .stat-item {
        text-align: center;
        padding: 0 1.5rem;
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 900;
        color: #2d3748;
        margin-bottom: 0.5rem;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }
    
    .stat-label {
        font-size: 1rem;
        color: #718096;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    /* Pulsante inizializzazione */
    .init-button {
        display: flex;
        justify-content: center;
        margin: 2rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 15px 30px;
        font-weight: 800;
        font-size: 1.1rem;
        transition: all 0.3s;
        box-shadow: 0 4px 12px rgba(72, 187, 120, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
        transform: translateY(-3px);
        box-shadow: 0 6px 18px rgba(72, 187, 120, 0.4);
    }
    
    /* Footer Railway */
    .railway-footer {
        text-align: center;
        color: #718096;
        font-size: 0.95rem;
        padding: 3rem 0;
        margin-top: 4rem;
        border-top: 2px solid #e2e8f0;
        background: #f7fafc;
        border-radius: 12px;
    }
    
    /* Filtri */
    .filter-container {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        margin-bottom: 2rem;
        box-shadow: 0 3px 10px rgba(0,0,0,0.05);
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .railway-title { font-size: 2.2rem; }
        .railway-subtitle { font-size: 1.4rem; }
        .stats-box { flex-direction: column; gap: 1.5rem; }
        .stat-value { font-size: 2rem; }
        .circolare-card { padding: 1.5rem; }
    }
    
    /* Messaggio di benvenuto */
    .welcome-message {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #e6fffa 0%, #ebf8ff 100%);
        border-radius: 12px;
        margin: 2rem 0;
        border: 2px solid #c6f6d5;
    }
    
    /* Loading spinner */
    .stSpinner > div {
        border-color: #4299e1 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================
# FUNZIONI DATABASE RAILWAY
# ============================================
def get_db_connection():
    """Crea connessione al database PostgreSQL su Railway"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            return None
        
        # Debug per development
        if os.environ.get('RAILWAY_ENVIRONMENT') != 'production':
            host = database_url.split('@')[1].split(':')[0] if '@' in database_url else 'unknown'
            print(f"🔗 Connessione database: {host}", file=sys.stderr)
        
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
        
    except Exception as e:
        print(f"❌ Errore connessione database: {e}", file=sys.stderr)
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
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Errore inizializzazione database: {e}", file=sys.stderr)
        return False

@st.cache_data(ttl=300, show_spinner=True)
def fetch_circolari(giorni=30):
    """Recupera circolari dal database PostgreSQL su Railway"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame(), "Errore di connessione al database Railway"
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
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
        print(f"❌ Errore query database: {e}", file=sys.stderr)
        return pd.DataFrame(), f"Errore database: {str(e)}"

# ============================================
# HEADER RAILWAY
# ============================================
st.markdown("""
<div class="railway-header">
    <div class="railway-title">🏫 Bacheca Circolari IC Anna Frank</div>
    <div class="railway-subtitle">Istituto Comprensivo Anna Frank - Agrigento</div>
    <div>
        <span class="online-badge">🟢 LIVE • RAILWAY • AUTO-UPDATE</span>
    </div>
    <div style="margin-top: 1rem; color: #cbd5e0; font-size: 1rem;">
        Sistema Automatico • Hosting su Railway • Realizzato da Prof. Davide Marziano
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# INFORMAZIONI SISTEMA RAILWAY
# ============================================
st.markdown("""
<div class="railway-info">
<strong style="font-size: 1.2rem;">🚀 Sistema 100% Railway - Completamente Automatico</strong><br>
<div style="margin-top: 0.8rem; line-height: 1.6;">
<strong>🚄 Piattaforma:</strong> Railway.app (WebApp + Database PostgreSQL)<br>
<strong>🤖 Robot:</strong> GitHub Actions - Esegue ogni ora 8:00-23:00<br>
<strong>🗄️ Database:</strong> PostgreSQL su Railway (1GB storage gratuito)<br>
<strong>⚡ Velocità:</strong> Server Europei - HTTPS automatico<br>
<strong>🔒 Sicurezza:</strong> SSL/TLS - Connessioni cifrate<br>
<strong>🔄 Aggiornamento:</strong> Auto-refresh ogni 5 minuti<br>
<br>
<small style="color: #4a5568;"><em>🚄 Deploy automatico • Zero manutenzione • Always online 24/7</em></small>
</div>
</div>
""", unsafe_allow_html=True)

# ============================================
# INIZIALIZZAZIONE DATABASE
# ============================================
st.markdown('<div class="init-button">', unsafe_allow_html=True)
if st.button("🔄 Inizializza/Verifica Database Railway", type="primary"):
    with st.spinner("Connessione al database Railway in corso..."):
        if init_database():
            st.success("✅ **Database Railway inizializzato correttamente!**")
            st.balloons()
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("❌ **Impossibile connettersi al database Railway**")
            st.info("""
            **Verifica:**
            1. La variabile DATABASE_URL è impostata su Railway
            2. Il database PostgreSQL è attivo
            3. Le credenziali sono corrette
            """)
st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# FILTRI DI VISUALIZZAZIONE
# ============================================
st.markdown('<div class="filter-container">', unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])
with col1:
    st.markdown("**🔍 Filtri di Visualizzazione**")
with col2:
    giorni_opzioni = [7, 14, 30, 60, 90]
    giorni_filtro = st.selectbox(
        "Mostra circolari degli ultimi:",
        giorni_opzioni,
        index=2,
        label_visibility="collapsed"
    )
st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# CARICAMENTO E VISUALIZZAZIONE CIRCOLARI
# ============================================
with st.spinner(f"🔄 Caricamento circolari degli ultimi {giorni_filtro} giorni..."):
    df, error = fetch_circolari(giorni_filtro)

if error:
    st.markdown("""
    <div class="welcome-message">
    <h3>📭 Benvenuto nel Sistema Circolari Railway!</h3>
    <p><strong>Il sistema è configurato correttamente e pronto all'uso.</strong></p>
    <p>Al momento non ci sono circolari nel database. Questo è normale perché:</p>
    <ul style="text-align: left; margin: 1rem auto; max-width: 600px;">
        <li>🤖 Il robot GitHub Actions si esegue automaticamente ogni ora</li>
        <li>⏰ La prima esecuzione avverrà al prossimo schedule (8:00-23:00)</li>
        <li>🗄️ Il database Railway PostgreSQL è attivo e pronto</li>
        <li>🌐 La WebApp è online 24/7 su Railway</li>
    </ul>
    <p><strong>Prossimi passi automatici:</strong></p>
    <ol style="text-align: left; margin: 1rem auto; max-width: 600px;">
        <li>Il robot scaricherà le circolari da ARGO</li>
        <li>Salverà i dati nel database Railway</li>
        <li>Le circolari appariranno automaticamente qui</li>
    </ol>
    <p style="color: #4a5568; margin-top: 1rem;">
    <em>🚄 Sistema Railway • ⚡ Always Online • 🔄 Aggiornamento Automatico</em>
    </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Debug info
    with st.expander("🔧 Informazioni tecniche sistema"):
        st.write(f"**Porta Streamlit:** 8080")
        st.write(f"**Variabile PORT impostata:** {'✅' if os.environ.get('PORT') else '❌'}")
        st.write(f"**Variabile DATABASE_URL impostata:** {'✅' if os.environ.get('DATABASE_URL') else '❌'}")
        if os.environ.get('DATABASE_URL'):
            db_url = os.environ.get('DATABASE_URL')
            host = db_url.split('@')[1].split(':')[0] if '@' in db_url else 'N/A'
            st.write(f"**Host database:** {host}")
        
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
                    f'<div style="text-align: center; margin: 1rem 0; padding: 10px; background: #e6fffa; border-radius: 8px; border-left: 4px solid #38b2ac;">'
                    f'📅 <strong>Ultima circolare:</strong> {latest.strftime("%d/%m/%Y alle %H:%M")} • '
                    f'🚄 <strong>Database Railway</strong> • 🔄 <strong>Auto-refresh attivo</strong>'
                    f'</div>',
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
                st.caption(f"📅 **Pubblicata:** {data_str} alle {ora_str} • 🚄 **Railway PostgreSQL**")
            
            # CONTENUTO
            if 'contenuto' in row and pd.notna(row['contenuto']):
                contenuto = str(row['contenuto'])
                if len(contenuto) > 600:
                    contenuto = contenuto[:597] + "..."
                st.markdown(f"<div style='margin: 15px 0; line-height: 1.7; color: #2d3748;'>{contenuto}</div>", unsafe_allow_html=True)
            
            # DOCUMENTI PDF
            if 'pdf_url' in row and pd.notna(row['pdf_url']):
                urls = str(row['pdf_url']).split(';;;')
                valid_urls = [url.strip() for url in urls if url.strip()]
                
                if valid_urls:
                    st.markdown("**📎 Documenti allegati:**")
                    col1, col2 = st.columns(2)
                    for i, url in enumerate(valid_urls):
                        nome_file = url.split('/')[-1] if '/' in url else f"Documento_{i+1}.pdf"
                        nome_file_display = nome_file[:35] + ("..." if len(nome_file) > 35 else "")
                        with col1 if i % 2 == 0 else col2:
                            st.markdown(
                                f'<a href="{url}" target="_blank" class="pdf-button">{nome_file_display}</a>',
                                unsafe_allow_html=True
                            )
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("""
        📭 **Nessuna circolare trovata nel periodo selezionato**
        
        **Stato sistema:**
        ✅ Database Railway: **Connesso**  
        ✅ WebApp: **Online su Railway**  
        ⏳ Robot: **Programmato ogni ora**
        
        Le circolari appariranno automaticamente dopo la prossima esecuzione del robot.
        """)

# ============================================
# FOOTER RAILWAY
# ============================================
st.markdown(f"""
<div class="railway-footer">
<strong style="font-size: 1.1rem;">🏫 Bacheca Circolari Automatica - IC Anna Frank Agrigento</strong><br>
<div style="margin: 0.8rem 0;">
<strong>🚄 Piattaforma:</strong> Railway.app • <strong>🗄️ Database:</strong> PostgreSQL • <strong>🌐 WebApp:</strong> Streamlit
</div>
<div style="font-size: 0.85rem; color: #718096; margin-top: 1rem;">
🤖 GitHub Actions → 🗄️ Railway PostgreSQL → 🌐 Railway WebApp<br>
⚡ Porta: 8080 • 🔄 Auto-refresh: 5 min • 🔒 HTTPS: Automatico • 🌍 Always Online
</div>
<div style="margin-top: 1.5rem; font-size: 0.8rem; color: #a0aec0;">
Sistema completamente automatico • Zero manutenzione • Realizzato da Prof. Davide Marziano
</div>
</div>
""", unsafe_allow_html=True)

# ============================================
# SCRIPT AUTO-REFRESH
# ============================================
st.markdown("""
<script>
// Auto-refresh ogni 5 minuti (300000 ms)
setTimeout(function() {
    window.location.reload();
}, 300000);

// Timer per prossimo aggiornamento
function updateRefreshTimer() {
    const now = new Date();
    const nextRefresh = new Date(now.getTime() + 300000);
    
    const options = { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit',
        timeZone: 'Europe/Rome'
    };
    
    const nextTime = nextRefresh.toLocaleTimeString('it-IT', options);
    
    // Cerca o crea l'elemento timer
    let timerElement = document.getElementById('refresh-timer');
    if (!timerElement) {
        timerElement = document.createElement('div');
        timerElement.id = 'refresh-timer';
        timerElement.style.cssText = 'text-align: center; font-size: 0.8rem; color: #718096; margin-top: 15px; padding: 8px; background: #edf2f7; border-radius: 6px;';
        document.querySelector('.railway-footer').appendChild(timerElement);
    }
    
    timerElement.innerHTML = `🔄 Prossimo aggiornamento automatico: <strong>${nextTime}</strong>`;
}

// Aggiorna timer ogni secondo
setInterval(updateRefreshTimer, 1000);
updateRefreshTimer();

// Mostra notifica quando la pagina si aggiorna
window.addEventListener('load', function() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('it-IT', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    });
    
    console.log(`🔄 Pagina aggiornata alle ${timeString}`);
});
</script>
""", unsafe_allow_html=True)

# ============================================
# DEBUG INFO PER RAILWAY
# ============================================
if os.environ.get('RAILWAY_ENVIRONMENT') != 'production':
    with st.sidebar:
        st.markdown("### 🐛 Debug Info")
        st.write(f"**PORT:** {os.environ.get('PORT', 'N/A')}")
        st.write(f"**RAILWAY_ENVIRONMENT:** {os.environ.get('RAILWAY_ENVIRONMENT', 'N/A')}")
        if os.environ.get('DATABASE_URL'):
            st.write(f"**DB Host:** {os.environ.get('DATABASE_URL').split('@')[1].split(':')[0]}")
