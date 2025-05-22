import calendar
from calendar import monthrange
from datetime import datetime

import mysql
import mysql.connector
from database.DB_connect import DBConnect
from model.dipendente import Dipendente

class Dao:
    """
    Data Access Object: operazioni CRUD su dipendenti, turni e constraint.
    """
    def __init__(self):
        self.conn = DBConnect.get_connection()
        self.cursor = self.conn.cursor(dictionary=True)

    def get_employees(self):
        query = "SELECT id, nome, cognome, in_vacation, contratto FROM Dipendenti"
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        res = {}
        for row in rows:
            res[row["id"]] = (Dipendente(row["id"],"" ,row["in_vacation"],row["nome"], row["cognome"], row["contratto"],0,0,0 ))
        return res

    def controlla_mese_precedente(self, year: int, month: int) -> bool:
        # Controlla se esistono turni per il mese precedente al 'month' specificato nell'anno 'year'.
        # Se 'month' è 1 (gennaio), si riferisce a dicembre dell'anno precedente.
        prev_month = month - 1
        prev_year = year
        if prev_month == 0: # Se il mese corrente è gennaio, il precedente è dicembre dell'anno prima
            prev_month = 12
            prev_year -= 1

        query = """
            SELECT 1
            FROM TurniAssegnati
            WHERE YEAR(data_turno) = %s AND MONTH(data_turno) = %s
            LIMIT 1
        """
        self.cursor.execute(query, (prev_year, prev_month))
        return self.cursor.fetchone() is not None

    import datetime  # Aggiungi questo import in cima al file


    def get_last_week_turni(self, year: int, month: int) -> dict[int, list[str]]:
        # Calcola il mese precedente
        prev_month = month - 1
        prev_year = year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1

        # Trova l'ultimo giorno del mese precedente
        num_days_prev_month = calendar.monthrange(prev_year, prev_month)[1]

        # start_date: 7 giorni prima dell'ultimo giorno del mese precedente
        # end_date: L'ultimo giorno del mese precedente
        end_date = datetime.date(prev_year, prev_month, num_days_prev_month)
        start_date = end_date - datetime.timedelta(days=6) # 7 giorni totali inclusa end_date

        print(f"DEBUG DAO: Calcolo ultima settimana. start_date: {start_date}, end_date: {end_date}")

        query = """
            SELECT
                codice_dipendente,
                data_turno,
                tipo_turno
            FROM
                TurniAssegnati
            WHERE
                data_turno BETWEEN %s AND %s
            ORDER BY
                codice_dipendente, data_turno
        """

        self.cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
        rows = self.cursor.fetchall()

        # Inizializza un dizionario per i turni giornalieri dei dipendenti (es. {emp_id: {data_str: tipo_turno}})
        temp_daily_schedule = {emp_id: {} for emp_id in self.get_employee_ids()}


        for row in rows:
            emp_id = row['codice_dipendente']
            db_data_turno = row['data_turno'] # Valore grezzo dal DB

            # --- STAMPE DI DEBUG (mantienile per il momento) ---
            print(f"DEBUG DAO - Tipo: {type(db_data_turno)}, Valore: {db_data_turno}")
            # -------------------------------------------------

            date_to_use = None
            if isinstance(db_data_turno, datetime.datetime):
                date_to_use = db_data_turno.date()
            elif isinstance(db_data_turno, datetime.date):
                date_to_use = db_data_turno
            elif isinstance(db_data_turno, str):
                try:
                    date_to_use = datetime.datetime.strptime(db_data_turno, '%Y-%m-%d').date()
                except ValueError:
                    print(f"ERRORE DAO: Formato data stringa inatteso: {db_data_turno}")
                    raise TypeError(f"Formato stringa data inatteso dal DB per 'data_turno'. Valore: {db_data_turno}")
            elif isinstance(db_data_turno, int):
                # Questo è il caso che genera l'errore se il DB restituisce un int.
                # Qui devi decidere come gestirlo. Se l'int è un timestamp Unix:
                # date_to_use = datetime.datetime.fromtimestamp(db_data_turno).date()
                print(f"ERRORE DAO: 'data_turno' è un intero! Non gestito come data. Valore: {db_data_turno}")
                raise TypeError(f"Il campo 'data_turno' è un intero ({db_data_turno}), ma dovrebbe essere una data/stringa data.")
            else:
                raise TypeError(f"Tipo di 'data_turno' inatteso dal DB: {type(db_data_turno)}. Valore: {db_data_turno}")

            if date_to_use:
                temp_daily_schedule[emp_id][date_to_use.isoformat()] = row['tipo_turno']

        # Dopo aver popolato temp_daily_schedule, ricostruisci la lista per l'ultima settimana.
        days_in_prev_week_range = [(start_date + datetime.timedelta(days=i)).isoformat() for i in range(7)]

        final_employee_schedules = {}
        for emp_id in self.get_employee_ids():
            schedule_list = []
            for day_str in days_in_prev_week_range:
                # Assicurati che ogni dipendente abbia un 'riposo' o il turno effettivo per ogni giorno del range.
                schedule_list.append(temp_daily_schedule.get(emp_id, {}).get(day_str, 'riposo'))
            final_employee_schedules[emp_id] = schedule_list

        return final_employee_schedules



    def get_employee_ids(self) -> list[int]:
        """Metodo helper per ottenere tutti gli ID dei dipendenti."""
        query = "SELECT id FROM Dipendenti"
        self.cursor.execute(query)
        return [row["id"] for row in self.cursor.fetchall()]

    def save_turni_mese(self, year: int, month: int, schedule: list[dict]):
        """
        Sovrascrive (o inserisce) la tabella `TurniAssegnati` per il mese.
        `schedule` è una lista di dict, dove ogni dict è un'assegnazione:
        {'data_turno': 'YYYY-MM-DD', 'codice_dipendente': int, 'tipo_turno': str, 'ore_assegnate': float, 'note': str (opzionale)}.
        """
        # 1. Cancelliamo tutti i turni esistenti per quel mese e anno
        # Questo garantisce che stiamo sovrascrivendo e non aggiungendo duplicati
        self.cursor.execute(
            "DELETE FROM TurniAssegnati WHERE YEAR(data_turno)=%s AND MONTH(data_turno)=%s",
            (year, month)
        )

        # 2. Inseriamo i nuovi turni uno per uno (o in batch per efficienza)
        # Usiamo execute_many per inserimenti più efficienti se ci sono molti record
        if schedule: # Assicurati che ci sia qualcosa da inserire
            insert_query = """
                INSERT INTO TurniAssegnati (data_turno, codice_dipendente, tipo_turno, ore_assegnate, note)
                VALUES (%s, %s, %s, %s, %s)
            """
            # Prepara i dati nel formato richiesto da execute_many (lista di tuple)
            data_to_insert = []
            for record in schedule:
                data_to_insert.append((
                    record['data_turno'],
                    record['codice_dipendente'],
                    record['tipo_turno'],
                    record['ore_assegnate'],
                    record.get('note', None) # Usa .get per 'note' dato che è opzionale
                ))

            self.cursor.executemany(insert_query, data_to_insert)

        self.conn.commit() # Commit delle modifiche al database


