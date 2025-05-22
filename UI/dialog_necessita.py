# necessita.py

import calendar
import flet
from flet import (
    UserControl,
    Page,
    Column,
    Text,
    Divider,
    Tabs,
    Tab,
    DataTable,
    DataColumn,
    DataRow,
    DataCell,
    Checkbox,
)
from flet_core import IconButton, icons, Row, Stack, Container, colors, MainAxisAlignment


class Necessita(UserControl):
    def __init__(self, page: Page, emp_id, mese):
        super().__init__()
        self.page = page
        self.page.title = "Gestione Necessità"
        self.page.horizontal_alignment = "CENTER"
        self.page.theme_mode = flet.ThemeMode.DARK
        self.emp_id = emp_id

        month_str, year_str = mese.split("-")
        self.month = int(month_str)
        self.year = int(year_str)

        # Controller verrà assegnato dopo
        self.controller = None

        # Mese/anno arbitrario

        self.weeks = calendar.monthcalendar(self.year, self.month)
        self.weekday_names = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]

        # Sei tipi di esigenza: (chiave, etichetta, nome metodo setter nel controller)
        self.constraint_types = [
            ("permessi_ferie",   "Permessi/Ferie",          "set_permessi_constraint"),
            ("mutua_infortunio", "Mutua/Infortunio",        "set_mutua_constraint"),
            ("non_retribuite",   "Esigenze non retribuite", "set_non_retribuite_constraint"),
            ("no_mattino",       "No Mattino",              "set_no_mattino_constraint"),
            ("no_pomeriggio",    "No Pomeriggio",           "set_no_pomeriggio_constraint"),
            ("no_notte",         "No Notte",                "set_no_notte_constraint"),
        ]

        # Colonna principale
        self.main_column = Column(expand=True, scroll="AUTO")

    def set_controller(self, controller):
        """Assegna il controller e permette il chaining."""
        self.controller = controller
        return self

    def load_interface(self):
        """Costruisce l'interfaccia dentro main_column."""
        if not self.controller:
            raise RuntimeError("Controller non impostato su Necessita")

        self.main_column.controls.clear()

        # Header con titolo e pulsante chiudi
        header = Row([
            Text(f"Necessità Emp #{self.emp_id} – {calendar.month_name[self.month]} {self.year}", size=20),
            IconButton(
                icon=icons.CLOSE_ROUNDED,
                tooltip="Chiudi",
                on_click=lambda e: self.controller.chiudi_necessita(self.page, self.emp_id)
            )
        ], alignment=MainAxisAlignment.SPACE_BETWEEN)
        self.main_column.controls.append(header)
        self.main_column.controls.append(Divider())

        # Costruzione dei Tabs
        tabs = []
        for key, label, setter_name in self.constraint_types:
            tabs.append(Tab(
                text=label,
                content=self._build_calendar_table(key, setter_name)
            ))

        # Inserimento dei Tabs
        self.main_column.controls.append(
            Column([
                Tabs(
                    selected_index=0,
                    tabs=tabs,
                    divider_color=colors.PURPLE,
                    scrollable=True,
                    animation_duration=300,
                    height=250
                ),
                Divider()
            ], spacing=0)
        )

        self.update()

    def _build_calendar_table(self, constraint_key: str, setter_method_name: str) -> DataTable:
        """
        Costruisce un DataTable 7xN per il mese.
        Ogni cella è un Checkbox il cui valore iniziale viene preso
        da self.controller.get_employee(emp_id).dizionarioNecessita[constraint_key][day].
        Alla modifica, chiama self.controller.<setter_method_name>(emp_id, day, valore).
        """
        # Intestazioni Lunedì–Domenica
        columns = [DataColumn(Text(d)) for d in self.weekday_names]

        # Preleva il dict delle necessità dal model via controller
        emp = self.controller.get_employee(self.emp_id)
        #print(emp)
        day_dict = emp.dizionarioNecessita.get(constraint_key, {})

        rows = []
        for week in self.weeks:
            cells = []
            for day in week:
                if day == 0:
                    cells.append(DataCell(Text("")))
                else:
                    # valore iniziale (False se non trovato)
                    initial = day_dict.get(day, False)

                    # factory per catturare day, setter E IL SUO VALORE
                    def make_on_change(current_day, setter):  # Aggiunto current_day
                        def _on_change(e):
                            # Passa il numero del giorno (int) e il valore (bool)
                            # non l'oggetto evento 'e' completo.
                            getattr(self.controller, setter)(self.emp_id, current_day,
                                                             e.control.value)  # <--- MODIFICA QUI
                            self.page.update()

                        return _on_change

                    chk = Checkbox(
                        value=initial,
                        label=str(day),
                        on_change=make_on_change(day, setter_method_name)  # <--- MODIFICA QUI: Passa 'day'
                    )
                    cells.append(DataCell(chk))
            rows.append(DataRow(cells=cells))

        return DataTable(
            columns=columns,
            rows=rows,
            heading_row_height=30,
            data_row_min_height=30,
            data_row_max_height=30,
            horizontal_lines={"color": "grey"},
            vertical_lines={"color": "grey"},
            horizontal_margin=10,
            column_spacing=10,
            expand=True
        )

    def build(self):
        """Restituisce il layout principale da inserire nella page."""
        barrier = Container(
            expand=True,
            bgcolor=colors.BLACK54
        )
        card = Container(
            content=self.main_column,
            width=900,
            padding=20,
            bgcolor=colors.BACKGROUND,
            border_radius=10
        )
        centered = Row([card], alignment="CENTER", expand=True)
        return Stack([barrier, centered])
