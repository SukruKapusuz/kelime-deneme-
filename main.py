import copy
import json
import os
import urllib.parse
import webbrowser

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.utils import get_color_from_hex, get_hex_from_color, platform, escape_markup
from kivy.core.window import Window
from kivy.properties import ListProperty, BooleanProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.modalview import ModalView
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.logger import Logger


# ==============================================================================
# 0. TÜRKÇE HARF DÖNÜŞÜMLERİ (Python'un lower/upper fonksiyonları Türkçe için yanlış)
# ==============================================================================
def tr_kucuk(metin):
    """'İLİM' -> 'ilim', 'IŞIK' -> 'ışık'"""
    return metin.replace("İ", "i").replace("I", "ı").lower()


def tr_buyuk(metin):
    """'ilim' -> 'İLİM', 'ışık' -> 'IŞIK'"""
    return metin.replace("i", "İ").replace("ı", "I").upper()


# ==============================================================================
# I. PLATFORM UYUMLU VERİ YOLU YÖNETİMİ (PC VE ANDROID)
# ==============================================================================
def veri_dosyasi_yolu(dosya_adi):
    if platform in ('android', 'ios'):
        app = App.get_running_app()
        if app and app.user_data_dir:
            return os.path.join(app.user_data_dir, dosya_adi)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), dosya_adi)


# ==============================================================================
# II. KAYITLI KÖKLER, LÜGATLER VE GEÇMİŞ YÖNETİMİ
# ==============================================================================
VARSAYILAN_LUGATLER = [
    {"isim": "Kubbealtı Lûgatı", "url": "https://lugatim.com/s/?", "aciklama": "Tarihî sözlük ve örnek beyitler"},
    {"isim": "Türk Dil Kurumu (TDK)", "url": "https://sozluk.gov.tr/?kelime=?", "aciklama": "Güncel Türkçe Sözlük"},
    {"isim": "Nişanyan Sözlük", "url": "https://www.nisanyansozluk.com/kelime/?", "aciklama": "Çağdaş Türkçenin Etimolojisi"},
    {"isim": "Luggat Osmanlıca", "url": "https://www.luggat.com/?", "aciklama": "Osmanlıca-Türkçe Ansiklopedik Sözlük"}
]

VARSAYILAN_KOKLER = [
    {"kelime": "kitap", "kok": "K-T-B", "uyum": "Kalın"},
    {"kelime": "ilim", "kok": "İ-L-M", "uyum": "İnce"},
    {"kelime": "hüküm", "kok": "H-K-M", "uyum": "İnce"},
    {"kelime": "şükür", "kok": "Ş-K-R", "uyum": "İnce"},
    {"kelime": "mühim", "kok": "H-M-M", "uyum": "İnce"},
    {"kelime": "iştirak", "kok": "Ş-R-K", "uyum": "İnce"},
    {"kelime": "istikbal", "kok": "K-B-L", "uyum": "Kalın"},
    {"kelime": "ihtimal", "kok": "H-M-L", "uyum": "Kalın"},
    {"kelime": "nizam", "kok": "N-Z-M", "uyum": "Kalın"},
    {"kelime": "fikir", "kok": "F-K-R", "uyum": "İnce"}
]


def url_olustur(sablon, kelime):
    """Şablondaki SON '?' işaretini kelimeyle değiştirir.
    'https://sozluk.gov.tr/?kelime=?' + 'kitap' -> 'https://sozluk.gov.tr/?kelime=kitap'"""
    kodlu = urllib.parse.quote(kelime, safe="") if kelime else ""
    son = sablon.rfind("?")
    if son == -1:
        return sablon + kodlu
    return sablon[:son] + kodlu + sablon[son + 1:]


def adresi_ac(adres):
    """Adresi açar. PC'de varsayılan tarayıcı, Android'de Intent ile tarayıcı.
    Android'de webbrowser.open güvenilir çalışmadığı için ayrı yol kullanılır."""
    if platform == 'android':
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            intent = Intent(Intent.ACTION_VIEW)
            intent.setData(Uri.parse(adres))
            PythonActivity.mActivity.startActivity(intent)
        except Exception as hata:
            Logger.error(f"Lugat: adres açılamadı ({hata})")
    else:
        webbrowser.open(adres)


