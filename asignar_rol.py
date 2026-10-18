import sqlite3
from base_datos import RUTA_BASE_DATOS

with sqlite3.connect(RUTA_BASE_DATOS) as conexion:
    conexion.execute(
        "UPDATE usuarios SET rol = 'Gerente' WHERE usuario = ?",
        ("emiliano",)
    )
print("Rol actualizado.")