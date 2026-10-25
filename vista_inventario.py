import tkinter as tk

import ui_tema
from base_datos import obtener_conexion
from ui_comunes import crear_boton, crear_tabla, crear_tarjeta_resumen


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
            "precio": f["costo_unitario"],
            "existencia": f["existencia"],
            "stock_minimo": f["stock_minimo"],
            "valor": f["existencia"] * f["costo_unitario"],
            "estado": estado,
        })
    return resultado


def consultar_movimientos(busqueda=""):
    """Registros diarios de inventario: stock inicial, entradas, salidas y final."""
    with obtener_conexion() as conexion:
        return conexion.execute(
            """
            SELECT i.fecha, p.nombre AS producto, p.unidad,
                   i.stock_inicial, i.entradas, i.salidas, i.stock_final
            FROM inventario i
            JOIN productos p ON p.id = i.producto_id
            WHERE p.nombre LIKE ?
            ORDER BY i.fecha DESC, p.nombre
            LIMIT 500
            """,
            (f"%{busqueda.strip()}%",)
        ).fetchall()


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
            "Consulta las existencias y los movimientos diarios de los productos."
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

        entrada = ui_tema.entrada(
            barra, textvariable=self.busqueda, font=("Segoe UI", 10),
            width=28
        )
        entrada.pack(side="left", padx=(8, 12), ipady=4)
        entrada.bind("<KeyRelease>", lambda e: self.cargar())

        self.check_alertas = tk.Checkbutton(
            barra, text="Solo productos con alerta",
            variable=self.solo_alertas, command=self.cargar,
            font=("Segoe UI", 10), bg=d.FONDO, fg=d.TEXTO,
            activebackground=d.FONDO, selectcolor=d.BLANCO,
            cursor="hand2", highlightthickness=0, bd=0
        )
        self.check_alertas.pack(side="left")

        # Selector de vista: existencias actuales o movimientos por día
        self.boton_movimientos = crear_boton(
            d, barra, "Movimientos por día",
            lambda: self.cambiar_vista("movimientos")
        )
        self.boton_movimientos.pack(side="right")
        self.boton_existencias = crear_boton(
            d, barra, "Existencias actuales",
            lambda: self.cambiar_vista("existencias")
        )
        self.boton_existencias.pack(side="right", padx=8)

        # Tabla de movimientos (tabla inventario del modelo)
        self.marco_movimientos, self.tabla_movimientos = crear_tabla(
            d, self.contenido, [
                ("fecha", "Fecha", 110, "w"),
                ("producto", "Producto", 210, "w"),
                ("stock_inicial", "Stock inicial", 120, "center"),
                ("entradas", "Entradas", 105, "center"),
                ("salidas", "Salidas", 105, "center"),
                ("stock_final", "Stock final", 120, "center"),
            ]
        )

        # Tabla de existencias
        self.marco_existencias, self.tabla = crear_tabla(d, self.contenido, [
            ("nombre", "Producto", 220, "w"),
            ("categoria", "Categoría", 160, "w"),
            ("unidad", "Unidad", 85, "center"),
            ("precio", "Precio", 110, "e"),
            ("existencia", "Existencia", 110, "center"),
            ("stock_minimo", "Stock mínimo", 125, "center"),
            ("estado", "Estado", 95, "center"),
        ])

        self.tabla.tag_configure("bajo", background="#FBF5E4")
        self.tabla.tag_configure("agotado", background="#FBECEC")

        self.cambiar_vista("existencias")

    def cambiar_vista(self, vista):
        d = self.dashboard
        self.vista = vista
        en_existencias = vista == "existencias"

        self.marco_existencias.pack_forget()
        self.marco_movimientos.pack_forget()
        marco = self.marco_existencias if en_existencias else self.marco_movimientos
        marco.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # Resalta el botón de la vista activa
        for boton, activo in (
            (self.boton_existencias, en_existencias),
            (self.boton_movimientos, not en_existencias),
        ):
            boton.configure(
                bg=d.VERDE_CLARO if activo else d.BLANCO,
                fg=d.VERDE_OSCURO,
                highlightthickness=0
            )

        self.check_alertas.configure(
            state="normal" if en_existencias else "disabled"
        )
        self.cargar()

    def cargar(self):
        if getattr(self, "vista", "existencias") == "movimientos":
            self.cargar_movimientos()
        else:
            self.cargar_existencias()

    def cargar_movimientos(self):
        self.tabla_movimientos.delete(*self.tabla_movimientos.get_children())

        for m in consultar_movimientos(self.busqueda.get()):
            unidad = m["unidad"]
            self.tabla_movimientos.insert("", "end", values=(
                m["fecha"],
                m["producto"],
                f"{m['stock_inicial']:g} {unidad}",
                f"+{m['entradas']:g}" if m["entradas"] else "0",
                f"-{m['salidas']:g}" if m["salidas"] else "0",
                f"{m['stock_final']:g} {unidad}",
            ))

    def cargar_existencias(self):
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
                f"${p['precio']:,.2f}",
                f"{p['existencia']:g}",
                f"{p['stock_minimo']:g}",
                p["estado"],
            ))
