import flet as ft


class Controller:
    def __init__(self, view, model):
        # the view, with the graphical elements of the UI
        self._view = view
        # the model, which implements the logic of the program and holds the data
        self._model = model


    def popolaTendinaAnno(self):
        anni = self._model.getAnni()
        for anno in anni:
            self._view.tendinaAnno.controls.append(ft.dropdown.Option(anno))

    def popolaTendinaBrand(self):
        brands = self._model.getBrands()
        for brand in brands:
            self._view.tendinaBrand.controls.append(ft.dropdown.Option(brand))

    def popolaTendinaRivenditore(self):
        rivenditori = self._model.getRivenditori()
        for rivenditore in rivenditori:
            self._view.tendinaRivenditore.controls.append(ft.dropdown.Option(rivenditore))

    def getMigliori(self, e):
        pass

    def getAnalisi(self, e):
        pass