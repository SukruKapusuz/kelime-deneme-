"""Ekran 1: kelimeyi seçili lügatın adresine gönderir (ör. https://lugatim.com/s/?kitap)."""
import flet as ft


class AraEkrani:
    def __init__(self, b):
        self.b = b
        self.giris = ft.TextField(label="Kelime yazın", autofocus=True, on_submit=self.ara)
        self.lugat = ft.Dropdown(label="Lügat")
        self.durum = ft.Text("", color=ft.Colors.ERROR)
        self.view = ft.Column(
            [ft.Text("Lügatte ara", style=ft.TextThemeStyle.HEADLINE_SMALL),
             self.giris, self.lugat,
             ft.ElevatedButton("Ara", icon=ft.Icons.SEARCH, on_click=self.ara),
             self.durum],
            spacing=16, scroll=ft.ScrollMode.AUTO)

    def yenile(self):
        aktif = [l["ad"] for l in self.b.ayarlar.aktif_lugatlar()]
        self.lugat.options = [ft.dropdown.Option(ad) for ad in aktif]
        if self.lugat.value not in aktif:
            varsayilan = self.b.ayarlar.veri["varsayilan_lugat"]
            self.lugat.value = varsayilan if varsayilan in aktif else (aktif[0] if aktif else None)

    def kelime_yukle(self, kelime):
        self.giris.value = kelime

    def ara(self, e=None):
        kelime = (self.giris.value or "").strip()
        if not kelime:
            self.durum.value = "Önce bir kelime yazın."
            self.b.page.update()
            return
        self.durum.value = ""
        self.b.ac_lugat(kelime, self.lugat.value)
