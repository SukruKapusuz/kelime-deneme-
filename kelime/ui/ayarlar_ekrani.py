"""Ayarlar: tema, lügat ekle/çıkar, kök tarama seçenekleri, geçmiş kaydı."""
import flet as ft

from .temalar import TEMALAR, tema_uygula


class AyarlarEkrani:
    def __init__(self, b):
        self.b = b
        v = b.ayarlar.veri
        self.tema = ft.Dropdown(label="Tema", value=v["tema"],
                                options=[ft.dropdown.Option(t) for t in TEMALAR],
                                on_change=self._tema)
        self.lugat_listesi = ft.Column(spacing=0)
        self.yeni_ad = ft.TextField(label="Lügat adı")
        self.yeni_sablon = ft.TextField(label="Adres şablonu", hint_text="https://site.com/ara?q={q}")
        self.hata = ft.Text("", color=ft.Colors.ERROR)
        k = v["kok"]
        self.s_tahmin = ft.Switch(label="Listede yoksa harflerden tahmin et", value=k["tahmin_kullan"],
                                  on_change=lambda e: self._kok("tahmin_kullan", e.control.value))
        self.s_onek = ft.Switch(label="Ön ek toleransı (mektup'taki m- gibi)", value=k["on_ek_toleransi"],
                                on_change=lambda e: self._kok("on_ek_toleransi", e.control.value))
        self.s_ar = ft.Switch(label="Kökün Arapça yazımını göster", value=k["arapca_goster"],
                              on_change=lambda e: self._kok("arapca_goster", e.control.value))
        self.maks = ft.Slider(min=10, max=200, divisions=19, value=k["en_fazla_sonuc"],
                              label="{value}", on_change_end=lambda e: self._kok("en_fazla_sonuc", int(e.control.value)))
        self.s_gecmis = ft.Switch(label="Aramaları geçmişe kaydet", value=v["gecmis_kaydet"],
                                  on_change=self._gecmis)
        self.view = ft.Column(
            [ft.Text("Ayarlar", style=ft.TextThemeStyle.HEADLINE_SMALL),
             self.tema, ft.Divider(),
             ft.Text("Lügatlar", style=ft.TextThemeStyle.TITLE_MEDIUM), self.lugat_listesi,
             self.yeni_ad, self.yeni_sablon,
             ft.ElevatedButton("Lügat ekle", icon=ft.Icons.ADD, on_click=self._ekle), self.hata,
             ft.Divider(),
             ft.Text("Kök tarama", style=ft.TextThemeStyle.TITLE_MEDIUM),
             self.s_tahmin, self.s_onek, self.s_ar,
             ft.Text("En fazla sonuç sayısı"), self.maks,
             ft.Divider(), self.s_gecmis],
            spacing=10, scroll=ft.ScrollMode.AUTO)

    def yenile(self):
        self.lugat_listesi.controls.clear()
        for l in self.b.ayarlar.veri["lugatlar"]:
            self.lugat_listesi.controls.append(ft.ListTile(
                title=ft.Text(l["ad"]), subtitle=ft.Text(l["sablon"]),
                leading=ft.Switch(value=l.get("aktif", True),
                                  on_change=lambda e, ad=l["ad"]: self._aktif(ad, e.control.value)),
                trailing=ft.IconButton(ft.Icons.DELETE, on_click=lambda e, ad=l["ad"]: self._sil(ad))))

    # --- olaylar --------------------------------------------------------
    def _tema(self, e):
        self.b.ayarlar.veri["tema"] = self.tema.value
        self.b.ayarlar.kaydet()
        tema_uygula(self.b.page, self.tema.value)

    def _kok(self, anahtar, deger):
        self.b.ayarlar.veri["kok"][anahtar] = deger
        self.b.ayarlar.kaydet()

    def _gecmis(self, e):
        self.b.ayarlar.veri["gecmis_kaydet"] = self.s_gecmis.value
        self.b.ayarlar.kaydet()

    def _hata_yaz(self, mesaj=""):
        self.hata.value = mesaj
        self.yenile()
        self.b.page.update()

    def _ekle(self, e):
        try:
            self.b.ayarlar.lugat_ekle(self.yeni_ad.value or "", self.yeni_sablon.value or "")
            self.yeni_ad.value = self.yeni_sablon.value = ""
            self._hata_yaz()
        except ValueError as ex:
            self._hata_yaz(str(ex))

    def _sil(self, ad):
        try:
            self.b.ayarlar.lugat_sil(ad)
            self._hata_yaz()
        except ValueError as ex:
            self._hata_yaz(str(ex))

    def _aktif(self, ad, deger):
        try:
            self.b.ayarlar.lugat_aktif_yap(ad, deger)
            self._hata_yaz()
        except ValueError as ex:
            self._hata_yaz(str(ex))
