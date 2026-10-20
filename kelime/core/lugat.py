"""Lügat adresleri: her lügat bir URL şablonudur, {q} yerine aranan kelime konur."""
from urllib.parse import quote

VARSAYILAN_LUGATLAR = [
    {"ad": "Kubbealtı", "sablon": "https://lugatim.com/s/?{q}", "aktif": True},
]


def sablon_gecerli(sablon: str) -> bool:
    s = sablon.strip().lower()
    return (s.startswith("http://") or s.startswith("https://")) and "{q}" in s


def url_uret(sablon: str, kelime: str) -> str:
    return sablon.replace("{q}", quote(kelime.strip(), safe=""))
