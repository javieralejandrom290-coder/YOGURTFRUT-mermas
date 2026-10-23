import sqlite3
import sys
import pathlib

ruta_raiz = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ruta_raiz))

import base_datos

productos_datos = [
    # (nombre_antiguo, nuevo_nombre, categoria, unidad, costo_unitario)
    ("Yogurt Natural", "Yogurt Natural", "Bases de yogur", "kg", 50.00),
    ("Fresa", "Fresa", "Frutas", "kg", 70.00),
    ("Mango", "Mango", "Frutas", "kg", 40.00),
    ("Kiwi", "Kiwi", "Frutas", "kg", 90.00),
    ("Uva", "Uva", "Frutas", "kg", 80.00),
    ("Blueberry", "Blueberry", "Frutas", "kg", 200.00),
    ("Brownie", "Brownie", "Toppings", "pz", 15.00),
    ("Pay de Queso", "Pay de Queso", "Toppings", "pz", 25.00),
    ("Pay de Manzana", "Pay de Manzana", "Toppings", "pz", 25.00),
    ("Frambuesa", "Frambuesa", "Frutas", "kg", 220.00),
    ("Granola", "Granola", "Toppings", "kg", 80.00),
    ("Coco Tostado", "Coco Tostado", "Toppings", "kg", 120.00),
    ("Lotus", "Lotus (Paquete)", "Toppings", "pz", 130.00),
    ("Almendras", "Almendras", "Toppings", "kg", 300.00),
    ("Chispas de Taro", "Chispas de Taro", "Toppings", "kg", 180.00),
    ("Amaranto", "Amaranto", "Toppings", "kg", 70.00),
    ("Nugs", "Nugs (Cereal/Chocolate)", "Toppings", "kg", 140.00),
    ("Mazapan", "Mazapan", "Toppings", "pz", 7.00),
    ("Cajeta", "Cajeta", "Salsas y jarabes", "kg", 120.00),
    ("Panditas", "Panditas", "Toppings", "kg", 90.00),
    ("Kranky", "Kranky", "Toppings", "kg", 160.00),
    ("Lechera", "Lechera (Lata)", "Salsas y jarabes", "pz", 30.00),
    ("Carnation", "Carnation (Lata)", "Salsas y jarabes", "pz", 25.00),
    ("Cobertura", "Cobertura de Chocolate", "Salsas y jarabes", "kg", 150.00),
    ("Etiqueta", "Etiqueta", "Empaques", "pz", 1.00),
    ("M&M's", "M&M's", "Toppings", "kg", 280.00),
    ("Mermelada de Piña", "Mermelada de Piña", "Salsas y jarabes", "kg", 75.00),
    ("Mermelada de Fresa", "Mermelada de Fresa", "Salsas y jarabes", "kg", 85.00),
    ("Mermelada de Zarzamora", "Mermelada de Zarzamora", "Salsas y jarabes", "kg", 95.00),
    ("Durazno", "Durazno (En almíbar)", "Frutas", "kg", 65.00),
    ("Cerezas", "Cerezas (Frasco)", "Frutas", "kg", 180.00),
    ("Bubulubu mini", "Bubulubu mini", "Toppings", "pz", 6.00),
]

def actualizar_precios_y_productos():
    base_datos.inicializar_base_datos()

    with base_datos.obtener_conexion() as conexion:
        cursor = conexion.cursor()

        # Categorías
        categorias = sorted(list(set(p[2] for p in productos_datos)))
        for cat in categorias:
            cursor.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (cat,))

        cursor.execute("SELECT id, nombre FROM categorias")
        cat_map = {row["nombre"]: row["id"] for row in cursor.fetchall()}

        actualizados = 0
        insertados = 0

        for nombre_antiguo, nuevo_nombre, categoria, unidad, costo in productos_datos:
            cat_id = cat_map[categoria]

            # Buscar por nuevo_nombre o nombre_antiguo
            cursor.execute(
                "SELECT id FROM productos WHERE nombre = ? OR nombre = ?",
                (nuevo_nombre, nombre_antiguo)
            )
            fila = cursor.fetchone()

            if fila:
                cursor.execute("""
                    UPDATE productos
                    SET nombre = ?, categoria_id = ?, unidad = ?, costo_unitario = ?, activo = 1
                    WHERE id = ?
                """, (nuevo_nombre, cat_id, unidad, costo, fila["id"]))
                actualizados += 1
            else:
                cursor.execute("""
                    INSERT INTO productos (nombre, categoria_id, unidad, costo_unitario, existencia, stock_minimo, activo)
                    VALUES (?, ?, ?, ?, 0.0, 0.0, 1)
                """, (nuevo_nombre, cat_id, unidad, costo))
                insertados += 1

        conexion.commit()
        print(f"Precios actualizados: {actualizados} actualizados, {insertados} insertados.")

if __name__ == "__main__":
    actualizar_precios_y_productos()
