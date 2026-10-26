import calendar
import tkinter as tk
from datetime import date, datetime
from tkinter import ttk


# Componentes visuales compartidos por los apartados del dashboard.
# El objeto "d" debe exponer los colores usados aquí:
# BLANCO, BORDE, VERDE_CLARO, VERDE_OSCURO, VERDE_SUAVE,
# TEXTO y TEXTO_SECUNDARIO.


def crear_boton(d, contenedor, texto, comando, principal=False):
    """Crea un botón principal verde o uno secundario blanco."""
    return tk.Button(
        contenedor,
        text=texto,
        command=comando,
        relief="flat",
        borderwidth=0,
        font=("Segoe UI", 10, "bold"),
        bg=d.VERDE_CLARO if principal else d.BLANCO,
        fg=d.BLANCO if principal else d.VERDE_OSCURO,
        activebackground="#72A800" if principal else d.VERDE_SUAVE,
        activeforeground=d.BLANCO if principal else d.VERDE_OSCURO,
        highlightbackground=d.BORDE,
        highlightthickness=0 if principal else 1,
        cursor="hand2",
        padx=16,
        pady=8,
    )


def activar_filas_alternadas(tabla, color="#EAF5D5"):
    """
    Aplica filas alternas a un ttk.Treeview y mantiene el patrón
    cuando se agregan nuevas filas con tabla.insert(...).
    """
    tabla.tag_configure("fila_par", background="#FFFFFF")
    tabla.tag_configure("fila_impar", background=color)

    # Conservar la función original para evitar envolverla más de una vez.
    if getattr(tabla, "_filas_alternadas_activadas", False):
        # Actualizar las etiquetas de filas existentes por si cambió el color.
        for indice, elemento in enumerate(tabla.get_children("")):
            etiqueta = "fila_par" if indice % 2 == 0 else "fila_impar"
            tabla.item(elemento, tags=(etiqueta,))
        return

    insertar_original = tabla.insert

    def insertar_con_filas(parent, index, iid=None, **opciones):
        # Respeta las etiquetas explícitas de otras partes del programa.
        if not opciones.get("tags"):
            cantidad = len(tabla.get_children(parent))
            opciones["tags"] = (
                "fila_par" if cantidad % 2 == 0 else "fila_impar",
            )

        if iid is None:
            return insertar_original(parent, index, **opciones)
        return insertar_original(parent, index, iid=iid, **opciones)

    tabla.insert = insertar_con_filas
    tabla._filas_alternadas_activadas = True

    # Aplicar el estilo a las filas que ya existían.
    for indice, elemento in enumerate(tabla.get_children("")):
        etiqueta = "fila_par" if indice % 2 == 0 else "fila_impar"
        tabla.item(elemento, tags=(etiqueta,))


def crear_tabla(d, contenedor, columnas):
    """
    Crea una tabla con encabezados modernos y barra de desplazamiento.
    columnas debe ser una secuencia de tuplas:
    (clave, encabezado, ancho, alineacion).
    Devuelve (marco, tabla).
    """
    estilo = ttk.Style()

    estilo.configure(
        "Custom.Treeview",
        background=d.BLANCO,
        foreground="#263238",
        rowheight=36,
        fieldbackground=d.BLANCO,
        borderwidth=0,
        font=("Segoe UI", 10),
    )
    estilo.configure(
        "Custom.Treeview.Heading",
        background="#EAF1E5",
        foreground=d.VERDE_OSCURO,
        font=("Segoe UI", 10, "bold"),
        borderwidth=0,
        relief="flat",
        padding=(8, 10),
    )
    estilo.map(
        "Custom.Treeview.Heading",
        background=[("active", "#DCEBCB")],
        foreground=[("active", d.VERDE_OSCURO)],
    )
    estilo.map(
        "Custom.Treeview",
        background=[("selected", d.VERDE_CLARO)],
        foreground=[("selected", "#FFFFFF")],
    )

    marco = tk.Frame(
        contenedor,
        bg=d.BLANCO,
        highlightbackground=d.BORDE,
        highlightthickness=1,
    )

    claves = [columna[0] for columna in columnas]
    tabla = ttk.Treeview(
        marco,
        columns=claves,
        show="headings",
        style="Custom.Treeview",
        selectmode="browse",
    )

    for clave, encabezado, ancho, alineacion in columnas:
        tabla.heading(clave, text=encabezado)
        tabla.column(clave, width=ancho, anchor=alineacion, minwidth=50)

    barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=barra.set)

    tabla.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(8, 0),
        pady=8,
    )
    barra.pack(side="right", fill="y", padx=(0, 8), pady=8)

    activar_filas_alternadas(tabla)
    return marco, tabla


