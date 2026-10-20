"""Ekran 3: geçmiş aramalar. Satıra dokununca kelime ilgili ekrana geri yüklenir."""
import flet as ft


class GecmisEkrani:
    def __init__(self, b):
        self.b = b
        self.liste = ft.Column(spacing=0)
        self.view = ft.Column(
            [ft.Row([ft.Text("Geçmiş", style=ft.TextThemeStyle.HEADLINE_SMALL, expand=True),
                     ft.TextButton("Temizle", icon=ft.Icons.DELETE_SWEEP, on_click=self.temizle)]),
             self.liste],
            spacing=12, scroll=ft.ScrollMode.AUTO)

    def yenile(self):
        self.liste.controls.clear()
        kayitlar = self.b.gecmis.listele()
        if not kayitlar:
            self.liste.controls.append(ft.Text("Henüz kayıt yok."))
        for kid, kelime, tur, lugat, zaman in kayitlar:
            simge = ft.Icons.MENU_BOOK if tur == "lugat" else ft.Icons.ACCOUNT_TREE
            alt = (lugat + " · " if lugat else "") + zaman
            self.liste.controls.append(ft.ListTile(
                leading=ft.Icon(simge), title=ft.Text(kelime), subtitle=ft.Text(alt),
                trailing=ft.IconButton(ft.Icons.CLOSE, on_click=lambda e, i=kid: self.sil(i)),
                on_click=lambda e, k=kelime, t=tur: self.b.git(0 if t == "lugat" else 1, k)))

    def sil(self, kid):
        self.b.gecmis.sil(kid)
        self.yenile()
        self.b.page.update()

    def temizle(self, e=None):
        self.b.gecmis.temizle()
        self.yenile()
        self.b.page.update()
