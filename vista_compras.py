import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

from base_datos import obtener_conexion, registrar_movimiento_inventario
from ui_comunes import crear_boton, crear_tabla, crear_logo


def leer_numero(texto):
    texto = texto.strip().replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


class ModuloCompras:

    # Paleta basada en el verde del logo de Yogufrut (#A1C534)
    VERDE_OSCURO = "#0F2A22"   # títulos y texto sobre el verde (contraste alto)
    VERDE_MEDIO = "#A1C534"    # botones y acentos: verde del logo
    VERDE_CLARO = "#E6F0BD"    # franjas de título de las tarjetas
    VERDE_HOVER = "#8DB02A"
    ENCABEZADO = "#A1C534"     # banda superior de la pestaña
    FONDO_GENERAL = "#F1F7DD"  # fondo de la pestaña con tinte del mismo verde
    TEXTO_SUAVE = "#2D4410"    # texto secundario sobre el verde
    BLANCO = "#FFFFFF"
    TEXTO_MAIN = "#0F172A"
    TEXTO_MUTED = "#64748B"
    GRIS_BORDE = "#CBD5E1"

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

        header = tk.Frame(self.contenido, bg=self.ENCABEZADO, height=78)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_content = tk.Frame(header, bg=self.ENCABEZADO)
        header_content.pack(fill="both", expand=True, padx=25, pady=7)

        # El logo va sobre una etiqueta blanca para conservar su color original
        # (si existe logo.png junto a main.py se usa; si no, el nombre).
        marca = tk.Frame(header_content, bg=self.BLANCO)
        marca.pack(side="left", padx=(0, 18))
        self.logo = crear_logo(
            marca, bg=self.BLANCO, alto=44, fg=self.VERDE_OSCURO
        )
        self.logo.pack(padx=14, pady=8)

        tk.Label(
            header_content, text="Registro de Compras",
            font=("Segoe UI", 16, "bold"), bg=self.ENCABEZADO, fg=self.VERDE_OSCURO
        ).pack(side="left")

        tk.Label(
            header_content, text="Registra las entradas de productos desde proveedores",
            font=("Segoe UI", 9), bg=self.ENCABEZADO, fg=self.TEXTO_SUAVE
        ).pack(side="right", padx=10)

        self.cargar_catalogos()

        frame_kpis = tk.Frame(self.contenido, bg=self.FONDO_GENERAL)
        frame_kpis.pack(fill="x", padx=25, pady=(10, 10))

        self._crear_kpi(frame_kpis, "TOTAL COMPRADO ESTE MES", self.var_kpi_total_mes, "#A1C534", "💰")
        self._crear_kpi(frame_kpis, "ÓRDENES REGISTRADAS", self.var_kpi_ordenes, "#7A9A22", "📑")

        cuerpo = tk.Frame(self.contenido, bg=self.FONDO_GENERAL)
        cuerpo.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        cuerpo.columnconfigure(0, weight=5, uniform="c")
        cuerpo.columnconfigure(1, weight=4, uniform="c")
        cuerpo.rowconfigure(0, weight=1)

        self.construir_formulario(cuerpo)
        self.construir_recientes(cuerpo)
        self.cargar_recientes()

    def _crear_kpi(self, padre, titulo, variable, color, icono):
        card = tk.Frame(padre, bg=self.BLANCO, bd=1, relief="solid")
        card.config(highlightbackground=self.GRIS_BORDE)
        card.pack(side="left", fill="both", expand=True, padx=4)

        borde = tk.Frame(card, bg=color, width=5)
        borde.pack(side="left", fill="y")

        info = tk.Frame(card, bg=self.BLANCO)
        info.pack(side="left", fill="both", expand=True, padx=12, pady=8)

        tk.Label(info, text=f"{icono} {titulo}", font=("Segoe UI", 8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).pack(anchor="w")
        tk.Label(info, textvariable=variable, font=("Segoe UI", 13, "bold"), bg=self.BLANCO, fg=self.TEXTO_MAIN).pack(anchor="w", pady=(2, 0))

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

        tarjeta = tk.Frame(cuerpo, bg=self.BLANCO, bd=1, relief="solid")
        tarjeta.config(highlightbackground=self.GRIS_BORDE)
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        tk.Frame(tarjeta, bg=self.VERDE_MEDIO, height=6).pack(fill="x")

        header_card = tk.Frame(tarjeta, bg=self.VERDE_CLARO)
        header_card.pack(fill="x", pady=(0, 6))
        tk.Label(
            header_card, text="📝 Nueva Orden de Compra",
            font=("Segoe UI", 11, "bold"), bg=self.VERDE_CLARO, fg=self.VERDE_OSCURO
        ).pack(anchor="w", padx=16, pady=8)

        form = tk.Frame(tarjeta, bg=self.BLANCO)
        form.pack(fill="x", padx=16, pady=(4, 6))
        for columna, peso in enumerate((4, 2, 2, 1)):
            form.columnconfigure(columna, weight=peso)

        tk.Label(form, text="PROVEEDOR:", font=("Segoe UI", 8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(2, 2))
        tk.Label(form, text="FECHA (AAAA-MM-DD):", font=("Segoe UI", 8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=0, column=2, columnspan=2, sticky="w", padx=4, pady=(2, 2))

        ttk.Combobox(
            form, textvariable=self.var_proveedor,
            values=list(self.proveedores.keys()),
            state="readonly", font=("Segoe UI", 9)
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, ipady=3)

        tk.Entry(
            form, textvariable=self.var_fecha, font=("Segoe UI", 9),
            relief="solid", bd=1, bg="#F8FAFC"
        ).grid(row=1, column=2, columnspan=2, sticky="ew", padx=4, ipady=3)

        tk.Label(form, text="PRODUCTO:", font=("Segoe UI", 8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=2, column=0, sticky="w", padx=4, pady=(6, 2))
        self.lbl_cantidad = tk.Label(form, text="CANTIDAD:", font=("Segoe UI", 8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED)
        self.lbl_cantidad.grid(row=2, column=1, sticky="w", padx=4, pady=(6, 2))
        tk.Label(form, text="PRECIO UNIT.:", font=("Segoe UI", 8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=2, column=2, sticky="w", padx=4, pady=(6, 2))

        combo_producto = ttk.Combobox(
            form, textvariable=self.var_producto,
            values=list(self.productos.keys()),
            state="readonly", font=("Segoe UI", 9)
        )
        combo_producto.grid(row=3, column=0, sticky="ew", padx=4, ipady=3)
        combo_producto.bind("<<ComboboxSelected>>", self.al_elegir_producto)

        tk.Entry(form, textvariable=self.var_cantidad, font=("Segoe UI", 9), relief="solid", bd=1, bg="#F8FAFC").grid(row=3, column=1, sticky="ew", padx=4, ipady=3)
        tk.Entry(form, textvariable=self.var_precio, font=("Segoe UI", 9), relief="solid", bd=1, bg="#F8FAFC").grid(row=3, column=2, sticky="ew", padx=4, ipady=3)
        
        tk.Button(
            form, text="＋ Agregar", font=("Segoe UI", 9, "bold"),
            bg=self.VERDE_MEDIO, fg=self.VERDE_OSCURO, activebackground=self.VERDE_HOVER,
            activeforeground=self.VERDE_OSCURO,
            relief="flat", cursor="hand2", command=self.agregar_renglon
        ).grid(row=3, column=3, sticky="ew", padx=4, ipady=3)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background=self.BLANCO,
                        foreground=self.TEXTO_MAIN,
                        rowheight=26,
                        font=("Segoe UI", 9),
                        fieldbackground=self.BLANCO,
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        background=self.VERDE_MEDIO,
                        foreground=self.VERDE_OSCURO,
                        font=("Segoe UI", 9, "bold"),
                        relief="flat")
        style.map("Treeview", background=[("selected", self.VERDE_MEDIO)], foreground=[("selected", self.VERDE_OSCURO)])

        marco, self.tabla_renglones = crear_tabla(d, tarjeta, [
            ("producto", "Producto", 160, "w"),
            ("cantidad", "Cantidad", 90, "center"),
            ("precio", "Precio", 80, "e"),
            ("subtotal", "Subtotal", 90, "e"),
        ])
        marco.configure(highlightthickness=0)
        marco.pack(fill="both", expand=True, padx=12, pady=6)
        self.tabla_renglones.configure(height=4)
        
        self.tabla_renglones.tag_configure("par", background="#F8FAFC")
        self.tabla_renglones.tag_configure("impar", background=self.BLANCO)

        pie = tk.Frame(tarjeta, bg=self.BLANCO)
        pie.pack(fill="x", padx=16, pady=(2, 8))

        tk.Button(
            pie, text="🗑 Quitar renglón", font=("Segoe UI", 8, "bold"),
            bg="#FEE2E2", fg="#B91C1C", activebackground="#FECACA",
            relief="flat", cursor="hand2", command=self.quitar_renglon
        ).pack(side="left", ipadx=8, ipady=4)

        tk.Label(
            pie, textvariable=self.var_total, font=("Segoe UI", 16, "bold"),
            bg=self.BLANCO, fg=self.VERDE_OSCURO
        ).pack(side="right")
        tk.Label(
            pie, text="TOTAL:", font=("Segoe UI", 10, "bold"),
            bg=self.BLANCO, fg=self.TEXTO_MUTED
        ).pack(side="right", padx=(0, 6))

        botones = tk.Frame(tarjeta, bg=self.BLANCO)
        botones.pack(fill="x", padx=16, pady=(0, 14))
        botones.columnconfigure(0, weight=3)
        botones.columnconfigure(1, weight=1)

        tk.Button(
            botones, text="GUARDAR COMPRA", command=self.guardar,
            font=("Segoe UI", 10, "bold"), bg=self.VERDE_MEDIO, fg=self.VERDE_OSCURO,
            activebackground=self.VERDE_HOVER, activeforeground=self.VERDE_OSCURO,
            relief="flat", cursor="hand2", pady=8
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        tk.Button(
            botones, text="LIMPIAR", command=self.limpiar,
            font=("Segoe UI", 9, "bold"), bg=self.VERDE_CLARO, fg=self.VERDE_OSCURO,
            activebackground="#D6E5A0", relief="flat", cursor="hand2", pady=8
        ).grid(row=0, column=1, sticky="ew")

    def construir_recientes(self, cuerpo):
        d = self.dashboard

        tarjeta_recientes = tk.Frame(cuerpo, bg=self.BLANCO, bd=1, relief="solid")
        tarjeta_recientes.config(highlightbackground=self.GRIS_BORDE)
        tarjeta_recientes.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        tk.Frame(tarjeta_recientes, bg=self.VERDE_MEDIO, height=6).pack(fill="x")

        header_card = tk.Frame(tarjeta_recientes, bg=self.VERDE_CLARO)
        header_card.pack(fill="x", pady=(0, 6))
        tk.Label(
            header_card, text="📋 Historial de Compras Recientes",
            font=("Segoe UI", 11, "bold"), bg=self.VERDE_CLARO, fg=self.VERDE_OSCURO
        ).pack(anchor="w", padx=16, pady=8)

        marco, self.tabla_recientes = crear_tabla(d, tarjeta_recientes, [
            ("fecha", "Fecha", 105, "w"),
            ("proveedor", "Proveedor", 140, "w"),
            ("total", "Total", 100, "e"),
        ])
        marco.pack(fill="both", expand=True, padx=12, pady=6)
        self.tabla_recientes.bind("<Double-1>", lambda evento: self.ver_detalle())

        tk.Label(
            tarjeta_recientes, text="💡 Doble clic en una compra para ver su detalle.",
            font=("Segoe UI", 8, "italic"), bg=self.BLANCO, fg=self.TEXTO_MUTED
        ).pack(anchor="w", padx=16, pady=(0, 12))

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
        top.geometry("450x420")
        top.config(bg=self.FONDO_GENERAL)
        top.transient(self.root)
        top.grab_set()

        head = tk.Frame(top, bg=self.VERDE_MEDIO)
        head.pack(fill="x")
        tk.Label(head, text="🧾 Recibo de Compra", font=("Segoe UI", 12, "bold"), bg=self.VERDE_MEDIO, fg=self.VERDE_OSCURO).pack(pady=10)

        card = tk.Frame(top, bg=self.BLANCO, bd=1, relief="solid")
        card.pack(fill="both", expand=True, padx=20, pady=15)

        tk.Label(card, text=f"Proveedor: {compra['proveedor']}", font=("Segoe UI", 10, "bold"), bg=self.BLANCO, fg=self.TEXTO_MAIN).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(card, text=f"Fecha: {compra['fecha'][:16]}", font=("Segoe UI", 9), bg=self.BLANCO, fg=self.TEXTO_MUTED).pack(anchor="w", padx=12, pady=(0, 10))

        tk.Frame(card, bg=self.GRIS_BORDE, height=1).pack(fill="x", padx=12, pady=4)

        for r in detalle:
            sub = r['cantidad'] * r['precio_unitario']
            txt = f"• {r['nombre']}: {r['cantidad']:g} {r['unidad']} x ${r['precio_unitario']:,.2f} = ${sub:,.2f}"
            tk.Label(card, text=txt, font=("Segoe UI", 9), bg=self.BLANCO, fg=self.TEXTO_MAIN).pack(anchor="w", padx=12, pady=2)

        tk.Frame(card, bg=self.GRIS_BORDE, height=1).pack(fill="x", padx=12, pady=8)

        tk.Label(card, text=f"TOTAL: ${compra['total']:,.2f}", font=("Segoe UI", 13, "bold"), bg=self.BLANCO, fg=self.VERDE_OSCURO).pack(anchor="e", padx=12, pady=5)

        tk.Button(top, text="Cerrar", font=("Segoe UI", 9, "bold"), bg=self.VERDE_MEDIO, fg=self.VERDE_OSCURO, relief="flat", command=top.destroy).pack(pady=(0, 15), ipadx=20)