def json_yukle(dosya_adi, varsayilan):
    yol = veri_dosyasi_yolu(dosya_adi)
    if not os.path.exists(yol):
        return copy.deepcopy(varsayilan)
    try:
        with open(yol, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as hata:
        # Bozuk dosyayı silmeden kenara al; kullanıcı verisi kaybolmasın
        Logger.error(f"Lugat: {dosya_adi} okunamadı ({hata}), yedeğe alındı.")
        try:
            os.replace(yol, yol + ".bozuk")
        except OSError:
            pass
        return copy.deepcopy(varsayilan)


def json_kaydet(dosya_adi, veri):
    """Önce geçici dosyaya yazar, sonra değiştirir. Yazma sırasında kapanırsa eski dosya bozulmaz."""
    yol = veri_dosyasi_yolu(dosya_adi)
    gecici = yol + ".tmp"
    try:
        with open(gecici, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(gecici, yol)
        return True
    except OSError as hata:
        Logger.error(f"Lugat: {dosya_adi} kaydedilemedi: {hata}")
        return False


# ==============================================================================
# III. SARF MOTORU (KÖK DÜZENLEME DESTEKLİ)
# ==============================================================================
class SafSarfMotoru:
    def __init__(self):
        # 24 kadim vezin, klasik sıraya göre
        self.sirali_vezinler = [
            ("İsm-i Fâil (Yapan / Eden)", "{f}â{a}i{l}"),
            ("İsm-i Mef'ûl (Yapılan / Edilen)", "m{E}{f}{a}û{l}"),
            ("Mef'al (Mekân / Kavram İsmi)", "m{E}{f}{a}{E}{l}"),
            ("Mef'il (Mekân / Menzil İsmi)", "m{E}{f}{a}i{l}"),
            ("Fi'âl (Sülâsî Masdar / İsim)", "{f}i{a}â{l}"),
            ("Fi'l (Sülâsî Masdar / Kavram)", "{f}i{a}{l}"),
            ("Fu'l (Sülâsî Masdar / Durum)", "{f}{Ü}{a}{l}"),
            ("Fe'l (Sülâsî Masdar / Eylem)", "{f}{E}{a}{l}"),
            ("Fe'îl (Kalıcı Sıfat)", "{f}{E}{a}î{l}"),
            ("Ef'al (En Üstünlük / Tafdil)", "{E}{f}{E}{a}{l}"),
            ("İf'âl (Oldurma / Geçişli Masdar)", "i{f}{a}â{l}"),
            ("Müf'il (İf'âl Yapan)", "m{Ü}{f}{a}i{l}"),
            ("Tef'îl (Pekiştirme / Çoğaltma)", "t{E}{f}{a}î{l}"),
            ("Müfe'il (Tef'îl Yapan / Meslek)", "m{Ü}{f}{E}{a}i{l}"),
            ("Müfâ'ale (Karşılıklı / İşteş Eylem)", "m{Ü}{f}â{a}{E}{l}{E}"),
            ("İfti'âl (Öze Dönük Eylem)", "i{f}ti{a}â{l}"),
            ("Müfte'il (İfti'âl Yapan / Olan)", "m{Ü}{f}t{E}{a}i{l}"),
            ("İstif'âl (İsteme / Talep Masdarı)", "isti{f}{a}â{l}"),
            ("Müstef'il (İstif'âl Yapan / Olan)", "m{Ü}st{E}{f}{a}i{l}"),
            ("Fe'âlet (Nitelik / Durum Masdarı)", "{f}{E}{a}â{l}{E}t"),
            ("Fa'âl (Mübalağa / Meslek Sıfatı)", "{f}{E}{a}{a}â{l}"),
            ("İnfi'âl (Kendi Kendine / Edilgen)", "in{f}i{a}â{l}"),
            ("Münfe'il (İnfi'âl Olan)", "m{Ü}n{f}{E}{a}i{l}"),
            ("Müf'al (İf'âl Yapılan)", "m{Ü}{f}{a}{E}{l}"),
        ]

        self.sesliler = "aeıioöuüâîûê"
        self.kalin_kok_harfleri = "khsztgqr"
        self.mudhaaf_lafizlar = [
            "mühim", "ehem", "muhib", "muhik", "mukir", "müzil", "hak",
            "his", "hal", "sir", "sır", "zam", "hat", "red", "sed", "zem",
            "zül", "şek", "şer", "fen", "tıp", "rab", "hac", "haz", "had"
        ]

    @staticmethod
    def _tek_harf_mi(parca):
        return len(parca) == 1 and parca.isalpha()

    def koku_cikar(self, girdi, kayitli_kokler=None):
        k = tr_kucuk(girdi).replace("'", "").replace("’", "").strip()
        if not k:
            return None, None

        # 1. Kullanıcı "K-T-B" veya "k t b" gibi kök girdiyse: tam olarak 3 tek harf olmalı
        if "-" in k or " " in k:
            parcalar = k.replace("-", " ").split()
            if len(parcalar) == 3 and all(self._tek_harf_mi(p) for p in parcalar):
                f, a, l = parcalar
                uyum = "Kalın" if f in self.kalin_kok_harfleri else "İnce"
                return (f, a, l), uyum
            return None, None

        # 2. Kayıtlı kökler defterinde bu kelime veya kök tanımlı mı?
        if kayitli_kokler:
            for kayit in kayitli_kokler:
                kelime_k = tr_kucuk(kayit.get("kelime", ""))
                kok_k = tr_kucuk(kayit.get("kok", ""))
                if kelime_k == k or kok_k == k:
                    harfler = [h for h in kok_k.split("-") if h]
                    if len(harfler) == 3:
                        return (harfler[0], harfler[1], harfler[2]), kayit.get("uyum", "Kalın")

        # 3. Algoritmik kök ayıklama
        ham_kelime = k
        for ek in ["iyyet", "iyet", "iyye", "iye", "lik", "lık", "luk", "lük", "at", "et", "ler", "lar"]:
            if k.endswith(ek) and len(k) > len(ek) + 2:
                k = k[:-len(ek)]
                break

        if k.endswith('p'):
            k = k[:-1] + 'b'
        elif k.endswith('ç'):
            k = k[:-1] + 'c'
        elif k.endswith('t') and not k.endswith('at'):
            k = k[:-1] + 'd'

        if k in self.mudhaaf_lafizlar:
            k += k[-1]

        # Teşekkür gibi şeddeli orta harfleri sadeleştir (k-k -> k)
        sessizler_ham = [h for h in k if h not in self.sesliler and h.isalpha()]
        if k.startswith(("te", "ta", "müte", "müta")) and len(sessizler_ham) >= 5:
            temiz_sessiz = []
            for idx, s in enumerate(sessizler_ham):
                if idx > 0 and s == sessizler_ham[idx - 1]:
                    continue
                temiz_sessiz.append(s)
            sessizler = temiz_sessiz
        else:
            sessizler = sessizler_ham

        if len(sessizler) < 2:
            return None, None

        if k.startswith("ist") and len(sessizler) >= 5:
            sessizler = sessizler[2:]
        elif k.startswith(("müste", "müsta")) and len(sessizler) >= 5:
            sessizler = sessizler[3:]
        elif k.startswith(("müte", "müta")) and len(sessizler) >= 4:
            sessizler = sessizler[2:]
        elif k.startswith("mün") and len(sessizler) >= 4:
            sessizler = sessizler[2:]
        elif k.startswith("in") and len(sessizler) >= 4:
            sessizler = sessizler[1:]
        elif k.startswith(("muh", "müh", "müş", "muş")) and len(sessizler) >= 4 and "t" in sessizler:
            sessizler.remove("t")
            sessizler = sessizler[1:]
        elif k.startswith("i") and len(sessizler) >= 4 and sessizler[1] == 't':
            sessizler.pop(1)
        elif k.startswith(("mü", "mu", "ma", "me", "te", "ta", "e")) and len(sessizler) >= 4:
            sessizler = sessizler[1:]

        if len(sessizler) == 3:
            f, a, l = sessizler[0], sessizler[1], sessizler[2]
        elif len(sessizler) == 2:
            f, a, l = sessizler[0], sessizler[1], sessizler[1]
        else:
            f, a, l = sessizler[0], sessizler[1], sessizler[-1]

        vowels = [h for h in ham_kelime if h in self.sesliler]
        kalin_mi = any(h in "aıouâû" for h in vowels) or (f in self.kalin_kok_harfleri)
        uyum = "Kalın" if kalin_mi else "İnce"
        return (f, a, l), uyum

    def _fonetik_sadelestir(self, kelime_ham):
        k = tr_kucuk(kelime_ham).replace(" ", "").replace("aâ", "â").replace("eâ", "e")
        if len(k) > 2 and k[-1] == k[-2] and k[-1] not in self.sesliler:
            k = k[:-1]
        if k.startswith("i"):
            return "İ" + k[1:]
        elif k.startswith("ı"):
            return "I" + k[1:]
        return k.capitalize()

    def kokten_vezin_uret(self, f, a, l, uyum="Kalın"):
        f, a, l = tr_kucuk(f).strip(), tr_kucuk(a).strip(), tr_kucuk(l).strip()
        if not (f and a and l):
            return None

        E, Ü = ('a', 'u') if uyum == 'Kalın' else ('e', 'ü')
        ciktilar = []

        for vezin_adi, kalip in self.sirali_vezinler:
            aktif_kalip = kalip
            if uyum == 'İnce':
                aktif_kalip = aktif_kalip.replace("â", E)

            # Şeddeli (mudaaf) köklerde idgam uyarlaması
            if a == l:
                if "İsm-i Fâil" in vezin_adi:
                    aktif_kalip = "{f}â{a}{l}"
                elif "Mef'al" in vezin_adi:
                    aktif_kalip = "m{E}{f}{E}{a}{l}"
                elif "Müf'il" in vezin_adi:
                    aktif_kalip = "m{Ü}{f}i{a}{l}"
                elif "Ef'al" in vezin_adi:
                    aktif_kalip = "{E}{f}{E}{a}{l}"

            ham_sonuc = aktif_kalip.format(f=f, a=a, l=l, E=E, Ü=Ü)
            duzgun_sonuc = self._fonetik_sadelestir(ham_sonuc)

            if duzgun_sonuc.endswith('b'):
                duzgun_sonuc = f"{duzgun_sonuc[:-1]}p ({duzgun_sonuc})"
            elif duzgun_sonuc.endswith('d'):
                duzgun_sonuc = f"{duzgun_sonuc[:-1]}t ({duzgun_sonuc})"
            elif duzgun_sonuc.endswith('c'):
                duzgun_sonuc = f"{duzgun_sonuc[:-1]}ç ({duzgun_sonuc})"

            ciktilar.append({"vezin": vezin_adi, "kelime": duzgun_sonuc})

        return {
            "f": tr_buyuk(f),
            "a": tr_buyuk(a),
            "l": tr_buyuk(l),
            "kok": f"{tr_buyuk(f)}-{tr_buyuk(a)}-{tr_buyuk(l)}",
            "uyum": uyum,
            "turevler": ciktilar
        }


sarf_motoru = SafSarfMotoru()


# ==============================================================================
# IV. KIVY GÖRSEL BİLEŞENLER VE TASARIM DİLİ
# ==============================================================================
class YuvarlakButon(ButtonBehavior, Label):
    bg_color = ListProperty([0.1, 0.4, 0.5, 1])
    radius_val = NumericProperty(dp(8))


class CerceveliKart(YuvarlakButon):
    cerceve_color = ListProperty([0.3, 0.3, 0.3, 1])


class ZarifInput(TextInput):
    pass


class AnaArayuz(BoxLayout):
    pass


KV_TASARIM = '''
<YuvarlakButon>:
    halign: 'center'
    valign: 'middle'
    text_size: self.size
    padding: dp(8), dp(4)
    canvas.before:
        Color:
            rgba: self.bg_color if self.state == 'normal' else (self.bg_color[0]*0.75, self.bg_color[1]*0.75, self.bg_color[2]*0.75, self.bg_color[3])
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.radius_val]

<CerceveliKart>:
    halign: 'center'
    valign: 'middle'
    text_size: self.size
    padding: dp(12), dp(8)
    canvas.after:
        Color:
            rgba: self.cerceve_color
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, self.radius_val)
            width: dp(1.1)

<ZarifInput>:
    background_normal: ''
    background_active: ''
    background_color: app.card_bg_color
    foreground_color: app.yazi_color
    hint_text_color: app.alt_yazi_color
    cursor_color: app.vurgu_color
    padding: [dp(12), dp(12), dp(12), dp(10)]
    canvas.after:
        Color:
            rgba: app.vurgu_color if self.focus else app.cerceve_color
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(8))
            width: dp(1.2)

<AnaArayuz>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: app.bg_color
        Rectangle:
            pos: self.pos
            size: self.size

    # ÜST SEKMELER (4 ANA BÖLÜM)
    BoxLayout:
        size_hint_y: None
        height: dp(54)
        canvas.before:
            Color:
                rgba: app.card_bg_color
            Rectangle:
                pos: self.pos
                size: self.size
            Color:
                rgba: app.cerceve_color
            Line:
                points: [self.x, self.y, self.right, self.y]
                width: dp(1)

        YuvarlakButon:
            text: "Lügat Arama"
            font_size: '14sp'
            bg_color: app.vurgu_color if sm.current == 'mana' else app.card_bg_color
            color: (1,1,1,1) if sm.current == 'mana' else app.yazi_color
            bold: True
            radius_val: 0
            on_release: sm.current = 'mana'
        YuvarlakButon:
            text: "Kök Tarama"
            font_size: '14sp'
            bg_color: app.vurgu_color if sm.current == 'kok' else app.card_bg_color
            color: (1,1,1,1) if sm.current == 'kok' else app.yazi_color
            bold: True
            radius_val: 0
            on_release: sm.current = 'kok'
        YuvarlakButon:
            text: "Geçmiş"
            font_size: '14sp'
            bg_color: app.vurgu_color if sm.current == 'gecmis' else app.card_bg_color
            color: (1,1,1,1) if sm.current == 'gecmis' else app.yazi_color
            bold: True
            radius_val: 0
            on_release:
                sm.current = 'gecmis'
                app.gecmisi_ciz()
        YuvarlakButon:
            text: "Ayarlar"
            font_size: '14sp'
            bg_color: app.vurgu_color if sm.current == 'ayarlar' else app.card_bg_color
            color: (1,1,1,1) if sm.current == 'ayarlar' else app.yazi_color
            bold: True
            radius_val: 0
            on_release: sm.current = 'ayarlar'

    ScreenManager:
        id: sm

        # 1. SEKME: LÜGAT ARAMA
        Screen:
            name: 'mana'
            BoxLayout:
                orientation: 'vertical'
                padding: dp(14)
                spacing: dp(12)

                YuvarlakButon:
                    id: serit_donus
                    text: "← Kök Taramasına Geri Dön"
                    size_hint_y: None
                    height: dp(38) if app.kokten_gelindi else dp(0)
                    bg_color: app.zumrut_color
                    color: (1,1,1,1)
                    bold: True
                    opacity: 1 if app.kokten_gelindi else 0
                    disabled: not app.kokten_gelindi
                    on_release: app.kok_taramasina_don()

                BoxLayout:
                    size_hint_y: None
                    height: dp(48)
                    spacing: dp(10)
                    ZarifInput:
                        id: txt_mana
                        hint_text: "Aranacak kelimeyi yazın..."
                        multiline: False
                        font_size: '16sp'
                        on_text_validate: app.ilk_lugate_git(self.text)
                    YuvarlakButon:
                        text: "Ara"
                        size_hint_x: 0.28
                        bg_color: app.vurgu_color
                        color: (1,1,1,1)
                        bold: True
                        on_release: app.ilk_lugate_git(txt_mana.text)

                Label:
                    text: "Kelimeyi aratmak istediğiniz sözlüğe dokunun:"
                    font_size: '13sp'
                    color: app.alt_yazi_color
                    size_hint_y: None
                    height: dp(22)
                    text_size: self.size
                    halign: 'left'
                    valign: 'middle'

                ScrollView:
                    BoxLayout:
                        id: menba_listesi_mana
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(10)

        # 2. SEKME: KÖK TARAMA VE DÜZENLEME
        Screen:
            name: 'kok'
            BoxLayout:
                orientation: 'vertical'
                padding: dp(14)
                spacing: dp(10)

                BoxLayout:
                    size_hint_y: None
                    height: dp(48)
                    spacing: dp(8)
                    ZarifInput:
                        id: txt_kok
                        hint_text: "Kelime veya kök yazın (örn: mektup, K-T-B)..."
                        multiline: False
                        font_size: '15sp'
                        on_text_validate: app.sulasi_tara(self.text)
                    YuvarlakButon:
                        text: "Türet"
                        size_hint_x: 0.26
                        bg_color: app.vurgu_color
                        color: (1,1,1,1)
                        bold: True
                        on_release: app.sulasi_tara(txt_kok.text)

                # HAZIR VE KAYITLI KÖKLER ŞERİDİ
                BoxLayout:
                    size_hint_y: None
                    height: dp(36)
                    spacing: dp(6)
                    Label:
                        text: "Hazır Kökler:"
                        size_hint_x: None
                        width: dp(85)
                        font_size: '12sp'
                        bold: True
                        color: app.alt_yazi_color
                        text_size: self.size
                        halign: 'left'
                        valign: 'middle'
                    ScrollView:
                        do_scroll_x: True
                        do_scroll_y: False
                        BoxLayout:
                            id: hazir_kokler_kutusu
                            orientation: 'horizontal'
                            size_hint_x: None
                            width: self.minimum_width
                            spacing: dp(6)

                # SONUÇLAR VE KÖK MÜDAHALE ALANI
                ScrollView:
                    BoxLayout:
                        id: sarf_sonuclari
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(10)

        # 3. SEKME: GEÇMİŞ
        Screen:
            name: 'gecmis'
            BoxLayout:
                orientation: 'vertical'
                padding: dp(14)
                spacing: dp(12)

                BoxLayout:
                    size_hint_y: None
                    height: dp(40)
                    Label:
                        text: "Son Aramalar ve Kök Tahlilleri"
                        font_size: '16sp'
                        bold: True
                        color: app.vurgu_color
                        text_size: self.size
                        halign: 'left'
                        valign: 'middle'
                    YuvarlakButon:
                        text: "Geçmişi Temizle"
                        size_hint_x: None
                        width: dp(130)
                        bg_color: (0.75, 0.22, 0.22, 1)
                        color: (1,1,1,1)
                        font_size: '13sp'
                        bold: True
                        on_release: app.gecmisi_temizle()

                ScrollView:
                    BoxLayout:
                        id: gecmis_listesi
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(8)

        # 4. SEKME: AYARLAR
        Screen:
            name: 'ayarlar'
            ScrollView:
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    padding: dp(14)
                    spacing: dp(14)

                    Label:
                        text: "Görünüm ve Temalar"
                        font_size: '16sp'
                        bold: True
                        color: app.vurgu_color
                        size_hint_y: None
                        height: dp(28)
                        text_size: self.size
                        halign: 'left'
                        valign: 'middle'

                    GridLayout:
                        cols: 2
                        size_hint_y: None
                        height: dp(145)
                        spacing: dp(8)
                        YuvarlakButon:
                            text: "Harman (Koyu Varsayılan)"
                            bg_color: app.vurgu_color
                            color: (1,1,1,1)
                            font_size: '13sp'
                            on_release: app.tema_degistir('harman')
                        YuvarlakButon:
                            text: "Gece Modu (Siyah)"
                            bg_color: app.vurgu_color
                            color: (1,1,1,1)
                            font_size: '13sp'
                            on_release: app.tema_degistir('gece')
                        YuvarlakButon:
                            text: "Çuha Yeşili (Koyu)"
                            bg_color: app.vurgu_color
                            color: (1,1,1,1)
                            font_size: '13sp'
                            on_release: app.tema_degistir('cuha')
                        YuvarlakButon:
                            text: "Kâşî Mavisi (Açık)"
                            bg_color: app.vurgu_color
                            color: (1,1,1,1)
                            font_size: '13sp'
                            on_release: app.tema_degistir('kasi')
                        YuvarlakButon:
                            text: "Gündüz Modu (Açık)"
                            bg_color: app.vurgu_color
                            color: (1,1,1,1)
                            font_size: '13sp'
                            on_release: app.tema_degistir('gunduz')

                    Label:
                        text: "Kayıtlı Kökler Yönetimi"
                        font_size: '16sp'
                        bold: True
                        color: app.vurgu_color
                        size_hint_y: None
                        height: dp(28)
                        text_size: self.size
                        halign: 'left'
                        valign: 'middle'

                    YuvarlakButon:
                        text: "+ Yeni Kök / Kelime Ekle"
                        size_hint_y: None
                        height: dp(44)
                        bg_color: app.zumrut_color
                        color: (1,1,1,1)
                        bold: True
                        on_release: app.yeni_kok_penceresi_ac()

                    BoxLayout:
                        id: ayar_kok_listesi
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(8)

                    Label:
                        text: "Kayıtlı Lügatler ve Sözlük Yönetimi"
                        font_size: '16sp'
                        bold: True
                        color: app.vurgu_color
                        size_hint_y: None
                        height: dp(28)
                        text_size: self.size
                        halign: 'left'
                        valign: 'middle'

                    YuvarlakButon:
                        text: "+ Yeni Lügat Ekle"
                        size_hint_y: None
                        height: dp(44)
                        bg_color: app.vurgu_color
                        color: (1,1,1,1)
                        bold: True
                        on_release: app.yeni_lugat_penceresi_ac()

                    BoxLayout:
                        id: ayar_menba_listesi
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(8)
'''

TEMALAR = {
    "harman": {"bg": "#1A221E", "card": "#242F2A", "yazi": "#EDE7D9", "alt_yazi": "#95A59B", "vurgu": "#007A87", "cerceve": "#36453E", "zumrut": "#52B788"},
    "gece": {"bg": "#141618", "card": "#202327", "yazi": "#EAE6DF", "alt_yazi": "#9E9E9E", "vurgu": "#4A90E2", "cerceve": "#33383B", "zumrut": "#2ECC71"},
    "cuha": {"bg": "#1A221E", "card": "#242F2A", "yazi": "#EDE7D9", "alt_yazi": "#95A59B", "vurgu": "#C5A059", "cerceve": "#36453E", "zumrut": "#52B788"},
    "kasi": {"bg": "#F2F5F6", "card": "#FFFFFF", "yazi": "#1A252C", "alt_yazi": "#5C717E", "vurgu": "#007A87", "cerceve": "#D0DCE0", "zumrut": "#008B74"},
    "gunduz": {"bg": "#F8F6F0", "card": "#FFFFFF", "yazi": "#22252A", "alt_yazi": "#636E72", "vurgu": "#1E3A5F", "cerceve": "#E0DBD1", "zumrut": "#1D7A5C"}
}


# ==============================================================================
# V. ANA UYGULAMA SINIFI VE İŞLEVLER
# ==============================================================================
class LugatApp(App):
    title = "Lugat"
    bg_color = ListProperty([0.1, 0.13, 0.11, 1])
    card_bg_color = ListProperty([0.14, 0.18, 0.16, 1])
    yazi_color = ListProperty([0.92, 0.9, 0.85, 1])
    alt_yazi_color = ListProperty([0.58, 0.64, 0.6, 1])
    vurgu_color = ListProperty([0, 0.47, 0.52, 1])
    cerceve_color = ListProperty([0.21, 0.27, 0.24, 1])
    zumrut_color = ListProperty([0.32, 0.71, 0.53, 1])
    kokten_gelindi = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._guncel_netice = {}      # her örnekte ayrı sözlük

    def build(self):
        Builder.load_string(KV_TASARIM)
        self.root = AnaArayuz()
        self.tema_degistir("harman")
        Clock.schedule_once(lambda dt: self._baslangic_hazirligi(), 0.15)
        return self.root

    def _baslangic_hazirligi(self):
        if hasattr(self, 'root') and self.root:
            self.lugatleri_ciz()
            self.hazir_kokleri_ciz()
            self.gecmisi_ciz()
            self.sulasi_tara("kitap", gecmise_ekle=False)

    def tema_degistir(self, kod):
        t = TEMALAR.get(kod, TEMALAR["harman"])
        self.bg_color = get_color_from_hex(t["bg"])
        self.card_bg_color = get_color_from_hex(t["card"])
        self.yazi_color = get_color_from_hex(t["yazi"])
        self.alt_yazi_color = get_color_from_hex(t["alt_yazi"])
        self.vurgu_color = get_color_from_hex(t["vurgu"])
        self.cerceve_color = get_color_from_hex(t["cerceve"])
        self.zumrut_color = get_color_from_hex(t["zumrut"])

        if hasattr(self, 'root') and self.root and 'menba_listesi_mana' in self.root.ids:
            self.lugatleri_ciz()
            self.hazir_kokleri_ciz()
            self.gecmisi_ciz()            # geçmiş kartları da yeni renklerle yeniden çizilsin
            if self._guncel_netice:
                self._sarf_sonuclarini_ciz()

    # --------------------------------------------------------------------------
    # GEÇMİŞ YÖNETİMİ
    # --------------------------------------------------------------------------
    def gecmise_kaydet(self, tur, sorgu, detay=""):
        sorgu = sorgu.strip()
        if not sorgu:
            return
        gecmis = json_yukle("gecmis.json", [])
        yeni_kayit = {"tur": tur, "sorgu": sorgu, "detay": detay}
        gecmis = [g for g in gecmis
                  if not (g.get("tur") == tur and tr_kucuk(g.get("sorgu", "")) == tr_kucuk(sorgu))]
        gecmis.insert(0, yeni_kayit)
        json_kaydet("gecmis.json", gecmis[:50])

    def gecmisi_ciz(self):
        if not self.root or 'gecmis_listesi' not in self.root.ids:
            return
        g_box = self.root.ids.gecmis_listesi
        g_box.clear_widgets()
        gecmis = json_yukle("gecmis.json", [])
        alt_hex = get_hex_from_color(self.alt_yazi_color)

        if not gecmis:
            g_box.add_widget(Label(
                text="Henüz arama veya kök tahlili geçmişi bulunmuyor.",
                color=self.alt_yazi_color, size_hint_y=None, height=dp(50)
            ))
            return

        for kayit in gecmis:
            tur = escape_markup(kayit.get("tur", "Kök"))
            sorgu = escape_markup(kayit.get("sorgu", ""))
            detay = escape_markup(kayit.get("detay", ""))
            etiket = f"[b]{sorgu}[/b]  ({detay})" if detay else f"[b]{sorgu}[/b]"

            btn = Factory.CerceveliKart(
                text=f"[size=12][color={alt_hex}]{tur} İşlemi[/color][/size]\n[size=15]{etiket}[/size]",
                markup=True,
                size_hint_y=None, height=dp(62),
                bg_color=self.card_bg_color,
                color=self.yazi_color,
                cerceve_color=self.cerceve_color
            )
            btn.bind(on_release=lambda b, k=kayit: self.gecmis_kaydini_ac(k))
            g_box.add_widget(btn)

    def gecmis_kaydini_ac(self, kayit):
        if kayit.get("tur") == "Lügat":
            self.root.ids.txt_mana.text = kayit.get("sorgu", "")
            self.root.ids.sm.current = 'mana'
        else:
            self.root.ids.txt_kok.text = kayit.get("sorgu", "")
            self.root.ids.sm.current = 'kok'
            self.sulasi_tara(kayit.get("sorgu", ""), gecmise_ekle=False)

    def gecmisi_temizle(self):
        json_kaydet("gecmis.json", [])
        self.gecmisi_ciz()

    # --------------------------------------------------------------------------
    # LÜGAT (SÖZLÜK) YÖNETİMİ VE ARAMA
    # --------------------------------------------------------------------------
    def lugatleri_ciz(self):
        if not self.root or 'menba_listesi_mana' not in self.root.ids:
            return

        m_list = self.root.ids.menba_listesi_mana
        m_list.clear_widgets()
        lugatler = json_yukle("siteler.json", VARSAYILAN_LUGATLER)
        alt_hex = get_hex_from_color(self.alt_yazi_color)

        for m in lugatler:
            btn = Factory.CerceveliKart(
                text=(f"[size=16][b]{escape_markup(m['isim'])}[/b][/size]\n"
                      f"[size=12][color={alt_hex}]{escape_markup(m.get('aciklama', ''))}[/color][/size]"),
                markup=True,
                size_hint_y=None, height=dp(68),
                bg_color=self.card_bg_color,
                color=self.yazi_color,
                cerceve_color=self.cerceve_color
            )
            btn.bind(on_release=lambda b, url=m['url'], isim=m['isim']: self.url_ac(url, isim))
            m_list.add_widget(btn)

        a_list = self.root.ids.ayar_menba_listesi
        a_list.clear_widgets()
        for idx, m in enumerate(lugatler):
            box = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
            lbl = Label(
                text=(f"[b]{escape_markup(m['isim'])}[/b]\n"
                      f"[size=11][color={alt_hex}]{escape_markup(m['url'])}[/color][/size]"),
                markup=True, color=self.yazi_color, halign='left', valign='middle'
            )
            lbl.bind(size=lbl.setter('text_size'))
            btn_sil = Factory.YuvarlakButon(
                text="Sil", size_hint_x=None, width=dp(70),
                bg_color=[0.8, 0.22, 0.22, 1], color=(1, 1, 1, 1), bold=True
            )
            btn_sil.bind(on_release=lambda b, i=idx: self.lugat_sil(i))
            box.add_widget(lbl)
            box.add_widget(btn_sil)
            a_list.add_widget(box)

    def url_ac(self, url_kalibi, lugat_ismi="Sözlük"):
        if 'txt_mana' not in self.root.ids:
            return
        kelime = self.root.ids.txt_mana.text.strip()
        if kelime:
            self.gecmise_kaydet("Lügat", kelime, lugat_ismi)
        adresi_ac(url_olustur(url_kalibi, kelime))

    def ilk_lugate_git(self, kelime=""):
        if not kelime and 'txt_mana' in self.root.ids:
            kelime = self.root.ids.txt_mana.text.strip()
        lugatler = json_yukle("siteler.json", VARSAYILAN_LUGATLER)
        if kelime and lugatler:
            self.url_ac(lugatler[0]["url"], lugatler[0]["isim"])

    def kelimeyi_manaya_naklet(self, hedef_kelime):
        temiz = hedef_kelime.split("(")[0].strip()
        self.root.ids.txt_mana.text = temiz
        self.kokten_gelindi = True
        self.root.ids.sm.current = 'mana'

    def kok_taramasina_don(self):
        self.kokten_gelindi = False
        self.root.ids.sm.current = 'kok'

    def lugat_sil(self, index):
        lugatler = json_yukle("siteler.json", VARSAYILAN_LUGATLER)
        if 0 <= index < len(lugatler):
            lugatler.pop(index)
            json_kaydet("siteler.json", lugatler)
            self.lugatleri_ciz()

    def yeni_lugat_penceresi_ac(self):
        modal = ModalView(size_hint=(0.92, None), height=dp(360), background_color=[0, 0, 0, 0.7])
        ana_kutu = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))

        with ana_kutu.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*self.bg_color)
            rect = RoundedRectangle(pos=ana_kutu.pos, size=ana_kutu.size, radius=[dp(12)])
        ana_kutu.bind(pos=lambda inst, val: setattr(rect, 'pos', val),
                      size=lambda inst, val: setattr(rect, 'size', val))

        baslik = Label(
            text="[b]Yeni Lügat (Sözlük) Ekle[/b]", markup=True,
            font_size='16sp', color=self.vurgu_color, size_hint_y=None, height=dp(30)
        )
        aciklama_bilgi = Label(
            text="İpucu: Adreste kelimenin yazılacağı yere son ? işaretini koyun.\nÖrn: https://lugatim.com/s/?",
            font_size='12sp', color=self.alt_yazi_color, size_hint_y=None, height=dp(38),
            halign='center', valign='middle'
        )
        aciklama_bilgi.bind(size=aciklama_bilgi.setter('text_size'))

        inp_isim = ZarifInput(hint_text="Lügat Adı (Örn: Kubbealtı Lûgatı)", multiline=False, size_hint_y=None, height=dp(44))
        inp_aciklama = ZarifInput(hint_text="Açıklama (Örn: Etimolojik sözlük)", multiline=False, size_hint_y=None, height=dp(44))
        inp_url = ZarifInput(hint_text="Arama URL (Örn: https://ornek.com/ara?q=?)", multiline=False, size_hint_y=None, height=dp(44))

        buton_kutu = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        btn_iptal = YuvarlakButon(text="İptal", bg_color=self.cerceve_color, color=self.yazi_color, bold=True)
        btn_kaydet = YuvarlakButon(text="Kaydet", bg_color=self.zumrut_color, color=(1, 1, 1, 1), bold=True)

        def kaydet_islem(*args):
            isim = inp_isim.text.strip()
            url = inp_url.text.strip()
            if isim and url:
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                lugatler = json_yukle("siteler.json", VARSAYILAN_LUGATLER)
                lugatler.append({
                    "isim": isim,
                    "aciklama": inp_aciklama.text.strip() or "Özel eklenen sözlük",
                    "url": url
                })
                json_kaydet("siteler.json", lugatler)
                self.lugatleri_ciz()
                modal.dismiss()

        btn_iptal.bind(on_release=modal.dismiss)
        btn_kaydet.bind(on_release=kaydet_islem)

        buton_kutu.add_widget(btn_iptal)
        buton_kutu.add_widget(btn_kaydet)

        ana_kutu.add_widget(baslik)
        ana_kutu.add_widget(aciklama_bilgi)
        ana_kutu.add_widget(inp_isim)
        ana_kutu.add_widget(inp_aciklama)
        ana_kutu.add_widget(inp_url)
        ana_kutu.add_widget(buton_kutu)

        modal.add_widget(ana_kutu)
        modal.open()

    # --------------------------------------------------------------------------
    # HAZIR KÖKLER, KÖK DÜZENLEME VE SARF TÜRETME
    # --------------------------------------------------------------------------
    def hazir_kokleri_ciz(self):
        if not self.root or 'hazir_kokler_kutusu' not in self.root.ids:
            return
        kutu = self.root.ids.hazir_kokler_kutusu
        kutu.clear_widgets()
        kokler = json_yukle("kokler.json", VARSAYILAN_KOKLER)

        for k in kokler:
            etiket = f"{k['kok']} ({k['kelime'].capitalize()})"
            btn = Factory.YuvarlakButon(
                text=etiket,
                size_hint_x=None,
                width=dp(len(etiket) * 8 + 18),
                bg_color=self.card_bg_color,
                color=self.zumrut_color,
                font_size='12sp',
                bold=True,
                radius_val=dp(6)
            )
            btn.bind(on_release=lambda b, klm=k['kelime']: self.hazir_kok_sec(klm))
            kutu.add_widget(btn)

        if 'ayar_kok_listesi' in self.root.ids:
            ayar_kutu = self.root.ids.ayar_kok_listesi
            ayar_kutu.clear_widgets()
            for idx, k in enumerate(kokler):
                satir = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
                lbl = Label(
                    text=(f"[b]{escape_markup(k['kok'])}[/b]  -  "
                          f"{escape_markup(k['kelime'].capitalize())} ({escape_markup(k.get('uyum', 'Kalın'))})"),
                    markup=True, color=self.yazi_color, halign='left', valign='middle'
                )
                lbl.bind(size=lbl.setter('text_size'))
                btn_sil = Factory.YuvarlakButon(
                    text="Sil", size_hint_x=None, width=dp(65),
                    bg_color=[0.8, 0.22, 0.22, 1], color=(1, 1, 1, 1), font_size='12sp', bold=True
                )
                btn_sil.bind(on_release=lambda b, i=idx: self.kok_sil(i))
                satir.add_widget(lbl)
                satir.add_widget(btn_sil)
                ayar_kutu.add_widget(satir)

    def hazir_kok_sec(self, kelime):
        self.root.ids.txt_kok.text = kelime
        self.sulasi_tara(kelime)

    def kok_sil(self, index):
        kokler = json_yukle("kokler.json", VARSAYILAN_KOKLER)
        if 0 <= index < len(kokler):
            kokler.pop(index)
            json_kaydet("kokler.json", kokler)
            self.hazir_kokleri_ciz()

    def kok_kaydet_veya_guncelle(self, kelime, f, a, l, uyum):
        f, a, l = f.strip(), a.strip(), l.strip()
        if not all(SafSarfMotoru._tek_harf_mi(h) for h in (f, a, l)):
            return
        kok_str = f"{tr_buyuk(f)}-{tr_buyuk(a)}-{tr_buyuk(l)}"
        kelime_temiz = tr_kucuk(kelime.strip()) or tr_kucuk(kok_str)

        kokler = json_yukle("kokler.json", VARSAYILAN_KOKLER)
        guncellendi = False
        for k in kokler:
            if tr_kucuk(k["kelime"]) == kelime_temiz or k["kok"] == kok_str:
                k["kelime"] = kelime_temiz
                k["kok"] = kok_str
                k["uyum"] = uyum
                guncellendi = True
                break
        if not guncellendi:
            kokler.insert(0, {"kelime": kelime_temiz, "kok": kok_str, "uyum": uyum})

        json_kaydet("kokler.json", kokler)
        self.hazir_kokleri_ciz()
        self.dogrudan_koku_sarf_et(f, a, l, uyum)

    def yeni_kok_penceresi_ac(self):
        modal = ModalView(size_hint=(0.92, None), height=dp(370), background_color=[0, 0, 0, 0.7])
        ana_kutu = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))

        with ana_kutu.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*self.bg_color)
            rect = RoundedRectangle(pos=ana_kutu.pos, size=ana_kutu.size, radius=[dp(12)])
        ana_kutu.bind(pos=lambda inst, val: setattr(rect, 'pos', val),
                      size=lambda inst, val: setattr(rect, 'size', val))

        baslik = Label(
            text="[b]Yeni Kök veya Kelime Tanımla[/b]", markup=True,
            font_size='16sp', color=self.zumrut_color, size_hint_y=None, height=dp(30)
        )
        inp_kelime = ZarifInput(hint_text="Örnek Kelime (Örn: miras, mekan, selam)", multiline=False, size_hint_y=None, height=dp(44))
        inp_kok = ZarifInput(hint_text="3 Kök Harfi (Örn: V-R-S veya K-V-N)", multiline=False, size_hint_y=None, height=dp(44))
        hata = Label(text="", color=[0.9, 0.3, 0.3, 1], font_size='12sp', size_hint_y=None, height=dp(20))

        uyum_secim = {"deger": "Kalın"}
        btn_uyum = YuvarlakButon(
            text="Ses Uyumu: Kalın (Dokun Değiştir)", size_hint_y=None, height=dp(40),
            bg_color=self.card_bg_color, color=self.vurgu_color, bold=True
        )

        def uyum_degistir(*args):
            uyum_secim["deger"] = "İnce" if uyum_secim["deger"] == "Kalın" else "Kalın"
            btn_uyum.text = f"Ses Uyumu: {uyum_secim['deger']} (Dokun Değiştir)"

        btn_uyum.bind(on_release=uyum_degistir)

        buton_kutu = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        btn_iptal = YuvarlakButon(text="İptal", bg_color=self.cerceve_color, color=self.yazi_color, bold=True)
        btn_kaydet = YuvarlakButon(text="Kaydet", bg_color=self.zumrut_color, color=(1, 1, 1, 1), bold=True)

        def kaydet_kok(*args):
            ham = inp_kok.text.strip().replace("-", " ")
            harfler = ham.split()
            if len(harfler) != 3 and len(inp_kok.text.strip()) == 3:
                harfler = list(inp_kok.text.strip())
            if len(harfler) == 3 and all(SafSarfMotoru._tek_harf_mi(h) for h in harfler):
                self.kok_kaydet_veya_guncelle(
                    inp_kelime.text.strip() or "-".join(harfler),
                    harfler[0], harfler[1], harfler[2],
                    uyum_secim["deger"]
                )
                modal.dismiss()
            else:
                hata.text = "Kök 3 tek harften oluşmalı (örn: K-T-B)."

        btn_iptal.bind(on_release=modal.dismiss)
        btn_kaydet.bind(on_release=kaydet_kok)
        buton_kutu.add_widget(btn_iptal)
        buton_kutu.add_widget(btn_kaydet)

        ana_kutu.add_widget(baslik)
        ana_kutu.add_widget(inp_kelime)
        ana_kutu.add_widget(inp_kok)
        ana_kutu.add_widget(hata)
        ana_kutu.add_widget(btn_uyum)
        ana_kutu.add_widget(buton_kutu)

        modal.add_widget(ana_kutu)
        modal.open()

    def sulasi_tara(self, kelime="", gecmise_ekle=True):
        if not kelime and 'txt_kok' in self.root.ids:
            kelime = self.root.ids.txt_kok.text.strip()
        if not kelime:
            return

        kayitli_kokler = json_yukle("kokler.json", VARSAYILAN_KOKLER)
        kok_harfleri, uyum = sarf_motoru.koku_cikar(kelime, kayitli_kokler)

        if not kok_harfleri:
            sonuc_box = self.root.ids.sarf_sonuclari
            sonuc_box.clear_widgets()
            sonuc_box.add_widget(Label(
                text="Sülâsî kök tespit edilemedi. Lütfen 3 harfli kök girin (örn: K-T-B).",
                color=[0.9, 0.3, 0.3, 1], size_hint_y=None, height=dp(45)
            ))
            return

        f, a, l = kok_harfleri
        netice = sarf_motoru.kokten_vezin_uret(f, a, l, uyum)
        self._guncel_netice = netice
        if gecmise_ekle:
            self.gecmise_kaydet("Kök", kelime, netice["kok"])
        self._sarf_sonuclarini_ciz()

    def dogrudan_koku_sarf_et(self, f, a, l, uyum):
        harfler = [tr_kucuk(x).strip() for x in (f, a, l)]
        if not all(SafSarfMotoru._tek_harf_mi(h) for h in harfler):
            return
        netice = sarf_motoru.kokten_vezin_uret(harfler[0], harfler[1], harfler[2], uyum)
        if netice:
            self._guncel_netice = netice
            self._sarf_sonuclarini_ciz()

    def _sarf_sonuclarini_ciz(self):
        if 'sarf_sonuclari' not in self.root.ids or not self._guncel_netice:
            return
        sonuc_box = self.root.ids.sarf_sonuclari
        sonuc_box.clear_widgets()
        netice = self._guncel_netice

        # DÜZENLENEBİLİR KÖK PANELİ
        duzen_kutu = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(96), spacing=dp(6))
        ust_bilgi = Label(
            text=f"[b]Kök Harfleri: {escape_markup(netice['kok'])}[/b]  (Harfleri değiştirip yeniden türetebilirsiniz)",
            markup=True, font_size='13sp', color=self.zumrut_color, size_hint_y=None, height=dp(24)
        )

        harf_satiri = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        inp_f = ZarifInput(text=netice["f"], multiline=False, halign='center', font_size='16sp', size_hint_x=0.16)
        inp_a = ZarifInput(text=netice["a"], multiline=False, halign='center', font_size='16sp', size_hint_x=0.16)
        inp_l = ZarifInput(text=netice["l"], multiline=False, halign='center', font_size='16sp', size_hint_x=0.16)

        aktif_uyum = {"deger": netice["uyum"]}
        btn_ahenk = YuvarlakButon(
            text=aktif_uyum["deger"], size_hint_x=0.22,
            bg_color=self.card_bg_color, color=self.yazi_color, font_size='13sp', bold=True
        )

        def ahenk_degis(*args):
            aktif_uyum["deger"] = "İnce" if aktif_uyum["deger"] == "Kalın" else "Kalın"
            btn_ahenk.text = aktif_uyum["deger"]
            self.dogrudan_koku_sarf_et(inp_f.text, inp_a.text, inp_l.text, aktif_uyum["deger"])

        btn_ahenk.bind(on_release=ahenk_degis)

        btn_yenile = YuvarlakButon(
            text="Yenile", size_hint_x=0.22,
            bg_color=self.vurgu_color, color=(1, 1, 1, 1), font_size='13sp', bold=True
        )
        btn_yenile.bind(on_release=lambda *a: self.dogrudan_koku_sarf_et(
            inp_f.text, inp_a.text, inp_l.text, aktif_uyum["deger"]))

        btn_kaydet = YuvarlakButon(
            text="Kaydet", size_hint_x=0.22,
            bg_color=self.zumrut_color, color=(1, 1, 1, 1), font_size='13sp', bold=True
        )
        btn_kaydet.bind(on_release=lambda *a: self.kok_kaydet_veya_guncelle(
            self.root.ids.txt_kok.text, inp_f.text, inp_a.text, inp_l.text, aktif_uyum["deger"]
        ))

        harf_satiri.add_widget(inp_f)
        harf_satiri.add_widget(inp_a)
        harf_satiri.add_widget(inp_l)
        harf_satiri.add_widget(btn_ahenk)
        harf_satiri.add_widget(btn_yenile)
        harf_satiri.add_widget(btn_kaydet)

        duzen_kutu.add_widget(ust_bilgi)
        duzen_kutu.add_widget(harf_satiri)
        sonuc_box.add_widget(duzen_kutu)

        # TÜM VEZİNLER (sıklık etiketi yok, klasik sırayla)
        alt_hex = get_hex_from_color(self.alt_yazi_color)

        for kalip_bilgi in netice["turevler"]:
            vezin = escape_markup(kalip_bilgi["vezin"])
            uretilen = escape_markup(kalip_bilgi["kelime"])

            btn = Factory.CerceveliKart(
                text=f"[size=12][color={alt_hex}]{vezin}[/color][/size]\n[size=17][b]{uretilen}[/b][/size]",
                markup=True,
                size_hint_y=None, height=dp(70),
                bg_color=self.card_bg_color,
                color=self.yazi_color,
                cerceve_color=self.cerceve_color
            )
            btn.bind(on_release=lambda b, w=kalip_bilgi["kelime"]: self.kelimeyi_manaya_naklet(w))
            sonuc_box.add_widget(btn)


if __name__ == '__main__':
    # Sadece bilgisayar ortamında pencere boyutunu sabitle; Android'de tam ekran çalışsın
    if platform not in ('android', 'ios'):
        Window.size = (420, 760)
    LugatApp().run()
