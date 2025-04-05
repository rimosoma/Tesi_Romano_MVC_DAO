import flet as ft


class Controller:
    def __init__(self, view, model):
        # the view, with the graphical elements of the UI
        self._view = view
        # the model, which implements the logic of the program and holds the data
        self._model = model


    #VARIABILI UTILI PER L'ANALISI
        self.anno = None
        self.checkanno = False
        self.brand = None
        self.checkbrand = False
        self.rivenditore = None
        self.checkriv = False


#ANNO
    def popolaTendinaAnno(self):
        anni = self._model.getAnni()
        for anno in anni:
            self._view.tendinaAnno.options.append(ft.dropdown.Option(anno))

    def setAnno(self, e):
        if e.control.value != "0":
            self.anno = int(e.control.value)
            self.checkanno = True
        else:
            self.anno = None
            self.checkanno = True

        if self.checkanno and self.checkbrand and self.checkriv:
            self._view.btnMigliori.visible = True
            self._view.btnAnalisi.visible = True
            self._view._page.update()


#BRAND
    def popolaTendinaBrand(self):
        brands = self._model.getBrands()
        for brand in brands:
            self._view.tendinaBrand.options.append(ft.dropdown.Option(brand))

    def setBrand(self, e):
        if e.control.value != "nessuno":
            self.brand = e.control.value
            self.checkbrand = True
        else:
            self.brand = None
            self.checkbrand = True
        if self.checkanno and self.checkbrand and self.checkriv:
            self._view.btnMigliori.visible = True
            self._view.btnAnalisi.visible = True
            self._view._page.update()


#RIVENDITORE
    def popolaTendinaRivenditore(self):
        rivenditori = self._model.getRivenditori()
        for codice,rivenditore in rivenditori.items():
            self._view.tendinaRivenditore.options.append(ft.dropdown.Option(key=codice, text=rivenditore))

    def setRivenditore(self, e):
        if e.control.value != "0":
            self.rivenditore = e.control.value #dovrebbe darmi il codice
            self.checkriv = True
        else:
            self.rivenditore = None
            self.checkriv = True

        if self.checkanno and self.checkbrand and self.checkriv:
            self._view.btnMigliori.visible = True
            self._view.btnAnalisi.visible = True
            self._view._page.update()


    def getMigliori(self, e):
        lista = self._model.getMiglioriModel(self.anno, self.brand, self.rivenditore)
        self._view.console.controls.clear()

        if lista:
            for riga in lista:
                rig = " | ".join(str(item) for item in riga)

                self._view.console.controls.append(ft.Text(rig))
        else:
            self._view.console.controls.append(ft.Text("Nessuna corrispondenza"))

        self._view._page.update()

    def getAnalisi(self, e):
        lista = self._model.getAnalisiModel(self.anno, self.brand, self.rivenditore)
        self._view.console.controls.clear()
        for riga in lista:
            self._view.console.controls.append(ft.Text(riga))
        self._view._page.update()
