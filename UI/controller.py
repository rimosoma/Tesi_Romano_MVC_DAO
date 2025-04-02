import flet as ft


class Controller:
    def __init__(self, view, model):
        # the view, with the graphical elements of the UI
        self._view = view
        # the model, which implements the logic of the program and holds the data
        self._model = model


    #VARIABILI UTILI PER L'ANALISI
        self.anno = None
        self.brand = None
        self.rivenditore = None


#ANNO
    def popolaTendinaAnno(self):
        anni = self._model.getAnni()
        for anno in anni:
            self._view.tendinaAnno.options.append(ft.dropdown.Option(anno))

    def setAnno(self, e):
        self.anno = int(e.control.value)
        print(self.anno)


#BRAND
    def popolaTendinaBrand(self):
        brands = self._model.getBrands()
        for brand in brands:
            self._view.tendinaBrand.options.append(ft.dropdown.Option(brand))

    def setBrand(self, e):
        self.brand = e.control.value
        print(e.control.value)



#RIVENDITORE
    def popolaTendinaRivenditore(self):
        rivenditori = self._model.getRivenditori()
        for codice,rivenditore in rivenditori.items():
            self._view.tendinaRivenditore.options.append(ft.dropdown.Option(key=codice, text=rivenditore))

    def setRivenditore(self, e):
        self.rivenditore = e.control.value #dovrebbe darmi il codice
        print(e.control.value)






  #def getMigliori(self, e):
        pass

  #def getAnalisi(self, e):
        pass