import sqlite3
import pathlib

# Ruta de la base de datos
RUTA_BASE_DATOS = pathlib.Path(__file__).resolve().parent / "mermas.db"

# Hash de la contraseña "test" (generado con LoginApp.generar_hash)
HASH_USUARIO_TEST = (
    "c31f3838ee747d93b7d8826f4190defc$"
    "7e00975737b846ef968f20e67771ed10dfeb68474c8e3c5ee6a3180e0872b714"
)

# Definición de la tabla usuarios (se usa al crearla y al migrarla)
SQL_TABLA_USUARIOS = """
    CREATE TABLE IF NOT EXISTS {tabla} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        usuario TEXT NOT NULL UNIQUE,
        contrasena_hash TEXT NOT NULL,
        rol TEXT NOT NULL DEFAULT 'Empleado'
            CHECK (rol IN ('Administrador', 'Gerente', 'Empleado')),
        activo INTEGER NOT NULL DEFAULT 1
            CHECK (activo IN (0, 1)),
        fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
"""


def obtener_conexion():
    """Abre una conexión con la base de datos SQLite."""
    conexion = sqlite3.connect(RUTA_BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def migrar_roles():
    """
    Actualiza la tabla usuarios para permitir el rol 'Gerente'.
    Si la tabla ya lo permite, o todavía no existe, no hace nada.
    Los datos existentes se conservan.
    """
    if not RUTA_BASE_DATOS.exists():
        return

    # isolation_level=None para controlar manualmente la transacción
    conexion = sqlite3.connect(RUTA_BASE_DATOS, isolation_level=None)

    try:
        fila = conexion.execute(
            """
            SELECT sql FROM sqlite_master
            WHERE type = 'table' AND name = 'usuarios'
            """
        ).fetchone()

        if fila is None or "'Gerente'" in fila[0]:
            return

        # Debe desactivarse fuera de la transacción para que
        # DROP TABLE no borre en cascada las mermas relacionadas
        conexion.execute("PRAGMA foreign_keys = OFF")
        conexion.execute("BEGIN")

        try:
            conexion.execute(SQL_TABLA_USUARIOS.format(tabla="usuarios_nueva"))

            conexion.execute(
                """
                INSERT INTO usuarios_nueva
                    (id, nombre, usuario, contrasena_hash,
                     rol, activo, fecha_creacion)
                SELECT
                    id, nombre, usuario, contrasena_hash,
                    rol, activo, fecha_creacion
                FROM usuarios
                """
            )

            conexion.execute("DROP TABLE usuarios")
            conexion.execute(
                "ALTER TABLE usuarios_nueva RENAME TO usuarios"
            )
            conexion.execute("COMMIT")

        except Exception:
            conexion.execute("ROLLBACK")
            raise

        conexion.execute("PRAGMA foreign_keys = ON")

    finally:
        conexion.close()


def inicializar_base_datos():
    """Crea las tablas necesarias si todavía no existen."""

    # Primero se actualiza el esquema de usuarios si hace falta
    migrar_roles()

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()

        # Tabla de usuarios
        cursor.execute(SQL_TABLA_USUARIOS.format(tabla="usuarios"))

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

        # Usuario de prueba compartido por el equipo (usuario: test, contraseña: test)
        cursor.execute(
            """
            INSERT OR IGNORE INTO usuarios
                (nombre, usuario, contrasena_hash, rol)
            VALUES ('Usuario de prueba', 'test', ?, 'Administrador')
            """,
            (HASH_USUARIO_TEST,)
        )

        conexion.commit()


if __name__ == "__main__":
    inicializar_base_datos()
    print("Base de datos inicializada correctamente.")
    print(f"Ubicación: {RUTA_BASE_DATOS}")