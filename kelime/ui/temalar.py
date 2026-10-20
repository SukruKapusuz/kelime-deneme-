import flet as ft

TEMALAR = {
    "Açık":     {"mod": ft.ThemeMode.LIGHT, "tohum": ft.Colors.TEAL,   "zemin": None},
    "Koyu":     {"mod": ft.ThemeMode.DARK,  "tohum": ft.Colors.TEAL,   "zemin": None},
    "Sepya":    {"mod": ft.ThemeMode.LIGHT, "tohum": ft.Colors.BROWN,  "zemin": "#F4ECD8"},
    "Lacivert": {"mod": ft.ThemeMode.DARK,  "tohum": ft.Colors.INDIGO, "zemin": None},
}


def tema_uygula(page: ft.Page, ad: str):
    t = TEMALAR.get(ad, TEMALAR["Açık"])
    page.theme_mode = t["mod"]
    page.theme = ft.Theme(color_scheme_seed=t["tohum"])
    page.dark_theme = ft.Theme(color_scheme_seed=t["tohum"])
    page.bgcolor = t["zemin"]
    page.update()
