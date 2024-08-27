--
-- File generated with SQLiteStudio v3.4.4 on dt. ag. 27 08:07:35 2024
--
-- Text encoding used: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: links
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT (23),
    description TEXT,
    url TEXT,
    icon TEXT,
    type INTEGER REFERENCES type (id) ON UPDATE CASCADE
);

-- Table: type
CREATE TABLE IF NOT EXISTS type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descripcion TEXT
);

INSERT INTO type (descripcion) VALUES ('Fixed');
INSERT INTO type (descripcion) VALUES ('Dynamic');
INSERT INTO type (descripcion) VALUES ('Highlighted');

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;