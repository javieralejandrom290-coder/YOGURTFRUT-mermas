import tkinter as tk
from tkinter import ttk, messagebox

from base_datos import obtener_conexion
from ui_comunes import crear_tabla


MOTIVOS = [
    "Caducidad",
    "Daño o mal estado",
    "Error de preparación",
    "Derrame o caída",
    "Contaminación",
    "Producto devuelto",
    "Otro",
]


class ErrorMerma(Exception):
    """Error de validación al registrar una merma."""


def registrar_merma(producto_id, usuario_id, cantidad, motivo, observaciones=""):
    """
    Registra una merma y descuenta la existencia del producto.

    Todo ocurre en una sola transacción: si algo falla, no se guarda nada.
    Devuelve el costo total de la merma.
    """
    try:
        cantidad = float(cantidad)
    except (TypeError, ValueError):
        raise ErrorMerma("La cantidad debe ser un número.")

    if cantidad <= 0:
        raise ErrorMerma("La cantidad debe ser mayor a 0.")

    if not motivo or not motivo.strip():
        raise ErrorMerma("Selecciona el motivo de la merma.")

    with obtener_conexion() as conexion:
        producto = conexion.execute(
            "SELECT nombre, unidad, costo_unitario, existencia, activo "
            "FROM productos WHERE id = ?",
            (producto_id,)
        ).fetchone()

        if producto is None:
            raise ErrorMerma("El producto seleccionado no existe.")

        if not producto["activo"]:
            raise ErrorMerma("El producto seleccionado está inactivo.")

        if cantidad > producto["existencia"]:
            raise ErrorMerma(
                f"No hay suficiente existencia de {producto['nombre']}.\n"
                f"Disponible: {producto['existencia']:g} {producto['unidad']}."
            )

        costo_total = round(cantidad * producto["costo_unitario"], 2)

        conexion.execute(
            """
            INSERT INTO mermas
                (producto_id, usuario_id, cantidad, motivo,
                 observaciones, costo_total, fecha)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            """,
            (producto_id, usuario_id, cantidad, motivo.strip(),
             observaciones.strip() or None, costo_total)
        )

        conexion.execute(
            "UPDATE productos SET existencia = existencia - ? WHERE id = ?",
            (cantidad, producto_id)
        )

    return costo_total


