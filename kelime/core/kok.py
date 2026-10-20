"""Kök-türev motoru.

Çalışma mantığı:
  1) CSV dosyalarındaki (kok, kelime) çiftleri bellekte bir SQLite tablosuna yüklenir.
  2) Girilen kelime tabloda aranır -> kökü bulunur -> aynı kökten gelen diğer kelimeler döner.
  3) Tabloda yoksa (ve ayar açıksa) kelimenin ünsüz iskeleti çıkarılıp köklerle kıyaslanır.
"""
import csv
import sqlite3
from pathlib import Path

from .metin import ascii_katla, sade

UNLULER = set("aeıioöuüâîû")
_ESIT = str.maketrans({"p": "b", "ç": "c", "ğ": "g", "q": "k"})   # Türkçedeki yumuşamalar


def kok_kiyas(kok: str) -> str:
    """'k-t-b' → 'ktb', 'ʿ-l-m' → 'lm' (ayın düşer, tire düşer)."""
    return "".join(c for c in sade(kok) if c.isalpha()).translate(_ESIT)


def iskelet(kelime: str) -> str:
    """'mektup' → 'mktb' (ünlüler düşer, p→b gibi yumuşamalar eşitlenir)."""
    return "".join(c for c in sade(kelime) if c.isalpha() and c not in UNLULER).translate(_ESIT)


def _altdizi(kisa: str, uzun: str) -> bool:
    it = iter(uzun)
    return all(c in it for c in kisa)


class KokMotoru:
    def __init__(self, csv_yollari):
        self.db = sqlite3.connect(":memory:", check_same_thread=False)
        self.db.execute("""CREATE TABLE kelimeler(
            kok TEXT, kok_ar TEXT, kelime TEXT, anlam TEXT,
            sade TEXT, ascii TEXT, kiyas TEXT)""")
        for yol in csv_yollari:
            if Path(yol).exists():
                self._yukle(yol)
        self.db.commit()

    def _yukle(self, yol):
        with open(yol, encoding="utf-8-sig", newline="") as f:
            for s in csv.DictReader(f):
                kok = (s.get("kok") or "").strip()
                kelime = (s.get("kelime") or "").strip()
                if not kok or not kelime:
                    continue
                self.db.execute(
                    "INSERT INTO kelimeler VALUES (?,?,?,?,?,?,?)",
                    (kok, (s.get("kok_ar") or "").strip(), kelime,
                     (s.get("anlam") or "").strip(),
                     sade(kelime), ascii_katla(kelime), kok_kiyas(kok)))

    # ------------------------------------------------------------------
    def _koklerden_turet(self, kokler, girdi, limit):
        sonuc, kok_bilgi = [], []
        for kok in kokler:
            satirlar = self.db.execute(
                "SELECT kok_ar, kelime, anlam FROM kelimeler WHERE kok=?", (kok,)).fetchall()
            kok_bilgi.append({"kok": kok, "kok_ar": satirlar[0][0] if satirlar else ""})
            for _, kelime, anlam in satirlar:
                if sade(kelime) != sade(girdi):
                    sonuc.append({"kelime": kelime, "anlam": anlam, "kok": kok})
        return kok_bilgi, sonuc[:limit]

    def bul(self, girdi: str, ayar: dict) -> dict:
        girdi = girdi.strip()
        limit = int(ayar.get("en_fazla_sonuc", 50))
        bos = {"girdi": girdi, "yontem": "yok", "kokler": [], "turevler": []}
        if not girdi:
            return bos

        # 1) veritabanında doğrudan ara (önce sade yazım, sonra ASCII)
        for sutun, deger in (("sade", sade(girdi)), ("ascii", ascii_katla(girdi))):
            kokler = [r[0] for r in self.db.execute(
                f"SELECT DISTINCT kok FROM kelimeler WHERE {sutun}=?", (deger,))]
            if kokler:
                bilgi, turevler = self._koklerden_turet(kokler, girdi, limit)
                return {"girdi": girdi, "yontem": "veritabani",
                        "kokler": bilgi, "turevler": turevler}

        # 2) tahmin
        if not ayar.get("tahmin_kullan", True):
            return bos
        isk = iskelet(girdi)
        if len(isk) < 2:
            return bos
        tum = self.db.execute("SELECT DISTINCT kok, kiyas FROM kelimeler").fetchall()
        tam = [k for k, kiyas in tum if kiyas == isk]
        kokler = tam
        if not kokler and ayar.get("on_ek_toleransi", True):
            kokler = [k for k, kiyas in tum if len(kiyas) >= 2 and _altdizi(kiyas, isk)]
        if not kokler:
            return bos
        bilgi, turevler = self._koklerden_turet(kokler, girdi, limit)
        return {"girdi": girdi, "yontem": "tahmin", "kokler": bilgi, "turevler": turevler}
