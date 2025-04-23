# populate_db.py

import random
import calendar
from datetime import date
from faker import Faker
import mysql.connector
from DB_connect import DBConnect   # importa la tua classe DBConnect

def populate_db(num_people: int = 10):
    fake = Faker()
    conn = DBConnect.get_connection()
    if conn is None:
        print("❌ Errore di connessione al database.")
        return

    cursor = conn.cursor()
    try:
        # (Opzionale) Ricrea le tabelle se non esistono
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Dipendenti (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(50),
            cognome VARCHAR(50),
            in_vacation BOOLEAN DEFAULT FALSE
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Turni (
            id INT AUTO_INCREMENT PRIMARY KEY,
            employee_id INT,
            date DATE,
            tipo VARCHAR(20),
            FOREIGN KEY (employee_id) REFERENCES Dipendenti(id)
        );
        """)

        # Calcola anno e mese correnti
        today = date.today()
        year, month = today.year, today.month
        _, days_in_month = calendar.monthrange(year, month)

        # Popola Dipendenti e Turni
        for _ in range(num_people):
            # Genera dati anagrafici
            nome = fake.first_name()
            cognome = fake.last_name()
            in_vac = random.choice([0, 1])

            # Inserisci il dipendente
            cursor.execute(
                "INSERT INTO Dipendenti (nome, cognome, in_vacation) VALUES (%s, %s, %s)",
                (nome, cognome, in_vac)
            )
            emp_id = cursor.lastrowid

            # Genera turni casuali (mattino/pomeriggio/notte)
            for tipo in ("mattino", "pomeriggio", "notte"):
                # numero casuale di turni per tipo
                num_shifts = random.randint(3, 8)
                # scegli giorni distinti
                days = random.sample(range(1, days_in_month + 1), num_shifts)
                for d in days:
                    shift_date = date(year, month, d)
                    cursor.execute(
                        "INSERT INTO Turni (employee_id, date, tipo) VALUES (%s, %s, %s)",
                        (emp_id, shift_date, tipo)
                    )

        conn.commit()
        print(f"✅ Ho inserito {num_people} dipendenti e i loro turni ({year}-{month:02d}) nel database.")
    except mysql.connector.Error as err:
        print(f"❌ Errore durante il popolamento: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Cambia qui il numero di dipendenti che vuoi generare
    populate_db(num_people=10)
