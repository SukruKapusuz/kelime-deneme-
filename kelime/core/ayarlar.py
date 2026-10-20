"""Ayarlar: tek bir JSON dosyası. Eksik anahtarlar varsayılanlarla tamamlanır."""
import copy
import json
from pathlib import Path

from .lugat import VARSAYILAN_LUGATLAR, sablon_gecerli

VARSAYILAN = {
    "tema": "Açık",
    "lugatlar": VARSAYILAN_LUGATLAR,
    "varsayilan_lugat": "Kubbealtı",
    "gecmis_kaydet": True,
    "kok": {
        "tahmin_kullan": True,     # veritabanında yoksa harflerden tahmin et
        "on_ek_toleransi": True,   # mektup'taki m- gibi ek harfleri tolere et
        "arapca_goster": True,     # kökün Arapça yazımını göster
        "en_fazla_sonuc": 50,
    },
}


class Ayarlar:
    def __init__(self, yol: Path):
        self.yol = Path(yol)
        self.veri = copy.deepcopy(VARSAYILAN)
        self._yukle()

    def _yukle(self):
        if not self.yol.exists():
            return
        try:
            kayitli = json.loads(self.yol.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return  # bozuk dosya: varsayılanlarla devam
        kok = kayitli.pop("kok", {})
        self.veri.update(kayitli)
        self.veri["kok"].update(kok)

    def kaydet(self):
        self.yol.write_text(json.dumps(self.veri, ensure_ascii=False, indent=2),
                            encoding="utf-8")

    # --- lügat yönetimi -------------------------------------------------
    def aktif_lugatlar(self):
        return [l for l in self.veri["lugatlar"] if l.get("aktif", True)]

    def lugat_bul(self, ad):
        for l in self.veri["lugatlar"]:
            if l["ad"] == ad:
                return l
        return None

    def lugat_ekle(self, ad: str, sablon: str):
        ad, sablon = ad.strip(), sablon.strip()
        if not ad:
            raise ValueError("Lügat adı boş olamaz.")
        if not sablon_gecerli(sablon):
            raise ValueError("Adres http(s):// ile başlamalı ve {q} içermeli.")
        if self.lugat_bul(ad):
            raise ValueError("Bu adla bir lügat zaten var.")
        self.veri["lugatlar"].append({"ad": ad, "sablon": sablon, "aktif": True})
        self.kaydet()

    def lugat_sil(self, ad: str):
        if len(self.veri["lugatlar"]) <= 1:
            raise ValueError("En az bir lügat kalmalı.")
        self.veri["lugatlar"] = [l for l in self.veri["lugatlar"] if l["ad"] != ad]
        if self.veri["varsayilan_lugat"] == ad:
            self.veri["varsayilan_lugat"] = self.veri["lugatlar"][0]["ad"]
        self.kaydet()

    def lugat_aktif_yap(self, ad: str, aktif: bool):
        l = self.lugat_bul(ad)
        if not l:
            return
        if not aktif and len(self.aktif_lugatlar()) <= 1 and l.get("aktif", True):
            raise ValueError("En az bir lügat açık kalmalı.")
        l["aktif"] = aktif
        self.kaydet()
