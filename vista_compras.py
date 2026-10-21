import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

from base_datos import obtener_conexion, registrar_movimiento_inventario
from ui_comunes import crear_boton, crear_tabla


def leer_numero(texto):
    """Convierte el texto a float; devuelve None si no es un número."""
    texto = texto.strip().replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


class ModuloCompras:
    """Apartado Compras: registra pedidos a proveedores y su detalle."""

    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.root = dashboard.root
        self.contenido = dashboard.contenido

        self.proveedores = {}
        self.productos = {}
        # Renglones de la compra en captura: producto_id -> dict
        self.renglones = {}

        self.var_proveedor = tk.StringVar()
        self.var_fecha = tk.StringVar(value=date.today().isoformat())
        self.var_producto = tk.StringVar()
        self.var_cantidad = tk.StringVar()
        self.var_precio = tk.StringVar()
        self.var_total = tk.StringVar(value="$0.00")


    def mostrar(self):
        d = self.dashboard
        d.limpiar_contenido()
        d.titulo_pagina(
            "Compras",
            "Registra los pedidos a proveedores. Las compras suben la existencia."
        )

        self.cargar_catalogos()

        cuerpo = tk.Frame(self.contenido, bg=d.FONDO)
        cuerpo.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        cuerpo.columnconfigure(0, weight=3, uniform="c")
        cuerpo.columnconfigure(1, weight=2, uniform="c")
        cuerpo.rowconfigure(0, weight=1)

        self.construir_formulario(cuerpo)
        self.construir_recientes(cuerpo)
        self.cargar_recientes()

    def cargar_catalogos(self):
        with obtener_conexion() as conexion:
            self.proveedores = {
                fila["nombre"]: fila["id"]
                for fila in conexion.execute(
                    "SELECT id, nombre FROM proveedores "
                    "WHERE activo = 1 ORDER BY nombre"
                )
            }
            self.productos = {
                fila["nombre"]: fila
                for fila in conexion.execute(
                    "SELECT id, nombre, unidad, costo_unitario FROM productos "
                    "WHERE activo = 1 ORDER BY nombre"
                )
            }

    def etiqueta(self, padre, texto, fila, columna, columnspan=1):
        d = self.dashboard
        etiqueta = tk.Label(
            padre, text=texto, font=("Segoe UI", 9, "bold"),
            bg=d.BLANCO, fg=d.TEXTO, anchor="w"
        )
        etiqueta.grid(
            row=fila, column=columna, columnspan=columnspan,
            sticky="w", padx=4, pady=(8, 2)
        )
        return etiqueta

    def entrada(self, padre, variable):
        d = self.dashboard
        return tk.Entry(
            padre, textvariable=variable, font=("Segoe UI", 11),
            relief="flat", bd=0, bg=d.BLANCO, fg=d.TEXTO,
            highlightthickness=1, highlightbackground=d.BORDE,
            highlightcolor=d.VERDE_CLARO, width=10
        )

    def construir_formulario(self, cuerpo):
        d = self.dashboard

        tarjeta = tk.Frame(
            cuerpo, bg=d.BLANCO,
            highlightbackground=d.BORDE, highlightthickness=1
        )
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Frame(tarjeta, bg=d.VERDE_CLARO, height=4).pack(fill="x")

        form = tk.Frame(tarjeta, bg=d.BLANCO)
        form.pack(fill="x", padx=16, pady=(4, 6))
        for columna, peso in enumerate((4, 2, 2, 1)):
            form.columnconfigure(columna, weight=peso)

        # Proveedor y fecha
        self.etiqueta(form, "PROVEEDOR", 0, 0, columnspan=2)
        self.etiqueta(form, "FECHA (AAAA-MM-DD)", 0, 2, columnspan=2)

        ttk.Combobox(
            form, textvariable=self.var_proveedor,
            values=list(self.proveedores.keys()),
            state="readonly", font=("Segoe UI", 10)
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, ipady=3)

        self.entrada(form, self.var_fecha).grid(
            row=1, column=2, columnspan=2, sticky="ew", padx=4, ipady=4
        )

        # Renglón a agregar
        self.etiqueta(form, "PRODUCTO", 2, 0)
        self.lbl_cantidad = self.etiqueta(form, "CANTIDAD", 2, 1)
        self.etiqueta(form, "PRECIO UNIT.", 2, 2)

        combo_producto = ttk.Combobox(
            form, textvariable=self.var_producto,
            values=list(self.productos.keys()),
            state="readonly", font=("Segoe UI", 10)
        )
        combo_producto.grid(row=3, column=0, sticky="ew", padx=4, ipady=3)
        combo_producto.bind("<<ComboboxSelected>>", self.al_elegir_producto)

        self.entrada(form, self.var_cantidad).grid(
            row=3, column=1, sticky="ew", padx=4, ipady=4
        )
        self.entrada(form, self.var_precio).grid(
            row=3, column=2, sticky="ew", padx=4, ipady=4
        )
        crear_boton(
            d, form, "Agregar", self.agregar_renglon, principal=True
        ).grid(row=3, column=3, sticky="ew", padx=4)

        # Renglones de la compra
        marco, self.tabla_renglones = crear_tabla(d, tarjeta, [
            ("producto", "Producto", 170, "w"),
            ("cantidad", "Cantidad", 90, "center"),
            ("precio", "Precio", 80, "e"),
            ("subtotal", "Subtotal", 90, "e"),
        ])
        marco.configure(highlightthickness=0)
        marco.pack(fill="both", expand=True, padx=8)
        # Pocas filas para que el total y los botones siempre quepan
        self.tabla_renglones.configure(height=6)

        pie = tk.Frame(tarjeta, bg=d.BLANCO)
        pie.pack(fill="x", padx=16, pady=(4, 6))

        crear_boton(
            d, pie, "Quitar renglón", self.quitar_renglon
        ).pack(side="left")

        tk.Label(
            pie, textvariable=self.var_total, font=("Segoe UI", 18, "bold"),
            bg=d.BLANCO, fg=d.VERDE_OSCURO
        ).pack(side="right")
        tk.Label(
            pie, text="Total:", font=("Segoe UI", 11),
            bg=d.BLANCO, fg=d.TEXTO_SECUNDARIO
        ).pack(side="right", padx=(0, 8))

        botones = tk.Frame(tarjeta, bg=d.BLANCO)
        botones.pack(fill="x", padx=16, pady=(0, 14))
        botones.columnconfigure(0, weight=3)
        botones.columnconfigure(1, weight=1)

        tk.Button(
            botones, text="GUARDAR COMPRA", command=self.guardar,
            font=("Segoe UI", 11, "bold"), bg=d.VERDE_CLARO, fg=d.BLANCO,
            activebackground="#6AA336", activeforeground=d.BLANCO,
            relief="flat", bd=0, cursor="hand2", pady=9
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        tk.Button(
            botones, text="LIMPIAR", command=self.limpiar,
            font=("Segoe UI", 10, "bold"), bg="#E8EFEA", fg=d.VERDE_OSCURO,
            activebackground=d.VERDE_SUAVE, activeforeground=d.VERDE_OSCURO,
            relief="flat", bd=0, cursor="hand2", pady=9
        ).grid(row=0, column=1, sticky="ew")

    def construir_recientes(self, cuerpo):
        d = self.dashboard

        lado = tk.Frame(cuerpo, bg=d.FONDO)
        lado.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        tk.Label(
            lado, text="Compras recientes", font=("Segoe UI", 13, "bold"),
            bg=d.FONDO, fg=d.VERDE_OSCURO
        ).pack(anchor="w", pady=(0, 6))

        marco, self.tabla_recientes = crear_tabla(d, lado, [
            ("fecha", "Fecha", 95, "w"),
            ("proveedor", "Proveedor", 130, "w"),
            ("total", "Total", 85, "e"),
        ])
        marco.pack(fill="both", expand=True)
        self.tabla_recientes.bind(
            "<Double-1>", lambda evento: self.ver_detalle()
        )

        tk.Label(
            lado, text="Doble clic en una compra para ver su detalle.",
            font=("Segoe UI", 9), bg=d.FONDO, fg=d.TEXTO_SECUNDARIO
        ).pack(anchor="w", pady=(4, 0))


    def al_elegir_producto(self, _evento=None):
        producto = self.productos.get(self.var_producto.get())
        if not producto:
            return
        self.lbl_cantidad.configure(text=f"CANTIDAD ({producto['unidad']})")
        self.var_precio.set(f"{producto['costo_unitario']:g}")

    def agregar_renglon(self):
        producto = self.productos.get(self.var_producto.get())
        if not producto:
            messagebox.showwarning(
                "Falta el producto", "Selecciona un producto.",
                parent=self.root
            )
            return

        cantidad = leer_numero(self.var_cantidad.get())
        if cantidad is None or cantidad <= 0:
            messagebox.showwarning(
                "Cantidad inválida",
                "Escribe una cantidad numérica mayor a 0.",
                parent=self.root
            )
            return

        precio = leer_numero(self.var_precio.get())
        if precio is None or precio < 0:
            messagebox.showwarning(
                "Precio inválido",
                "Escribe un precio numérico mayor o igual a 0.",
                parent=self.root
            )
            return

        # Si el producto ya estaba en la compra se suma la cantidad
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
        self.lbl_cantidad.configure(text="CANTIDAD")
        self.pintar_renglones()

    def quitar_renglon(self):
        seleccion = self.tabla_renglones.selection()
        if not seleccion:
            messagebox.showwarning(
                "Sin selección", "Selecciona un renglón para quitarlo.",
                parent=self.root
            )
            return
        self.renglones.pop(int(seleccion[0]), None)
        self.pintar_renglones()

    def pintar_renglones(self):
        self.tabla_renglones.delete(*self.tabla_renglones.get_children())
        total = 0

        for producto_id, renglon in self.renglones.items():
            subtotal = renglon["cantidad"] * renglon["precio"]
            total += subtotal
            self.tabla_renglones.insert(
                "", "end", iid=str(producto_id),
                values=(
                    renglon["nombre"],
                    f"{renglon['cantidad']:g} {renglon['unidad']}",
                    f"${renglon['precio']:,.2f}",
                    f"${subtotal:,.2f}",
                )
            )

        self.var_total.set(f"${total:,.2f}")

    def limpiar(self):
        self.renglones = {}
        self.var_proveedor.set("")
        self.var_fecha.set(date.today().isoformat())
        self.var_producto.set("")
        self.var_cantidad.set("")
        self.var_precio.set("")
        self.lbl_cantidad.configure(text="CANTIDAD")
        self.pintar_renglones()

    def guardar(self):
        padre = self.root

        proveedor_id = self.proveedores.get(self.var_proveedor.get())
        if not proveedor_id:
            messagebox.showwarning(
                "Falta el proveedor",
                "Selecciona un proveedor. Si no hay, agrégalo en el "
                "apartado Proveedores.",
                parent=padre
            )
            return

        if not self.renglones:
            messagebox.showwarning(
                "Compra vacía",
                "Agrega al menos un producto a la compra.",
                parent=padre
            )
            return

        try:
            fecha = datetime.strptime(self.var_fecha.get().strip(), "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning(
                "Fecha inválida",
                "Usa el formato AAAA-MM-DD, por ejemplo 2026-10-20.",
                parent=padre
            )
            return

        if fecha.date() > date.today():
            messagebox.showwarning(
                "Fecha inválida", "La fecha no puede ser posterior a hoy.",
                parent=padre
            )
            return

        total = round(sum(
            r["cantidad"] * r["precio"] for r in self.renglones.values()
        ), 2)
        fecha_hora = f"{fecha:%Y-%m-%d} {datetime.now():%H:%M:%S}"

        # Todo en una sola transacción: si algo falla no se guarda nada
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
                        (compra_id, producto_id,
                         renglon["cantidad"], renglon["precio"])
                    )

                    # Sube la existencia y actualiza el costo al último precio
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
            messagebox.showerror(
                "Error al guardar",
                f"No se pudo registrar la compra.\n\n{error}",
                parent=padre
            )
            return

        messagebox.showinfo(
            "Compra registrada",
            f"Se registró la compra a {self.var_proveedor.get()}.\n"
            f"Total: ${total:,.2f}",
            parent=padre
        )

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

        for compra in compras:
            self.tabla_recientes.insert(
                "", "end", iid=str(compra["id"]),
                values=(
                    compra["fecha"][:10],
                    compra["proveedor"],
                    f"${compra['total']:,.2f}",
                )
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

        lineas = "\n".join(
            f"•  {r['nombre']}: {r['cantidad']:g} {r['unidad']} "
            f"× ${r['precio_unitario']:,.2f} = "
            f"${r['cantidad'] * r['precio_unitario']:,.2f}"
            for r in detalle
        )

        messagebox.showinfo(
            "Detalle de la compra",
            f"Proveedor: {compra['proveedor']}\n"
            f"Fecha: {compra['fecha'][:16]}\n\n"
            f"{lineas}\n\n"
            f"Total: ${compra['total']:,.2f}",
            parent=self.root
        )
