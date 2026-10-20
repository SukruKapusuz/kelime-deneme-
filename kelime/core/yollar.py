"""Dosya yolları: uygulamanın kendi dosyaları ile kullanıcının dosyaları burada ayrılır."""
import os
from pathlib import Path

PROJE_KLASORU = Path(__file__).resolve().parent.parent
VERI_KLASORU = PROJE_KLASORU / "data"
HAZIR_KOK_CSV = VERI_KLASORU / "kokler.csv"          # uygulamayla gelen örnek veri


def kullanici_klasoru() -> Path:
    """Kullanıcıya ait yazılabilir klasör (ayarlar, geçmiş, kendi kök listesi).
    Mobilde Flet bu yolu FLET_APP_STORAGE_DATA ile verir; PC'de ev klasörü kullanılır."""
    ortam = os.getenv("FLET_APP_STORAGE_DATA")
    klasor = Path(ortam) if ortam else Path.home() / ".kelime"
    klasor.mkdir(parents=True, exist_ok=True)
    return klasor


def ayar_dosyasi() -> Path:
    return kullanici_klasoru() / "ayarlar.json"


def gecmis_dosyasi() -> Path:
    return kullanici_klasoru() / "gecmis.db"


def kullanici_kok_csv() -> Path:
    return kullanici_klasoru() / "benim_kokler.csv"   # kullanıcının eklediği kökler