class ModuloMermas:
    """Apartado Registrar merma: formulario y últimas mermas registradas."""

    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.root = dashboard.root
        self.contenido = dashboard.contenido

        self.productos = {}  # texto del combobox -> fila del producto
        self.var_producto = tk.StringVar()
        self.var_cantidad = tk.StringVar()
        self.var_motivo = tk.StringVar()
        self.var_info = tk.StringVar(value="Selecciona un producto.")
        self.var_costo = tk.StringVar(value="Costo estimado: $0.00")

    # ------------------------------------------------------------------
    def mostrar(self):
        d = self.dashboard
        d.limpiar_contenido()
        d.titulo_pagina(
            "Registrar merma",
            "Registra las pérdidas de productos de la heladería."
        )

        cuerpo = tk.Frame(self.contenido, bg=d.FONDO)
        cuerpo.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        cuerpo.columnconfigure(0, weight=0)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        self.crear_formulario(cuerpo)
        self.crear_tabla_recientes(cuerpo)

        self.cargar_productos()
        self.cargar_recientes()

    # ------------------------------------------------------------------
    def crear_formulario(self, padre):
        d = self.dashboard

        tarjeta = tk.Frame(
            padre,
            bg=d.BLANCO,
            highlightbackground=d.BORDE,
            highlightthickness=1
        )
        tarjeta.grid(row=0, column=0, sticky="ns", padx=(0, 16))

        def etiqueta(texto):
            tk.Label(
                tarjeta,
                text=texto,
                font=("Segoe UI", 10, "bold"),
                bg=d.BLANCO,
                fg=d.VERDE_OSCURO
            ).pack(anchor="w", padx=24, pady=(14, 4))

        tk.Label(
            tarjeta,
            text="Nueva merma",
            font=("Segoe UI", 16, "bold"),
            bg=d.BLANCO,
            fg=d.VERDE_OSCURO
        ).pack(anchor="w", padx=24, pady=(20, 0))

        etiqueta("Producto")
        self.combo_producto = ttk.Combobox(
            tarjeta,
            textvariable=self.var_producto,
            state="readonly",
            width=30,
            font=("Segoe UI", 10)
        )
        self.combo_producto.pack(padx=24, anchor="w")
        self.combo_producto.bind("<<ComboboxSelected>>", self.al_elegir_producto)

        tk.Label(
            tarjeta,
            textvariable=self.var_info,
            font=("Segoe UI", 9),
            bg=d.BLANCO,
            fg=d.TEXTO_SECUNDARIO,
            justify="left"
        ).pack(anchor="w", padx=24, pady=(4, 0))

        etiqueta("Cantidad")
        entrada = tk.Entry(
            tarjeta,
            textvariable=self.var_cantidad,
            font=("Segoe UI", 11),
            relief="flat",
            highlightbackground=d.BORDE,
            highlightcolor=d.VERDE_CLARO,
            highlightthickness=1,
            width=32
        )
        entrada.pack(padx=24, anchor="w", ipady=5)
        self.var_cantidad.trace_add("write", lambda *_: self.actualizar_costo())

        tk.Label(
            tarjeta,
            textvariable=self.var_costo,
            font=("Segoe UI", 9, "bold"),
            bg=d.BLANCO,
            fg=d.VERDE_CLARO
        ).pack(anchor="w", padx=24, pady=(4, 0))

        etiqueta("Motivo")
        ttk.Combobox(
            tarjeta,
            textvariable=self.var_motivo,
            values=MOTIVOS,
            state="readonly",
            width=30,
            font=("Segoe UI", 10)
        ).pack(padx=24, anchor="w")

        etiqueta("Observaciones (opcional)")
        self.txt_observaciones = tk.Text(
            tarjeta,
            height=4,
            width=32,
            font=("Segoe UI", 10),
            relief="flat",
            highlightbackground=d.BORDE,
            highlightcolor=d.VERDE_CLARO,
            highlightthickness=1
        )
        self.txt_observaciones.pack(padx=24, anchor="w")

        tk.Button(
            tarjeta,
            text="REGISTRAR MERMA",
            command=self.guardar,
            font=("Segoe UI", 10, "bold"),
            bg=d.VERDE_CLARO,
            fg=d.BLANCO,
            activebackground="#689F38",
            activeforeground=d.BLANCO,
            relief="flat",
            cursor="hand2",
            pady=10
        ).pack(fill="x", padx=24, pady=(20, 24))

    # ------------------------------------------------------------------
    def crear_tabla_recientes(self, padre):
        d = self.dashboard

        marco = tk.Frame(
            padre,
            bg=d.BLANCO,
            highlightbackground=d.BORDE,
            highlightthickness=1
        )
        marco.grid(row=0, column=1, sticky="nsew")

        tk.Label(
            marco,
            text="Últimas mermas registradas",
            font=("Segoe UI", 13, "bold"),
            bg=d.BLANCO,
            fg=d.VERDE_OSCURO
        ).pack(anchor="w", padx=20, pady=(16, 8))

        tabla_marco, self.tabla = crear_tabla(d, marco, [
            ("fecha", "Fecha", 95, "w"),
            ("producto", "Producto", 105, "w"),
            ("cantidad", "Cantidad", 80, "center"),
            ("motivo", "Motivo", 115, "w"),
            ("costo", "Costo", 70, "e"),
        ])
        tabla_marco.configure(highlightthickness=0)
        tabla_marco.pack(fill="both", expand=True, padx=4, pady=(0, 6))

    # ------------------------------------------------------------------
    def cargar_productos(self):
        self.productos = {}

        with obtener_conexion() as conexion:
            filas = conexion.execute(
                """
                SELECT id, nombre, unidad, costo_unitario, existencia
                FROM productos
                WHERE activo = 1
                ORDER BY nombre
                """
            ).fetchall()

        for fila in filas:
            self.productos[fila["nombre"]] = fila

        self.combo_producto["values"] = list(self.productos.keys())

        if not self.productos:
            self.var_info.set(
                "No hay productos activos. Agrégalos en el apartado Productos."
            )

    def producto_actual(self):
        return self.productos.get(self.var_producto.get())

    def al_elegir_producto(self, _evento=None):
        p = self.producto_actual()
        if p:
            self.var_info.set(
                f"Disponible: {p['existencia']:g} {p['unidad']}  ·  "
                f"Costo: ${p['costo_unitario']:,.2f} por {p['unidad']}"
            )
        self.actualizar_costo()

    def actualizar_costo(self):
        p = self.producto_actual()
        try:
            cantidad = float(self.var_cantidad.get())
        except ValueError:
            cantidad = 0

        total = cantidad * p["costo_unitario"] if p and cantidad > 0 else 0
        self.var_costo.set(f"Costo estimado: ${total:,.2f}")

    def cargar_recientes(self):
        self.tabla.delete(*self.tabla.get_children())

        with obtener_conexion() as conexion:
            filas = conexion.execute(
                """
                SELECT m.fecha, p.nombre AS producto, p.unidad,
                       m.cantidad, m.motivo, m.costo_total
                FROM mermas m
                JOIN productos p ON p.id = m.producto_id
                ORDER BY m.id DESC
                LIMIT 20
                """
            ).fetchall()

        for f in filas:
            self.tabla.insert("", "end", values=(
                f"{f['fecha'][8:10]}/{f['fecha'][5:7]} {f['fecha'][11:16]}",
                f["producto"],
                f"{f['cantidad']:g} {f['unidad']}",
                f["motivo"],
                f"${f['costo_total']:,.2f}",
            ))

    # ------------------------------------------------------------------
    def guardar(self):
        p = self.producto_actual()

        if p is None:
            messagebox.showwarning(
                "Producto requerido", "Selecciona un producto.")
            return

        try:
            costo = registrar_merma(
                p["id"],
                self.dashboard.usuario_id,
                self.var_cantidad.get().strip(),
                self.var_motivo.get(),
                self.txt_observaciones.get("1.0", "end")
            )
        except ErrorMerma as error:
            messagebox.showwarning("No se pudo registrar", str(error))
            return

        messagebox.showinfo(
            "Merma registrada",
            f"Se registró la merma por ${costo:,.2f}."
        )

        # Limpiar formulario y refrescar datos
        self.var_cantidad.set("")
        self.var_motivo.set("")
        self.txt_observaciones.delete("1.0", "end")
        self.cargar_productos()
        self.al_elegir_producto()
        self.cargar_recientes()
