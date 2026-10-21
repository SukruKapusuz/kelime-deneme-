"""Giriş noktası: çekirdeği kurar, 4 ekranı yerleştirir.
Çalıştırma:  flet run          (PC)      |  flet run --android  (telefon, Flet uygulamasıyla)
"""
import flet as ft

from core import yollar
from core.ayarlar import Ayarlar
from core.gecmis import Gecmis
from core.kok import KokMotoru
from core.lugat import url_uret
from ui.ara_ekrani import AraEkrani
from ui.ayarlar_ekrani import AyarlarEkrani
from ui.gecmis_ekrani import GecmisEkrani
from ui.kok_ekrani import KokEkrani
from ui.temalar import tema_uygula

GENIS_EKRAN = 800   # bu genişlikten sonra alttaki çubuk yerine yan menü gösterilir


class Baglam:
    """Ekranların ortak kullandığı nesneler ve ekranlar arası geçiş."""

    def __init__(self, page):
        self.page = page
        self.ayarlar = Ayarlar(yollar.ayar_dosyasi())
        self.gecmis = Gecmis(yollar.gecmis_dosyasi())
        self.motor = KokMotoru([yollar.HAZIR_KOK_CSV, yollar.kullanici_kok_csv()])
        self.git_fn = None

    def ac_lugat(self, kelime, lugat_ad=None):
        lugat = self.ayarlar.lugat_bul(lugat_ad or self.ayarlar.veri["varsayilan_lugat"]) \
            or self.ayarlar.aktif_lugatlar()[0]
        self.page.launch_url(url_uret(lugat["sablon"], kelime))
        if self.ayarlar.veri["gecmis_kaydet"]:
            self.gecmis.ekle(kelime, "lugat", lugat["ad"])

    def git(self, indeks, kelime=None):
        self.git_fn(indeks, kelime)


def main(page: ft.Page):
    page.title = "Kelime"
    page.padding = 0
    b = Baglam(page)
    tema_uygula(page, b.ayarlar.veri["tema"])

    ekranlar = [AraEkrani(b), KokEkrani(b), GecmisEkrani(b), AyarlarEkrani(b)]
    icerik = ft.Container(expand=True, padding=16)

    simgeler = [(ft.Icons.SEARCH, "Ara"), (ft.Icons.ACCOUNT_TREE, "Kök"),
                (ft.Icons.HISTORY, "Geçmiş"), (ft.Icons.SETTINGS, "Ayarlar")]

    def sekme_degisti(e):
        goster(int(e.control.selected_index))

    rail = ft.NavigationRail(
        selected_index=0, label_type=ft.NavigationRailLabelType.ALL, on_change=sekme_degisti,
        destinations=[ft.NavigationRailDestination(icon=i, label=t) for i, t in simgeler])
    bar = ft.NavigationBar(
        selected_index=0, on_change=sekme_degisti,
        destinations=[ft.NavigationBarDestination(icon=i, label=t) for i, t in simgeler])

    def goster(i, kelime=None):
        ekran = ekranlar[i]
        ekran.yenile()
        if kelime is not None and hasattr(ekran, "kelime_yukle"):
            ekran.kelime_yukle(kelime)
        icerik.content = ekran.view
        rail.selected_index = bar.selected_index = i
        page.update()

    def yerlestir(e=None):
        genis = (page.width or 0) >= GENIS_EKRAN
        rail.visible, bar.visible = genis, not genis
        page.update()

    b.git_fn = goster
    page.navigation_bar = bar
    page.on_resized = yerlestir   # eski Flet sürümleri
    page.on_resize = yerlestir    # yeni Flet sürümleri
    page.add(ft.SafeArea(ft.Row([rail, ft.VerticalDivider(width=1), icerik], expand=True), expand=True))
    goster(0)
    yerlestir()


if __name__ == "__main__":
    ft.app(target=main)
