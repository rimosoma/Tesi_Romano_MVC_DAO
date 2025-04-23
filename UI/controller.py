import flet

from UI.dialog_necessita import Necessita
from model.model import Model

class Controller:
    """
    Gestisce l'interazione tra view e model.
    """
    def __init__(self, view, model):
        self.model = Model()
          # Dizionario che tiene traccia delle istanze Necessita per ogni dipendente
        self._necessita_views = {}

    def get_employees(self):
        return self.model.get_employees()

    def get_turni_counts(self, emp_id):
        return self.model.get_turni_counts(emp_id)

    def generate_turni(self):
        return self.model.generate_turni()

    def export_to_xml(self, path: str = "turni.xml"):
        return self.model.export_to_xml(path)












    def apri_necessita(self, page, emp_id):
        # crea o riusa la view Necessita
        if emp_id not in self._necessita_views:
            nv = Necessita(page, emp_id).set_controller(self)
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

