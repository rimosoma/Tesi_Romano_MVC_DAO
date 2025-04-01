import flet as ft


class View(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()

        # page stuff
        self._page = page
        self._page.title = "Analizza Vendite"
        self._page.horizontal_alignment = 'CENTER'
        self._page.theme_mode = ft.ThemeMode.DARK
        self._controller = None


        # graphical elements
        self._title = None

        self.row1 = None
        self.tendinaAnno = None
        self.tendinaBrand = None
        self.tendinaRivenditore = None

        self.row2 = None
        self.btnMigliori = None
        self.btnAnalisi = None

    def load_interface(self):
        # title
        self._title = ft.Text("Analizza Vendite", color="blue", size=24)
        self._page.controls.append(self._title)
        self._page.update()


        # PRIMA RIGA
        self.tendinaAnno = ft.Dropdown(label="Tendina Anno", options=[])
        self._controller.popolaTendinaAnno()
        self.tendinaBrand = ft.Dropdown(label="Tendina Brand", options=[])
        self._controller.popolaTendinaBrand()
        self.tendinaRivenditore = ft.Dropdown(label="Tendina Rivenditore", options=[])
        self._controller.popolaTendinaRivenditore()
        self.row1 = ft.Row(controls=[self.tendinaAnno, self.tendinaBrand, self.tendinaRivenditore])
        self._page.controls.append(self.row1)
        self._page.update()


        #SECONDA RIGA
        self.btnMigliori = ft.ElevatedButton(text="Migliori vendite", on_click=self._controller.getMigliori())
        self.btnAnalisi = ft.ElevatedButton(text="Analisi vendite", on_click=self._controller.getAnalisi())
        self.row2 = ft.Row(controls=[self.btnMigliori, self.btnAnalisi])
        self._page.controls.append(self.row2)



    @property
    def controller(self):
        return self._controller

    @controller.setter
    def controller(self, controller):
        self._controller = controller

    def set_controller(self, controller):
        self._controller = controller

    def create_alert(self, message):
        dlg = ft.AlertDialog(title=ft.Text(message))
        self._page.dialog = dlg
        dlg.open = True
        self._page.update()

    def update_page(self):
        self._page.update()
