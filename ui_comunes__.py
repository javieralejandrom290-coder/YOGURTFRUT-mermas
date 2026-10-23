import calendar
import tkinter as tk
from datetime import date, datetime
from tkinter import ttk


# Componentes visuales compartidos por los apartados del dashboard.
# Todos reciben el dashboard (d) para usar su misma paleta de colores.


def crear_boton(d, contenedor, texto, comando, principal=False):
    """Botón verde (principal) o blanco con borde (secundario)."""
    return tk.Button(
        contenedor,
        text=texto,
        command=comando,
        font=("Segoe UI", 10, "bold"),
        bg=d.VERDE_CLARO if principal else d.BLANCO,
        fg=d.BLANCO if principal else d.VERDE_OSCURO,
        activebackground="#689F38" if principal else d.VERDE_SUAVE,
        activeforeground=d.BLANCO if principal else d.VERDE_OSCURO,
        relief="flat",
        bd=0,
        highlightbackground=d.BORDE,
        highlightthickness=0 if principal else 1,
        cursor="hand2",
        padx=16,
        pady=8
    )


def crear_tabla(d, contenedor, columnas):
    """
    Crea una tabla con barra de desplazamiento.
    columnas: lista de (clave, encabezado, ancho, alineacion).
    Devuelve (marco, tabla).
    """
    marco = tk.Frame(
        contenedor,
        bg=d.BLANCO,
        highlightbackground=d.BORDE,
        highlightthickness=1
    )

    tabla = ttk.Treeview(
        marco,
        columns=[clave for clave, _, _, _ in columnas],
        show="headings",
        style="Mermas.Treeview",
        selectmode="browse"
    )

    for clave, encabezado, ancho, alineacion in columnas:
        tabla.heading(clave, text=encabezado)
        tabla.column(clave, width=ancho, anchor=alineacion)

    barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=barra.set)

    tabla.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
    barra.pack(side="right", fill="y", padx=(0, 8), pady=8)

    activar_filas_alternadas(tabla)

    return marco, tabla


def activar_filas_alternadas(tabla, color="#F6F9F7"):
    """
    Pinta de gris muy claro una fila sí y otra no.
    Respeta las filas que ya traen su propio color (stock bajo, agotado...).
    """
    tabla.tag_configure("zebra", background=color)
    insertar_original = tabla.insert

    def insertar(parent, index, iid=None, **opciones):
        if not opciones.get("tags") and len(tabla.get_children(parent)) % 2 == 1:
            opciones["tags"] = ("zebra",)
        return insertar_original(parent, index, iid=iid, **opciones)

    tabla.insert = insertar


def crear_tarjeta_resumen(d, contenedor, titulo, variable):
    """Tarjeta con un título pequeño y un valor grande ligado a un StringVar."""
    tarjeta = tk.Frame(
        contenedor,
        bg=d.BLANCO,
        highlightbackground=d.BORDE,
        highlightthickness=1
    )

    tk.Frame(tarjeta, bg=d.VERDE_CLARO, height=4).pack(fill="x")

    tk.Label(
        tarjeta,
        text=titulo,
        font=("Segoe UI", 9, "bold"),
        bg=d.BLANCO,
        fg=d.TEXTO_SECUNDARIO
    ).pack(anchor="w", padx=16, pady=(12, 2))

    tk.Label(
        tarjeta,
        textvariable=variable,
        font=("Segoe UI", 20, "bold"),
        bg=d.BLANCO,
        fg=d.VERDE_OSCURO
    ).pack(anchor="w", padx=16, pady=(0, 14))

    return tarjeta


# ----------------------------------------------------------------------
# Selector de fecha (calendario desplegable, sin instalar nada)
# ----------------------------------------------------------------------
MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
    "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]
DIAS_SEMANA = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]