def crear_tarjeta_resumen(d, padre, titulo, variable):
    """Tarjeta compacta para mostrar una estadística del dashboard."""
    tarjeta = tk.Frame(
        padre,
        bg=d.BLANCO,
        highlightbackground=d.BORDE,
        highlightthickness=1,
    )

    tk.Frame(tarjeta, bg=d.VERDE_CLARO, height=4).pack(fill="x")

    contenido = tk.Frame(tarjeta, bg=d.BLANCO)
    contenido.pack(fill="both", expand=True, padx=15, pady=13)

    tk.Label(
        contenido,
        text=titulo,
        font=("Segoe UI", 9, "bold"),
        bg=d.BLANCO,
        fg="#68756A",
    ).pack(anchor="w")

    tk.Label(
        contenido,
        textvariable=variable,
        font=("Segoe UI", 22, "bold"),
        bg=d.BLANCO,
        fg=d.VERDE_OSCURO,
    ).pack(anchor="w", pady=(5, 0))

    return tarjeta


MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
DIAS_SEMANA = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]


def leer_fecha(texto):
    """Convierte AAAA-MM-DD en date; devuelve None si el texto no es válido."""
    try:
        return datetime.strptime(texto.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


class CalendarioFecha(tk.Toplevel):
    """Ventana emergente de calendario para seleccionar una fecha."""

    def __init__(self, d, ancla, variable, permitir_vacio=False):
        super().__init__(ancla.winfo_toplevel())

        self.d = d
        self.variable = variable
        self.permitir_vacio = permitir_vacio

        fecha_inicial = leer_fecha(variable.get()) or date.today()
        self.seleccionada = leer_fecha(variable.get())
        self.anio = fecha_inicial.year
        self.mes = fecha_inicial.month

        self.title("Elegir fecha")
        self.configure(bg=d.BLANCO)
        self.resizable(False, False)
        self.transient(ancla.winfo_toplevel())
        self.bind("<Escape>", lambda _evento: self.destroy())

        self.encabezado = tk.Frame(self, bg=d.BLANCO)
        self.encabezado.pack(fill="x", padx=10, pady=(10, 4))

        self.cuadricula = tk.Frame(self, bg=d.BLANCO)
        self.cuadricula.pack(padx=10)

        self.pie = tk.Frame(self, bg=d.BLANCO)
        self.pie.pack(fill="x", padx=10, pady=(6, 10))

        self.dibujar()

        self.update_idletasks()
        x = ancla.winfo_rootx()
        y = ancla.winfo_rooty() + ancla.winfo_height() + 4
        ancho = self.winfo_reqwidth()
        alto = self.winfo_reqheight()
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()

        # Evitar que la ventana se salga de los bordes de la pantalla.
        x = max(0, min(x, pantalla_ancho - ancho))
        y = max(0, min(y, pantalla_alto - alto))
        self.geometry(f"+{x}+{y}")
        self.focus_set()

        try:
            self.grab_set()
        except tk.TclError:
            pass

    def boton(self, padre, texto, comando, **extra):
        d = self.d
        return tk.Button(
            padre,
            text=texto,
            command=comando,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10),
            bg=extra.pop("bg", d.BLANCO),
            fg=extra.pop("fg", d.TEXTO),
            cursor="hand2",
            activebackground=d.VERDE_SUAVE,
            activeforeground=d.VERDE_OSCURO,
            padx=5,
            pady=4,
            **extra,
        )

    def cambiar_mes(self, delta):
        mes_nuevo = self.mes + delta
        self.anio += (mes_nuevo - 1) // 12
        self.mes = (mes_nuevo - 1) % 12 + 1
        self.dibujar()

    def dibujar(self):
        d = self.d

        for marco in (self.encabezado, self.cuadricula, self.pie):
            for hijo in marco.winfo_children():
                hijo.destroy()

        self.boton(
            self.encabezado,
            "‹",
            lambda: self.cambiar_mes(-1),
            width=3,
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")

        self.boton(
            self.encabezado,
            "›",
            lambda: self.cambiar_mes(1),
            width=3,
            font=("Segoe UI", 14, "bold"),
        ).pack(side="right")

        tk.Label(
            self.encabezado,
            text=f"{MESES[self.mes - 1]} {self.anio}",
            font=("Segoe UI", 11, "bold"),
            bg=d.BLANCO,
            fg=d.VERDE_OSCURO,
        ).pack(expand=True)

        for columna, nombre in enumerate(DIAS_SEMANA):
            tk.Label(
                self.cuadricula,
                text=nombre,
                width=4,
                font=("Segoe UI", 9, "bold"),
                bg=d.BLANCO,
                fg=d.TEXTO_SECUNDARIO,
            ).grid(row=0, column=columna, pady=(0, 3))

        hoy = date.today()
        semanas = calendar.Calendar(firstweekday=0).monthdayscalendar(
            self.anio, self.mes
        )

        for fila, semana in enumerate(semanas, start=1):
            for columna, dia in enumerate(semana):
                if dia == 0:
                    continue

                fecha = date(self.anio, self.mes, dia)
                if fecha == self.seleccionada:
                    estilo = {"bg": d.VERDE_CLARO, "fg": "#FFFFFF"}
                elif fecha == hoy:
                    estilo = {"bg": d.VERDE_SUAVE, "fg": d.VERDE_OSCURO}
                else:
                    estilo = {"bg": d.BLANCO, "fg": d.TEXTO}

                self.boton(
                    self.cuadricula,
                    str(dia),
                    lambda fecha_elegida=fecha: self.elegir(fecha_elegida),
                    width=4,
                    **estilo,
                ).grid(row=fila, column=columna, padx=1, pady=1)

        self.boton(
            self.pie,
            "Hoy",
            lambda: self.elegir(date.today()),
            fg=d.VERDE_OSCURO,
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")

        if self.permitir_vacio:
            self.boton(
                self.pie,
                "Borrar fecha",
                lambda: self.elegir(None),
                fg=d.TEXTO_SECUNDARIO,
                font=("Segoe UI", 9),
            ).pack(side="right")

    def elegir(self, fecha):
        self.variable.set(fecha.isoformat() if fecha else "")
        self.destroy()


def crear_campo_fecha(
    d,
    padre,
    variable,
    fuente=("Segoe UI", 11),
    ancho=12,
    permitir_vacio=False,
):
    """
    Crea un campo de fecha AAAA-MM-DD con botón de calendario.
    Devuelve el marco; la entrada está disponible como marco.entrada.
    """
    marco = tk.Frame(
        padre,
        bg=d.BLANCO,
        highlightbackground=d.BORDE,
        highlightcolor=d.VERDE_CLARO,
        highlightthickness=1,
    )

    entrada = tk.Entry(
        marco,
        textvariable=variable,
        font=fuente,
        width=ancho,
        relief="flat",
        bd=0,
        bg=d.BLANCO,
        fg=d.TEXTO,
        insertbackground=d.VERDE_OSCURO,
        highlightthickness=0,
    )
    entrada.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(8, 0),
        ipady=5,
    )

    boton_calendario = tk.Button(
        marco,
        text="▦",
        font=("Segoe UI", 11),
        relief="flat",
        bd=0,
        bg=d.BLANCO,
        fg=d.VERDE_OSCURO,
        cursor="hand2",
        activebackground=d.VERDE_SUAVE,
        activeforeground=d.VERDE_OSCURO,
        padx=8,
        command=lambda: CalendarioFecha(
            d, marco, variable, permitir_vacio
        ),
    )
    boton_calendario.pack(side="right", fill="y")

    marco.entrada = entrada
    marco.boton_calendario = boton_calendario
    return marco
