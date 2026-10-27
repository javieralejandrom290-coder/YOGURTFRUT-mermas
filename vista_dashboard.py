import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta

import base_datos
import ui_tema
from base_datos import obtener_conexion
from ui_comunes import Tarjeta, crear_kpi, crear_logo
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
        self.root.geometry("1240x760")
        self.root.minsize(1040, 660)
        self.root.resizable(True, True)
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
        self.SIDEBAR = ui_tema.SIDEBAR
        self.SIDEBAR_ACTIVO = ui_tema.SIDEBAR_ACTIVO
        self.ACENTO = ui_tema.ACENTO
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

    def crear_menu_lateral(self):
        self.menu = tk.Frame(
            self.root,
            bg=self.SIDEBAR,
            width=264,
            highlightbackground=self.BORDE,
            highlightthickness=1,
            bd=0,
        )
        self.menu.pack(side="left", fill="y")
        self.menu.pack_propagate(False)

        # Marca: logo oficial + nombre del sistema
        marca = tk.Frame(self.menu, bg=self.SIDEBAR)
        marca.pack(fill="x", padx=20, pady=(14, 6))

        self.logo_menu = crear_logo(
            marca, bg=self.SIDEBAR, alto=42, texto=""
        )
        self.logo_menu.pack(side="left")

        textos_marca = tk.Frame(marca, bg=self.SIDEBAR)
        textos_marca.pack(side="left", padx=(10, 0))

        tk.Label(
            textos_marca,
            text="YOGUFRUT",
            font=ui_tema.fuente_titulo(16),
            bg=self.SIDEBAR,
            fg=self.VERDE_OSCURO,
        ).pack(anchor="w")

        tk.Label(
            textos_marca,
            text="CONTROL DE MERMAS",
            font=ui_tema.fuente_texto(7, "bold"),
            bg=self.SIDEBAR,
            fg=self.TEXTO_SECUNDARIO,
        ).pack(anchor="w", pady=(2, 0))

        tk.Frame(
            self.menu, bg=self.ACENTO, height=3, width=42
        ).pack(anchor="w", padx=20, pady=(0, 10))

        tk.Frame(self.menu, bg=self.BORDE, height=1).pack(
            fill="x", padx=20, pady=(0, 6)
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
        self.acentos_menu = {}
        self.seccion_activa = None

        for titulo_grupo, opciones in grupos:
            tk.Label(
                self.menu,
                text=titulo_grupo,
                font=ui_tema.fuente_texto(7, "bold"),
                bg=self.SIDEBAR,
                fg=self.TEXTO_SECUNDARIO,
                anchor="w",
            ).pack(fill="x", padx=24, pady=(10, 3))

            for texto, comando in opciones:
                item = tk.Frame(self.menu, bg=self.SIDEBAR)
                item.pack(fill="x", padx=12, pady=1)

                acento = tk.Frame(item, bg=self.SIDEBAR, width=3)
                acento.pack(side="left", fill="y")

                boton = tk.Button(
                    item,
                    text=texto,
                    command=comando,
                    font=ui_tema.fuente_texto(10),
                    anchor="w",
                    bg=self.SIDEBAR,
                    fg=self.TEXTO,
                    activebackground=self.SIDEBAR_ACTIVO,
                    activeforeground=self.VERDE_OSCURO,
                    relief="flat",
                    bd=0,
                    highlightthickness=0,
                    cursor="hand2",
                    padx=16,
                    pady=7,
                )
                boton.pack(side="left", fill="x", expand=True)
                self.botones_menu[texto] = boton
                self.acentos_menu[texto] = acento

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
        usuario = Tarjeta(self.menu, bg=self.BLANCO, padding=8)
        usuario.pack(side="bottom", fill="x", padx=14, pady=10)

        inicial = tk.Canvas(
            usuario.cuerpo, width=34, height=34, bg=self.BLANCO,
            highlightthickness=0
        )
        inicial.pack(side="left", padx=(2, 8), pady=3)
        inicial.create_oval(
            1, 1, 33, 33, fill=self.VERDE_CLARO, outline=""
        )
        inicial.create_text(
            17, 17, text=(self.nombre.strip()[:1] or "U").upper(),
            fill=self.VERDE_OSCURO, font=ui_tema.fuente_titulo(12)
        )

        datos = tk.Frame(usuario.cuerpo, bg=self.BLANCO)
        datos.pack(side="left", fill="x", expand=True, pady=4)

        tk.Label(
            datos,
            text=self.nombre,
            font=ui_tema.fuente_texto(9, "bold"),
            bg=self.BLANCO,
            fg=self.VERDE_OSCURO,
            anchor="w",
            wraplength=150,
        ).pack(anchor="w")

        tk.Label(
            datos,
            text=self.rol,
            font=ui_tema.fuente_texto(8),
            bg=self.BLANCO,
            fg=self.TEXTO_SECUNDARIO,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))
        
        
        # Botón para cerrar sesión y cambiar de usuario
        self.btn_cerrar_sesion = tk.Button(
            self.menu,
            text="↪  Cerrar sesión",
            command=self.cerrar_sesion,
            font=ui_tema.fuente_texto(10, "bold"),
            bg=self.SIDEBAR_ACTIVO,
            fg=self.VERDE_OSCURO,
            activebackground=self.VERDE_SUAVE,
            activeforeground=self.VERDE_OSCURO,
            relief="flat",
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            pady=10,
        )
        self.btn_cerrar_sesion.pack(
            side="bottom",
            fill="x",
            padx=14,
            pady=(0, 12),
        )

        self.btn_cerrar_sesion.bind(
            "<Enter>",
            lambda evento: self.btn_cerrar_sesion.configure(
                bg=self.VERDE_SUAVE
            ),
        )
        self.btn_cerrar_sesion.bind(
            "<Leave>",
            lambda evento: self.btn_cerrar_sesion.configure(
                bg=self.SIDEBAR_ACTIVO
            ),
        )
        
        
    def cerrar_sesion(self):
        """Regresa al login para permitir cambiar de usuario."""

        confirmar = messagebox.askyesno(
            "Cerrar sesión",
            f"¿Deseas cerrar la sesión de {self.nombre}?",
            parent=self.root,
        )

        if not confirmar:
            return

        # Eliminar el dashboard y sus módulos de la ventana actual.
        for widget in self.root.winfo_children():
            widget.destroy()

        try:
            # Reutilizar la misma ventana para regresar al login.
            from vista_login import LoginApp
            LoginApp(self.root)

        except Exception as error:
            messagebox.showerror(
                "Error al cerrar sesión",
                "No se pudo regresar a la pantalla de inicio.\n\n"
                f"Detalle: {error}",
                parent=self.root,
            )



    def color_boton_menu(self, texto, pasando=False):
        """Color del botón del menú: activo, con el mouse encima o normal."""
        if texto == self.seccion_activa:
            return self.SIDEBAR_ACTIVO
        return self.VERDE_SUAVE if pasando else self.SIDEBAR

    def resaltar_menu(self, texto):
        """Marca en el menú lateral la sección que se está viendo."""
        self.seccion_activa = texto
        for nombre, boton in self.botones_menu.items():
            activo = nombre == texto
            boton.configure(
                bg=self.color_boton_menu(nombre),
                fg=self.VERDE_OSCURO if activo else self.TEXTO,
                font=ui_tema.fuente_texto(10, "bold" if activo else "normal"),
            )
            self.acentos_menu[nombre].configure(
                bg=self.VERDE_PRIMARIO if activo else self.SIDEBAR
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
        encabezado.pack(fill="x", padx=32, pady=(28, 20))

        fila = tk.Frame(encabezado, bg=self.FONDO)
        fila.pack(fill="x")

        tk.Frame(
            fila, bg=self.VERDE_PRIMARIO, width=4, height=48
        ).pack(side="left", padx=(0, 14))

        textos = tk.Frame(fila, bg=self.FONDO)
        textos.pack(side="left", fill="x", expand=True)

        tk.Label(
            textos,
            text=titulo,
            font=ui_tema.fuente_titulo(24),
            bg=self.FONDO,
            fg=self.VERDE_OSCURO
        ).pack(anchor="w")

        tk.Label(
            textos,
            text=descripcion,
            font=ui_tema.fuente_texto(10),
            bg=self.FONDO,
            fg=self.TEXTO_SECUNDARIO
        ).pack(anchor="w", pady=(4, 0))

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

    def crear_tarjeta(self, contenedor, titulo, valor, detalle, color=None):
        return crear_kpi(
            self,
            contenedor,
            titulo,
            valor=valor,
            detalle=detalle,
            color=color or self.VERDE_PRIMARIO,
        )

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
        tarjetas.pack(fill="x", padx=32)
        tarjetas.grid_rowconfigure(0, weight=1)

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

        colores_kpi = [
            ui_tema.VERDE_CLARO,
            ui_tema.VERDE_MEDIO,
            ui_tema.ACENTO,
            ui_tema.VERDE_CLARO,
        ]

        for indice, (titulo, valor, detalle) in enumerate(tarjetas_info):
            tarjeta = self.crear_tarjeta(
                tarjetas, titulo, valor, detalle,
                color=colores_kpi[indice % len(colores_kpi)],
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
            font=ui_tema.fuente_titulo(16),
            bg=self.FONDO,
            fg=self.VERDE_OSCURO
        ).pack(anchor="w", padx=32, pady=(16, 10))

        tabla_frame, tabla = crear_tabla(self, self.contenido, [
            ("fecha", "Fecha", 150, "center"),
            ("producto", "Producto", 190, "w"),
            ("cantidad", "Cantidad", 100, "center"),
            ("motivo", "Motivo", 180, "w"),
            ("costo", "Costo", 120, "e"),
        ])
        tabla_frame.pack(
            fill="both",
            expand=True,
            padx=32,
            pady=(0, 28)
        )

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
                tabla_frame.cuerpo,
                text="Todavía no hay mermas registradas.",
                font=ui_tema.fuente_texto(10),
                bg=self.BLANCO,
                fg=self.TEXTO_SECUNDARIO
            ).place(relx=0.5, rely=0.5, anchor="center")

    
    def crear_paneles_inicio(self):
        """Gráfica de los últimos 7 días y productos con stock bajo."""
        fila = tk.Frame(self.contenido, bg=self.FONDO)
        fila.pack(fill="x", padx=32, pady=(14, 0))
        fila.columnconfigure(0, weight=3, uniform="p")
        fila.columnconfigure(1, weight=2, uniform="p")

        # ---- Costo de los últimos 7 días ----
        izquierda = tk.Frame(fila, bg=self.FONDO)
        izquierda.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(
            izquierda, text="Pérdidas de los últimos 7 días",
            font=ui_tema.fuente_titulo(12), bg=self.FONDO, fg=self.VERDE_OSCURO
        ).pack(anchor="w", pady=(0, 8))

        marco_g = Tarjeta(izquierda, bg=self.BLANCO, padding=12)
        marco_g.pack(fill="x")
        grafica = GraficaLinea(self, marco_g.cuerpo, alto=160)
        grafica.pack(fill="x")

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
            font=ui_tema.fuente_titulo(12), bg=self.FONDO, fg=self.VERDE_OSCURO
        ).pack(anchor="w", pady=(0, 8))

        marco_s, tabla_s = crear_tabla(self, derecha, [
            ("producto", "Producto", 105, "w"),
            ("existencia", "Existencia", 90, "center"),
            ("estado", "Estado", 65, "center"),
        ])
        marco_s.pack(fill="x")
        tabla_s.configure(height=3)
        tabla_s.tag_configure(
            "bajo", background=ui_tema.PELIGRO_FONDO,
            foreground=ui_tema.PELIGRO
        )
        tabla_s.tag_configure(
            "agotado", background=ui_tema.PELIGRO_FONDO,
            foreground=ui_tema.PELIGRO
        )

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
                marco_s.cuerpo, text="Sin alertas de stock.",
                font=ui_tema.fuente_texto(10), bg=self.BLANCO,
                fg=self.TEXTO_SECUNDARIO
            ).place(relx=0.5, rely=0.55, anchor="center")

    def mostrar_modulo_pendiente(self, titulo, descripcion):
        self.limpiar_contenido()
        self.titulo_pagina(titulo, descripcion)

        tarjeta = Tarjeta(self.contenido, bg=self.BLANCO, padding=24)
        tarjeta.pack(fill="x", padx=32, pady=10)

        tk.Label(
            tarjeta.cuerpo,
            text=titulo,
            font=ui_tema.fuente_titulo(18),
            bg=self.BLANCO,
            fg=self.VERDE_OSCURO
        ).pack(pady=(20, 10))

        tk.Label(
            tarjeta.cuerpo,
            text="Este módulo se conectará próximamente.",
            font=ui_tema.fuente_texto(11),
            bg=self.BLANCO,
            fg=self.TEXTO_SECUNDARIO
        ).pack(pady=(0, 20))

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