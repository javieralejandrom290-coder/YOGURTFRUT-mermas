import sqlite3
import pathlib
import sys
from datetime import date

import seguridad

# Carpeta del programa. Empaquetado como .exe (PyInstaller), __file__ apunta
# a una carpeta interna o temporal, así que la base se guarda junto al .exe
# para que los datos no se pierdan al cerrarlo.
if getattr(sys, "frozen", False):
    CARPETA_PROGRAMA = pathlib.Path(sys.executable).resolve().parent
else:
    CARPETA_PROGRAMA = pathlib.Path(__file__).resolve().parent

# Ruta de la base de datos
RUTA_BASE_DATOS = CARPETA_PROGRAMA / "mermas.db"

# Tipos de merma del catálogo (modelo relacional, tabla TipoMerma)
TIPOS_MERMA = ["Natural", "Operativa", "Administrativa", "Hurto"]

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


def agregar_columna_si_falta(conexion, tabla, columna, definicion):
    """Agrega una columna a una tabla existente si todavía no la tiene."""
    columnas = [
        fila[1]
        for fila in conexion.execute(f"PRAGMA table_info({tabla})")
    ]

    if columna not in columnas:
        conexion.execute(
            f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}"
        )


def registrar_movimiento_inventario(conexion, producto_id, entrada=0, salida=0,
                                    fecha=None):
    """
    Registra una entrada o salida en el inventario del día.
    Se llama DESPUÉS de actualizar la existencia del producto, dentro
    de la misma transacción. Si es el primer movimiento del día se crea
    el registro con su stock inicial; si no, se acumula.
    La fecha es hoy, salvo que se indique otra (lo usa datos_prueba.py).
    """
    hoy = (fecha or date.today()).isoformat()

    existencia = conexion.execute(
        "SELECT existencia FROM productos WHERE id = ?",
        (producto_id,)
    ).fetchone()[0]

    registro = conexion.execute(
        "SELECT id FROM inventario WHERE producto_id = ? AND fecha = ?",
        (producto_id, hoy)
    ).fetchone()

    if registro:
        conexion.execute(
            """
            UPDATE inventario
            SET entradas = entradas + ?,
                salidas = salidas + ?,
                stock_final = ?
            WHERE id = ?
            """,
            (entrada, salida, existencia, registro[0])
        )
    else:
        conexion.execute(
            """
            INSERT INTO inventario
                (producto_id, fecha, stock_inicial,
                 entradas, salidas, stock_final)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                producto_id,
                hoy,
                existencia - entrada + salida,
                entrada,
                salida,
                existencia
            )
        )


def migrar_usuario_test(cursor):
    """
    Versiones anteriores creaban el usuario test/test. Si sigue con su
    contraseña original y no existe 'admin', se convierte en admin/admin.
    Si ya hay un 'admin' se deja como está para no bloquear a nadie.
    """
    test = cursor.execute(
        "SELECT id, contrasena_hash FROM usuarios WHERE usuario = 'test'"
    ).fetchone()

    if not test or not seguridad.verificar_hash("test", test[1]):
        return

    hay_admin = cursor.execute(
        "SELECT 1 FROM usuarios WHERE usuario = 'admin'"
    ).fetchone()
    if hay_admin:
        return

    cursor.execute(
        """
        UPDATE usuarios
        SET usuario = 'admin', nombre = 'Administrador',
            contrasena_hash = ?, rol = 'Administrador', activo = 1
        WHERE id = ?
        """,
        (seguridad.generar_hash("admin"), test[0])
    )


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

        # Tabla de proveedores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                telefono TEXT,
                correo TEXT,
                activo INTEGER NOT NULL DEFAULT 1
                    CHECK (activo IN (0, 1))
            )
        """)

        # Tabla de compras (encabezado de cada pedido a un proveedor)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor_id INTEGER NOT NULL,
                usuario_id INTEGER,
                fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                total REAL NOT NULL DEFAULT 0
                    CHECK (total >= 0),
                FOREIGN KEY (proveedor_id)
                    REFERENCES proveedores(id),
                FOREIGN KEY (usuario_id)
                    REFERENCES usuarios(id)
                    ON DELETE SET NULL
            )
        """)

        # Tabla de detalle de compras (productos de cada compra)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compra_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad REAL NOT NULL CHECK (cantidad > 0),
                precio_unitario REAL NOT NULL
                    CHECK (precio_unitario >= 0),
                FOREIGN KEY (compra_id)
                    REFERENCES compras(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (producto_id)
                    REFERENCES productos(id)
            )
        """)

        # Tabla de empleados (personal que genera o reporta mermas)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empleados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                puesto TEXT NOT NULL,
                turno TEXT NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1
                    CHECK (activo IN (0, 1))
            )
        """)

        # Catálogo de tipos de merma
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipos_merma (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            )
        """)

        for tipo in TIPOS_MERMA:
            cursor.execute(
                "INSERT OR IGNORE INTO tipos_merma (nombre) VALUES (?)",
                (tipo,)
            )

        # Tabla de mermas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mermas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                usuario_id INTEGER,
                empleado_id INTEGER,
                tipo_merma_id INTEGER,
                cantidad REAL NOT NULL CHECK (cantidad > 0),
                motivo TEXT NOT NULL,
                observaciones TEXT,
                costo_total REAL NOT NULL CHECK (costo_total >= 0),
                fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (producto_id)
                    REFERENCES productos(id),
                FOREIGN KEY (usuario_id)
                    REFERENCES usuarios(id)
                    ON DELETE SET NULL,
                FOREIGN KEY (empleado_id)
                    REFERENCES empleados(id),
                FOREIGN KEY (tipo_merma_id)
                    REFERENCES tipos_merma(id)
            )
        """)

        # Bases creadas antes de existir empleados y tipos de merma
        agregar_columna_si_falta(
            conexion, "mermas", "empleado_id",
            "INTEGER REFERENCES empleados(id)"
        )
        agregar_columna_si_falta(
            conexion, "mermas", "tipo_merma_id",
            "INTEGER REFERENCES tipos_merma(id)"
        )

        # Tabla de inventario: un registro por producto y por día
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                stock_inicial REAL NOT NULL DEFAULT 0,
                entradas REAL NOT NULL DEFAULT 0
                    CHECK (entradas >= 0),
                salidas REAL NOT NULL DEFAULT 0
                    CHECK (salidas >= 0),
                stock_final REAL NOT NULL DEFAULT 0,
                UNIQUE (producto_id, fecha),
                FOREIGN KEY (producto_id)
                    REFERENCES productos(id)
            )
        """)

        # Si la base no tiene usuarios se crea el administrador inicial
        # (usuario: admin, contraseña: admin). Se cambian en Usuarios → Mi cuenta.
        if cursor.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
            cursor.execute(
                """
                INSERT INTO usuarios (nombre, usuario, contrasena_hash, rol)
                VALUES ('Administrador', 'admin', ?, 'Administrador')
                """,
                (seguridad.generar_hash("admin"),)
            )

        migrar_usuario_test(cursor)

        conexion.commit()


if __name__ == "__main__":
    inicializar_base_datos()
    print("Base de datos inicializada correctamente.")
    print(f"Ubicación: {RUTA_BASE_DATOS}")