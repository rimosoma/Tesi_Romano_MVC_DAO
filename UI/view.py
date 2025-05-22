import threading
from cProfile import label
import calendar
from datetime import date
from tkinter.constants import CENTER

import flet
from flet import (Page,DataTable,DataColumn,DataRow,DataCell,Checkbox,TextField,ElevatedButton,Text,Column,Row,IconButton,icons,Divider)
from flet_core import Container, MainAxisAlignment
from flet import UserControl, Page, ElevatedButton, Text
from pygments.styles.gh_dark import RED_2

from UI.controller import Controller


class View(UserControl):

# ---COSTRUTTORE-------------------------------------------------------------------------------------------------------------
    def __init__(self, page: flet.Page):
        super().__init__()

        self._page = page
        self._page.title = "Gestione Turni Casa di Riposo"
        self._page.horizontal_alignment = 'CENTER'
        self._page.theme_mode = flet.ThemeMode.DARK
        self._controller = None
        self._title = None

        self.page = page

        self.mese = None

        # prepariamo il dialog ma non lo apriamo ancora
        self.month_dialog = flet.AlertDialog(
            title=flet.Text("Seleziona mese di riferimento"),
            content=flet.Dropdown(),  # placeholder, lo riempiamo subito
            actions=[
                flet.ElevatedButton("Conferma", on_click=self._on_confirm),
            ],
            actions_alignment="end",
        )
        self.page.dialog = self.month_dialog


    def show_month_selector(self):
        # calcola le opzioni
        today = date.today()
        opts = []
        for i in range(12):
            m = (today.month - 1 + i) % 12 + 1
            y = today.year + ((today.month - 1 + i) // 12)
            label = f"{calendar.month_name[m]} {y}"
            value = f"{m}-{y}"  # <-- valore “11-2025”
            opts.append(flet.dropdown.Option(text=label, key=value))
        # assegna le opzioni e valore iniziale
        dd = self.month_dialog.content
        dd.options = opts
        dd.value = opts[0].key
        # apri il dialog
        self.month_dialog.open = True
        self.page.update()


    def _on_confirm(self, e):
        selected = self.month_dialog.content.value
        self.month_dialog.open = False

        self.mese = selected
        print(selected)

        if self._controller.passaMese(self.mese):
            self._load_interface()

#---CREO GLI ELEMENTI E LI IMPAGINO-------------------------------------------------------------------------------------------------------------
    def _load_interface(self):
        self._page.controls.clear()
        if not self._controller:
            raise Exception("Controller non impostato su View")
    # ----CREO Titolo------------------------------------------------------------------------------------------------------------
        self._title = Text("Gestore turni OSS RSA", color="blue", size=24)
        # ----CREO Tabella------------------------------------------------------------------------------------------------------------
        self._table = self._create_employee_table()
    # ----CREO Pulsanti------------------------------------------------------------------------------------------------------------
        self.generate_button = ElevatedButton(
            text="Genera Turni",
            icon=icons.PLAY_CIRCLE,
            on_click=self._on_generate_click)
        export_button = ElevatedButton(
            text="Export in XML",
            icon=icons.FILE_DOWNLOAD,
            on_click=self.tutti_si)
    # ----IMPAGINO------------------------------------------------------------------------------------------------------------
        main = flet.ListView(expand=1, spacing=10, padding=20, auto_scroll=True,
            controls=[
                # ----Titolo centrato------------------------------------------------------------------------------------------------------------
                Row([self._title], alignment=MainAxisAlignment.CENTER),
                Row(),
                Row([flet.Text(f"Interfaccia per la generazione dei turni del mese {self.mese}")], alignment=MainAxisAlignment.CENTER),

                # ----Tabella centrata------------------------------------------------------------------------------------------------------------
                Row([Container(
                        content=self._table,
                        expand=True,)],
                    alignment=MainAxisAlignment.CENTER,
                    expand=True,),
                Row(),
                Row(),
                Row(),
                # ----Bottoni------------------------------------------------------------------------------------------------------------
                Row(
                    [self.generate_button, export_button],
                    alignment=MainAxisAlignment.CENTER,
                    spacing=20)],)
        self._page.add(main)
        self._page.update()


# ----FUNZIONE CHE CREA LA TABELLA DEI DIPENDENTI CHIAMATA SOPRA------------------------------------------------------------------------------------------------------------
    def _create_employee_table(self):
        columns = [DataColumn(Text("Ferie")),
                    DataColumn(Text("Da Includere")),
                    DataColumn(Text("Nome e Cognome")),
                    DataColumn(Text("Contratto")),
                    DataColumn(Text("Notti")),
                    DataColumn(Text("Mattini")),
                    DataColumn(Text("Pomeriggi")),
                    DataColumn(Text("Necessità")),]
        rows = []
        dipendenti = list(self._controller.get_employees().values())

        for emp in dipendenti:
            if emp.tipoContratto == "FTN":
                max_val = 5
            elif emp.tipoContratto == "PTN":
                max_val = 4
            elif emp.tipoContratto == "PTL":
                max_val = 3

                # -----riga completa, con esattamente 7 celle:-----------------------------------------------------------------------------------------------------------------------------
            row = DataRow(cells=[
                DataCell(
                    flet.Container(
                        alignment=flet.alignment.center,  # Allineamento centrale
                        expand=True,  # Occupa tutto lo spazio disponibile
                        padding=5,
                        content=flet.Switch(
                        value=True if emp.has_vacation else False,
                        on_change=lambda e, emp_id=emp.id: self._controller.update_vacation(emp_id, e.control.value)
                    ))),
                #----------------------------------------------------------------------------------------------------------------
                DataCell(
                    flet.Container(
                        content=flet.RadioGroup(
                            value= emp.daIncludere,  # Valore iniziale (es. "da includere")
                            on_change=lambda e, emp_id=emp.id: self._controller.update_daIncludere(emp_id, e.control.value),
                            content=flet.Row([
                                flet.Radio(value="SI", label="SI"),
                                    flet.Radio(value="MT", label="MT"),
                                flet.Radio(value="ASP", label="ASP"),
                            ], spacing=5)),padding=5)),
                # ----------------------------------------------------------------------------------------------------------------
                DataCell(Text(f"{emp.nome} {emp.cognome}")),
                DataCell(Text(f"{emp.tipoContratto}")),##################################

                DataCell(
                    flet.Container(
                        content=flet.Dropdown(
                            value=str(emp.esigenzeNottiSettimanali) ,
                            options=[flet.dropdown.Option(str(i)) for i in range(0,  (max_val-int(emp.esigenzePomeriggiSettimanali)-int(emp.esigenzeMattiniSettimanali))+1)],
                            expand=True,  # Adatta il dropdown al contenitore
                            dense=True,  # Compatta leggermente il contenuto
                            text_style=flet.TextStyle(size=12),  # Assicura leggibilità
                            on_change=lambda e, emp_id=emp.id:
                            self._controller.updateNrNotti(emp_id, e) ,
                            disabled = emp.daIncludere in ("MT", "ASP", ""),
                            color = RED_2 if (int(emp.esigenzeNottiSettimanali) + int(emp.esigenzeMattiniSettimanali) + int(emp.esigenzePomeriggiSettimanali) < max_val) else None

                        ),
                        padding=5,
                        alignment=flet.alignment.center,
                        expand=True,)),
                # ----------------------------------------------------------------------------------------------------------------
                DataCell(
                    flet.Container(
                        content=flet.Dropdown(
                            value=str(emp.esigenzeMattiniSettimanali),
                            options=[flet.dropdown.Option(str(i)) for i in range(0,  (max_val-int(emp.esigenzePomeriggiSettimanali)-int(emp.esigenzeNottiSettimanali))+1)],
                            expand=True,  # Adatta il dropdown al contenitore
                            dense=True,  # Compatta leggermente il contenuto
                            text_style=flet.TextStyle(size=12),  # Assicura leggibilità
                            on_change=lambda e, emp_id=emp.id:
                            self._controller.updateNrMattini(emp_id, e),
                            disabled = emp.daIncludere in ("MT", "ASP", ""),
                            color = RED_2 if (int(emp.esigenzeNottiSettimanali) + int(emp.esigenzeMattiniSettimanali) + int(emp.esigenzePomeriggiSettimanali) < max_val) else None

                        ),
                        padding=5,
                        alignment=flet.alignment.center,
                        expand=True,)),
                # ----------------------------------------------------------------------------------------------------------------
                DataCell(
                    flet.Container(
                        content=flet.Dropdown(
                            value=str(emp.esigenzePomeriggiSettimanali),
                            options=[flet.dropdown.Option(str(i)) for i in range(0,  (max_val-int(emp.esigenzeNottiSettimanali)-int(emp.esigenzeMattiniSettimanali))+1)],
                            expand=True,  # Adatta il dropdown al contenitore
                            dense=True,  # Compatta leggermente il contenuto
                            text_style=flet.TextStyle(size=12),  # Assicura leggibilità
                            on_change=lambda e, emp_id=emp.id:
                            self._controller.updateNrPomeriggi(emp_id, e),
                            disabled = emp.daIncludere in ("MT", "ASP", ""),
                            color = RED_2 if (int(emp.esigenzeNottiSettimanali) + int(emp.esigenzeMattiniSettimanali) + int(emp.esigenzePomeriggiSettimanali) < max_val) else None

                        ),
                        padding=5,
                        alignment=flet.alignment.center,
                        expand=True,)),
                # ----------------------------------------------------------------------------------------------------------------
                DataCell(
                    flet.Container(
                        content=IconButton(
                            icon=icons.SETTINGS,
                            tooltip="Necessità",
                            on_click=lambda e, page=self._page, emp_id=emp.id: self._controller.apri_necessita(page,emp_id=emp_id),
                            disabled=emp.daIncludere in ("MT", "ASP", "")),
                        alignment=flet.alignment.center,  # Allineamento centrale
                        expand=True,  # Occupa tutto lo spazio disponibile
                        padding=5,  ))])
            rows.append(row)
        # ----------------------------------------------------------------------------------------------------------------
        return DataTable(
            columns=columns,
            rows=rows,
            horizontal_margin=20,
            column_spacing=20,
            heading_row_color="bluegrey",
            horizontal_lines=flet.BorderSide(1, "grey"),
            vertical_lines=flet.BorderSide(1, "grey"),
            expand=True, )
# ----------------------------------------------------------------------------------------------------------------------------------
    def set_controller(self, controller: Controller):
        # Assegna il controller e costruisci l'interfaccia
        self._controller = controller
        #self._load_interface()
# ----------------------------------------------------------------------------------------------------------------------------------
    def _show_snackbar(self, message):
        self._page.snack_bar = Text(message)
        print(message)
        self._page.snack_bar.open = True
        self._page.update()
# ----------------------------------------------------------------------------------------------------------------------------------
    def update_page(self):
        self._page.update()
# ----------------------------------------------------------------------------------------------------------------------------------
    def update_table_view(self):
        self._page.update()
        self._load_interface()
# ----------------------------------------------------------------------------------------------------------------------------------
    def _on_generate_click(self, e):
        # Disabilita il bottone e feedback immediato
        self.generate_button.disabled = True
        self._show_snackbar("Generazione in corso…")
        self.update_page()

        # Avvia il metodo _background_generate in un thread a parte
        threading.Thread(target=self._background_generate, daemon=True).start()


    def _background_generate(self):
        """
        Metodo eseguito in un thread separato:
        - chiama il controller
        - salva/apre l’Excel
        - aggiorna la UI direttamente (Flet supporta update() da thread)
        """
        try:
            output_path = self._controller.generate_turni()

            # Torno alla UI per mostrare completamento
            # direttamente, senza call_later
            self._page.snack_bar = Text(f"Turni pronti: {output_path}")
            self._page.snack_bar.open = True
            self.generate_button.disabled = False
            self._page.update()

        except Exception as ex:
            # Mostro errore direttamente
            self._page.snack_bar = Text(f"Errore: {ex}")
            self._page.snack_bar.open = True
            self.generate_button.disabled = False
            self._page.update()

# ----------------------------------------------------------------------------------------------------------------------------------
    def tutti_si(self, e):
        for emp in (list(self._controller.get_employees().values())):
            self._controller.update_daIncludere(emp.id, "SI")

        self.update_table_view()


