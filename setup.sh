#!/bin/bash
echo "🔧 Setup applicazione Bacheca Circolari..."

# Crea directory se non esiste
mkdir -p ~/.streamlit

# Configura Streamlit
cat > ~/.streamlit/config.toml << EOF
[server]
headless = true
port = \$PORT
enableCORS = false
enableXsrfProtection = false

[browser]
serverAddress = "0.0.0.0"
serverPort = \$PORT
EOF

echo "✅ Setup completato!"
