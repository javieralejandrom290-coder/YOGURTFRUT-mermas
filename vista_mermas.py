import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

from base_datos import obtener_conexion


class RegistrarMermaView:
    """Apartado 'Registrar merma'. Se dibuja dentro del contenido del dashboard."""

    MOTIVOS = [
        "Caducidad",
        "Daño o ruptura",
        "Mal almacenamiento",
        "Error de preparación",
        "Producto derramado",
        "Devolución de cliente",
        "Otro",
    ]

    ROJO = "#C62828"

    def __init__(self, app):
        # app = instancia de DashboardApp (de ahí tomamos colores, usuario, etc.)
        self.app = app
        self.productos = {}

    # ------------------------------------------------------------------
    # Pantalla principal
    # ------------------------------------------------------------------
    def mostrar(self):
        app = self.app
        app.limpiar_contenido()
        app.titulo_pagina(
            "Registrar merma",
            "Registra las pérdidas de productos de la heladería."
        )

        try:
            self.cargar_productos()
        except Exception as error:
            messagebox.showerror(
                "Error de base de datos",
                f"No se pudieron cargar los productos.\n\n{error}",
                parent=app.root
            )
            return

        self.construir_formulario()
        self.construir_tabla_reciente()
        self.actualizar_resumen()

    # ------------------------------------------------------------------
    # Datos
    # ------------------------------------------------------------------
    def cargar_productos(self):
        with obtener_conexion() as conexion:
            filas = conexion.execute(
                """
                SELECT id, nombre, unidad, costo_unitario, existencia
                FROM productos
                WHERE activo = 1
                ORDER BY nombre
                """
            ).fetchall()
        self.productos = {fila["nombre"]: fila for fila in filas}

    # ------------------------------------------------------------------
    # Formulario
    # ------------------------------------------------------------------
    def etiqueta(self, padre, texto, fila, columna, columnspan=1, padx=0):
        app = self.app
        etiqueta = tk.Label(
            padre,
            text=texto,
            font=("Segoe UI", 10, "bold"),
            bg=app.BLANCO,
            fg=app.TEXTO,
            anchor="w"
        )
        etiqueta.grid(
            row=fila, column=columna, columnspan=columnspan,
            sticky="w", padx=padx, pady=(10, 4)
        )
        return etiqueta

    def crear_entrada(self, padre, variable):
        app = self.app
        return tk.Entry(
            padre,
            textvariable=variable,
            font=("Segoe UI", 12),
            relief="flat",
            bd=0,
            bg=app.BLANCO,
            fg=app.TEXTO,
            highlightthickness=1,
            highlightbackground=app.BORDE,
            highlightcolor=app.VERDE_CLARO
        )

    def construir_formulario(self):
        app = self.app

        cuerpo = tk.Frame(app.contenido, bg=app.FONDO)
        cuerpo.pack(fill="x", padx=30)
        cuerpo.columnconfigure(0, weight=3)
        cuerpo.columnconfigure(1, weight=2)

        # ---------- Tarjeta del formulario ----------
        tarjeta = tk.Frame(
            cuerpo,
            bg=app.BLANCO,
            highlightbackground=app.BORDE,
            highlightthickness=1
        )
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        tk.Frame(tarjeta, bg=app.VERDE_CLARO, height=4).pack(fill="x")

        form = tk.Frame(tarjeta, bg=app.BLANCO)
        form.pack(fill="both", expand=True, padx=22, pady=(4, 18))
        form.columnconfigure(0, weight=1, uniform="col")
        form.columnconfigure(1, weight=1, uniform="col")

        self.var_producto = tk.StringVar()
        self.var_cantidad = tk.StringVar()
        self.var_motivo = tk.StringVar()
        self.var_fecha = tk.StringVar(value=date.today().isoformat())

        # Fila 1: producto y cantidad
        self.etiqueta(form, "PRODUCTO", 0, 0, padx=(0, 10))
        self.lbl_cantidad = self.etiqueta(form, "CANTIDAD", 0, 1, padx=(10, 0))

        self.cb_producto = ttk.Combobox(
            form,
            textvariable=self.var_producto,
            values=list(self.productos.keys()),
            state="readonly",
            font=("Segoe UI", 11)
        )
        self.cb_producto.grid(
            row=1, column=0, sticky="ew", padx=(0, 10), ipady=5
        )
        self.cb_producto.bind(
            "<<ComboboxSelected>>",
            lambda evento: self.actualizar_resumen()
        )

        self.entrada_cantidad = self.crear_entrada(form, self.var_cantidad)
        self.entrada_cantidad.grid(
            row=1, column=1, sticky="ew", padx=(10, 0), ipady=6
        )
        self.var_cantidad.trace_add(
            "write", lambda *args: self.actualizar_resumen()
        )

        # Fila 2: motivo y fecha
        self.etiqueta(form, "MOTIVO", 2, 0, padx=(0, 10))
        self.etiqueta(form, "FECHA (AAAA-MM-DD)", 2, 1, padx=(10, 0))

        self.cb_motivo = ttk.Combobox(
            form,
            textvariable=self.var_motivo,
            values=self.MOTIVOS,
            state="readonly",
            font=("Segoe UI", 11)
        )
        self.cb_motivo.grid(
            row=3, column=0, sticky="ew", padx=(0, 10), ipady=5
        )

        entrada_fecha = self.crear_entrada(form, self.var_fecha)
        entrada_fecha.grid(
            row=3, column=1, sticky="ew", padx=(10, 0), ipady=6
        )

        # Fila 3: observaciones
        self.etiqueta(form, "OBSERVACIONES (opcional)", 4, 0, columnspan=2)

        self.txt_observaciones = tk.Text(
            form,
            height=3,
            font=("Segoe UI", 11),
            relief="flat",
            bd=0,
            wrap="word",
            bg=app.BLANCO,
            fg=app.TEXTO,
            highlightthickness=1,
            highlightbackground=app.BORDE,
            highlightcolor=app.VERDE_CLARO
        )
        self.txt_observaciones.grid(
            row=5, column=0, columnspan=2, sticky="ew"
        )

        # Botones
        botones = tk.Frame(form, bg=app.BLANCO)
        botones.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(18, 0))
        botones.columnconfigure(0, weight=3)
        botones.columnconfigure(1, weight=1)

        tk.Button(
            botones,
            text="GUARDAR MERMA",
            command=self.guardar,
            font=("Segoe UI", 11, "bold"),
            bg=app.VERDE_CLARO,
            fg=app.BLANCO,
            activebackground="#6AA336",
            activeforeground=app.BLANCO,
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=10
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        tk.Button(
            botones,
            text="LIMPIAR",
            command=self.limpiar_formulario,
            font=("Segoe UI", 10, "bold"),
            bg="#E8EFEA",
            fg=app.VERDE_OSCURO,
            activebackground=app.VERDE_SUAVE,
            activeforeground=app.VERDE_OSCURO,
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=10
        ).grid(row=0, column=1, sticky="ew")

        # ---------- Tarjeta del resumen ----------
        resumen = tk.Frame(
            cuerpo,
            bg=app.BLANCO,
            highlightbackground=app.BORDE,
            highlightthickness=1
        )
        resumen.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        tk.Frame(resumen, bg=app.VERDE_CLARO, height=4).pack(fill="x")

        tk.Label(
            resumen,
            text="Resumen",
            font=("Segoe UI", 14, "bold"),
            bg=app.BLANCO,
            fg=app.VERDE_OSCURO
        ).pack(anchor="w", padx=20, pady=(14, 4))

        self.var_unidad = tk.StringVar(value="—")
        self.var_existencia = tk.StringVar(value="—")
        self.var_costo_unitario = tk.StringVar(value="—")
        self.var_costo_total = tk.StringVar(value="$0.00")

        self.lbl_existencia = None
        for titulo, variable in (
            ("Unidad", self.var_unidad),
            ("Existencia actual", self.var_existencia),
            ("Costo unitario", self.var_costo_unitario),
        ):
            fila = tk.Frame(resumen, bg=app.BLANCO)
            fila.pack(fill="x", padx=20, pady=5)

            tk.Label(
                fila,
                text=titulo,
                font=("Segoe UI", 10),
                bg=app.BLANCO,
                fg=app.TEXTO_SECUNDARIO
            ).pack(side="left")

            etiqueta_valor = tk.Label(
                fila,
                textvariable=variable,
                font=("Segoe UI", 10, "bold"),
                bg=app.BLANCO,
                fg=app.TEXTO
            )
            etiqueta_valor.pack(side="right")

            if titulo == "Existencia actual":
                self.lbl_existencia = etiqueta_valor

        caja_costo = tk.Frame(resumen, bg=app.VERDE_SUAVE)
        caja_costo.pack(fill="x", padx=20, pady=(14, 20))

        tk.Label(
            caja_costo,
            text="Costo de la merma",
            font=("Segoe UI", 10),
            bg=app.VERDE_SUAVE,
            fg=app.TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=14, pady=(12, 0))

        tk.Label(
            caja_costo,
            textvariable=self.var_costo_total,
            font=("Segoe UI", 23, "bold"),
            bg=app.VERDE_SUAVE,
            fg=app.VERDE_OSCURO
        ).pack(anchor="w", padx=14, pady=(0, 12))

    # ------------------------------------------------------------------
    # Tabla de últimas mermas
    # ------------------------------------------------------------------
    def construir_tabla_reciente(self):
        app = self.app

        tk.Label(
            app.contenido,
            text="Últimas mermas registradas",
            font=("Segoe UI", 16, "bold"),
            bg=app.FONDO,
            fg=app.VERDE_OSCURO
        ).pack(anchor="w", padx=30, pady=(20, 10))

        tabla_frame = tk.Frame(
            app.contenido,
            bg=app.BLANCO,
            highlightbackground=app.BORDE,
            highlightthickness=1
        )
        tabla_frame.pack(fill="both", expand=True, padx=30, pady=(0, 22))

        columnas = ("fecha", "producto", "cantidad", "motivo", "costo")
        encabezados = {
            "fecha": "Fecha",
            "producto": "Producto",
            "cantidad": "Cantidad",
            "motivo": "Motivo",
            "costo": "Costo"
        }
        anchos = {
            "fecha": 150,
            "producto": 180,
            "cantidad": 100,
            "motivo": 180,
            "costo": 120
        }

        self.tabla = ttk.Treeview(
            tabla_frame,
            columns=columnas,
            show="headings",
            height=4,
            style="Mermas.Treeview"
        )
        for columna in columnas:
            self.tabla.heading(columna, text=encabezados[columna])
            self.tabla.column(columna, width=anchos[columna], anchor="center")

        barra = ttk.Scrollbar(
            tabla_frame, orient="vertical", command=self.tabla.yview
        )
        self.tabla.configure(yscrollcommand=barra.set)

        self.tabla.pack(
            side="left", fill="both", expand=True, padx=(8, 0), pady=8
        )
        barra.pack(side="right", fill="y", padx=(0, 8), pady=8)

        self.cargar_tabla_reciente()

    def cargar_tabla_reciente(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        try:
            with obtener_conexion() as conexion:
                registros = conexion.execute(
                    """
                    SELECT
                        m.fecha,
                        p.nombre AS producto,
                        m.cantidad,
                        p.unidad,
                        m.motivo,
                        m.costo_total
                    FROM mermas m
                    INNER JOIN productos p ON p.id = m.producto_id
                    ORDER BY m.id DESC
                    LIMIT 10
                    """
                ).fetchall()
        except Exception as error:
            messagebox.showerror(
                "Error de base de datos",
                f"No se pudo cargar el historial reciente.\n\n{error}",
                parent=self.app.root
            )
            return

        for registro in registros:
            self.tabla.insert(
                "",
                "end",
                values=(
                    registro["fecha"],
                    registro["producto"],
                    f"{registro['cantidad']:g} {registro['unidad']}",
                    registro["motivo"],
                    f"${registro['costo_total']:,.2f}"
                )
            )

    # ------------------------------------------------------------------
    # Lógica
    # ------------------------------------------------------------------
    def leer_cantidad(self):
        """Devuelve la cantidad como float, o None si no es un número válido."""
        texto = self.var_cantidad.get().strip().replace(",", ".")
        if not texto:
            return None
        try:
            return float(texto)
        except ValueError:
            return None

    def actualizar_resumen(self):
        app = self.app
        producto = self.productos.get(self.var_producto.get())

        if not producto:
            self.lbl_cantidad.configure(text="CANTIDAD")
            self.var_unidad.set("—")
            self.var_existencia.set("—")
            self.var_costo_unitario.set("—")
            self.var_costo_total.set("$0.00")
            self.lbl_existencia.configure(fg=app.TEXTO)
            return

        unidad = producto["unidad"]
        self.lbl_cantidad.configure(text=f"CANTIDAD ({unidad})")
        self.var_unidad.set(unidad)
        self.var_existencia.set(f"{producto['existencia']:g} {unidad}")
        self.var_costo_unitario.set(f"${producto['costo_unitario']:,.2f}")

        cantidad = self.leer_cantidad()
        if cantidad is not None and cantidad > 0:
            self.var_costo_total.set(
                f"${cantidad * producto['costo_unitario']:,.2f}"
            )
            excede = cantidad > producto["existencia"]
        else:
            self.var_costo_total.set("$0.00")
            excede = False

        self.lbl_existencia.configure(fg=self.ROJO if excede else app.TEXTO)

    def limpiar_formulario(self):
        self.var_producto.set("")
        self.var_cantidad.set("")
        self.var_motivo.set("")
        self.var_fecha.set(date.today().isoformat())
        self.txt_observaciones.delete("1.0", "end")
        self.actualizar_resumen()

    def guardar(self):
        app = self.app
        padre = app.root

        # --- Validaciones ---
        if not self.productos:
            messagebox.showwarning(
                "Sin productos",
                "No hay productos activos. Agrega productos en el apartado "
                "Productos antes de registrar una merma.",
                parent=padre
            )
            return

        producto = self.productos.get(self.var_producto.get())
        if not producto:
            messagebox.showwarning(
                "Falta el producto", "Selecciona un producto.", parent=padre
            )
            return

        cantidad = self.leer_cantidad()
        if cantidad is None or cantidad <= 0:
            messagebox.showwarning(
                "Cantidad inválida",
                "Escribe una cantidad numérica mayor a 0.",
                parent=padre
            )
            return

        motivo = self.var_motivo.get().strip()
        if not motivo:
            messagebox.showwarning(
                "Falta el motivo", "Selecciona el motivo de la merma.",
                parent=padre
            )
            return

        try:
            fecha = datetime.strptime(self.var_fecha.get().strip(), "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning(
                "Fecha inválida",
                "Usa el formato AAAA-MM-DD, por ejemplo 2026-10-13.",
                parent=padre
            )
            return

        if fecha.date() > date.today():
            messagebox.showwarning(
                "Fecha inválida",
                "La fecha no puede ser posterior a hoy.",
                parent=padre
            )
            return

        observaciones = self.txt_observaciones.get("1.0", "end").strip() or None

        # --- Guardado (todo en una sola transacción) ---
        try:
            with obtener_conexion() as conexion:
                actual = conexion.execute(
                    """
                    SELECT costo_unitario, existencia
                    FROM productos
                    WHERE id = ?
                    """,
                    (producto["id"],)
                ).fetchone()

                if cantidad > actual["existencia"]:
                    messagebox.showwarning(
                        "Existencia insuficiente",
                        f"Solo hay {actual['existencia']:g} {producto['unidad']} "
                        f"de {producto['nombre']} en existencia.",
                        parent=padre
                    )
                    return

                costo_total = round(cantidad * actual["costo_unitario"], 2)
                fecha_hora = (
                    f"{fecha:%Y-%m-%d} {datetime.now():%H:%M:%S}"
                )

                conexion.execute(
                    """
                    INSERT INTO mermas (
                        producto_id, usuario_id, cantidad, motivo,
                        observaciones, costo_total, fecha
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        producto["id"],
                        app.usuario_id,
                        cantidad,
                        motivo,
                        observaciones,
                        costo_total,
                        fecha_hora
                    )
                )

                conexion.execute(
                    """
                    UPDATE productos
                    SET existencia = existencia - ?
                    WHERE id = ?
                    """,
                    (cantidad, producto["id"])
                )
        except Exception as error:
            messagebox.showerror(
                "Error al guardar",
                f"No se pudo registrar la merma.\n\n{error}",
                parent=padre
            )
            return

        messagebox.showinfo(
            "Merma registrada",
            f"Se registró la merma de {producto['nombre']}.\n"
            f"Costo: ${costo_total:,.2f}",
            parent=padre
        )

        # Recargar productos (cambió la existencia) y refrescar pantalla
        try:
            self.cargar_productos()
            self.cb_producto.configure(values=list(self.productos.keys()))
        except Exception:
            pass

        self.limpiar_formulario()
        self.cargar_tabla_reciente()