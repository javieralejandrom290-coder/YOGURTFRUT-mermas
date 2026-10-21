"""
Genera la base de datos de prueba mermas_prueba.db con datos falsos.

    python datos_prueba.py      -> (re)genera la base de prueba
    python main.py --prueba     -> abre el programa con esa base

La base de prueba es independiente de mermas.db. Como siempre se genera
igual (semilla fija), si alguien la modifica basta con volver a generarla.
"""
import random
from datetime import date, datetime, timedelta

import base_datos
import seguridad
from vista_mermas import RegistrarMermaView


RUTA_PRUEBA = base_datos.RUTA_BASE_DATOS.with_name("mermas_prueba.db")
DIAS_DE_HISTORIA = 45

USUARIOS = [
    # (nombre, usuario, contraseña, rol). admin/admin lo crea base_datos.
    ("Gerente de prueba", "gerente", "gerente", "Gerente"),
    ("Empleado de prueba", "empleado", "empleado", "Empleado"),
]

# categoría -> [(producto, unidad, costo, stock mínimo)]
PRODUCTOS = {
    "Bases de yogur": [
        ("Yogur natural", "L", 38, 10),
        ("Yogur griego", "L", 55, 6),
        ("Base de helado de vainilla", "L", 62, 8),
    ],
    "Frutas": [
        ("Fresa", "kg", 48, 5),
        ("Plátano", "kg", 22, 5),
        ("Mango", "kg", 35, 4),
        ("Kiwi", "kg", 70, 2),
    ],
    "Toppings": [
        ("Granola", "kg", 95, 3),
        ("Chispas de chocolate", "kg", 120, 2),
        ("Nuez picada", "kg", 260, 1),
    ],
    "Salsas y jarabes": [
        ("Jarabe de chocolate", "L", 85, 3),
        ("Lechera", "L", 70, 3),
    ],
    "Empaques": [
        ("Vaso 12 oz", "pza", 1.8, 150),
        ("Cuchara desechable", "pza", 0.4, 200),
    ],
}

# proveedor (datos ficticios) -> categorías que surte
PROVEEDORES = [
    ("Lácteos del Norte (ficticio)", "81 0000 0001", "ventas@lacteos.example.com",
     ["Bases de yogur", "Salsas y jarabes"]),
    ("Frutas La Huerta (ficticio)", "81 0000 0002", "pedidos@lahuerta.example.com",
     ["Frutas"]),
    ("Dulces y Toppings (ficticio)", "81 0000 0003", "contacto@toppings.example.com",
     ["Toppings"]),
    ("Empaques Regio (ficticio)", "81 0000 0004", "ventas@empaques.example.com",
     ["Empaques"]),
]

EMPLEADOS = [
    ("Laura Prueba", "Encargada de turno", "Matutino"),
    ("Carlos Prueba", "Preparador", "Matutino"),
    ("Sofía Prueba", "Cajera", "Vespertino"),
    ("Miguel Prueba", "Preparador", "Vespertino"),
    ("Daniela Prueba", "Almacenista", "Completo"),
]

# tipo de merma -> motivos posibles (deben existir en RegistrarMermaView)
MOTIVOS_POR_TIPO = {
    "Natural": ["Caducidad", "Mal almacenamiento"],
    "Operativa": ["Error de preparación", "Producto derramado", "Daño o ruptura"],
    "Administrativa": ["Devolución de cliente", "Otro"],
    "Hurto": ["Otro"],
}
PESOS_TIPO = {"Natural": 5, "Operativa": 4, "Administrativa": 1, "Hurto": 1}

assert all(
    motivo in RegistrarMermaView.MOTIVOS
    for motivos in MOTIVOS_POR_TIPO.values() for motivo in motivos
)


def hora_aleatoria(azar, dia):
    return datetime.combine(dia, datetime.min.time()) + timedelta(
        hours=azar.randint(9, 20), minutes=azar.randint(0, 59)
    )


def generar():
    azar = random.Random(2026)

    if RUTA_PRUEBA.exists():
        RUTA_PRUEBA.unlink()

    ruta_original = base_datos.RUTA_BASE_DATOS
    base_datos.RUTA_BASE_DATOS = RUTA_PRUEBA
    try:
        base_datos.inicializar_base_datos()
        with base_datos.obtener_conexion() as conexion:
            llenar(conexion, azar)
    finally:
        base_datos.RUTA_BASE_DATOS = ruta_original

    print(f"Base de prueba generada: {RUTA_PRUEBA}")


