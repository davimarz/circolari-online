#!/usr/bin/env python3
"""
SCRIPT COMPLETO PER FIX DATABASE
1. Elimina righe corrotte
2. Aggiunge colonna 'fonte'
3. Ripara la struttura
"""
import os
import psycopg2
import sys

DATABASE_URL = os.environ.get('DATABASE_URL')

def fix_database_completo():
    print("=== FIX DATABASE COMPLETO ===")
    
    try:
        # Connessione con autocommit per DDL
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("1. Analizzo situazione attuale...")
        
        # Trova righe corrotte
        cur.execute("""
            SELECT id, titolo, data_pubblicazione, fonte
            FROM circolari 
            WHERE data_pubblicazione IS NULL 
               OR titolo IS NULL
               OR (id = 36 AND titolo = 'fonte')  -- riga specifica corrotta
        """)
        
        righe_corrotte = cur.fetchall()
        
        if righe_corrotte:
            print(f"   Trovate {len(righe_corrotte)} righe corrotte:")
            for riga in righe_corrotte:
                print(f"   - ID {riga[0]}: titolo='{riga[1]}', data='{riga[2]}'")
            
            # Elimina righe corrotte
            cur.execute("""
                DELETE FROM circolari 
                WHERE data_pubblicazione IS NULL 
                   OR titolo IS NULL
                   OR (id = 36 AND titolo = 'fonte')
            """)
            print(f"   ✅ Righe corrotte eliminate")
        else:
            print("   ✅ Nessuna riga corrotta trovata")
        
        print("\n2. Aggiungo colonna 'fonte'...")
        
        # Verifica se la colonna esiste già
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'circolari' 
                AND column_name = 'fonte'
            )
        """)
        
        if not cur.fetchone()[0]:
            # Aggiungi colonna
            cur.execute("""
                ALTER TABLE circolari 
                ADD COLUMN fonte TEXT DEFAULT 'sito_scuola'
            """)
            print("   ✅ Colonna 'fonte' aggiunta")
        else:
            print("   ✅ Colonna 'fonte' già presente")
        
        print("\n3. Aggiorno valori NULL nella colonna fonte...")
        cur.execute("""
            UPDATE circolari 
            SET fonte = 'sito_scuola' 
            WHERE fonte IS NULL
        """)
        print(f"   ✅ Righe aggiornate: {cur.rowcount}")
        
        print("\n4. Verifico vincoli NOT NULL...")
        try:
            cur.execute("ALTER TABLE circolari ALTER COLUMN data_pubblicazione SET NOT NULL")
            print("   ✅ Vincolo NOT NULL su data_pubblicazione")
        except Exception as e:
            print(f"   ℹ️ data_pubblicazione: {e}")
        
        try:
            cur.execute("ALTER TABLE circolari ALTER COLUMN titolo SET NOT NULL")
            print("   ✅ Vincolo NOT NULL su titolo")
        except Exception as e:
            print(f"   ℹ️ titolo: {e}")
        
        print("\n5. Struttura finale della tabella:")
        cur.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = 'circolari'
            ORDER BY ordinal_position
        """)
        
        colonne = cur.fetchall()
        for col in colonne:
            nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
            default = f"DEFAULT {col[3]}" if col[3] else ""
            print(f"   - {col[0]} ({col[1]}) {nullable} {default}")
        
        print("\n6. Statistiche:")
        cur.execute("SELECT COUNT(*) FROM circolari")
        totale = cur.fetchone()[0]
        print(f"   Totale circolari: {totale}")
        
        cur.close()
        conn.close()
        
        print("\n🎉 FIX DATABASE COMPLETATO CON SUCCESSO!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRORE DURANTE IL FIX: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Questo script eseguirà le seguenti operazioni:")
    print("1. Eliminerà righe corrotte (dati NULL)")
    print("2. Aggiungerà la colonna 'fonte'")
    print("3. Aggiornerà i valori NULL")
    print("4. Aggiungerà vincoli NOT NULL")
    print("\n⚠️  Assicurati di avere un backup del database!")
    
    risposta = input("\nProcedere? (s/n): ")
    
    if risposta.lower() == 's':
        success = fix_database_completo()
        sys.exit(0 if success else 1)
    else:
        print("Operazione annullata.")
        sys.exit(0)
