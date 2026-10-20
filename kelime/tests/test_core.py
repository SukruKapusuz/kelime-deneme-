import tempfile
import unittest
from pathlib import Path

from core import yollar
from core.ayarlar import Ayarlar
from core.gecmis import Gecmis
from core.kok import KokMotoru, iskelet
from core.lugat import url_uret
from core.metin import sade

AYAR = {"tahmin_kullan": True, "on_ek_toleransi": True, "en_fazla_sonuc": 50}


class Testler(unittest.TestCase):
    def setUp(self):
        self.motor = KokMotoru([yollar.HAZIR_KOK_CSV])

    def kelimeler(self, sonuc):
        return {sade(t["kelime"]) for t in sonuc["turevler"]}

    def test_kitap(self):
        s = self.motor.bul("kitap", AYAR)
        self.assertEqual(s["yontem"], "veritabani")
        self.assertTrue({"katip", "mektup", "mektep", "kütüp"} <= self.kelimeler(s))
        self.assertNotIn("kitap", self.kelimeler(s))

    def test_sapkali_ve_buyuk_harf(self):
        self.assertEqual(self.motor.bul("KÂTİP", AYAR)["kokler"][0]["kok"], "k-t-b")

    def test_ascii_yazim(self):
        self.assertEqual(self.motor.bul("kutup", AYAR)["yontem"], "veritabani")

    def test_tahmin_on_ek(self):
        s = self.motor.bul("kitaplık", AYAR)
        self.assertEqual(s["yontem"], "tahmin")
        self.assertEqual(s["kokler"][0]["kok"], "k-t-b")

    def test_tahmin_kapali(self):
        self.assertEqual(self.motor.bul("kitaplık", {**AYAR, "tahmin_kullan": False})["yontem"], "yok")

    def test_toleranssiz(self):
        self.assertEqual(self.motor.bul("kitaplık", {**AYAR, "on_ek_toleransi": False})["yontem"], "yok")

    def test_iskelet(self):
        self.assertEqual(iskelet("mektup"), "mktb")

    def test_url(self):
        self.assertEqual(url_uret("https://lugatim.com/s/?{q}", "kitap"), "https://lugatim.com/s/?kitap")
        self.assertIn("%C3%A2", url_uret("https://x/?{q}", "â"))

    def test_ayar_lugat(self):
        with tempfile.TemporaryDirectory() as d:
            a = Ayarlar(Path(d) / "a.json")
            a.lugat_ekle("Deneme", "https://x.com/?q={q}")
            self.assertEqual(len(Ayarlar(Path(d) / "a.json").veri["lugatlar"]), 2)
            with self.assertRaises(ValueError):
                a.lugat_ekle("Kötü", "ftp://x/{q}")
            a.lugat_sil("Deneme")
            with self.assertRaises(ValueError):
                a.lugat_sil("Kubbealtı")

    def test_gecmis(self):
        with tempfile.TemporaryDirectory() as d:
            g = Gecmis(Path(d) / "g.db")
            g.ekle("kitap", "kok")
            g.ekle("ilim", "lugat", "Kubbealtı")
            self.assertEqual(g.listele()[0][1], "ilim")
            g.sil(g.listele()[0][0])
            self.assertEqual(len(g.listele()), 1)
            g.temizle()
            self.assertEqual(g.listele(), [])


if __name__ == "__main__":
    unittest.main()
