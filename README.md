# 🏫 Bacheca Circolari Automatica - Railway Edition

Sistema completamente automatico per la pubblicazione delle circolari scolastiche su **Railway.app**.

## 🌐 Link all'applicazione
https://tuo-progetto.railway.app (dopo il deploy su Railway)

## 🚄 Architettura su Railway
1. **🤖 Robot GitHub Actions**: Esegue ogni ora lo scraping ARGO
2. **🗄️ Database PostgreSQL**: Su Railway (1GB gratuito)
3. **🌐 WebApp Streamlit**: Hosting su Railway (always online)

## 🚀 Deploy in 5 Minuti

### Passo 1: Preparare il Repository GitHub
1. Crea un nuovo repository su GitHub
2. Carica tutti i file nella struttura:
