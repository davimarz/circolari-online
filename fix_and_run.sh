#!/bin/bash
echo "=== 🛠️  FIX DATABASE E AVVIO ROBOT ==="

# Aggiorna database
echo "1. Aggiornamento database..."
python -c "
import sys
sys.path.append('.')
from database import init_database
result = init_database()
print(result)
"

# Esegui robot
echo "2. Esecuzione robot..."
python leggi_circolari.py

echo "=== ✅ COMPLETATO ==="
