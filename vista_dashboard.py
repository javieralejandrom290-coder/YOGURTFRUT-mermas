import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta

import base_datos
import ui_tema
from base_datos import obtener_conexion
from ui_comunes import crear_logo
from vista_productos import ModuloProductos
from vista_mermas import RegistrarMermaView
from vista_inventario import ModuloInventario, consultar_inventario
from vista_historial import ModuloHistorial
from vista_reportes import ModuloReportes, costo_por_dia
from ui_graficas import GraficaLinea
from ui_comunes import crear_tabla
from vista_proveedores import ModuloProveedores
from vista_compras import ModuloCompras
from vista_empleados import ModuloEmpleados
from vista_usuarios import ModuloUsuarios


class DashboardApp:
    def __init__(self, root, usuario_id, nombre, rol):
        self.root = root
        self.usuario_id = usuario_id
        self.nombre = nombre
        self.rol = rol

        titulo = "YOGUFRUT | Control de Mermas"
        if base_datos.RUTA_BASE_DATOS.name != "mermas.db":
            titulo += "  [BASE DE PRUEBA]"
        self.root.title(titulo)
        self.root.geometry("1240x760")
        self.root.minsize(1040, 660)
        self.root.configure(bg=ui_tema.FONDO)

        # Paleta pastel compartida con el resto de pantallas
        self.VERDE_OSCURO = ui_tema.VERDE_OSCURO
        self.VERDE_HOVER = ui_tema.VERDE_HOVER
        self.VERDE_CLARO = ui_tema.VERDE_CLARO
        self.VERDE_PRIMARIO = ui_tema.VERDE_PRIMARIO
        self.VERDE_SUAVE = ui_tema.VERDE_SUAVE
        self.VERDE_ACTIVO = ui_tema.VERDE_ACTIVO
        self.BLANCO = ui_tema.BLANCO
        self.FONDO = ui_tema.FONDO
        self.FONDO_SUAVE = ui_tema.FONDO_SUAVE
        self.TEXTO = ui_tema.TEXTO
        self.TEXTO_SECUNDARIO = ui_tema.TEXTO_SECUNDARIO
        self.BORDE = ui_tema.BORDE

        self.configurar_estilos()
        self.crear_menu_lateral()
        self.crear_contenido()

        self.vista_mermas = RegistrarMermaView(self)

        self.mostrar_inicio()

    def configurar_estilos(self):
        ui_tema.aplicar_tema(self.root)

        estilo = ttk.Style()
        estilo.configure(
            "Mermas.Treeview",
            background=self.BLANCO,
            foreground=self.TEXTO,
            fieldbackground=self.BLANCO,
            rowheight=40,
            borderwidth=0,
            font=("Segoe UI", 10)
        )

        estilo.configure(
            "Mermas.Treeview.Heading",
            background=self.VERDE_SUAVE,
            foreground=self.VERDE_OSCURO,
            font=("Segoe UI", 10, "bold"),
            padding=10,
            relief="flat"
        )

        estilo.map(
            "Mermas.Treeview",
            background=[("selected", self.VERDE_ACTIVO)],
            foreground=[("selected", self.VERDE_OSCURO)]
        )

    def crear_menu_lateral(self):
        self.menu = tk.Frame(
            self.root,
            bg=self.BLANCO,
            width=252,
            highlightbackground=self.BORDE,
            highlightthickness=1,
            bd=0,
        )
        self.menu.pack(side="left", fill="y")
        self.menu.pack_propagate(False)

        # Marca: logo oficial + nombre del sistema
        marca = tk.Frame(self.menu, bg=self.BLANCO)
        marca.pack(fill="x", padx=20, pady=(18, 14))

        self.logo_menu = crear_logo(marca, bg=self.BLANCO, alto=44)
        self.logo_menu.pack(side="left")

        textos_marca = tk.Frame(marca, bg=self.BLANCO)
        textos_marca.pack(side="left", padx=(10, 0))

        tk.Label(
            textos_marca,
            text="YOGUFRUT",
            font=("Segoe UI", 15, "bold"),
            bg=self.BLANCO,
            fg=self.VERDE_OSCURO,
        ).pack(anchor="w")

        tk.Label(
            textos_marca,
            text="CONTROL DE MERMAS",
            font=("Segoe UI", 7, "bold"),
            bg=self.BLANCO,
            fg=self.TEXTO_SECUNDARIO,
        ).pack(anchor="w", pady=(2, 0))

        tk.Frame(self.menu, bg=self.BORDE, height=1).pack(
            fill="x", padx=20, pady=(0, 8)
        )

        grupos = [
            ("PRINCIPAL", [
                ("Inicio", self.mostrar_inicio),
            ]),
            ("GESTIÓN", [
                ("Productos", self.abrir_productos),
                ("Proveedores", self.abrir_proveedores),
                ("Compras", self.abrir_compras),
                ("Registrar merma", self.abrir_mermas),
                ("Inventario", self.abrir_inventario),
                ("Historial", self.abrir_historial),
                ("Reportes", self.abrir_reportes),
            ]),
            ("PERSONAL", [
                ("Empleados", self.abrir_empleados),
            ]),
        ]

        # Solo los administradores manejan las cuentas del sistema
        if self.rol == "Administrador":
            grupos[-1][1].append(("Usuarios", self.abrir_usuarios))

        self.botones_menu = {}
        self.seccion_activa = None

        for titulo_grupo, opciones in grupos:
            tk.Label(
                self.menu,
                text=titulo_grupo,
                font=("Segoe UI", 7, "bold"),
                bg=self.BLANCO,
                fg=self.TEXTO_SECUNDARIO,
                anchor="w",
            ).pack(fill="x", padx=24, pady=(12, 4))

            for texto, comando in opciones:
                boton = tk.Button(
                    self.menu,
                    text=texto,
                    command=comando,
                    font=("Segoe UI", 10),
                    anchor="w",
                    bg=self.BLANCO,
                    fg=self.TEXTO,
                    activebackground=self.VERDE_SUAVE,
                    activeforeground=self.VERDE_OSCURO,
                    relief="flat",
                    bd=0,
                    highlightthickness=0,
                    cursor="hand2",
                    padx=18,
                    pady=8,
                )
                boton.pack(fill="x", padx=14, pady=1)
                self.botones_menu[texto] = boton

                boton.bind(
                    "<Enter>",
                    lambda evento, b=boton, t=texto:
                        b.configure(bg=self.color_boton_menu(t, pasando=True))
                )
                boton.bind(
                    "<Leave>",
                    lambda evento, b=boton, t=texto:
                        b.configure(bg=self.color_boton_menu(t))
                )

        # Tarjeta del usuario en la parte inferior
        usuario = tk.Frame(self.menu, bg=self.FONDO_SUAVE)
        usuario.pack(side="bottom", fill="x", padx=16, pady=18)

        inicial = tk.Canvas(
            usuario, width=38, height=38, bg=self.FONDO_SUAVE,
            highlightthickness=0
        )
        inicial.pack(side="left", padx=(10, 8), pady=10)
        inicial.create_oval(
            1, 1, 37, 37, fill=self.VERDE_CLARO, outline=""
        )
        inicial.create_text(
            19, 19, text=(self.nombre.strip()[:1] or "U").upper(),
            fill=self.VERDE_OSCURO, font=("Segoe UI", 12, "bold")
        )

        datos = tk.Frame(usuario, bg=self.FONDO_SUAVE)
        datos.pack(side="left", fill="x", expand=True, pady=10)

        tk.Label(
            datos,
            text=self.nombre,
            font=("Segoe UI", 9, "bold"),
            bg=self.FONDO_SUAVE,
            fg=self.VERDE_OSCURO,
            anchor="w",
            wraplength=150,
        ).pack(anchor="w")

        tk.Label(
            datos,
            text=self.rol,
            font=("Segoe UI", 8),
            bg=self.FONDO_SUAVE,
            fg=self.TEXTO_SECUNDARIO,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

    def color_boton_menu(self, texto, pasando=False):
        """Color del botón del menú: activo, con el mouse encima o normal."""
        if texto == self.seccion_activa:
            return self.VERDE_ACTIVO
        return self.VERDE_SUAVE if pasando else self.BLANCO

    def resaltar_menu(self, texto):
        """Marca en el menú lateral la sección que se está viendo."""
        self.seccion_activa = texto
        for nombre, boton in self.botones_menu.items():
            activo = nombre == texto
            boton.configure(
                bg=self.color_boton_menu(nombre),
                fg=self.VERDE_OSCURO if activo else self.TEXTO,
                font=("Segoe UI", 10, "bold" if activo else "normal"),
            )

    def crear_contenido(self):
        self.contenido = tk.Frame(
            self.root,
            bg=self.FONDO
        )
        self.contenido.pack(
            side="left",
            fill="both",
            expand=True
        )

    def limpiar_contenido(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()
        # Cada apartado puede pintar su propio fondo; al cambiar de pestaña
        # se vuelve al fondo base para que el color no se "contagie".
        self.contenido.config(bg=self.FONDO)

    def titulo_pagina(self, titulo, descripcion):
        encabezado = tk.Frame(
            self.contenido,
            bg=self.FONDO
        )
        encabezado.pack(fill="x", padx=30, pady=(26, 20))

        fila = tk.Frame(encabezado, bg=self.FONDO)
        fila.pack(fill="x")

        tk.Frame(
            fila, bg=self.VERDE_CLARO, width=4, height=42
        ).pack(side="left", padx=(0, 12))

        textos = tk.Frame(fila, bg=self.FONDO)
        textos.pack(side="left", fill="x", expand=True)

        tk.Label(
            textos,
            text=titulo,
            font=("Segoe UI", 22, "bold"),
            bg=self.FONDO,
            fg=self.VERDE_OSCURO
        ).pack(anchor="w")

        tk.Label(
            textos,
            text=descripcion,
            font=("Segoe UI", 9),
            bg=self.FONDO,
            fg=self.TEXTO_SECUNDARIO
        ).pack(anchor="w", pady=(3, 0))

    def obtener_estadisticas(self):
        estadisticas = {
            "mermas_hoy": 0,
            "productos": 0,
            "costo_hoy": 0.0,
            "costo_mes": 0.0
        }

        hoy = date.today()
        inicio_mes = hoy.replace(day=1).isoformat()

        with obtener_conexion() as conexion:
            estadisticas["mermas_hoy"] = conexion.execute(
                """
                SELECT COUNT(*)
                FROM mermas
                WHERE date(fecha) = date(?)
                """,
                (hoy.isoformat(),)
            ).fetchone()[0]

            estadisticas["productos"] = conexion.execute(
                """
                SELECT COUNT(*)
                FROM productos
                WHERE activo = 1
                """
            ).fetchone()[0]

            estadisticas["costo_hoy"] = conexion.execute(
                """
                SELECT COALESCE(SUM(costo_total), 0)
                FROM mermas
                WHERE date(fecha) = date(?)
                """,
                (hoy.isoformat(),)
            ).fetchone()[0]

            estadisticas["costo_mes"] = conexion.execute(
                """
                SELECT COALESCE(SUM(costo_total), 0)
                FROM mermas
                WHERE date(fecha) >= date(?)
                  AND date(fecha) <= date(?)
                """,
                (inicio_mes, hoy.isoformat())
            ).fetchone()[0]

        return estadisticas

    def crear_tarjeta(self, contenedor, titulo, valor, detalle):
        tarjeta = tk.Frame(
            contenedor,
            bg=self.BLANCO,
            highlightbackground=self.BORDE,
            highlightthickness=1
        )

        tk.Frame(
            tarjeta,
            bg=self.VERDE_CLARO,
            height=3
        ).pack(fill="x")

        tk.Label(
            tarjeta,
            text=titulo,
            font=("Segoe UI", 9, "bold"),
            bg=self.BLANCO,
            fg=self.TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=18, pady=(15, 5))

        tk.Label(
            tarjeta,
            text=valor,
            font=("Segoe UI", 23, "bold"),
            bg=self.BLANCO,
            fg=self.VERDE_OSCURO
        ).pack(anchor="w", padx=18)

        tk.Label(
            tarjeta,
            text=detalle,
            font=("Segoe UI", 8),
            bg=self.BLANCO,
            fg=self.TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=18, pady=(5, 16))

        return tarjeta

    def mostrar_inicio(self):
        self.resaltar_menu("Inicio")
        self.limpiar_contenido()
        self.titulo_pagina(
            "Panel principal",
            f"Bienvenido, {self.nombre}. Aquí tienes el resumen de YOGUFRUT."
        )

        try:
            datos = self.obtener_estadisticas()
        except Exception as error:
            messagebox.showerror(
                "Error de base de datos",
                f"No se pudieron cargar las estadísticas.\n\n{error}",
                parent=self.root
            )
            return

        tarjetas = tk.Frame(
            self.contenido,
            bg=self.FONDO
        )
        tarjetas.pack(fill="x", padx=22)

        tarjetas_info = [
            (
                "Mermas de hoy",
                str(datos["mermas_hoy"]),
                "Registros del día"
            ),
            (
                "Productos activos",
                str(datos["productos"]),
                "En el catálogo"
            ),
            (
                "Costo de hoy",
                f"${datos['costo_hoy']:,.2f}",
                "Pérdidas del día"
            ),
            (
                "Costo del mes",
                f"${datos['costo_mes']:,.2f}",
                "Desde el primer día del mes"
            ),
        ]

        for indice, (titulo, valor, detalle) in enumerate(tarjetas_info):
            tarjeta = self.crear_tarjeta(
                tarjetas, titulo, valor, detalle
            )
            tarjeta.grid(
                row=0,
                column=indice,
                sticky="nsew",
                padx=7,
                pady=5
            )
            tarjetas.columnconfigure(indice, weight=1)

        
        self.crear_paneles_inicio()

        tk.Label(
            self.contenido,
            text="Últimas mermas registradas",
            font=("Segoe UI", 16, "bold"),
            bg=self.FONDO,
            fg=self.VERDE_OSCURO
        ).pack(anchor="w", padx=30, pady=(14, 8))

        tabla_frame = tk.Frame(
            self.contenido,
            bg=self.BLANCO,
            highlightbackground=self.BORDE,
            highlightthickness=1
        )
        tabla_frame.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(0, 25)
        )

        columnas = (
            "fecha", "producto", "cantidad", "motivo", "costo"
        )

        tabla = ttk.Treeview(
            tabla_frame,
            columns=columnas,
            show="headings",
            style="Mermas.Treeview"
        )

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

        for columna in columnas:
            tabla.heading(columna, text=encabezados[columna])
            tabla.column(
                columna,
                width=anchos[columna],
                anchor="center"
            )

        barra = ttk.Scrollbar(
            tabla_frame,
            orient="vertical",
            command=tabla.yview,
            style="Tema.Vertical.TScrollbar"
        )
        tabla.configure(yscrollcommand=barra.set)

        tabla.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        barra.pack(side="right", fill="y", padx=(0, 8), pady=8)

        with obtener_conexion() as conexion:
            registros = conexion.execute(
                """
                SELECT
                    m.fecha,
                    p.nombre AS producto,
                    m.cantidad,
                    m.motivo,
                    m.costo_total
                FROM mermas m
                INNER JOIN productos p ON p.id = m.producto_id
                ORDER BY m.id DESC
                LIMIT 10
                """
            ).fetchall()

        for registro in registros:
            tabla.insert(
                "",
                "end",
                values=(
                    registro["fecha"],
                    registro["producto"],
                    registro["cantidad"],
                    registro["motivo"],
                    f"${registro['costo_total']:,.2f}"
                )
            )

        if not registros:
            tk.Label(
                tabla_frame,
                text="Todavía no hay mermas registradas.",
                font=("Segoe UI", 10),
                bg=self.BLANCO,
                fg=self.TEXTO_SECUNDARIO
            ).place(relx=0.5, rely=0.5, anchor="center")

    
    def crear_paneles_inicio(self):
        """Gráfica de los últimos 7 días y productos con stock bajo."""
        fila = tk.Frame(self.contenido, bg=self.FONDO)
        fila.pack(fill="x", padx=30, pady=(12, 0))
        fila.columnconfigure(0, weight=3, uniform="p")
        fila.columnconfigure(1, weight=2, uniform="p")

        # ---- Costo de los últimos 7 días ----
        izquierda = tk.Frame(fila, bg=self.FONDO)
        izquierda.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(
            izquierda, text="Pérdidas de los últimos 7 días",
            font=("Segoe UI", 12, "bold"), bg=self.FONDO, fg=self.VERDE_OSCURO
        ).pack(anchor="w", pady=(0, 6))

        marco_g = tk.Frame(
            izquierda, bg=self.BLANCO,
            highlightbackground=self.BORDE, highlightthickness=1
        )
        marco_g.pack(fill="x")
        grafica = GraficaLinea(self, marco_g, alto=150)
        grafica.pack(fill="x", padx=8, pady=8)

        hoy = date.today()
        try:
            grafica.mostrar(costo_por_dia(
                (hoy - timedelta(days=6)).isoformat(), hoy.isoformat()
            ))
        except Exception:
            grafica.mostrar([])

        # ---- Productos con stock bajo ----
        derecha = tk.Frame(fila, bg=self.FONDO)
        derecha.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(
            derecha, text="Productos con stock bajo",
            font=("Segoe UI", 12, "bold"), bg=self.FONDO, fg=self.VERDE_OSCURO
        ).pack(anchor="w", pady=(0, 6))

        marco_s, tabla_s = crear_tabla(self, derecha, [
            ("producto", "Producto", 105, "w"),
            ("existencia", "Existencia", 90, "center"),
            ("estado", "Estado", 65, "center"),
        ])
        marco_s.pack(fill="x")
        tabla_s.configure(height=3)
        tabla_s.tag_configure("bajo", background="#FBF5E4")
        tabla_s.tag_configure("agotado", background="#FBECEC")

        try:
            alertas = consultar_inventario(solo_alertas=True)
        except Exception:
            alertas = []

        # Primero los agotados, luego los más cercanos a quedarse sin stock
        alertas.sort(key=lambda p: (
            p["estado"] != "Agotado",
            p["existencia"] / p["stock_minimo"] if p["stock_minimo"] else 0
        ))

        for p in alertas[:30]:
            tabla_s.insert("", "end", tags=(p["estado"].lower(),), values=(
                p["nombre"], f"{p['existencia']:g} {p['unidad']}", p["estado"]
            ))

        if not alertas:
            tk.Label(
                marco_s, text="Sin alertas de stock.",
                font=("Segoe UI", 10), bg=self.BLANCO,
                fg=self.TEXTO_SECUNDARIO
            ).place(relx=0.5, rely=0.55, anchor="center")

    def mostrar_modulo_pendiente(self, titulo, descripcion):
        self.limpiar_contenido()
        self.titulo_pagina(titulo, descripcion)

        tarjeta = tk.Frame(
            self.contenido,
            bg=self.BLANCO,
            highlightbackground=self.BORDE,
            highlightthickness=1
        )
        tarjeta.pack(fill="x", padx=30, pady=10)

        tk.Label(
            tarjeta,
            text=titulo,
            font=("Segoe UI", 17, "bold"),
            bg=self.BLANCO,
            fg=self.VERDE_OSCURO
        ).pack(pady=(30, 10))

        tk.Label(
            tarjeta,
            text="Este módulo se conectará próximamente.",
            font=("Segoe UI", 11),
            bg=self.BLANCO,
            fg=self.TEXTO_SECUNDARIO
        ).pack(pady=(0, 30))

    def abrir_productos(self):
        self.resaltar_menu("Productos")
        ModuloProductos(self).mostrar()

    def abrir_mermas(self):
        self.resaltar_menu("Registrar merma")
        self.vista_mermas.mostrar()

    def abrir_inventario(self):
        self.resaltar_menu("Inventario")
        ModuloInventario(self).mostrar()

    def abrir_historial(self):
        self.resaltar_menu("Historial")
        ModuloHistorial(self).mostrar()

    def abrir_reportes(self):
        self.resaltar_menu("Reportes")
        ModuloReportes(self).mostrar()

    def abrir_proveedores(self):
        self.resaltar_menu("Proveedores")
        ModuloProveedores(self).mostrar()

    def abrir_compras(self):
        self.resaltar_menu("Compras")
        ModuloCompras(self).mostrar()

    def abrir_empleados(self):
        self.resaltar_menu("Empleados")
        ModuloEmpleados(self).mostrar()

    def abrir_usuarios(self):
        self.resaltar_menu("Usuarios")
        ModuloUsuarios(self).mostrar()


if __name__ == "__main__":
    inicializar = __import__(
        "base_datos", fromlist=["inicializar_base_datos"]
    ).inicializar_base_datos

    inicializar()

    root = tk.Tk()
    DashboardApp(
        root,
        usuario_id=1,
        nombre="Administrador",
        rol="Administrador"
    )
    root.mainloop()