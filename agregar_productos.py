import sqlite3
import sys
import pathlib

# Asegurar import de base_datos
ruta_raiz = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ruta_raiz))

import base_datos

productos_a_insertar = [
    # (nombre, categoria, unidad, costo_unitario, existencia, stock_minimo)
    ("Yogurt Natural", "Bases de yogur", "L", 0.0, 0.0, 0.0),
    ("Fresa", "Frutas", "kg", 0.0, 0.0, 0.0),
    ("Mango", "Frutas", "kg", 0.0, 0.0, 0.0),
    ("Kiwi", "Frutas", "kg", 0.0, 0.0, 0.0),
    ("Uva", "Frutas", "kg", 0.0, 0.0, 0.0),
    ("Blueberry", "Frutas", "kg", 0.0, 0.0, 0.0),
    ("Brownie", "Toppings", "pza", 0.0, 0.0, 0.0),
    ("Pay de Queso", "Toppings", "pza", 0.0, 0.0, 0.0),
    ("Pay de Manzana", "Toppings", "pza", 0.0, 0.0, 0.0),
    ("Frambuesa", "Frutas", "kg", 0.0, 0.0, 0.0),
    ("Granola", "Toppings", "kg", 0.0, 0.0, 0.0),
    ("Coco Tostado", "Toppings", "kg", 0.0, 0.0, 0.0),
    ("Lotus", "Toppings", "pza", 0.0, 0.0, 0.0),
    ("Almendras", "Toppings", "kg", 0.0, 0.0, 0.0),
    ("Chispas de Taro", "Toppings", "kg", 0.0, 0.0, 0.0),
    ("Amaranto", "Toppings", "kg", 0.0, 0.0, 0.0),
    ("Nugs", "Toppings", "kg", 0.0, 0.0, 0.0),
    ("Mazapan", "Toppings", "pza", 0.0, 0.0, 0.0),
    ("Cajeta", "Salsas y jarabes", "L", 0.0, 0.0, 0.0),
    ("Panditas", "Toppings", "kg", 0.0, 0.0, 0.0),
    ("Kranky", "Toppings", "kg", 0.0, 0.0, 0.0),
    ("Lechera", "Salsas y jarabes", "L", 0.0, 0.0, 0.0),
    ("Carnation", "Salsas y jarabes", "L", 0.0, 0.0, 0.0),
    ("Cobertura", "Salsas y jarabes", "kg", 0.0, 0.0, 0.0),
    ("Etiqueta", "Empaques", "pza", 0.0, 0.0, 0.0),
    ("M&M's", "Toppings", "kg", 0.0, 0.0, 0.0),
    ("Mermelada de Piña", "Salsas y jarabes", "kg", 0.0, 0.0, 0.0),
    ("Mermelada de Fresa", "Salsas y jarabes", "kg", 0.0, 0.0, 0.0),
    ("Mermelada de Zarzamora", "Salsas y jarabes", "kg", 0.0, 0.0, 0.0),
    ("Durazno", "Frutas", "kg", 0.0, 0.0, 0.0),
    ("Cerezas", "Frutas", "kg", 0.0, 0.0, 0.0),
    ("Bubulubu mini", "Toppings", "pza", 0.0, 0.0, 0.0),
]

def agregar_productos():
    base_datos.inicializar_base_datos()
    
    with base_datos.obtener_conexion() as conexion:
        cursor = conexion.cursor()
        
        # 1. Asegurar categorías
        categorias = sorted(list(set(p[1] for p in productos_a_insertar)))
        for cat in categorias:
            cursor.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (cat,))
        
        cursor.execute("SELECT id, nombre FROM categorias")
        cat_map = {row["nombre"]: row["id"] for row in cursor.fetchall()}
        
        # 2. Insertar o actualizar productos
        insertados = 0
        actualizados = 0
        
        for nombre, categoria, unidad, costo, existencia, stock_min in productos_a_insertar:
            cat_id = cat_map.get(categoria)
            
            cursor.execute("SELECT id FROM productos WHERE nombre = ?", (nombre,))
            existente = cursor.fetchone()
            
            if existente:
                cursor.execute("""
                    UPDATE productos
                    SET categoria_id = ?, unidad = ?, activo = 1
                    WHERE id = ?
                """, (cat_id, unidad, existente["id"]))
                actualizados += 1
            else:
                cursor.execute("""
                    INSERT INTO productos (nombre, categoria_id, unidad, costo_unitario, existencia, stock_minimo, activo)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (nombre, cat_id, unidad, costo, existencia, stock_min))
                insertados += 1
                
        conexion.commit()
        print(f"Completado exitosamente: {insertados} productos insertados, {actualizados} actualizados.")

if __name__ == "__main__":
    agregar_productos()

