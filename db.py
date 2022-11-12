import sqlite3


class Db:

    def __init__(self, file = "meter.db"):
        self.connection = sqlite3.connect(file)

    def setup(self):
        cur = self.connection.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            secIndex INTEGER NOT NULL,
            power_W REAL NOT_NULL,
            energy_Wh REAL NOT_NULL
        );
        """)
        self.connection.commit()
    
    def add(self, secIndex, power, energy):
        cur = self.connection.cursor()
        cur.execute("INSERT INTO readings (secIndex, power_W, energy_Wh) VALUES (?,?,?)",
                    (secIndex, power, energy))
        self.connection.commit()
