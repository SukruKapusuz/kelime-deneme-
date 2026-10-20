"""Ekran 2: Arapça asıllı kelimenin kökünü bulur, aynı kökten türeyenleri listeler."""
import flet as ft


class KokEkrani:
    def __init__(self, b):
        self.b = b
        self.giris = ft.TextField(label="Kelime yazın (ör. kitap)", autofocus=True,
                                  on_submit=self.bul)
        self.baslik = ft.Text("", style=ft.TextThemeStyle.TITLE_MEDIUM)
        self.not_ = ft.Text("", italic=True)
        self.liste = ft.Column(spacing=0)
        self.view = ft.Column(
            [ft.Text("Kök ve türevler", style=ft.TextThemeStyle.HEADLINE_SMALL),
             self.giris,
             ft.ElevatedButton("Türevleri bul", icon=ft.Icons.ACCOUNT_TREE, on_click=self.bul),
             self.baslik, self.not_, self.liste],
            spacing=12, scroll=ft.ScrollMode.AUTO)

    def yenile(self):
        pass

    def kelime_yukle(self, kelime):
        self.giris.value = kelime
        self.bul()

    def bul(self, e=None):
        kelime = (self.giris.value or "").strip()
        if not kelime:
            return
        ayar = self.b.ayarlar.veri["kok"]
        sonuc = self.b.motor.bul(kelime, ayar)
        if self.b.ayarlar.veri["gecmis_kaydet"]:
            self.b.gecmis.ekle(kelime, "kok")

        self.liste.controls.clear()
        if sonuc["yontem"] == "yok":
            self.baslik.value = "Sonuç bulunamadı."
            self.not_.value = "Kelime kök listesinde yok. Ayarlardan tahmini açabilir veya kendi kök listenize ekleyebilirsiniz."
        else:
            kokler = []
            for k in sonuc["kokler"]:
                kokler.append(k["kok"] + (f"  ({k['kok_ar']})" if ayar["arapca_goster"] and k["kok_ar"] else ""))
            self.baslik.value = "Kök: " + " · ".join(kokler)
            self.not_.value = ("" if sonuc["yontem"] == "veritabani"
                               else "Bu sonuç harflerden tahmin edildi, kesin olmayabilir.")
            for t in sonuc["turevler"]:
                self.liste.controls.append(ft.ListTile(
                    title=ft.Text(t["kelime"]), subtitle=ft.Text(t["anlam"]),
                    trailing=ft.Icon(ft.Icons.OPEN_IN_NEW),
                    on_click=lambda ev, k=t["kelime"]: self.b.ac_lugat(k)))
        self.b.page.update()
