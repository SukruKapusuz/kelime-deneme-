"""Kelime yazımını karşılaştırılabilir hale getiren küçük yardımcılar."""

_SADE = str.maketrans({"â": "a", "î": "i", "û": "u",
                       "ʿ": "", "ʾ": "", "'": "", "’": "", "`": ""})
_ASCII = str.maketrans({"ı": "i", "ö": "o", "ü": "u", "ş": "s", "ç": "c", "ğ": "g"})


def kucult(metin: str) -> str:
    """Türkçe'ye uygun küçük harf (İ→i, I→ı)."""
    return metin.replace("İ", "i").replace("I", "ı").lower()


def sade(metin: str) -> str:
    """'Kâtip' → 'katip' (şapkalı harfleri ve ayın/hemze işaretlerini sadeleştirir)."""
    return kucult(metin.strip()).translate(_SADE)


def ascii_katla(metin: str) -> str:
    """'Kütüp' → 'kutup' (Türkçe harfleri de düzleştirir; son çare eşleştirme)."""
    return sade(metin).translate(_ASCII)
