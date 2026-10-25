import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

import ui_tema
from base_datos import obtener_conexion, registrar_movimiento_inventario
from ui_comunes import Tarjeta, crear_kpi, crear_tabla, crear_campo_fecha


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

    # Paleta pastel compartida con el resto del sistema
    VERDE_OSCURO = ui_tema.VERDE_OSCURO
    VERDE_MEDIO = ui_tema.VERDE_PRIMARIO
    VERDE_SUAVE = ui_tema.VERDE_SUAVE
    VERDE_CLARO = ui_tema.VERDE_CLARO
    VERDE_HOVER = ui_tema.VERDE_HOVER
    FONDO_GENERAL = ui_tema.FONDO
    BLANCO = ui_tema.BLANCO
    TEXTO_MAIN = ui_tema.TEXTO
    TEXTO_MUTED = ui_tema.TEXTO_SECUNDARIO
    GRIS_BORDE = ui_tema.BORDE
    CAMPO = ui_tema.CAMPO
    ROJO = ui_tema.PELIGRO

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
        frame_kpis.pack(fill="x", padx=32, pady=(14, 14))
        self._crear_kpi(
            frame_kpis, "MERMAS REGISTRADAS HOY",
            self.var_kpi_hoy, ui_tema.VERDE_CLARO
        )
        self._crear_kpi(
            frame_kpis, "COSTO PERDIDO HOY",
            self.var_kpi_costo_hoy, ui_tema.VERDE_MEDIO
        )
        self._crear_kpi(
            frame_kpis, "COSTO PERDIDO ESTE MES",
            self.var_kpi_costo_mes, ui_tema.ACENTO
        )

        cuerpo = tk.Frame(app.contenido, bg=self.FONDO_GENERAL)
        cuerpo.pack(fill="both", expand=True, padx=32, pady=(0, 24))
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
        header = tk.Frame(
            self.app.contenido, bg=self.FONDO_GENERAL, height=92
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        contenido = tk.Frame(header, bg=self.FONDO_GENERAL)
        contenido.pack(fill="both", expand=True, padx=32, pady=14)

        tk.Frame(
            contenido, bg=self.VERDE_MEDIO, width=4, height=48
        ).pack(side="left", padx=(0, 14))

        textos = tk.Frame(contenido, bg=self.FONDO_GENERAL)
        textos.pack(side="left", fill="y")

        tk.Label(
            textos, text="Registro de mermas",
            font=ui_tema.fuente_titulo(22),
            bg=self.FONDO_GENERAL, fg=self.VERDE_OSCURO, anchor="w"
        ).pack(anchor="w", pady=(4, 0))

        tk.Label(
            textos,
            text="Registra las pérdidas de productos de la heladería Yogufrut",
            font=ui_tema.fuente_texto(9),
            bg=self.FONDO_GENERAL, fg=self.TEXTO_MUTED, anchor="w"
        ).pack(anchor="w", pady=(3, 0))

    def _crear_kpi(self, padre, titulo, variable, color):
        tarjeta = crear_kpi(
            self.app, padre, titulo, variable=variable, color=color,
        )
        tarjeta.pack(side="left", fill="both", expand=True, padx=6)
        return tarjeta

    def _crear_tarjeta(self, padre, titulo):
        """Tarjeta blanca con título y acento pastel."""
        tarjeta = Tarjeta(padre, bg=self.BLANCO, padding=14)
        tarjeta.cuerpo.pack_propagate(True)

        fila_titulo = tk.Frame(tarjeta.cuerpo, bg=self.BLANCO)
        fila_titulo.pack(fill="x", pady=(0, 8))

        punto = tk.Canvas(
            fila_titulo, width=10, height=10, bg=self.BLANCO,
            highlightthickness=0, bd=0,
        )
        punto.create_oval(0, 0, 10, 10, fill=self.VERDE_MEDIO, outline="")
        punto.pack(side="left", padx=(0, 8))

        tk.Label(
            fila_titulo, text=titulo, font=ui_tema.fuente_titulo(14),
            bg=self.BLANCO, fg=self.VERDE_OSCURO
        ).pack(side="left")

        tarjeta.titulo = fila_titulo
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
            self.productos = {}
            for fila in filas:
                etiqueta = fila["nombre"]
                if fila["existencia"] <= 0:
                    etiqueta += "  (sin existencia)"
                self.productos[etiqueta] = fila

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
            padre, text=texto, font=ui_tema.fuente_texto(8, "bold"),
            bg=self.BLANCO, fg=self.TEXTO_MUTED, anchor="w"
        )
        etiqueta.grid(
            row=fila, column=columna, columnspan=columnspan,
            sticky="w", padx=4, pady=pady
        )
        return etiqueta

    def crear_entrada(self, padre, variable):
        return ui_tema.entrada(
            padre, textvariable=variable, font=ui_tema.fuente_texto(10)
        )

    def crear_combo(self, padre, variable, valores):
        return ttk.Combobox(
            padre, textvariable=variable, values=valores,
            state="readonly", font=ui_tema.fuente_texto(10),
            style="Tema.TCombobox"
        )

    def construir_formulario(self, cuerpo):
        tarjeta = self._crear_tarjeta(cuerpo, "Nueva merma")
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        caja = tarjeta.cuerpo

        self.construir_avisos(caja)

        # Los botones se reservan antes que el formulario para que siempre
        # queden visibles aunque la ventana sea pequeña.
        botones = tk.Frame(caja, bg=self.BLANCO)
        botones.pack(side="bottom", fill="x", pady=(10, 0))
        botones.columnconfigure(0, weight=3)
        botones.columnconfigure(1, weight=1)

        form = tk.Frame(caja, bg=self.BLANCO)
        form.pack(fill="both", expand=True)
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
        # Se puede escribir para buscar: la lista se filtra al teclear
        self.cb_producto.configure(state="normal")
        self.cb_producto.bind("<KeyRelease>", self.filtrar_productos)
        self.cb_producto.bind("<FocusOut>", self.confirmar_producto)
        self.cb_producto.bind("<Return>", self.confirmar_producto)
        self.cb_producto.bind("<<ComboboxSelected>>", self.al_elegir_producto)

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
        self.preseleccionar_unicos()

        # Fila 3: motivo (causa) y fecha
        self.etiqueta(form, "MOTIVO (CAUSA):", 4, 0)
        self.etiqueta(form, "FECHA (AAAA-MM-DD):", 4, 1)

        self.cb_motivo = self.crear_combo(form, self.var_motivo, self.MOTIVOS)
        self.cb_motivo.grid(row=5, column=0, sticky="ew", padx=4, ipady=3)

        campo_fecha = crear_campo_fecha(
            self.app, form, self.var_fecha, fuente=ui_tema.fuente_texto(10)
        )
        campo_fecha.grid(row=5, column=1, sticky="ew", padx=4)

        # Fila 4: observaciones
        self.etiqueta(form, "OBSERVACIONES (opcional):", 6, 0, columnspan=2)

        self.txt_observaciones = tk.Text(
            form, height=4, font=ui_tema.fuente_texto(10), relief="flat", bd=0,
            wrap="word", bg=self.CAMPO, fg=self.TEXTO_MAIN,
            highlightthickness=1, highlightbackground=self.GRIS_BORDE,
            highlightcolor=self.VERDE_CLARO, insertbackground=self.VERDE_OSCURO
        )
        self.txt_observaciones.grid(
            row=7, column=0, columnspan=2, sticky="nsew", padx=4, pady=(0, 4)
        )
        form.rowconfigure(7, weight=1)

        # Botones
        ui_tema.boton(
            botones, "GUARDAR MERMA", self.guardar, principal=True
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ui_tema.boton(
            botones, "LIMPIAR", self.limpiar_formulario
        ).grid(row=0, column=1, sticky="ew")

    # ------------------------------------------------------------------
    # Resumen (lado derecho, arriba)
    # ------------------------------------------------------------------
    def construir_resumen(self, derecha):
        resumen = self._crear_tarjeta(derecha, "Resumen de la merma")
        resumen.pack(fill="x", pady=(0, 10))
        caja = resumen.cuerpo

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
            fila = tk.Frame(caja, bg=self.BLANCO)
            fila.pack(fill="x", pady=2)

            tk.Label(
                fila, text=titulo, font=ui_tema.fuente_texto(9),
                bg=self.BLANCO, fg=self.TEXTO_MUTED
            ).pack(side="left")

            valor = tk.Label(
                fila, textvariable=variable, font=ui_tema.fuente_texto(9, "bold"),
                bg=self.BLANCO, fg=self.TEXTO_MAIN
            )
            valor.pack(side="right")

            if titulo == "Existencia actual":
                self.lbl_existencia = valor

        caja_costo = tk.Frame(caja, bg=self.VERDE_SUAVE)
        caja_costo.pack(fill="x", pady=(10, 0))

        tk.Label(
            caja_costo, text="COSTO DE LA MERMA",
            font=ui_tema.fuente_texto(8, "bold"), bg=self.VERDE_SUAVE,
            fg=self.TEXTO_MUTED
        ).pack(anchor="w", padx=14, pady=(10, 0))

        tk.Label(
            caja_costo, textvariable=self.var_costo_total,
            font=ui_tema.fuente_titulo(22), bg=self.VERDE_SUAVE,
            fg=self.VERDE_OSCURO
        ).pack(anchor="w", padx=14, pady=(2, 10))

    # ------------------------------------------------------------------
    # Tabla de últimas mermas (lado derecho, abajo)
    # ------------------------------------------------------------------
    def construir_tabla_reciente(self, derecha):
        tarjeta = self._crear_tarjeta(derecha, "Mermas recientes")
        tarjeta.pack(fill="both", expand=True)
        caja = tarjeta.cuerpo

        marco, self.tabla = crear_tabla(self.app, caja, [
            ("fecha", "Fecha", 88, "w"),
            ("producto", "Producto", 128, "w"),
            ("costo", "Costo", 84, "e"),
        ])
        self.tabla.tag_configure("par", background=self.CAMPO)
        self.tabla.tag_configure("impar", background=self.BLANCO)
        self.tabla.bind("<Double-1>", lambda evento: self.ver_detalle())

        tk.Label(
            caja,
            text="Doble clic en una merma para ver su detalle.",
            font=ui_tema.fuente_texto(8, "italic"), bg=self.BLANCO,
            fg=self.TEXTO_MUTED
        ).pack(side="bottom", anchor="w", pady=(10, 0))

        marco.pack(fill="both", expand=True)

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
        top.geometry("500x560")
        top.config(bg=self.FONDO_GENERAL)
        top.transient(self.app.root)
        top.grab_set()

        tarjeta = Tarjeta(top, bg=self.BLANCO, padding=22)
        tarjeta.pack(fill="both", expand=True, padx=22, pady=18)
        card = tarjeta.cuerpo

        tk.Label(
            card, text="Ficha de merma", font=ui_tema.fuente_titulo(18),
            bg=self.BLANCO, fg=self.VERDE_OSCURO
        ).pack(anchor="w")

        tk.Frame(card, bg=self.VERDE_MEDIO, height=3, width=46).pack(
            anchor="w", pady=(6, 14)
        )

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
            fila.pack(fill="x", pady=4)
            tk.Label(
                fila, text=etiqueta, font=ui_tema.fuente_texto(9, "bold"),
                bg=self.BLANCO, fg=self.TEXTO_MUTED, width=20, anchor="w"
            ).pack(side="left")
            tk.Label(
                fila, text=str(valor), font=ui_tema.fuente_texto(9, "bold"),
                bg=self.BLANCO, fg=self.TEXTO_MAIN, anchor="w"
            ).pack(side="left", fill="x", expand=True)

        tk.Label(
            card, text="Observaciones / Notas:", font=ui_tema.fuente_texto(9, "bold"),
            bg=self.BLANCO, fg=self.TEXTO_MUTED
        ).pack(anchor="w", pady=(12, 4))

        tk.Label(
            card, text=f["observaciones"] or "Sin observaciones registradas.",
            font=ui_tema.fuente_texto(9, "italic"), bg=self.CAMPO, fg=self.TEXTO_MAIN,
            padx=12, pady=10, justify="left",
            anchor="nw", wraplength=410
        ).pack(fill="both", expand=True)

        ui_tema.boton(
            top, "Cerrar", top.destroy, principal=True,
            fuente=ui_tema.fuente_texto(9, "bold")
        ).pack(pady=(0, 18))

    # ------------------------------------------------------------------
    # Lógica
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Lista de productos: búsqueda y avisos
    # ------------------------------------------------------------------
    def valores_productos(self):
        return list(self.productos.keys())

    def filtrar_productos(self, evento=None):
        """Filtra la lista de productos mientras se escribe."""
        teclas_ignoradas = (
            "Up", "Down", "Left", "Right", "Return", "Tab", "Escape",
            "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L",
            "Alt_R", "Caps_Lock"
        )
        if evento is not None and evento.keysym in teclas_ignoradas:
            return

        texto = self.var_producto.get().strip().lower()
        todos = self.valores_productos()
        self.cb_producto.configure(
            values=[p for p in todos if texto in p.lower()] if texto else todos
        )
        self.actualizar_resumen()

    def confirmar_producto(self, evento=None):
        """Si lo escrito coincide con un solo producto, lo selecciona."""
        texto = self.var_producto.get().strip().lower()
        if texto and self.var_producto.get() not in self.productos:
            empiezan = [p for p in self.productos if p.lower().startswith(texto)]
            contienen = [p for p in self.productos if texto in p.lower()]
            if len(empiezan) == 1:
                self.var_producto.set(empiezan[0])
            elif len(contienen) == 1:
                self.var_producto.set(contienen[0])
        self.actualizar_resumen()

    def preseleccionar_unicos(self):
        """Si solo hay un empleado registrado, ya queda elegido."""
        if len(self.empleados) == 1 and not self.var_empleado.get():
            self.var_empleado.set(next(iter(self.empleados)))

    def al_elegir_producto(self, evento=None):
        # Al elegir, la lista vuelve a mostrar todos los productos
        self.cb_producto.configure(values=self.valores_productos())
        self.actualizar_resumen()

    def requisitos_pendientes(self):
        """
        Lo que falta para poder registrar una merma, como lista de
        (mensaje, texto del botón, acción).
        """
        pendientes = []

        if not self.productos:
            pendientes.append((
                "No hay productos registrados.",
                "Cargar catálogo", self.cargar_catalogo
            ))
        elif not any(p["existencia"] > 0 for p in self.productos.values()):
            pendientes.append((
                "Ningún producto tiene existencia.",
                "Ir a Compras", self.app.abrir_compras
            ))

        if not self.empleados:
            pendientes.append((
                "No hay empleados registrados.",
                "Ir a Empleados", self.app.abrir_empleados
            ))

        return pendientes

    def construir_avisos(self, tarjeta):
        """Avisa qué falta antes de poder guardar una merma."""
        pendientes = self.requisitos_pendientes()
        if not pendientes:
            return

        fondo, borde, color = (
            ui_tema.AVISO_FONDO, ui_tema.AVISO_BORDE, ui_tema.AVISO_TEXTO
        )
        aviso = tk.Frame(
            tarjeta, bg=fondo, highlightbackground=borde, highlightthickness=1
        )
        aviso.pack(fill="x", padx=16, pady=(0, 8))

        tk.Label(
            aviso, text="Antes de registrar una merma falta:",
            font=ui_tema.fuente_texto(9, "bold"), bg=fondo, fg=color
        ).pack(anchor="w", padx=12, pady=(8, 2))

        for mensaje, texto_boton, comando in pendientes:
            fila = tk.Frame(aviso, bg=fondo)
            fila.pack(fill="x", padx=12, pady=(0, 8))
            ui_tema.boton(
                fila, texto_boton, comando,
                fuente=ui_tema.fuente_texto(8, "bold")
            ).pack(side="right")
            tk.Label(
                fila, text=f"— {mensaje}", font=ui_tema.fuente_texto(9),
                bg=fondo, fg=color, anchor="w", justify="left"
            ).pack(side="left", fill="x", expand=True, padx=(0, 8))

    def cargar_catalogo(self):
        """Carga los productos de Yogufrut (script agregar_productos.py)."""
        padre = self.app.root
        try:
            import agregar_productos
            agregar_productos.actualizar_precios_y_productos()
        except Exception as error:
            messagebox.showerror(
                "No se pudo cargar el catálogo", str(error), parent=padre
            )
            return

        messagebox.showinfo(
            "Catálogo cargado",
            "Se cargaron los productos con sus precios.\n\n"
            "Para poder registrar mermas, primero dales existencia "
            "registrando una compra en el apartado Compras.",
            parent=padre
        )
        self.mostrar()

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
        sin_existencia = producto["existencia"] <= 0
        self.var_existencia.set(
            f"0 {unidad} (sin existencia)" if sin_existencia
            else f"{producto['existencia']:g} {unidad}"
        )
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

        self.lbl_existencia.configure(
            fg=self.ROJO if (excede or sin_existencia) else app.TEXTO
        )

    def limpiar_formulario(self):
        self.var_producto.set("")
        self.cb_producto.configure(values=self.valores_productos())
        self.var_cantidad.set("")
        self.var_motivo.set("")
        self.var_tipo.set("")
        self.var_empleado.set("")
        self.preseleccionar_unicos()
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

                if actual["existencia"] <= 0:
                    messagebox.showwarning(
                        "Producto sin existencia",
                        f"{producto['nombre']} no tiene existencia.\n\n"
                        "Registra primero una compra en el apartado Compras "
                        "para darle existencia.",
                        parent=padre
                    )
                    return

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