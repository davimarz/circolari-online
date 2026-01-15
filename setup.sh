#!/bin/bash
echo "🔧 Configurazione Streamlit per Railway..."

# Installa dipendenze di sistema se necessarie
apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Crea directory di configurazione Streamlit
mkdir -p ~/.streamlit

# Crea configurazione Streamlit per Railway
cat > ~/.streamlit/config.toml << EOF
[server]
headless = true
port = \$PORT
enableCORS = true
enableXsrfProtection = true
maxUploadSize = 200
enableWebsocketCompression = false

[browser]
serverAddress = "0.0.0.0"
serverPort = \$PORT
gatherUsageStats = false

[theme]
primaryColor = "#1a365d"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
EOF

# Crea credentials per disabilitare warning
cat > ~/.streamlit/credentials.toml << EOF
[general]
email = ""
EOF

echo "✅ Configurazione Streamlit completata!"
echo "📊 Porta configurata: \$PORT"
echo "🚀 Pronto per avviare l'applicazione..."
