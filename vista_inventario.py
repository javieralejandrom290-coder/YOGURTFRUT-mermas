import tkinter as tk

from base_datos import obtener_conexion
from ui_comunes import crear_tabla, crear_tarjeta_resumen


def estado_stock(existencia, stock_minimo):
    """Devuelve 'Agotado', 'Bajo' u 'OK' según la existencia."""
    if existencia <= 0:
        return "Agotado"
    if existencia <= stock_minimo:
        return "Bajo"
    return "OK"


def consultar_inventario(busqueda="", solo_alertas=False):
    """Productos activos con su valor en inventario y estado de stock."""
    with obtener_conexion() as conexion:
        filas = conexion.execute(
            """
            SELECT p.id, p.nombre, COALESCE(c.nombre, 'Sin categoría') AS categoria,
                   p.unidad, p.existencia, p.stock_minimo, p.costo_unitario
            FROM productos p
            LEFT JOIN categorias c ON c.id = p.categoria_id
            WHERE p.activo = 1 AND p.nombre LIKE ?
            ORDER BY p.nombre
            """,
            (f"%{busqueda.strip()}%",)
        ).fetchall()

    resultado = []
    for f in filas:
        estado = estado_stock(f["existencia"], f["stock_minimo"])
        if solo_alertas and estado == "OK":
            continue
        resultado.append({
            "nombre": f["nombre"],
            "categoria": f["categoria"],
            "unidad": f["unidad"],
            "existencia": f["existencia"],
            "stock_minimo": f["stock_minimo"],
            "valor": f["existencia"] * f["costo_unitario"],
            "estado": estado,
        })
    return resultado


class ModuloInventario:
    """Apartado Inventario: existencias, valor y alertas de stock."""

    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.contenido = dashboard.contenido

        self.busqueda = tk.StringVar()
        self.solo_alertas = tk.BooleanVar(value=False)
        self.var_total = tk.StringVar(value="0")
        self.var_valor = tk.StringVar(value="$0.00")
        self.var_alertas = tk.StringVar(value="0")

    def mostrar(self):
        d = self.dashboard
        d.limpiar_contenido()
        d.titulo_pagina(
            "Inventario",
            "Consulta las existencias de los productos."
        )

        # Tarjetas de resumen
        tarjetas = tk.Frame(self.contenido, bg=d.FONDO)
        tarjetas.pack(fill="x", padx=30, pady=(0, 14))
        for i in range(3):
            tarjetas.columnconfigure(i, weight=1, uniform="t")

        crear_tarjeta_resumen(
            d, tarjetas, "PRODUCTOS ACTIVOS", self.var_total
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        crear_tarjeta_resumen(
            d, tarjetas, "VALOR DEL INVENTARIO", self.var_valor
        ).grid(row=0, column=1, sticky="ew", padx=8)
        crear_tarjeta_resumen(
            d, tarjetas, "BAJOS O AGOTADOS", self.var_alertas
        ).grid(row=0, column=2, sticky="ew", padx=(8, 0))

        # Barra de filtros
        barra = tk.Frame(self.contenido, bg=d.FONDO)
        barra.pack(fill="x", padx=30, pady=(0, 12))

        tk.Label(
            barra, text="Buscar:", font=("Segoe UI", 10),
            bg=d.FONDO, fg=d.TEXTO
        ).pack(side="left")

        entrada = tk.Entry(
            barra, textvariable=self.busqueda, font=("Segoe UI", 11),
            relief="solid", bd=1, width=28
        )
        entrada.pack(side="left", padx=(8, 12), ipady=4)
        entrada.bind("<KeyRelease>", lambda e: self.cargar())

        tk.Checkbutton(
            barra, text="Solo productos con alerta",
            variable=self.solo_alertas, command=self.cargar,
            font=("Segoe UI", 10), bg=d.FONDO, fg=d.TEXTO,
            activebackground=d.FONDO, cursor="hand2"
        ).pack(side="left")

        # Tabla
        marco, self.tabla = crear_tabla(d, self.contenido, [
            ("nombre", "Producto", 210, "w"),
            ("categoria", "Categoría", 150, "w"),
            ("unidad", "Unidad", 80, "center"),
            ("existencia", "Existencia", 105, "center"),
            ("stock_minimo", "Stock mínimo", 125, "center"),
            ("valor", "Valor", 110, "e"),
            ("estado", "Estado", 90, "center"),
        ])
        marco.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self.tabla.tag_configure("bajo", background="#FFF4E0")
        self.tabla.tag_configure("agotado", background="#FDECEA")

        self.cargar()

    def cargar(self):
        self.tabla.delete(*self.tabla.get_children())

        # Los totales se calculan sobre todos los productos activos,
        # sin importar el filtro de la tabla.
        todos = consultar_inventario()
        self.var_total.set(str(len(todos)))
        self.var_valor.set(f"${sum(p['valor'] for p in todos):,.2f}")
        self.var_alertas.set(str(sum(p["estado"] != "OK" for p in todos)))

        for p in consultar_inventario(
            self.busqueda.get(), self.solo_alertas.get()
        ):
            etiqueta = {"Bajo": "bajo", "Agotado": "agotado"}.get(p["estado"], "")
            self.tabla.insert("", "end", tags=(etiqueta,), values=(
                p["nombre"],
                p["categoria"],
                p["unidad"],
                f"{p['existencia']:g}",
                f"{p['stock_minimo']:g}",
                f"${p['valor']:,.2f}",
                p["estado"],
            ))
