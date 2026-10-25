import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

from base_datos import obtener_conexion, registrar_movimiento_inventario
from ui_comunes import crear_tabla, crear_campo_fecha


class RegistrarMermaView:
    """Apartado 'Registrar merma'. Se dibuja dentro del contenido del dashboard.

    Usa el mismo diseño que Compras e Historial: encabezado verde, tarjetas
    de indicadores, tarjetas con barra superior y tablas con filas alternadas.
    """

    MOTIVOS = [
        "Caducidad",
        "Daño o ruptura",
        "Mal almacenamiento",
        "Error de preparación",
        "Producto derramado",
        "Devolución de cliente",
        "Otro",
    ]

    # Paleta compartida con Compras e Historial
    VERDE_OSCURO = "#064E3B"
    VERDE_MEDIO = "#059669"
    VERDE_SUAVE = "#DCFCE7"
    VERDE_HOVER = "#047857"
    FONDO_GENERAL = "#F0FDF4"
    BLANCO = "#FFFFFF"
    TEXTO_MAIN = "#0F172A"
    TEXTO_MUTED = "#64748B"
    GRIS_BORDE = "#CBD5E1"
    CAMPO = "#F8FAFC"
    ROJO = "#C62828"

    def __init__(self, app):
        # app = instancia de DashboardApp (de ahí tomamos el contenedor, usuario, etc.)
        self.app = app
        self.productos = {}
        self.tipos_merma = {}
        self.empleados = {}
        self.var_kpi_hoy = tk.StringVar(value="0")
        self.var_kpi_costo_hoy = tk.StringVar(value="$0.00")
        self.var_kpi_costo_mes = tk.StringVar(value="$0.00")

    # ------------------------------------------------------------------
    # Pantalla principal
    # ------------------------------------------------------------------
    def mostrar(self):
        app = self.app
        app.limpiar_contenido()
        app.contenido.config(bg=self.FONDO_GENERAL)

        try:
            self.cargar_productos()
        except Exception as error:
            messagebox.showerror(
                "Error de base de datos",
                f"No se pudieron cargar los productos.\n\n{error}",
                parent=app.root
            )
            return

        self.construir_encabezado()

        frame_kpis = tk.Frame(app.contenido, bg=self.FONDO_GENERAL)
        frame_kpis.pack(fill="x", padx=25, pady=(10, 10))
        self._crear_kpi(frame_kpis, "MERMAS REGISTRADAS HOY", self.var_kpi_hoy, "#0284C7", "📦")
        self._crear_kpi(frame_kpis, "COSTO PERDIDO HOY", self.var_kpi_costo_hoy, "#D97706", "🏷️")
        self._crear_kpi(frame_kpis, "COSTO PERDIDO ESTE MES", self.var_kpi_costo_mes, "#DC2626", "💰")

        cuerpo = tk.Frame(app.contenido, bg=self.FONDO_GENERAL)
        cuerpo.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        cuerpo.columnconfigure(0, weight=3, uniform="c")
        cuerpo.columnconfigure(1, weight=2, uniform="c")
        cuerpo.rowconfigure(0, weight=1)

        self.construir_formulario(cuerpo)

        derecha = tk.Frame(cuerpo, bg=self.FONDO_GENERAL)
        derecha.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.construir_resumen(derecha)
        self.construir_tabla_reciente(derecha)

        self.actualizar_resumen()

    def construir_encabezado(self):
        header = tk.Frame(self.app.contenido, bg=self.VERDE_OSCURO, height=65)
        header.pack(fill="x")
        header.pack_propagate(False)

        contenido = tk.Frame(header, bg=self.VERDE_OSCURO)
        contenido.pack(fill="both", expand=True, padx=25, pady=12)

        tk.Label(
            contenido, text="🗑️ Registro de Mermas",
            font=("Segoe UI", 15, "bold"), bg=self.VERDE_OSCURO, fg=self.BLANCO
        ).pack(side="left")

        tk.Label(
            contenido,
            text="Registra las pérdidas de productos de la heladería Yogufrut",
            font=("Segoe UI", 9), bg=self.VERDE_OSCURO, fg="#A7F3D0"
        ).pack(side="right", padx=10)

    def _crear_kpi(self, padre, titulo, variable, color, icono):
        card = tk.Frame(padre, bg=self.BLANCO, bd=1, relief="solid")
        card.config(highlightbackground=self.GRIS_BORDE)
        card.pack(side="left", fill="both", expand=True, padx=4)

        tk.Frame(card, bg=color, width=5).pack(side="left", fill="y")

        info = tk.Frame(card, bg=self.BLANCO)
        info.pack(side="left", fill="both", expand=True, padx=12, pady=8)

        tk.Label(
            info, text=f"{icono} {titulo}", font=("Segoe UI", 8, "bold"),
            bg=self.BLANCO, fg=self.TEXTO_MUTED
        ).pack(anchor="w")
        tk.Label(
            info, textvariable=variable, font=("Segoe UI", 13, "bold"),
            bg=self.BLANCO, fg=self.TEXTO_MAIN
        ).pack(anchor="w", pady=(2, 0))

    def _crear_tarjeta(self, padre, titulo):
        """Tarjeta blanca con barra verde superior y título, como en Compras."""
        tarjeta = tk.Frame(padre, bg=self.BLANCO, bd=1, relief="solid")
        tarjeta.config(highlightbackground=self.GRIS_BORDE)

        tk.Frame(tarjeta, bg=self.VERDE_OSCURO, height=4).pack(fill="x")

        encabezado = tk.Frame(tarjeta, bg=self.BLANCO)
        encabezado.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(
            encabezado, text=titulo, font=("Segoe UI", 11, "bold"),
            bg=self.BLANCO, fg=self.VERDE_OSCURO
        ).pack(anchor="w")
        return tarjeta

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

            self.tipos_merma = {
                fila["nombre"]: fila["id"]
                for fila in conexion.execute(
                    "SELECT id, nombre FROM tipos_merma ORDER BY id"
                )
            }
            self.empleados = {
                f"{fila['nombre']} ({fila['turno']})": fila["id"]
                for fila in conexion.execute(
                    "SELECT id, nombre, turno FROM empleados "
                    "WHERE activo = 1 ORDER BY nombre"
                )
            }

    def cargar_indicadores(self):
        hoy = date.today()
        inicio_mes = hoy.replace(day=1).isoformat()
        try:
            with obtener_conexion() as conexion:
                dia = conexion.execute(
                    """
                    SELECT COUNT(*) AS registros,
                           COALESCE(SUM(costo_total), 0) AS costo
                    FROM mermas
                    WHERE date(fecha) = date(?)
                    """,
                    (hoy.isoformat(),)
                ).fetchone()
                mes = conexion.execute(
                    """
                    SELECT COALESCE(SUM(costo_total), 0) AS costo
                    FROM mermas
                    WHERE date(fecha) >= date(?) AND date(fecha) <= date(?)
                    """,
                    (inicio_mes, hoy.isoformat())
                ).fetchone()
        except Exception:
            return

        self.var_kpi_hoy.set(f"{dia['registros']:,}")
        self.var_kpi_costo_hoy.set(f"${dia['costo']:,.2f}")
        self.var_kpi_costo_mes.set(f"${mes['costo']:,.2f}")

    # ------------------------------------------------------------------
    # Formulario
    # ------------------------------------------------------------------
    def etiqueta(self, padre, texto, fila, columna, columnspan=1, pady=(8, 2)):
        etiqueta = tk.Label(
            padre, text=texto, font=("Segoe UI", 8, "bold"),
            bg=self.BLANCO, fg=self.TEXTO_MUTED, anchor="w"
        )
        etiqueta.grid(
            row=fila, column=columna, columnspan=columnspan,
            sticky="w", padx=4, pady=pady
        )
        return etiqueta

    def crear_entrada(self, padre, variable):
        return tk.Entry(
            padre, textvariable=variable, font=("Segoe UI", 10),
            relief="solid", bd=1, bg=self.CAMPO, fg=self.TEXTO_MAIN
        )

    def crear_combo(self, padre, variable, valores):
        return ttk.Combobox(
            padre, textvariable=variable, values=valores,
            state="readonly", font=("Segoe UI", 10)
        )

    def construir_formulario(self, cuerpo):
        tarjeta = self._crear_tarjeta(cuerpo, "📝 Nueva Merma")
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        form = tk.Frame(tarjeta, bg=self.BLANCO)
        form.pack(fill="both", expand=True, padx=16, pady=(0, 6))
        form.columnconfigure(0, weight=1, uniform="col")
        form.columnconfigure(1, weight=1, uniform="col")

        self.var_producto = tk.StringVar()
        self.var_cantidad = tk.StringVar()
        self.var_motivo = tk.StringVar()
        self.var_tipo = tk.StringVar()
        self.var_empleado = tk.StringVar()
        self.var_fecha = tk.StringVar(value=date.today().isoformat())

        # Fila 1: producto y cantidad
        self.etiqueta(form, "PRODUCTO:", 0, 0, pady=(2, 2))
        self.lbl_cantidad = self.etiqueta(form, "CANTIDAD:", 0, 1, pady=(2, 2))

        self.cb_producto = self.crear_combo(
            form, self.var_producto, list(self.productos.keys())
        )
        self.cb_producto.grid(row=1, column=0, sticky="ew", padx=4, ipady=3)
        self.cb_producto.bind(
            "<<ComboboxSelected>>", lambda evento: self.actualizar_resumen()
        )

        self.entrada_cantidad = self.crear_entrada(form, self.var_cantidad)
        self.entrada_cantidad.grid(row=1, column=1, sticky="ew", padx=4, ipady=4)
        self.var_cantidad.trace_add(
            "write", lambda *args: self.actualizar_resumen()
        )

        # Fila 2: tipo de merma y empleado
        self.etiqueta(form, "TIPO DE MERMA:", 2, 0)
        self.etiqueta(form, "EMPLEADO QUE LA REPORTA:", 2, 1)

        self.cb_tipo = self.crear_combo(
            form, self.var_tipo, list(self.tipos_merma.keys())
        )
        self.cb_tipo.grid(row=3, column=0, sticky="ew", padx=4, ipady=3)

        self.cb_empleado = self.crear_combo(
            form, self.var_empleado, list(self.empleados.keys())
        )
        self.cb_empleado.grid(row=3, column=1, sticky="ew", padx=4, ipady=3)

        # Fila 3: motivo (causa) y fecha
        self.etiqueta(form, "MOTIVO (CAUSA):", 4, 0)
        self.etiqueta(form, "FECHA (AAAA-MM-DD):", 4, 1)

        self.cb_motivo = self.crear_combo(form, self.var_motivo, self.MOTIVOS)
        self.cb_motivo.grid(row=5, column=0, sticky="ew", padx=4, ipady=3)

        campo_fecha = crear_campo_fecha(
            self.app, form, self.var_fecha, fuente=("Segoe UI", 10)
        )
        campo_fecha.configure(
            bg=self.CAMPO, highlightbackground=self.GRIS_BORDE
        )
        campo_fecha.grid(row=5, column=1, sticky="ew", padx=4)

        # Fila 4: observaciones
        self.etiqueta(form, "OBSERVACIONES (opcional):", 6, 0, columnspan=2)

        self.txt_observaciones = tk.Text(
            form, height=4, font=("Segoe UI", 10), relief="solid", bd=1,
            wrap="word", bg=self.CAMPO, fg=self.TEXTO_MAIN
        )
        self.txt_observaciones.grid(
            row=7, column=0, columnspan=2, sticky="nsew", padx=4, pady=(0, 4)
        )
        form.rowconfigure(7, weight=1)

        # Botones
        botones = tk.Frame(tarjeta, bg=self.BLANCO)
        botones.pack(fill="x", padx=16, pady=(8, 14))
        botones.columnconfigure(0, weight=3)
        botones.columnconfigure(1, weight=1)

        tk.Button(
            botones, text="GUARDAR MERMA", command=self.guardar,
            font=("Segoe UI", 10, "bold"), bg=self.VERDE_MEDIO, fg=self.BLANCO,
            activebackground=self.VERDE_HOVER, activeforeground=self.BLANCO,
            relief="flat", cursor="hand2", pady=8
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        tk.Button(
            botones, text="LIMPIAR", command=self.limpiar_formulario,
            font=("Segoe UI", 9, "bold"), bg="#E2E8F0", fg=self.TEXTO_MAIN,
            activebackground="#CBD5E1", relief="flat", cursor="hand2", pady=8
        ).grid(row=0, column=1, sticky="ew")

    # ------------------------------------------------------------------
    # Resumen (lado derecho, arriba)
    # ------------------------------------------------------------------
    def construir_resumen(self, derecha):
        resumen = self._crear_tarjeta(derecha, "📊 Resumen de la Merma")
        resumen.pack(fill="x", pady=(0, 10))

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
            fila = tk.Frame(resumen, bg=self.BLANCO)
            fila.pack(fill="x", padx=16, pady=3)

            tk.Label(
                fila, text=titulo, font=("Segoe UI", 9),
                bg=self.BLANCO, fg=self.TEXTO_MUTED
            ).pack(side="left")

            valor = tk.Label(
                fila, textvariable=variable, font=("Segoe UI", 9, "bold"),
                bg=self.BLANCO, fg=self.TEXTO_MAIN
            )
            valor.pack(side="right")

            if titulo == "Existencia actual":
                self.lbl_existencia = valor

        caja_costo = tk.Frame(resumen, bg=self.VERDE_SUAVE)
        caja_costo.pack(fill="x", padx=16, pady=(10, 14))

        tk.Label(
            caja_costo, text="COSTO DE LA MERMA",
            font=("Segoe UI", 8, "bold"), bg=self.VERDE_SUAVE,
            fg=self.TEXTO_MUTED
        ).pack(anchor="w", padx=12, pady=(8, 0))

        tk.Label(
            caja_costo, textvariable=self.var_costo_total,
            font=("Segoe UI", 20, "bold"), bg=self.VERDE_SUAVE,
            fg=self.VERDE_OSCURO
        ).pack(anchor="w", padx=12, pady=(0, 8))

    # ------------------------------------------------------------------
    # Tabla de últimas mermas (lado derecho, abajo)
    # ------------------------------------------------------------------
    def construir_tabla_reciente(self, derecha):
        tarjeta = self._crear_tarjeta(derecha, "📋 Mermas Recientes")
        tarjeta.pack(fill="both", expand=True)

        marco, self.tabla = crear_tabla(self.app, tarjeta, [
            ("fecha", "Fecha", 90, "w"),
            ("producto", "Producto", 130, "w"),
            ("costo", "Costo", 85, "e"),
        ])
        marco.configure(highlightthickness=0)
        marco.pack(fill="both", expand=True, padx=12, pady=6)
        self.tabla.tag_configure("par", background=self.CAMPO)
        self.tabla.tag_configure("impar", background=self.BLANCO)
        self.tabla.bind("<Double-1>", lambda evento: self.ver_detalle())

        tk.Label(
            tarjeta,
            text="💡 Doble clic en una merma para ver su detalle.",
            font=("Segoe UI", 8, "italic"), bg=self.BLANCO, fg=self.TEXTO_MUTED
        ).pack(anchor="w", padx=16, pady=(0, 12))

        self.cargar_tabla_reciente()

    def cargar_tabla_reciente(self):
        self.tabla.delete(*self.tabla.get_children())

        try:
            with obtener_conexion() as conexion:
                registros = conexion.execute(
                    """
                    SELECT m.id, m.fecha, p.nombre AS producto, m.costo_total
                    FROM mermas m
                    INNER JOIN productos p ON p.id = m.producto_id
                    ORDER BY m.fecha DESC, m.id DESC
                    LIMIT 30
                    """
                ).fetchall()
        except Exception as error:
            messagebox.showerror(
                "Error de base de datos",
                f"No se pudo cargar el historial reciente.\n\n{error}",
                parent=self.app.root
            )
            return

        for idx, registro in enumerate(registros):
            tag = "par" if idx % 2 == 0 else "impar"
            self.tabla.insert(
                "", "end", iid=str(registro["id"]),
                values=(
                    registro["fecha"][:10],
                    registro["producto"],
                    f"${registro['costo_total']:,.2f}",
                ),
                tags=(tag,)
            )

        self.cargar_indicadores()

    def ver_detalle(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return

        try:
            with obtener_conexion() as conexion:
                f = conexion.execute(
                    """
                    SELECT m.fecha, p.nombre AS producto, p.unidad, m.cantidad,
                           m.motivo, m.costo_total, m.observaciones,
                           COALESCE(t.nombre, 'Sin tipo') AS tipo,
                           COALESCE(e.nombre, 'Sin empleado') AS empleado,
                           COALESCE(u.nombre, 'Usuario eliminado') AS usuario
                    FROM mermas m
                    JOIN productos p ON p.id = m.producto_id
                    LEFT JOIN tipos_merma t ON t.id = m.tipo_merma_id
                    LEFT JOIN empleados e ON e.id = m.empleado_id
                    LEFT JOIN usuarios u ON u.id = m.usuario_id
                    WHERE m.id = ?
                    """,
                    (int(seleccion[0]),)
                ).fetchone()
        except Exception as error:
            messagebox.showerror(
                "Error de base de datos",
                f"No se pudo cargar el detalle.\n\n{error}",
                parent=self.app.root
            )
            return

        if f is None:
            return

        top = tk.Toplevel(self.app.root)
        top.title("Detalle de Merma - Yogufrut")
        top.geometry("480x520")
        top.config(bg=self.FONDO_GENERAL)
        top.transient(self.app.root)
        top.grab_set()

        head = tk.Frame(top, bg=self.VERDE_OSCURO)
        head.pack(fill="x")
        tk.Label(
            head, text="📋 Ficha de Merma", font=("Segoe UI", 12, "bold"),
            bg=self.VERDE_OSCURO, fg=self.BLANCO
        ).pack(pady=12)

        card = tk.Frame(top, bg=self.BLANCO, bd=1, relief="solid")
        card.config(highlightbackground=self.GRIS_BORDE)
        card.pack(fill="both", expand=True, padx=20, pady=15)

        detalles = [
            ("Fecha / Hora:", f["fecha"][:16]),
            ("Producto:", f["producto"]),
            ("Cantidad mermada:", f"{f['cantidad']:g} {f['unidad']}"),
            ("Tipo de merma:", f["tipo"]),
            ("Motivo:", f["motivo"]),
            ("Costo de la pérdida:", f"${f['costo_total']:,.2f}"),
            ("Empleado:", f["empleado"]),
            ("Capturado por:", f["usuario"]),
        ]
        for etiqueta, valor in detalles:
            fila = tk.Frame(card, bg=self.BLANCO)
            fila.pack(fill="x", padx=15, pady=4)
            tk.Label(
                fila, text=etiqueta, font=("Segoe UI", 9, "bold"),
                bg=self.BLANCO, fg=self.TEXTO_MUTED, width=22, anchor="w"
            ).pack(side="left")
            tk.Label(
                fila, text=str(valor), font=("Segoe UI", 9, "bold"),
                bg=self.BLANCO, fg=self.TEXTO_MAIN, anchor="w"
            ).pack(side="left", fill="x", expand=True)

        tk.Label(
            card, text="Observaciones / Notas:", font=("Segoe UI", 9, "bold"),
            bg=self.BLANCO, fg=self.TEXTO_MUTED
        ).pack(anchor="w", padx=15, pady=(8, 2))

        tk.Label(
            card, text=f["observaciones"] or "Sin observaciones registradas.",
            font=("Segoe UI", 9, "italic"), bg=self.CAMPO, fg=self.TEXTO_MAIN,
            relief="solid", bd=1, padx=10, pady=8, justify="left",
            anchor="nw", wraplength=400
        ).pack(fill="both", expand=True, padx=15, pady=(0, 15))

        tk.Button(
            top, text="Cerrar", font=("Segoe UI", 9, "bold"),
            bg=self.VERDE_OSCURO, fg=self.BLANCO,
            activebackground=self.VERDE_HOVER, relief="flat", cursor="hand2",
            command=top.destroy
        ).pack(pady=(0, 15), ipadx=25, ipady=5)

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
            self.lbl_cantidad.configure(text="CANTIDAD:")
            self.var_unidad.set("—")
            self.var_existencia.set("—")
            self.var_costo_unitario.set("—")
            self.var_costo_total.set("$0.00")
            self.lbl_existencia.configure(fg=app.TEXTO)
            return

        unidad = producto["unidad"]
        self.lbl_cantidad.configure(text=f"CANTIDAD ({unidad}):")
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
        self.var_tipo.set("")
        self.var_empleado.set("")
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

        tipo_merma_id = self.tipos_merma.get(self.var_tipo.get())
        if not tipo_merma_id:
            messagebox.showwarning(
                "Falta el tipo", "Selecciona el tipo de merma.",
                parent=padre
            )
            return

        empleado_id = self.empleados.get(self.var_empleado.get())
        if not empleado_id:
            messagebox.showwarning(
                "Falta el empleado",
                "Selecciona el empleado que reporta la merma. Si no hay, "
                "agrégalo en el apartado Empleados.",
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
                        producto_id, usuario_id, empleado_id, tipo_merma_id,
                        cantidad, motivo, observaciones, costo_total, fecha
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        producto["id"],
                        app.usuario_id,
                        empleado_id,
                        tipo_merma_id,
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

                registrar_movimiento_inventario(
                    conexion, producto["id"], salida=cantidad
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