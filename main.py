import flet as ft

from model.model import SchedulingModel
from UI.view import View
from UI.controller import Controller


def main(page: ft.Page):
    my_model = SchedulingModel()
    my_view = View(page)
    my_controller = Controller(my_view, my_model)
    my_view.set_controller(my_controller)
    my_view.show_month_selector()


ft.app(target=main)