def leer_fecha(texto):
    """Convierte 'AAAA-MM-DD' en date, o devuelve None si no es válida."""
    try:
        return datetime.strptime(texto.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


class CalendarioFecha(tk.Toplevel):
    """Ventana pequeña con el mes; al elegir un día escribe AAAA-MM-DD."""

    def __init__(self, d, ancla, variable, permitir_vacio=False):
        super().__init__(ancla)
        self.d = d
        self.variable = variable
        self.permitir_vacio = permitir_vacio

        inicial = leer_fecha(variable.get()) or date.today()
        self.seleccionada = leer_fecha(variable.get())
        self.anio, self.mes = inicial.year, inicial.month

        self.title("Elegir fecha")
        self.configure(bg=d.BLANCO, highlightbackground=d.BORDE,
                       highlightthickness=1)
        self.resizable(False, False)
        self.transient(ancla.winfo_toplevel())
        self.bind("<Escape>", lambda e: self.destroy())

        self.encabezado = tk.Frame(self, bg=d.BLANCO)
        self.encabezado.pack(fill="x", padx=10, pady=(10, 4))
        self.cuadricula = tk.Frame(self, bg=d.BLANCO)
        self.cuadricula.pack(padx=10)
        self.pie = tk.Frame(self, bg=d.BLANCO)
        self.pie.pack(fill="x", padx=10, pady=(6, 10))

        self.dibujar()

        # Aparece justo debajo del campo
        self.update_idletasks()
        x = ancla.winfo_rootx()
        y = ancla.winfo_rooty() + ancla.winfo_height() + 4
        self.geometry(f"+{x}+{y}")
        self.focus_set()
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def boton(self, padre, texto, comando, **extra):
        d = self.d
        return tk.Button(
            padre, text=texto, command=comando, relief="flat", bd=0,
            font=("Segoe UI", 10), bg=extra.pop("bg", d.BLANCO),
            fg=extra.pop("fg", d.TEXTO), cursor="hand2",
            activebackground=d.VERDE_SUAVE, **extra
        )

    def cambiar_mes(self, delta):
        mes = self.mes + delta
        self.anio += (mes - 1) // 12
        self.mes = (mes - 1) % 12 + 1
        self.dibujar()

    def dibujar(self):
        d = self.d
        for marco in (self.encabezado, self.cuadricula, self.pie):
            for hijo in marco.winfo_children():
                hijo.destroy()

        self.boton(self.encabezado, "‹", lambda: self.cambiar_mes(-1),
                   width=3).pack(side="left")
        self.boton(self.encabezado, "›", lambda: self.cambiar_mes(1),
                   width=3).pack(side="right")
        tk.Label(
            self.encabezado, text=f"{MESES[self.mes - 1]} {self.anio}",
            font=("Segoe UI", 11, "bold"), bg=d.BLANCO, fg=d.VERDE_OSCURO
        ).pack(expand=True)

        for columna, nombre in enumerate(DIAS_SEMANA):
            tk.Label(
                self.cuadricula, text=nombre, width=4,
                font=("Segoe UI", 9, "bold"), bg=d.BLANCO,
                fg=d.TEXTO_SECUNDARIO
            ).grid(row=0, column=columna, pady=(0, 2))

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
                    estilo = {"bg": d.VERDE_CLARO, "fg": d.BLANCO}
                elif fecha == hoy:
                    estilo = {"bg": d.VERDE_SUAVE, "fg": d.VERDE_OSCURO}
                else:
                    estilo = {}
                self.boton(
                    self.cuadricula, str(dia),
                    lambda f=fecha: self.elegir(f), width=4, **estilo
                ).grid(row=fila, column=columna, padx=1, pady=1)

        self.boton(self.pie, "Hoy", lambda: self.elegir(date.today()),
                   fg=d.VERDE_OSCURO).pack(side="left")
        if self.permitir_vacio:
            self.boton(self.pie, "Borrar", lambda: self.elegir(None),
                       fg=d.TEXTO_SECUNDARIO).pack(side="right")

    def elegir(self, fecha):
        self.variable.set(fecha.isoformat() if fecha else "")
        self.destroy()


def crear_campo_fecha(d, padre, variable, fuente=("Segoe UI", 11),
                      ancho=12, permitir_vacio=False):
    """
    Campo de fecha AAAA-MM-DD con un botón que abre un calendario.
    Devuelve el marco: colócalo con pack() o grid().
    El usuario también puede seguir escribiendo la fecha a mano.
    """
    marco = tk.Frame(
        padre, bg=d.BLANCO,
        highlightbackground=d.BORDE, highlightcolor=d.VERDE_CLARO,
        highlightthickness=1
    )

    entrada = tk.Entry(
        marco, textvariable=variable, font=fuente, width=ancho,
        relief="flat", bd=0, bg=d.BLANCO, fg=d.TEXTO,
        highlightthickness=0
    )
    entrada.pack(side="left", fill="x", expand=True, padx=(8, 0), ipady=5)

    boton = tk.Button(
        marco, text="▦", font=("Segoe UI", 11), relief="flat", bd=0,
        bg=d.BLANCO, fg=d.VERDE_OSCURO, cursor="hand2",
        activebackground=d.VERDE_SUAVE, padx=8,
        command=lambda: CalendarioFecha(d, marco, variable, permitir_vacio)
    )
    boton.pack(side="right", fill="y")

    marco.entrada = entrada
    return marco