def llenar(conexion, azar):
    for nombre, usuario, contrasena, rol in USUARIOS:
        conexion.execute(
            "INSERT INTO usuarios (nombre, usuario, contrasena_hash, rol) "
            "VALUES (?, ?, ?, ?)",
            (nombre, usuario, seguridad.generar_hash(contrasena), rol)
        )

    productos_por_categoria = {}
    for categoria, productos in PRODUCTOS.items():
        categoria_id = conexion.execute(
            "INSERT INTO categorias (nombre) VALUES (?)", (categoria,)
        ).lastrowid
        productos_por_categoria[categoria] = []

        for nombre, unidad, costo, minimo in productos:
            producto_id = conexion.execute(
                """
                INSERT INTO productos
                    (nombre, categoria_id, unidad, costo_unitario, stock_minimo)
                VALUES (?, ?, ?, ?, ?)
                """,
                (nombre, categoria_id, unidad, costo, minimo)
            ).lastrowid
            productos_por_categoria[categoria].append(
                {"id": producto_id, "unidad": unidad, "costo": costo,
                 "minimo": minimo}
            )

    proveedores = []
    for nombre, telefono, correo, categorias in PROVEEDORES:
        proveedor_id = conexion.execute(
            "INSERT INTO proveedores (nombre, telefono, correo) VALUES (?, ?, ?)",
            (nombre, telefono, correo)
        ).lastrowid
        proveedores.append((proveedor_id, categorias))

    empleados = [
        conexion.execute(
            "INSERT INTO empleados (nombre, puesto, turno) VALUES (?, ?, ?)",
            empleado
        ).lastrowid
        for empleado in EMPLEADOS
    ]

    tipos = {
        fila["nombre"]: fila["id"]
        for fila in conexion.execute("SELECT id, nombre FROM tipos_merma")
    }
    admin_id = conexion.execute(
        "SELECT id FROM usuarios WHERE usuario = 'admin'"
    ).fetchone()[0]

    hoy = date.today()
    for dias_atras in range(DIAS_DE_HISTORIA, -1, -1):
        dia = hoy - timedelta(days=dias_atras)

        # Compras: cada proveedor surte más o menos cada 4 días
        # (el primer día se surte todo para arrancar con inventario)
        for proveedor_id, categorias in proveedores:
            if dias_atras != DIAS_DE_HISTORIA and azar.random() > 0.25:
                continue
            registrar_compra(
                conexion, azar, dia, proveedor_id, admin_id,
                [p for c in categorias for p in productos_por_categoria[c]]
            )

        # Mermas: entre 0 y 3 al día
        todos = [p for ps in productos_por_categoria.values() for p in ps]
        for _ in range(azar.randint(0, 3)):
            registrar_merma(
                conexion, azar, dia, azar.choice(todos),
                azar.choice(empleados), tipos, admin_id
            )


def registrar_compra(conexion, azar, dia, proveedor_id, usuario_id, productos):
    renglones = []
    for producto in productos:
        if azar.random() < 0.3:
            continue
        cantidad = round(producto["minimo"] * azar.uniform(1.5, 3))
        # El precio varía un poco entre compras
        precio = round(producto["costo"] * azar.uniform(0.92, 1.1), 2)
        renglones.append((producto, cantidad, precio))

    if not renglones:
        return

    total = round(sum(cantidad * precio for _, cantidad, precio in renglones), 2)
    compra_id = conexion.execute(
        "INSERT INTO compras (proveedor_id, usuario_id, fecha, total) "
        "VALUES (?, ?, ?, ?)",
        (proveedor_id, usuario_id,
         f"{hora_aleatoria(azar, dia):%Y-%m-%d %H:%M:%S}", total)
    ).lastrowid

    for producto, cantidad, precio in renglones:
        conexion.execute(
            "INSERT INTO detalle_compras "
            "(compra_id, producto_id, cantidad, precio_unitario) "
            "VALUES (?, ?, ?, ?)",
            (compra_id, producto["id"], cantidad, precio)
        )
        conexion.execute(
            "UPDATE productos SET existencia = existencia + ?, "
            "costo_unitario = ? WHERE id = ?",
            (cantidad, precio, producto["id"])
        )
        base_datos.registrar_movimiento_inventario(
            conexion, producto["id"], entrada=cantidad, fecha=dia
        )


def registrar_merma(conexion, azar, dia, producto, empleado_id, tipos, usuario_id):
    actual = conexion.execute(
        "SELECT existencia, costo_unitario FROM productos WHERE id = ?",
        (producto["id"],)
    ).fetchone()

    if actual["existencia"] <= 0:
        return

    # Merma pequeña: hasta 8% de lo que hay (piezas enteras en empaques)
    cantidad = actual["existencia"] * azar.uniform(0.02, 0.08)
    cantidad = max(1, round(cantidad)) if producto["unidad"] == "pza" \
        else max(0.1, round(cantidad, 1))
    cantidad = min(cantidad, actual["existencia"])

    tipo = azar.choices(list(PESOS_TIPO), weights=PESOS_TIPO.values())[0]
    motivo = azar.choice(MOTIVOS_POR_TIPO[tipo])

    conexion.execute(
        """
        INSERT INTO mermas (producto_id, usuario_id, empleado_id, tipo_merma_id,
                            cantidad, motivo, costo_total, fecha)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            producto["id"], usuario_id, empleado_id, tipos[tipo], cantidad,
            motivo, round(cantidad * actual["costo_unitario"], 2),
            f"{hora_aleatoria(azar, dia):%Y-%m-%d %H:%M:%S}",
        )
    )
    conexion.execute(
        "UPDATE productos SET existencia = existencia - ? WHERE id = ?",
        (cantidad, producto["id"])
    )
    base_datos.registrar_movimiento_inventario(
        conexion, producto["id"], salida=cantidad, fecha=dia
    )


if __name__ == "__main__":
    generar()
