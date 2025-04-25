from cProfile import label
from tkinter.constants import CENTER

import flet
from flet import (Page,DataTable,DataColumn,DataRow,DataCell,Checkbox,TextField,ElevatedButton,Text,Column,Row,IconButton,icons,Divider)
from flet_core import Container, MainAxisAlignment

from UI.controller import Controller


class View(flet.UserControl):


    def __init__(self, page: Page):
        super().__init__()

        self._page = page
        self._page.title = "Gestione Turni Casa di Riposo"
        self._page.horizontal_alignment = 'CENTER'
        self._page.theme_mode = flet.ThemeMode.DARK
        self._controller = None


        self._title = None




    def _load_interface(self):
        self._page.controls.clear()
        if not self._controller:
            raise Exception("Controller non impostato su View")

        # Titolo
        self._title = Text("Gestore turni OSS RSA", color="blue", size=24)

        # Tabella dipendenti (già con expand=True)
        self._table = self._create_employee_table()

        # Pulsanti
        generate_button = ElevatedButton(
            text="Genera Turni",
            icon=icons.PLAY_CIRCLE,
            on_click=self._generate_turns
        )
        export_button = ElevatedButton(
            text="Export in XML",
            icon=icons.FILE_DOWNLOAD,
            on_click=self._export_xml
        )

        # Costruisci layout



        main = flet.ListView(expand=1, spacing=10, padding=20, auto_scroll=True,
            controls=[
                # 1) Titolo centrato
                Row([self._title], alignment=MainAxisAlignment.CENTER),

                Row(),
                Row(),

                # 2) Tabella centrata e che espande
                Row(
                    [Container(
                        content=self._table,
                        expand=True,
                    )],
                    alignment=MainAxisAlignment.CENTER,
                    expand=True,
                ),

                Row(),
                Row(),
                Row(),

                # 3) Pulsanti
                Row(
                    [generate_button, export_button],
                    alignment=MainAxisAlignment.CENTER,
                    spacing=20
                )
            ],

            #scroll=flet.ScrollMode.AUTO
            #scroll="AUTO"
        )

        self._page.add(main)
        self._page.update()

    def _create_employee_table(self):
        columns = [
            DataColumn(Text("Ferie")),
            DataColumn(Text("Da Includere")),
            DataColumn(Text("Nome e Cognome")),
            DataColumn(Text("Notti")),
            DataColumn(Text("Mattini")),
            DataColumn(Text("Pomeriggi")),
            DataColumn(Text("Necessità")),
        ]
        rows = []

        dipendenti = list(self._controller.get_employees().values())


        for emp in dipendenti:
            shifts = self._controller.get_turni_counts(emp.id)
            #btn = self._create_settings_button(emp)
            cek1 = Checkbox(label="SI", value=True if emp.daIncludere =="SI" else False,
                                         on_change=lambda e, emp_id=emp.id: self._controller.update_daIncludere(emp_id,"SI",e))

            cek2 = Checkbox(label="MAT",value=True if emp.daIncludere =="MAT" else False,
                                         on_change=lambda e, emp_id=emp.id: self._controller.update_daIncludere(emp_id,"MAT", e))

            cek3 = Checkbox(label="ASP",value=True if emp.daIncludere =="ASP" else False,
                                         on_change=lambda e, emp_id=emp.id: self._controller.update_daIncludere(emp_id,"ASP",e))


            # Una sola riga completa, con esattamente 7 celle:
            row = DataRow(cells=[
                DataCell(
                    flet.Container(
                        alignment=flet.alignment.center,  # Allineamento centrale
                        expand=True,  # Occupa tutto lo spazio disponibile
                        padding=5,
                        content=flet.Switch(
                        value=True if emp.has_vacation else False,
                        on_change=lambda e, emp_id=emp.id: self._controller.update_vacation(emp_id, e.control.value)
                    ))
                ),
                DataCell(
                    flet.Container(
                        content=flet.Row(
                            controls=[
                                Checkbox(label="SI", value=True if emp.daIncludere =="SI" else False,
                                         on_change=lambda e, emp_id=emp.id: self._controller.update_no_mattino(emp_id,
                                                                                                               e.control.value)),
                                Checkbox(label="MAT",value=True if emp.daIncludere =="MAT" else False,
                                         on_change=lambda e, emp_id=emp.id: self._controller.update_no_pomeriggio(
                                             emp_id, e.control.value)),
                                Checkbox(label="ASP",value=True if emp.daIncludere =="ASP" else False,
                                         on_change=lambda e, emp_id=emp.id: self._controller.update_no_notte(emp_id,
                                                                                                             e.control.value)),
                            ],
                            alignment=flet.MainAxisAlignment.CENTER,  # Centra orizzontalmente
                            spacing=10,  # Spazio tra i checkbox
                        ),
                        alignment=flet.alignment.center,
                        expand=True,
                        padding=10,
                    )
                ),


                DataCell(Text(f"{emp.nome} {emp.cognome}")),
                DataCell(
                    flet.Container(
                        content=flet.Dropdown(
                            value=str(emp.notti),
                            options=[flet.dropdown.Option(str(i)) for i in range(0, (5-int(emp.pomeriggi)-int(emp.mattini))+1)],
                            expand=True,  # Adatta il dropdown al contenitore
                            dense=True,  # Compatta leggermente il contenuto
                            text_style=flet.TextStyle(size=12),  # Assicura leggibilità
                            on_change=lambda e, emp_id=emp.id:
                            self._controller.updateNrNotti(emp_id, e)
                        ),
                        padding=5,
                        alignment=flet.alignment.center,
                        expand=True,  # Fa sì che il Container riempia la cella
                    )
                ),


                DataCell(
                    flet.Container(
                        content=flet.Dropdown(
                            value=str(emp.mattini),
                            options=[flet.dropdown.Option(str(i)) for i in range(0,  (5-int(emp.pomeriggi)-int(emp.notti))+1)],
                            expand=True,  # Adatta il dropdown al contenitore
                            dense=True,  # Compatta leggermente il contenuto
                            text_style=flet.TextStyle(size=12),  # Assicura leggibilità
                            on_change=lambda e, emp_id=emp.id:
                            self._controller.updateNrMattini(emp_id, e)
                        ),
                        padding=5,
                        alignment=flet.alignment.center,
                        expand=True,  # Fa sì che il Container riempia la cella
                    )
                ),
                DataCell(
                    flet.Container(
                        content=flet.Dropdown(
                            value=str(emp.pomeriggi),
                            options=[flet.dropdown.Option(str(i)) for i in range(0,  (5-int(emp.notti)-int(emp.mattini))+1)],
                            expand=True,  # Adatta il dropdown al contenitore
                            dense=True,  # Compatta leggermente il contenuto
                            text_style=flet.TextStyle(size=12),  # Assicura leggibilità
                            on_change=lambda e, emp_id=emp.id:
                            self._controller.updateNrPomeriggi(emp_id, e)
                        ),
                        padding=5,
                        alignment=flet.alignment.center,
                        expand=True,  # Fa sì che il Container riempia la cella
                    )
                ),
                DataCell(
                    flet.Container(
                        content=IconButton(
                            icon=icons.SETTINGS,
                            tooltip="Necessità",
                            on_click=lambda e, page=self._page: self._controller.apri_necessita(page, emp_id=emp.id),
                        ),
                        alignment=flet.alignment.center,  # Allineamento centrale
                        expand=True,  # Occupa tutto lo spazio disponibile
                        padding=5,  # Spaziatura interna opzionale
                    )
                )
            ])
            rows.append(row)

        return DataTable(
            columns=columns,
            rows=rows,
            horizontal_margin=20,
            column_spacing=20,
            heading_row_color="bluegrey",
            horizontal_lines=flet.BorderSide(1, "grey"),
            vertical_lines=flet.BorderSide(1, "grey"),
            expand=True,  # si allarga in larghezza
            # NON impostare width o height fissi
        )





    def set_controller(self, controller: Controller):
        # Assegna il controller e costruisci l'interfaccia
        self._controller = controller
        self._load_interface()



    def _show_snackbar(self, message):
        self._page.snack_bar = Text(message)
        self._page.snack_bar.open = True
        self._page.update()

    def update_page(self):
        self._page.update()

    def update_table_view(self):
        self._page.update()
        self._load_interface()


    def _generate_turns(self, e):
        self._controller.generate_turni()
        self._show_snackbar("Turni generati con successo.")

    def _export_xml(self, e):
        xml_path = self._controller.export_to_xml()
        self._show_snackbar(f"Export completato: {xml_path}")