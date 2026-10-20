"""Arama geçmişi: SQLite. tur = 'lugat' (ekran 1) veya 'kok' (ekran 2)."""
import sqlite3


class Gecmis:
    def __init__(self, yol):
        self.db = sqlite3.connect(str(yol), check_same_thread=False)
        self.db.execute("""CREATE TABLE IF NOT EXISTS gecmis(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kelime TEXT NOT NULL,
            tur TEXT NOT NULL,
            lugat TEXT DEFAULT '',
            zaman TEXT DEFAULT CURRENT_TIMESTAMP)""")
        self.db.commit()

    def ekle(self, kelime, tur, lugat=""):
        self.db.execute("INSERT INTO gecmis(kelime, tur, lugat) VALUES (?,?,?)",
                        (kelime.strip(), tur, lugat))
        self.db.commit()

    def listele(self, limit=200):
        return self.db.execute(
            "SELECT id, kelime, tur, lugat, zaman FROM gecmis ORDER BY id DESC LIMIT ?",
            (limit,)).fetchall()

    def sil(self, kayit_id):
        self.db.execute("DELETE FROM gecmis WHERE id=?", (kayit_id,))
        self.db.commit()

    def temizle(self):
        self.db.execute("DELETE FROM gecmis")
        self.db.commit()
