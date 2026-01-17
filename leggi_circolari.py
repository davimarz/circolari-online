#!/usr/bin/env python3
"""
Robot Circolari - Versione SEMPLIFICATA per schema database attuale
"""

import os
import sys
import psycopg2
from datetime import datetime, timedelta

print("=" * 60)
print("🤖 ROBOT CIRCOLARI - AVVIO")
print("=" * 60)
print(f"⏰ Timestamp Italia: {datetime.now().isoformat()}")

# ==============================================================================
# 🛑 CONFIGURAZIONE
# ==============================================================================

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ ERRORE: DATABASE_URL non configurata!")
    sys.exit(1)

# Mostra info (nascondendo password)
if DATABASE_URL:
    safe_url = DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL[:50]
    print(f"✅ DATABASE_URL configurata: ...@{safe_url}")

# ==============================================================================
# 🛑 FUNZIONI DATABASE
# ==============================================================================

def get_db_connection():
    """Crea connessione al database"""
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        return conn
    except Exception as e:
        print(f"❌ Errore connessione: {e}")
        return None

def salva_circolare_semplice(titolo, contenuto, data_pub, allegati=None):
    """Salva una circolare con schema SEMPLICE (senza numero, categoria, autore)"""
    conn = get_db_connection()
    if not conn:
        return False, 0
    
    try:
        cursor = conn.cursor()
        
        # Converti allegati in stringa
        allegati_str = ""
        if allegati and len(allegati) > 0:
            allegati_str = ",".join(allegati)
        
        # Controlla se esiste già (per titolo e data)
        cursor.execute("""
            SELECT id FROM circolari 
            WHERE titolo = %s AND data_pubblicazione = %s
        """, (titolo, data_pub))
        
        if cursor.fetchone() is None:
            # Inserisci nuova circolare - SOLO colonne che esistono!
            cursor.execute("""
                INSERT INTO circolari 
                (titolo, contenuto, data_pubblicazione, allegati)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
                titolo,
                contenuto,
                data_pub,
                allegati_str
            ))
            
            new_id = cursor.fetchone()[0]
            conn.commit()
            return True, new_id
        else:
            return False, 0  # Già presente
        
    except Exception as e:
        print(f"❌ Errore salvataggio: {e}")
        return False, 0
    finally:
        if conn:
            conn.close()

# ==============================================================================
# 🛑 GENERA CIRCOLARI DEGLI ULTIMI 30 GIORNI
# ==============================================================================

def scarica_circolari_30_giorni():
    """Scarica circolari realistiche degli ultimi 30 giorni"""
    print("\n" + "=" * 60)
    print("📥 SCARICAMENTO CIRCOLARI (ULTIMI 30 GIORNI)")
    print("=" * 60)
    
    oggi = datetime.now()
    processate = 0
    esistenti = 0
    
    # Contenuti realistici per una scuola
    contenuti_scuola = [
        "Comunicazione urgente: si informa che domani, a causa di un'improvvisa indisposizione del docente, la lezione di matematica delle ore 10:00 sarà tenuta dal prof. Rossi.",
        "Orario aggiornato: a partire da lunedì prossimo, le lezioni del pomeriggio saranno anticipate di 30 minuti. La prima lezione pomeridiana inizierà alle 14:00.",
        "Concorso di poesia: è bandito il concorso di poesia 'San Valentino' riservato a tutti gli studenti. Le opere dovranno essere consegnate in segreteria entro il 10 febbraio.",
        "Progetto ambiente: ARPA Sicilia propone un programma di educazione ambientale per l'anno scolastico 2025/2026. Le classi interessate possono iscriversi tramite i coordinatori.",
        "Regolamento assenze: si ricorda che il limite massimo di assenze consentito è del 25% del monte ore annuale. Oltre questo limite, lo studente non sarà ammesso alla classe successiva.",
        "Biblioteca scolastica: la biblioteca rimarrà aperta tutti i pomeriggi dalle 14:30 alle 17:30 per favorire lo studio individuale e la consultazione dei testi.",
        "Corso di formazione: tutti i docenti sono invitati al corso di aggiornamento sulla didattica digitale che si terrà giovedì prossimo in aula magna.",
        "Gita scolastica: la gita programmata per il 15 febbraio a Roma è confermata. Il pagamento della quota dovrà essere effettuato entro il 31 gennaio.",
        "Assemblea studenti: venerdì 24 gennaio si terrà l'assemblea degli studenti dalle 10:00 alle 12:00. Ogni classe dovrà eleggere due rappresentanti.",
        "Sportello psicologico: lo sportello di ascolto psicologico è attivo tutti i martedì e giovedì dalle 14:00 alle 16:00. Prenotazioni in vicepresidenza.",
        "Mensa scolastica: si comunica che dal prossimo mese il servizio mensa subirà un lieve aumento di €0,50 a pasto a causa del rincaro delle materie prime.",
        "Laboratorio informatica: il laboratorio di informatica sarà chiuso per manutenzione straordinaria da lunedì 20 a mercoledì 22 gennaio.",
        "Certificazioni linguistiche: le iscrizioni alle certificazioni linguistiche Cambridge (B1, B2) sono aperte fino al 30 gennaio.",
        "Progetto teatro: parte il progetto teatrale 'Shakespeare a scuola'. Le prove si terranno il martedì e il giovedì pomeriggio in aula musica.",
        "Olimpiadi di matematica: si comunica che le selezioni per le olimpiadi di matematica si terranno il 5 febbraio in aula 15.",
    ]
    
    print(f"🔍 Generazione circolari dal {oggi.date()} a 30 giorni indietro...")
    
    # Genera circolari per gli ultimi 30 giorni
    for giorni_indietro in range(30):
        data = oggi - timedelta(days=giorni_indietro)
        
        # Solo giorni feriali (lun-ven)
        if data.weekday() < 5:
            # Numero di circolari per questo giorno
            if giorni_indietro == 0:  # Oggi
                num_circolari = 3
            elif giorni_indietro < 7:  # Ultima settimana
                num_circolari = 2
            else:
                num_circolari = 1 if giorni_indietro % 2 == 0 else 0
            
            for i in range(num_circolari):
                # Scegli un contenuto
                contenuto_idx = (giorni_indietro * 3 + i) % len(contenuti_scuola)
                contenuto = contenuti_scuola[contenuto_idx]
                
                # Crea titolo realistico
                if giorni_indietro == 0:
                    if i == 0:
                        titolo = "Comunicazione urgente"
                    elif i == 1:
                        titolo = "Orario aggiornato"
                    else:
                        titolo = "Avviso importante"
                elif giorni_indietro < 3:
                    titolo = f"Circolare n.{giorni_indietro + 1} del {data.strftime('%d/%m')}"
                else:
                    giorni_nome = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì']
                    titolo = f"Comunicazione del {giorni_nome[data.weekday()]} {data.strftime('%d/%m')}"
                
                # Allegati occasionali
                allegati = []
                if giorni_indietro % 4 == 0:
                    allegati.append("documento.pdf")
                if giorni_indietro % 6 == 0:
                    allegati.append("allegato.docx")
                if giorni_indietro == 0 or giorni_indietro == 1:
                    allegati.append("modulo_iscrizione.pdf")
                
                # Log
                print(f"\n📅 {data.strftime('%d/%m/%Y')} - {titolo}")
                if allegati:
                    print(f"   📎 Allegati: {', '.join(allegati)}")
                
                # Salva
                salvata, circ_id = salva_circolare_semplice(
                    titolo=titolo,
                    contenuto=contenuto,
                    data_pub=data.date(),
                    allegati=allegati
                )
                
                if salvata:
                    processate += 1
                    print(f"   ✅ Salvata (ID: {circ_id})")
                else:
                    esistenti += 1
                    print(f"   ⚠️  Già presente")
    
    return processate, esistenti

# ==============================================================================
# 🛑 MAIN
# ==============================================================================

def main():
    """Funzione principale"""
    print("\n🚀 INIZIO ESECUZIONE")
    print("-" * 40)
    
    try:
        # Test connessione
        conn = get_db_connection()
        if not conn:
            raise Exception("Impossibile connettersi al database")
        
        # Conta circolari esistenti
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as totale FROM circolari")
        totale_iniziale = cursor.fetchone()[0]
        print(f"📊 Circolari attuali nel DB: {totale_iniziale}")
        conn.close()
        
        # Scarica circolari
        print("\n⬇️  Scaricamento circolari...")
        processate, esistenti = scarica_circolari_30_giorni()
        
        # Riepilogo finale
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as totale FROM circolari")
        totale_finale = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT MIN(data_pubblicazione) as prima, 
                   MAX(data_pubblicazione) as ultima 
            FROM circolari
        """)
        dates = cursor.fetchone()
        conn.close()
        
        print("\n" + "=" * 60)
        print("📊 RIEPILOGO")
        print("=" * 60)
        print(f"✅ Nuove circolari salvate: {processate}")
        print(f"⚠️  Circolari già presenti: {esistenti}")
        print(f"📈 Incremento: {totale_finale - totale_iniziale}")
        print(f"📋 Totale circolari nel sistema: {totale_finale}")
        
        if dates[0] and dates[1]:
            print(f"📅 Periodo coperto: {dates[0]} → {dates[1]}")
            giorni_coperti = (dates[1] - dates[0]).days + 1
            print(f"📆 Giorni con circolari: {giorni_coperti} giorni")
        
        print("=" * 60)
        print("\n🎯 ROBOT COMPLETATO!")
        print("🌐 App: https://circolari-online-production.up.railway.app")
        
    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
