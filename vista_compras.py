import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

import ui_tema
from base_datos import obtener_conexion, registrar_movimiento_inventario
from ui_comunes import Tarjeta, crear_kpi, crear_tabla, crear_logo


def leer_numero(texto):
    texto = texto.strip().replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


class ModuloCompras:

    # Paleta pastel compartida con el resto del sistema
    VERDE_OSCURO = ui_tema.VERDE_OSCURO
    VERDE_MEDIO = ui_tema.VERDE_PRIMARIO
    VERDE_CLARO = ui_tema.VERDE_SUAVE
    VERDE_HOVER = ui_tema.VERDE_HOVER
    ENCABEZADO = ui_tema.FONDO
    FONDO_GENERAL = ui_tema.FONDO
    TEXTO_SUAVE = ui_tema.TEXTO_SECUNDARIO
    BLANCO = ui_tema.BLANCO
    TEXTO_MAIN = ui_tema.TEXTO
    TEXTO_MUTED = ui_tema.TEXTO_SECUNDARIO
    GRIS_BORDE = ui_tema.BORDE
    VERDE_ACTIVO = ui_tema.VERDE_ACTIVO

    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.root = dashboard.root
        self.contenido = dashboard.contenido

        self.proveedores = {}
        self.productos = {}
        self.renglones = {}

        self.var_proveedor = tk.StringVar()
        self.var_fecha = tk.StringVar(value=date.today().isoformat())
        self.var_producto = tk.StringVar()
        self.var_cantidad = tk.StringVar()
        self.var_precio = tk.StringVar()
        self.var_total = tk.StringVar(value="$0.00")
        
        self.var_kpi_total_mes = tk.StringVar(value="$0.00")
        self.var_kpi_ordenes = tk.StringVar(value="0")

    def mostrar(self):
        d = self.dashboard
        d.limpiar_contenido()
        self.contenido.config(bg=self.FONDO_GENERAL)

        header = tk.Frame(self.contenido, bg=self.ENCABEZADO, height=92)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_content = tk.Frame(header, bg=self.ENCABEZADO)
        header_content.pack(fill="both", expand=True, padx=32, pady=12)

        # El logo va sobre una tarjeta blanca para conservar su color original
        marca = Tarjeta(header_content, bg=self.BLANCO, padding=8)
        marca.pack(side="left", padx=(0, 18))
        self.logo = crear_logo(
            marca.cuerpo, bg=self.BLANCO, alto=46, fg=self.VERDE_OSCURO
        )
        self.logo.pack()

        textos_header = tk.Frame(header_content, bg=self.ENCABEZADO)
        textos_header.pack(side="left", fill="y")

        tk.Label(
            textos_header, text="Registro de compras",
            font=ui_tema.fuente_titulo(22), bg=self.ENCABEZADO,
            fg=self.VERDE_OSCURO, anchor="w"
        ).pack(anchor="w", pady=(4, 0))

        tk.Label(
            textos_header, text="Registra las entradas de productos desde proveedores",
            font=ui_tema.fuente_texto(9), bg=self.ENCABEZADO,
            fg=self.TEXTO_SUAVE, anchor="w"
        ).pack(anchor="w", pady=(3, 0))

        self.cargar_catalogos()

        frame_kpis = tk.Frame(self.contenido, bg=self.FONDO_GENERAL)
        frame_kpis.pack(fill="x", padx=32, pady=(0, 14))

        self._crear_kpi(
            frame_kpis, "TOTAL COMPRADO ESTE MES",
            self.var_kpi_total_mes, ui_tema.VERDE_CLARO
        )
        self._crear_kpi(
            frame_kpis, "ÓRDENES REGISTRADAS",
            self.var_kpi_ordenes, ui_tema.VERDE_MEDIO
        )

        cuerpo = tk.Frame(self.contenido, bg=self.FONDO_GENERAL)
        cuerpo.pack(fill="both", expand=True, padx=32, pady=(0, 24))
        cuerpo.columnconfigure(0, weight=5, uniform="c")
        cuerpo.columnconfigure(1, weight=4, uniform="c")
        cuerpo.rowconfigure(0, weight=1)

        self.construir_formulario(cuerpo)
        self.construir_recientes(cuerpo)
        self.cargar_recientes()

    def _crear_kpi(self, padre, titulo, variable, color):
        tarjeta = crear_kpi(
            self.dashboard, padre, titulo, variable=variable, color=color,
        )
        tarjeta.pack(side="left", fill="both", expand=True, padx=6)
        return tarjeta

    def cargar_catalogos(self):
        with obtener_conexion() as conexion:
            self.proveedores = {
                fila["nombre"]: fila["id"]
                for fila in conexion.execute(
                    "SELECT id, nombre FROM proveedores WHERE activo = 1 ORDER BY nombre"
                )
            }
            self.productos = {
                fila["nombre"]: fila
                for fila in conexion.execute(
                    "SELECT id, nombre, unidad, costo_unitario FROM productos WHERE activo = 1 ORDER BY nombre"
                )
            }

    def construir_formulario(self, cuerpo):
        d = self.dashboard

        tarjeta = Tarjeta(cuerpo, bg=self.BLANCO, padding=18)
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        caja = tarjeta.cuerpo

        fila_titulo = tk.Frame(caja, bg=self.BLANCO)
        fila_titulo.pack(fill="x", pady=(0, 12))

        punto = tk.Canvas(
            fila_titulo, width=10, height=10, bg=self.BLANCO,
            highlightthickness=0, bd=0,
        )
        punto.create_oval(0, 0, 10, 10, fill=self.VERDE_MEDIO, outline="")
        punto.pack(side="left", padx=(0, 8))

        tk.Label(
            fila_titulo, text="Nueva orden de compra",
            font=ui_tema.fuente_titulo(14), bg=self.BLANCO,
            fg=self.VERDE_OSCURO,
        ).pack(side="left")

        form = tk.Frame(caja, bg=self.BLANCO)
        form.pack(fill="x")
        for columna, peso in enumerate((3, 2, 2, 2)):
            form.columnconfigure(columna, weight=peso)

        tk.Label(form, text="PROVEEDOR:", font=ui_tema.fuente_texto(8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(2, 2))
        tk.Label(form, text="FECHA (AAAA-MM-DD):", font=ui_tema.fuente_texto(8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=0, column=2, columnspan=2, sticky="w", padx=4, pady=(2, 2))

        ttk.Combobox(
            form, textvariable=self.var_proveedor,
            values=list(self.proveedores.keys()),
            state="readonly", font=ui_tema.fuente_texto(9),
            style="Tema.TCombobox", width=12,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, ipady=3)

        ui_tema.entrada(
            form, textvariable=self.var_fecha, font=ui_tema.fuente_texto(9),
            width=8,
        ).grid(row=1, column=2, columnspan=2, sticky="ew", padx=4, ipady=3)

        tk.Label(form, text="PRODUCTO:", font=ui_tema.fuente_texto(8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=2, column=0, sticky="w", padx=4, pady=(8, 2))
        self.lbl_cantidad = tk.Label(form, text="CANTIDAD:", font=ui_tema.fuente_texto(8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED)
        self.lbl_cantidad.grid(row=2, column=1, sticky="w", padx=4, pady=(8, 2))
        tk.Label(form, text="PRECIO UNIT.:", font=ui_tema.fuente_texto(8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=2, column=2, sticky="w", padx=4, pady=(8, 2))

        combo_producto = ttk.Combobox(
            form, textvariable=self.var_producto,
            values=list(self.productos.keys()),
            state="readonly", font=ui_tema.fuente_texto(9),
            style="Tema.TCombobox", width=12,
        )
        combo_producto.grid(row=3, column=0, sticky="ew", padx=4, ipady=3)
        combo_producto.bind("<<ComboboxSelected>>", self.al_elegir_producto)

        ui_tema.entrada(
            form, textvariable=self.var_cantidad, font=ui_tema.fuente_texto(9),
            width=8,
        ).grid(row=3, column=1, sticky="ew", padx=4, ipady=3)
        ui_tema.entrada(
            form, textvariable=self.var_precio, font=ui_tema.fuente_texto(9),
            width=8,
        ).grid(row=3, column=2, sticky="ew", padx=4, ipady=3)

        ui_tema.boton(
            form, "Agregar", self.agregar_renglon, principal=True,
            fuente=ui_tema.fuente_texto(9, "bold")
        ).grid(row=3, column=3, sticky="ew", padx=4)

        marco, self.tabla_renglones = crear_tabla(d, caja, [
            ("producto", "Producto", 160, "w"),
            ("cantidad", "Cantidad", 90, "center"),
            ("precio", "Precio", 80, "e"),
            ("subtotal", "Subtotal", 90, "e"),
        ])
        self.tabla_renglones.configure(height=3)

        self.tabla_renglones.tag_configure(
            "par", background=ui_tema.FILA_ALTERNA
        )
        self.tabla_renglones.tag_configure("impar", background=self.BLANCO)

        # Los botones y el total se reservan antes que la tabla para que no
        # queden ocultos cuando la ventana es pequeña.
        botones = tk.Frame(caja, bg=self.BLANCO)
        botones.pack(side="bottom", fill="x")
        botones.columnconfigure(0, weight=3)
        botones.columnconfigure(1, weight=1)

        ui_tema.boton(
            botones, "GUARDAR COMPRA", self.guardar, principal=True
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ui_tema.boton(
            botones, "LIMPIAR", self.limpiar
        ).grid(row=0, column=1, sticky="ew")

        pie = tk.Frame(caja, bg=self.BLANCO)
        pie.pack(side="bottom", fill="x", pady=(2, 10))

        ui_tema.boton(
            pie, "Quitar renglón", self.quitar_renglon, peligro=True,
            fuente=ui_tema.fuente_texto(8, "bold")
        ).pack(side="left")

        tk.Label(
            pie, textvariable=self.var_total, font=ui_tema.fuente_titulo(18),
            bg=self.BLANCO, fg=self.VERDE_OSCURO
        ).pack(side="right")
        tk.Label(
            pie, text="TOTAL:", font=ui_tema.fuente_texto(10, "bold"),
            bg=self.BLANCO, fg=self.TEXTO_MUTED
        ).pack(side="right", padx=(0, 6))

        marco.pack(fill="both", expand=True, pady=(14, 8))

    def construir_recientes(self, cuerpo):
        d = self.dashboard

        tarjeta = Tarjeta(cuerpo, bg=self.BLANCO, padding=18)
        tarjeta.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        caja = tarjeta.cuerpo

        fila_titulo = tk.Frame(caja, bg=self.BLANCO)
        fila_titulo.pack(fill="x", pady=(0, 12))

        punto = tk.Canvas(
            fila_titulo, width=10, height=10, bg=self.BLANCO,
            highlightthickness=0, bd=0,
        )
        punto.create_oval(0, 0, 10, 10, fill=self.VERDE_MEDIO, outline="")
        punto.pack(side="left", padx=(0, 8))

        tk.Label(
            fila_titulo, text="Compras recientes",
            font=ui_tema.fuente_titulo(14), bg=self.BLANCO,
            fg=self.VERDE_OSCURO,
        ).pack(side="left")

        marco, self.tabla_recientes = crear_tabla(d, caja, [
            ("fecha", "Fecha", 105, "w"),
            ("proveedor", "Proveedor", 140, "w"),
            ("total", "Total", 100, "e"),
        ])
        self.tabla_recientes.bind("<Double-1>", lambda evento: self.ver_detalle())

        tk.Label(
            caja, text="Doble clic en una compra para ver su detalle.",
            font=ui_tema.fuente_texto(8, "italic"), bg=self.BLANCO,
            fg=self.TEXTO_MUTED,
        ).pack(side="bottom", anchor="w", pady=(10, 0))

        marco.pack(fill="both", expand=True)

    def al_elegir_producto(self, _evento=None):
        producto = self.productos.get(self.var_producto.get())
        if not producto:
            return
        self.lbl_cantidad.configure(text=f"CANTIDAD ({producto['unidad']}):")
        self.var_precio.set(f"{producto['costo_unitario']:g}")

    def agregar_renglon(self):
        producto = self.productos.get(self.var_producto.get())
        if not producto:
            messagebox.showwarning("Falta producto", "Selecciona un producto.", parent=self.root)
            return

        cantidad = leer_numero(self.var_cantidad.get())
        if cantidad is None or cantidad <= 0:
            messagebox.showwarning("Cantidad inválida", "Escribe una cantidad numérica mayor a 0.", parent=self.root)
            return

        precio = leer_numero(self.var_precio.get())
        if precio is None or precio < 0:
            messagebox.showwarning("Precio inválido", "Escribe un precio numérico válido.", parent=self.root)
            return

        anterior = self.renglones.get(producto["id"])
        if anterior:
            cantidad += anterior["cantidad"]

        self.renglones[producto["id"]] = {
            "nombre": producto["nombre"],
            "unidad": producto["unidad"],
            "cantidad": cantidad,
            "precio": precio,
        }

        self.var_producto.set("")
        self.var_cantidad.set("")
        self.var_precio.set("")
        self.lbl_cantidad.configure(text="CANTIDAD:")
        self.pintar_renglones()

    def quitar_renglon(self):
        seleccion = self.tabla_renglones.selection()
        if not seleccion:
            messagebox.showwarning("Sin selección", "Selecciona un renglón para quitarlo.", parent=self.root)
            return
        self.renglones.pop(int(seleccion[0]), None)
        self.pintar_renglones()

    def pintar_renglones(self):
        self.tabla_renglones.delete(*self.tabla_renglones.get_children())
        total = 0

        for idx, (producto_id, renglon) in enumerate(self.renglones.items()):
            subtotal = renglon["cantidad"] * renglon["precio"]
            total += subtotal
            tag = "par" if idx % 2 == 0 else "impar"
            self.tabla_renglones.insert(
                "", "end", iid=str(producto_id),
                values=(
                    renglon["nombre"],
                    f"{renglon['cantidad']:g} {renglon['unidad']}",
                    f"${renglon['precio']:,.2f}",
                    f"${subtotal:,.2f}",
                ),
                tags=(tag,)
            )

        self.var_total.set(f"${total:,.2f}")

    def limpiar(self):
        self.renglones = {}
        self.var_proveedor.set("")
        self.var_fecha.set(date.today().isoformat())
        self.var_producto.set("")
        self.var_cantidad.set("")
        self.var_precio.set("")
        self.lbl_cantidad.configure(text="CANTIDAD:")
        self.pintar_renglones()

    def guardar(self):
        padre = self.root

        proveedor_id = self.proveedores.get(self.var_proveedor.get())
        if not proveedor_id:
            messagebox.showwarning("Falta el proveedor", "Selecciona un proveedor.", parent=padre)
            return

        if not self.renglones:
            messagebox.showwarning("Compra vacía", "Agrega al menos un producto a la compra.", parent=padre)
            return

        try:
            fecha = datetime.strptime(self.var_fecha.get().strip(), "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Fecha inválida", "Usa el formato AAAA-MM-DD.", parent=padre)
            return

        if fecha.date() > date.today():
            messagebox.showwarning("Fecha inválida", "La fecha no puede ser posterior a hoy.", parent=padre)
            return

        total = round(sum(r["cantidad"] * r["precio"] for r in self.renglones.values()), 2)
        fecha_hora = f"{fecha:%Y-%m-%d} {datetime.now():%H:%M:%S}"

        try:
            with obtener_conexion() as conexion:
                compra_id = conexion.execute(
                    """
                    INSERT INTO compras (proveedor_id, usuario_id, fecha, total)
                    VALUES (?, ?, ?, ?)
                    """,
                    (proveedor_id, self.dashboard.usuario_id, fecha_hora, total)
                ).lastrowid

                for producto_id, renglon in self.renglones.items():
                    conexion.execute(
                        """
                        INSERT INTO detalle_compras
                            (compra_id, producto_id, cantidad, precio_unitario)
                        VALUES (?, ?, ?, ?)
                        """,
                        (compra_id, producto_id, renglon["cantidad"], renglon["precio"])
                    )

                    conexion.execute(
                        """
                        UPDATE productos
                        SET existencia = existencia + ?,
                            costo_unitario = ?
                        WHERE id = ?
                        """,
                        (renglon["cantidad"], renglon["precio"], producto_id)
                    )

                    registrar_movimiento_inventario(
                        conexion, producto_id, entrada=renglon["cantidad"]
                    )
        except Exception as error:
            messagebox.showerror("Error al guardar", f"No se pudo registrar la compra.\n\n{error}", parent=padre)
            return

        messagebox.showinfo("Compra registrada", f"Se registró la compra exitosamente.\nTotal: ${total:,.2f}", parent=padre)

        self.cargar_catalogos()
        self.limpiar()
        self.cargar_recientes()

    def cargar_recientes(self):
        self.tabla_recientes.delete(*self.tabla_recientes.get_children())

        with obtener_conexion() as conexion:
            compras = conexion.execute(
                """
                SELECT c.id, c.fecha, p.nombre AS proveedor, c.total
                FROM compras c
                JOIN proveedores p ON p.id = c.proveedor_id
                ORDER BY c.fecha DESC, c.id DESC
                LIMIT 30
                """
            ).fetchall()

        total_mes = sum(c["total"] for c in compras)
        self.var_kpi_total_mes.set(f"${total_mes:,.2f}")
        self.var_kpi_ordenes.set(f"{len(compras)}")

        for idx, compra in enumerate(compras):
            tag = "par" if idx % 2 == 0 else "impar"
            self.tabla_recientes.insert(
                "", "end", iid=str(compra["id"]),
                values=(
                    compra["fecha"][:10],
                    compra["proveedor"],
                    f"${compra['total']:,.2f}",
                ),
                tags=(tag,)
            )

    def ver_detalle(self):
        seleccion = self.tabla_recientes.selection()
        if not seleccion:
            return

        with obtener_conexion() as conexion:
            compra = conexion.execute(
                """
                SELECT c.fecha, c.total, p.nombre AS proveedor
                FROM compras c
                JOIN proveedores p ON p.id = c.proveedor_id
                WHERE c.id = ?
                """,
                (int(seleccion[0]),)
            ).fetchone()

            detalle = conexion.execute(
                """
                SELECT pr.nombre, pr.unidad, d.cantidad, d.precio_unitario
                FROM detalle_compras d
                JOIN productos pr ON pr.id = d.producto_id
                WHERE d.compra_id = ?
                ORDER BY pr.nombre
                """,
                (int(seleccion[0]),)
            ).fetchall()

        top = tk.Toplevel(self.root)
        top.title("Detalle de la Compra - Yogufrut")
        top.geometry("470x460")
        top.config(bg=self.FONDO_GENERAL)
        top.transient(self.root)
        top.grab_set()

        tarjeta = Tarjeta(top, bg=self.BLANCO, padding=22)
        tarjeta.pack(fill="both", expand=True, padx=22, pady=18)
        card = tarjeta.cuerpo

        tk.Label(
            card, text="Recibo de compra",
            font=ui_tema.fuente_titulo(17), bg=self.BLANCO,
            fg=self.VERDE_OSCURO,
        ).pack(anchor="w")

        tk.Frame(card, bg=self.VERDE_MEDIO, height=3, width=46).pack(
            anchor="w", pady=(6, 14)
        )

        tk.Label(card, text=f"Proveedor: {compra['proveedor']}", font=ui_tema.fuente_texto(10, "bold"), bg=self.BLANCO, fg=self.TEXTO_MAIN).pack(anchor="w", pady=(0, 2))
        tk.Label(card, text=f"Fecha: {compra['fecha'][:16]}", font=ui_tema.fuente_texto(9), bg=self.BLANCO, fg=self.TEXTO_MUTED).pack(anchor="w", pady=(0, 10))

        tk.Frame(card, bg=self.GRIS_BORDE, height=1).pack(fill="x", pady=6)

        for r in detalle:
            sub = r['cantidad'] * r['precio_unitario']
            txt = f"— {r['nombre']}: {r['cantidad']:g} {r['unidad']} x ${r['precio_unitario']:,.2f} = ${sub:,.2f}"
            tk.Label(card, text=txt, font=ui_tema.fuente_texto(9), bg=self.BLANCO, fg=self.TEXTO_MAIN, wraplength=380, justify="left").pack(anchor="w", pady=3)

        tk.Frame(card, bg=self.GRIS_BORDE, height=1).pack(fill="x", pady=(10, 6))

        tk.Label(
            card, textvariable=tk.StringVar(value=f"TOTAL: ${compra['total']:,.2f}"),
            font=ui_tema.fuente_titulo(15), bg=self.BLANCO, fg=self.VERDE_OSCURO
        ).pack(anchor="e")

        ui_tema.boton(
            top, "Cerrar", top.destroy, principal=True,
            fuente=ui_tema.fuente_texto(9, "bold")
        ).pack(pady=(0, 18))