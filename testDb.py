import mysql.connector

try:
    cnx = mysql.connector.connect(
        host="localhost",     # Cambia se il server è su un'altra macchina
        user="root",          # Cambia con il tuo username
        password="rivoli2003", # Metti la password corretta
        database="go_sales"  # Cambia con il nome del database da testare
    )
    print("✅ Connessione riuscita!")
    cnx.close()

except mysql.connector.Error as err:
    print(f"❌ Errore di connessione: {err}")
