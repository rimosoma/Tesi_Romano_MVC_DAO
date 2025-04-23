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
        query = "SELECT id, nome, cognome, in_vacation FROM Dipendenti"
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        res = {}
        for row in rows:
            res[row["id"]] = (Dipendente(row["id"], row["nome"], row["cognome"], row["in_vacation"]))
        return res

    def get_turni_counts(self, emp_id: int):
        query = (
            "SELECT tipo, COUNT(*) as count "
            "FROM Turni WHERE employee_id = %s GROUP BY tipo"
        )
        self.cursor.execute(query, (emp_id,))
        return {row['tipo']: row['count'] for row in self.cursor.fetchall()}

    def get_constraints(self, emp_id: int, ctype: str):
        query = (
            "SELECT day "
            "FROM Constraint "
            "WHERE employee_id = %s AND type = %s"
        )
        self.cursor.execute(query, (emp_id, ctype))
        return [row['day'] for row in self.cursor.fetchall()]
