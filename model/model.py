from database.DAO import Dao
from database import DB_connect

class Model:
    """
    Logica di business per la generazione e gestione dei turni.
    """
    def __init__(self):
        # Configurazione DB, da parametrizzare esternamente
        self.dao = Dao()
        self.turni = []  # lista di turni generati
        self.dictDipendenti = self.dao.get_employees()

    def get_employees(self):
        return self.dictDipendenti

    def updateNrNotti(self,emp_id,nr):
        self.dictDipendenti[emp_id].setNotti(nr)
        return True

    def updateNrMattini(self,emp_id,nr):
        self.dictDipendenti[emp_id].setMattini(nr)
        return True

    def updateNrPomeriggi(self, emp_id,nr):
        self.dictDipendenti[emp_id].setPomeriggi(nr)
        return True






    def get_turni_counts(self, emp_id):
        return self.dao.get_turni_counts(emp_id)

    def get_constraints(self, emp_id, ctype):
        return self.dao.get_constraints(emp_id, ctype)

    def generate_turni(self):
        # Esempio semplice di algoritmo: distribuisce equamente i turni
        employees = self.get_employees()
        days = 30  # numero di giorni del mese
        self.turni.clear()
        for day in range(1, days + 1):
            for emp in employees:
                # logica di assegnazione qui
                # rispetto dei vincoli: skip se day in constraints
                if day in self.get_constraints(emp['id'], 'no_notte'):
                    continue
                self.turni.append({
                    'employee_id': emp['id'],
                    'date': f"2025-05-{day:02d}",
                    'tipo': 'notte'
                })
        return self.turni

    def export_to_xml(self, path: str = "turni.xml"):
        import xml.etree.ElementTree as ET
        root = ET.Element('Turni')
        for t in self.turni:
            turno_el = ET.SubElement(root, 'Turno')
            ET.SubElement(turno_el, 'EmployeeID').text = str(t['employee_id'])
            ET.SubElement(turno_el, 'Date').text = t['date']
            ET.SubElement(turno_el, 'Tipo').text = t['tipo']
        tree = ET.ElementTree(root)
        tree.write(path, encoding='utf-8', xml_declaration=True)
        return path