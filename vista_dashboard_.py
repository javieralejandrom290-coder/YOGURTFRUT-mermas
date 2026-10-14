
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from base_datos import obtener_conexion
from vista_productos import ModuloProductos
from vista_mermas import ModuloMermas
from vista_inventario import ModuloInventario
from vista_historial import ModuloHistorial
from vista_reportes import ModuloReportes


class DashboardApp:
    def __init__(self, root, usuario_id, nombre, rol):
        self.root = root
        self.usuario_id = usuario_id
        self.nombre = nombre
        self.rol = rol

        self.root.title("YOGURTFRUT | Control de Mermas")
        self.root.geometry("1200x720")
        self.root.minsize(1000, 620)
        self.root.configure(bg="#F3F6F4")

        
        self.VERDE_OSCURO = "#173B32"
        self.VERDE_HOVER = "#245747"
        self.VERDE_CLARO = "#7CB342"
        self.VERDE_SUAVE = "#E8F3E5"
        self.BLANCO = "#FFFFFF"
        self.FONDO = "#F3F6F4"
        self.TEXTO = "#263238"
        self.TEXTO_SECUNDARIO = "#78909C"
        self.BORDE = "#E0E6E3"

        self.configurar_estilos()
        self.crear_menu_lateral()
        self.crear_contenido()

        self.mostrar_inicio()

    
    def configurar_estilos(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")

        estilo.configure(
            "Mermas.Treeview",
            background=self.BLANCO,
            foreground=self.TEXTO,
            fieldbackground=self.BLANCO,
            rowheight=35,
            borderwidth=0,
            font=("Segoe UI", 10)
        )

        estilo.configure(
            "Mermas.Treeview.Heading",
            background="#E8EFEA",
            foreground=self.VERDE_OSCURO,
            font=("Segoe UI", 10, "bold"),
            padding=10,
            relief="flat"
        )

        estilo.map(
            "Mermas.Treeview",
            background=[("selected", self.VERDE_SUAVE)],
            foreground=[("selected", self.VERDE_OSCURO)]
        )

    
    def crear_menu_lateral(self):
        self.menu = tk.Frame(
            self.root,
            bg=self.VERDE_OSCURO,
            width=240
        )
        self.menu.pack(side="left", fill="y")
        self.menu.pack_propagate(False)

        tk.Label(
            self.menu,
            text="YOGURTFRUT",
            font=("Segoe UI", 22, "bold"),
            bg=self.VERDE_OSCURO,
            fg=self.BLANCO
        ).pack(pady=(28, 2))

        tk.Label(
            self.menu,
            text="CONTROL DE MERMAS",
            font=("Segoe UI", 9, "bold"),
            bg=self.VERDE_OSCURO,
            fg="#B9D8A5"
        ).pack(pady=(0, 30))

        opciones = [
            ("⌂", "Inicio", self.mostrar_inicio),
            ("▣", "Productos", self.abrir_productos),
            ("＋", "Registrar merma", self.abrir_mermas),
            ("▤", "Inventario", self.abrir_inventario),
            ("◷", "Historial", self.abrir_historial),
            ("▥", "Reportes", self.abrir_reportes),
        ]

        self.botones_menu = {}

        for icono, texto, comando in opciones:
            boton = tk.Button(
                self.menu,
                text=f"  {icono}     {texto}",
                command=comando,
                font=("Segoe UI", 11),
                anchor="w",
                bg=self.VERDE_OSCURO,
                fg=self.BLANCO,
                activebackground=self.VERDE_HOVER,
                activeforeground=self.BLANCO,
                relief="flat",
                bd=0,
                cursor="hand2",
                padx=15,
                pady=12
            )
            boton.pack(fill="x", padx=10, pady=3)
            self.botones_menu[texto] = boton

            boton.bind(
                "<Enter>",
                lambda evento, b=boton:
                    b.configure(bg=self.VERDE_HOVER)
            )
            boton.bind(
                "<Leave>",
                lambda evento, b=boton:
                    b.configure(bg=self.VERDE_OSCURO)
            )

        
        separador = tk.Frame(
            self.menu,
            bg="#416358",
            height=1
        )
        separador.pack(side="bottom", fill="x", padx=18, pady=(0, 10))

        tk.Label(
            self.menu,
            text=f"  {self.nombre}",
            font=("Segoe UI", 10, "bold"),
            bg=self.VERDE_OSCURO,
            fg=self.BLANCO,
            anchor="w",
            wraplength=205
        ).pack(side="bottom", anchor="w", padx=15, pady=(0, 4))

        tk.Label(
            self.menu,
            text=f"  {self.rol}",
            font=("Segoe UI", 9),
            bg=self.VERDE_OSCURO,
            fg="#B9D8A5",
            anchor="w"
        ).pack(side="bottom", anchor="w", padx=15, pady=(0, 15))

    
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

    def titulo_pagina(self, titulo, descripcion):
        encabezado = tk.Frame(
            self.contenido,
            bg=self.FONDO
        )
        encabezado.pack(fill="x", padx=30, pady=(28, 20))

        tk.Label(
            encabezado,
            text=titulo,
            font=("Segoe UI", 24, "bold"),
            bg=self.FONDO,
            fg=self.VERDE_OSCURO
        ).pack(anchor="w")

        tk.Label(
            encabezado,
            text=descripcion,
            font=("Segoe UI", 10),
            bg=self.FONDO,
            fg=self.TEXTO_SECUNDARIO
        ).pack(anchor="w", pady=(5, 0))

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
            height=4
        ).pack(fill="x")

        tk.Label(
            tarjeta,
            text=titulo,
            font=("Segoe UI", 10),
            bg=self.BLANCO,
            fg=self.TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=16, pady=(15, 5))

        tk.Label(
            tarjeta,
            text=valor,
            font=("Segoe UI", 23, "bold"),
            bg=self.BLANCO,
            fg=self.VERDE_OSCURO
        ).pack(anchor="w", padx=16)

        tk.Label(
            tarjeta,
            text=detalle,
            font=("Segoe UI", 9),
            bg=self.BLANCO,
            fg=self.TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=16, pady=(4, 16))

        return tarjeta

    def mostrar_inicio(self):
        self.limpiar_contenido()
        self.titulo_pagina(
            "Panel principal",
            f"Bienvenido, {self.nombre}. Aquí tienes el resumen de YOGURTFRUT."
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

        
        tk.Label(
            self.contenido,
            text="Últimas mermas registradas",
            font=("Segoe UI", 16, "bold"),
            bg=self.FONDO,
            fg=self.VERDE_OSCURO
        ).pack(anchor="w", padx=30, pady=(28, 12))

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
            command=tabla.yview
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
        ModuloProductos(self).mostrar()

    def abrir_mermas(self):
        ModuloMermas(self).mostrar()

    def abrir_inventario(self):
        ModuloInventario(self).mostrar()

    def abrir_historial(self):
        ModuloHistorial(self).mostrar()

    def abrir_reportes(self):
        ModuloReportes(self).mostrar()


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
