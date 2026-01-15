# 🏫 Bacheca Circolari Automatica

Sistema completamente automatico per la pubblicazione delle circolari scolastiche.

## 🌐 Link all'applicazione
https://bacheca-circolari.onrender.com (o tuo link Railway/Render)

## 🏗️ Architettura
1. **🤖 Robot GitHub Actions**: Esegue ogni ora lo scraping ARGO
2. **🗄️ Database PostgreSQL**: Su Railway (gratuito, illimitato)
3. **🌐 WebApp Streamlit**: Visualizzazione pubblica

## 🔧 Configurazione

### 1. Database su Railway
1. Vai su https://railway.app
2. Crea nuovo progetto → "Provision PostgreSQL"
3. Copia la `DATABASE_URL`

### 2. Secrets su GitHub
Vai su GitHub → Repository → Settings → Secrets and variables → Actions
Aggiungi:
- `ARGO_USER`: `davide.marziano.sc26953`
- `ARGO_PASS`: `dvd2Frank.`
- `DATABASE_URL`: `postgresql://...` (da Railway)

### 3. Deploy WebApp
#### Opzione A: Railway (consigliato)
1. Su Railway: New Project → Deploy from GitHub
2. Seleziona il repository
3. Railway rileverà automaticamente l'app Streamlit

#### Opzione B: Render.com
1. Vai su https://render.com
2. New Web Service → Connect GitHub
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `streamlit run app.py --server.port=$PORT`

## ⚙️ Funzionamento Automatico
- **Robot**: Esegue ogni ora (8:00-23:00 italiane)
- **Database**: PostgreSQL su Railway, sempre attivo
- **WebApp**: Aggiornamento automatico ogni 5 minuti
- **PDF**: Download diretto degli allegati

## 📊 Manutenzione
Il sistema è completamente automatico. Per verificare:
1. **Robot**: GitHub → Actions → "Robot Circolari Orario"
2. **Database**: Railway Dashboard → PostgreSQL
3. **WebApp**: Railway/Render Dashboard → Logs

## 🔐 Credenziali
- ARGO: fornite sopra
- Database: gestito automaticamente da Railway
- WebApp: pubblica, nessun login richiesto

## 🚨 Risoluzione Problemi
1. **Robot non si avvia**: Controlla secrets su GitHub
2. **Nessuna circolare**: Verifica credenziali ARGO
3. **Database error**: Railway Dashboard → Database → Connection Info
4. **WebApp offline**: Railway/Render → Redeploy
