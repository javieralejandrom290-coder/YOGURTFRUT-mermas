
import sqlite3
from pathlib import Path

# Ruta de la base de datos
RUTA_BASE_DATOS = Path(__file__).resolve().parent / "mermas.db"


def obtener_conexion():
    """Abre una conexión con la base de datos SQLite."""
    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def inicializar_base_datos():
    """Crea las tablas necesarias si todavía no existen."""

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()

        # Tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                usuario TEXT NOT NULL UNIQUE,
                contrasena_hash TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'Empleado'
                    CHECK (rol IN ('Administrador', 'Empleado')),
                activo INTEGER NOT NULL DEFAULT 1
                    CHECK (activo IN (0, 1)),
                fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla de categorías
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT
            )
        """)

        # Tabla de productos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                categoria_id INTEGER,
                unidad TEXT NOT NULL,
                costo_unitario REAL NOT NULL DEFAULT 0
                    CHECK (costo_unitario >= 0),
                existencia REAL NOT NULL DEFAULT 0
                    CHECK (existencia >= 0),
                stock_minimo REAL NOT NULL DEFAULT 0
                    CHECK (stock_minimo >= 0),
                activo INTEGER NOT NULL DEFAULT 1
                    CHECK (activo IN (0, 1)),
                FOREIGN KEY (categoria_id)
                    REFERENCES categorias(id)
            )
        """)

        # Tabla de mermas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mermas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                usuario_id INTEGER,
                cantidad REAL NOT NULL CHECK (cantidad > 0),
                motivo TEXT NOT NULL,
                observaciones TEXT,
                costo_total REAL NOT NULL CHECK (costo_total >= 0),
                fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (producto_id)
                    REFERENCES productos(id),
                FOREIGN KEY (usuario_id)
                    REFERENCES usuarios(id)
                    ON DELETE SET NULL
            )
        """)

        conexion.commit()


if __name__ == "__main__":
    inicializar_base_datos()
    print("Base de datos inicializada correctamente.")
    print(f"Ubicación: {RUTA_BASE_DATOS}")
