# necessita.py

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
import calendar

from flet_core import IconButton, icons, Row, Stack, Container, colors, ThemeMode, Theme
from flet_core.colors import PURPLE, BLACK, GREY_50, GREY_100
from flet_core.icons import LIGHT


class Necessita(UserControl):
    def __init__(self, page: Page, emp_id):
        super().__init__()
        self.page = page
        self.page.title = "Gestione Necessità"
        self.page.horizontal_alignment = "CENTER"
        self.page.theme_mode = flet.ThemeMode.DARK
        self.emp_id = emp_id

        # Controller verrà assegnato dopo
        self.controller = None

        # Imposta un mese arbitrario (modificabile)
        self.year = 2025
        self.month = 7
        self.weeks = calendar.monthcalendar(self.year, self.month)
        self.weekday_names = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]

        # Definizione dei sei tipi di esigenza:
        # (chiave, etichetta, nome metodo setter nel controller)
        self.constraint_types = [
            ("permessi_ferie",   "Permessi/Ferie",          "set_permessi_constraint"),
            ("mutua_infortunio", "Mutua/Infortunio",        "set_mutua_constraint"),
            ("non_retribuite",   "Esigenze non retribuite", "set_non_retribuite_constraint"),
            ("no_mattino",       "No Mattino",              "set_no_mattino_constraint"),
            ("no_pomeriggio",    "No Pomeriggio",           "set_no_pomeriggio_constraint"),
            ("no_notte",         "No Notte",                "set_no_notte_constraint"),
        ]

        # Colonna principale che build() restituirà
        self.main_column = Column(expand=True, scroll="AUTO")

    def set_controller(self, controller):
        """Assegna il controller e permette il chaining."""
        self.controller = controller
        return self

    def load_interface(self):
        """Costruisce l'interfaccia dentro main_column."""
        if not self.controller:
            raise RuntimeError("Controller non impostato su Necessita")

        # Pulisce e costruisce da zero
        self.main_column.controls.clear()

        # Titolo
        header = Row([
            Text(f"Necessità di Emp #{self.emp_id} – {calendar.month_name[self.month]} {self.year}", size=20),
            IconButton(icon=icons.CLOSE_ROUNDED, tooltip="Chiudi",
                       on_click=lambda e: self.controller.chiudi_necessita(self.page, self.emp_id))
        ], alignment=flet.MainAxisAlignment.SPACE_AROUND)
        self.main_column.controls.append(header)
        self.main_column.controls.append(Divider())

        # Crea un Tab per ciascun tipo di esigenza
        tabs = []
        for key, label, setter_name in self.constraint_types:
            tabs.append(
                Tab(
                    text=label,

                    content=self._build_calendar_table(setter_name)

                )
            )

        # Aggiunge i Tabs
        self.main_column.controls.append(
            Column([
                Tabs(
                    selected_index=0,
                    tabs=tabs,
                    divider_color=PURPLE,
                    scrollable=True,
                    animation_duration=300,
                    height=250
                ),
                Divider()
            ], spacing=0)
        )

        self.update()

    def _build_calendar_table(self, setter_method_name: str) -> DataTable:
        """
        Costruisce un DataTable 7xN per il mese.
        Ogni cella è un Checkbox inizialmente False.
        Alla modifica, chiama:
          self.controller.<setter_method_name>(year, month, day, value)
        """
        # Intestazioni Lunedì–Domenica
        columns = [DataColumn(Text(d)) for d in self.weekday_names]

        # Costruzione delle righe settimanali
        rows = []
        for week in self.weeks:
            cells = []
            for day in week:
                if day == 0:
                    # Giorni fuori mese
                    cells.append(DataCell(Text("")))
                else:
                    chk = Checkbox(
                        value=False,
                        label=day,
                        on_change=lambda e, d=day, m=setter_method_name:
                            [getattr(self.controller, m)(self.year, self.month, d, e.control.value), self.page.update()]
                    )
                    cells.append(DataCell(chk))
            rows.append(DataRow(cells=cells))

        return DataTable(

            columns=columns,
            rows=rows,
            heading_row_height=30,
            data_row_min_height=30,  # Riduci l'altezza
            data_row_max_height=30,
            horizontal_lines={"color": "grey"},
            vertical_lines={"color": "grey"},
            horizontal_margin=10,  # Aggiungi margini
            column_spacing=10,
        )

    def build(self):
        """Restituisce il layout principale da inserire nella page."""
        # sfondo semi-trasparente
        barrier = Container(
            expand=True,
            bgcolor=colors.BLACK54
        )

        # card centrale con tema light forzato
        card = Container(
            content=self.main_column,
            width=900,
            padding=20,
            bgcolor=colors.BACKGROUND,
            border_radius=10,
            #theme_mode=ThemeMode.LIGHT  # imposta questo container in tema chiaro
        )

        # centra il card
        centered = Row([card], alignment="CENTER", expand=True)

        return Stack([barrier, centered])