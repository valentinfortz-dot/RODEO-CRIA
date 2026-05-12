import sqlite3
import os

DB_PATH = os.environ.get('DB_PATH', 'rodeo.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS toros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ide TEXT,
            idv TEXT,
            nombre TEXT,
            ce REAL,
            aptitud TEXT,
            edad INTEGER,
            origen TEXT,
            padre TEXT,
            notas TEXT
        );

        CREATE TABLE IF NOT EXISTS vacas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ide TEXT UNIQUE NOT NULL,
            anio_nacimiento INTEGER,
            origen TEXT,
            clase TEXT,
            estado TEXT DEFAULT 'Activa',
            motivo_baja TEXT,
            ide_madre TEXT,
            observaciones TEXT
        );

        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ide_vaca TEXT NOT NULL,
            temporada INTEGER NOT NULL,
            dao_sincro TEXT,
            toro_iatf TEXT,
            diagnostico_iatf TEXT,
            ecografia_final TEXT,
            toro_entore TEXT,
            eco_entore TEXT,
            caravana_ternero TEXT,
            observaciones TEXT,
            FOREIGN KEY (ide_vaca) REFERENCES vacas(ide)
        );

        CREATE TABLE IF NOT EXISTS terneros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caravana TEXT,
            ide_madre TEXT NOT NULL,
            temporada INTEGER,
            sexo TEXT,
            raza TEXT,
            semana_nacimiento TEXT,
            potrero TEXT,
            peso_destete REAL,
            fecha_destete TEXT,
            dias_destete INTEGER,
            gmd REAL,
            FOREIGN KEY (ide_madre) REFERENCES vacas(ide)
        );

        CREATE INDEX IF NOT EXISTS idx_vacas_ide ON vacas(ide);
        CREATE INDEX IF NOT EXISTS idx_eventos_vaca ON eventos(ide_vaca);
        CREATE INDEX IF NOT EXISTS idx_terneros_madre ON terneros(ide_madre);
    ''')
    conn.commit()
    conn.close()
