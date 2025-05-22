import flet

from UI.dialog_necessita import Necessita
from model.model import SchedulingModel
from UI import view
class Controller:
    """
    Gestisce l'interazione tra view e model.
    """
    def __init__(self, view, model):
        self.model = SchedulingModel()
        self.view = view
          # Dizionario che tiene traccia delle istanze Necessita per ogni dipendente
        self._necessita_views = {}
        self.mese = None

    def passaMese(self, mese):
        self.mese = mese
        return self.model.controllo_mese(mese)

    def get_employees(self):
        dict = self.model.get_employeesM()

        #for employee in dict:
            #print(dict[employee].id, dict[employee].nome, dict[employee].cognome, dict[employee].notti, dict[employee].mattini, dict[employee].pomeriggi)
        return self.model.get_employeesM()

    def get_employee(self, emp_id):
        return self.model.get_employeeM(emp_id)

    def get_turni_counts(self, emp_id):
        return self.model.get_turni_counts(emp_id)


    def update_daIncludere(self, emp_id, tipo):
        self.model.updateDaIncludere(emp_id,tipo)
        self.aggiornaTabView()

    def updateNrNotti(self, emp_id,e):
        if self.model.updateNrNotti(emp_id,e.control.value):
            self.aggiornaTabView()


    def updateNrMattini(self, emp_id,e):
        if self.model.updateNrMattini(emp_id,e.control.value):
            self.aggiornaTabView()


    def updateNrPomeriggi(self, emp_id,e):
        if self.model.updateNrPomeriggi(emp_id,e.control.value):
            self.aggiornaTabView()

    def aggiornaTabView(self):
        self.view.update_table_view()




    def generate_turni(self):
        return self.model.genera_turni_mese()

    def export_to_xml(self, path: str = "turni.xml"):
        return self.model.export_to_xml(path)












    def apri_necessita(self, page, emp_id):
        # crea o riusa la view Necessita
        if emp_id not in self._necessita_views:
            nv = Necessita(page, emp_id, self.mese).set_controller(self)
            self._necessita_views[emp_id] = nv
        else:
            nv = self._necessita_views[emp_id]

        # (Re)popola i dati salvati
        nv.load_interface()

        # mette in overlay se non già presente
        if nv not in page.overlay:
            page.overlay.append(nv)
            page.update()

    def chiudi_necessita(self, page, emp_id):
        # rimuove la view dal dizionario e dall'overlay
        if emp_id in self._necessita_views:
            nv = self._necessita_views.pop(emp_id)
            if nv in page.overlay:
                page.overlay.remove(nv)
                page.update()

        # Per aggiungere un metodo per leggere i dati inseriti nei calendari
        def salva_necessita(self, emp_id, tipo, giorno, valore):
            print(f"Salvataggio: emp_id={emp_id}, tipo={tipo}, giorno={giorno}, valore={valore}")

        def set_permessi_constraint(self, emp_id: int, giorno: int, valore: bool):  # <--- MODIFICA QUI
            self.model.set_permesso_dipendente(emp_id, giorno, valore)  # <--- MODIFICA QUI

        def set_mutua_constraint(self, emp_id: int, giorno: int, valore: bool):  # <--- MODIFICA QUI
            self.model.set_mutua_dipendente(emp_id, giorno, valore)  # <--- MODIFICA QUI

        def set_non_retribuite_constraint(self, emp_id: int, giorno: int, valore: bool):  # <--- MODIFICA QUI
            self.model.set_esigenza_dipendente(emp_id, giorno, valore)  # <--- MODIFICA QUI

        def set_no_notte_constraint(self, emp_id: int, giorno: int, valore: bool):  # <--- MODIFICA QUI
            self.model.set_pref_noNott_dipendente(emp_id, giorno, valore)  # <--- MODIFICA QUI

        def set_no_mattino_constraint(self, emp_id: int, giorno: int, valore: bool):  # <--- MODIFICA QUI
            self.model.set_pref_noMatt_dipendente(emp_id, giorno, valore)  # <--- MODIFICA QUI

        def set_no_pomeriggio_constraint(self, emp_id: int, giorno: int, valore: bool):  # <--- MODIFICA QUI
            self.model.set_pref_noPom_dipendente(emp_id, giorno, valore)  # <--- MODIFICA QUI





