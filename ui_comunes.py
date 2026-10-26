import calendar
import pathlib
import tkinter as tk
from datetime import date, datetime
from tkinter import ttk

import ui_tema


# Componentes visuales compartidos del dashboard.
# Se conserva la compatibilidad con las pantallas que ya usan estas funciones.


class Tarjeta(tk.Frame):
    """Contenedor tipo tarjeta con fondo, borde y sombra suave."""

    def __init__(
        self,
        padre,
        bg=ui_tema.BLANCO,
        radio=ui_tema.RADIO_TARJETA,
        sombra=True,
        padding=ui_tema.ESPACIO_M,
        **extra,
    ):
        self._fondo_padre = ui_tema._color_padre(padre)
        super().__init__(
            padre,
            bg=self._fondo_padre,
            highlightthickness=0,
            bd=0,
            **extra,
        )
        self._fondo_tarjeta = bg
        self._radio = radio
        self._sombra = sombra
        self._padding = padding

        self._canvas = tk.Canvas(
            self, bg=self._fondo_padre, highlightthickness=0, bd=0
        )
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.cuerpo = tk.Frame(self, bg=bg)
        self.cuerpo.pack(fill="both", expand=True, padx=padding, pady=padding)

        self.bind("<Configure>", self._redibujar)
        self.after_idle(self._redibujar)

    def _redibujar(self, _evento=None):
        self._canvas.delete("all")
        ancho = max(1, self.winfo_width())
        alto = max(1, self.winfo_height())

        if self._sombra:
            ui_tema.rectangulo_redondeado(
                self._canvas,
                1, 4, ancho - 1, alto - 1,
                radio=self._radio,
                fill=ui_tema.SOMBRA_SUAVE,
                outline="",
            )

        ui_tema.rectangulo_redondeado(
            self._canvas,
            1, 1, ancho - 1, alto - 3,
            radio=self._radio,
            fill=self._fondo_tarjeta,
            outline=ui_tema.BORDE,
            width=1,
        )


def crear_boton(d, contenedor, texto, comando, principal=False):
    """Botón con el tema visual compartido."""
    return ui_tema.boton(
        contenedor,
        texto,
        comando,
        principal=principal,
        fuente=ui_tema.fuente_texto(10, "bold"),
    )


def activar_filas_alternadas(tabla, color=None):
    """Aplica colores alternos a filas existentes y nuevas."""
    color = color or getattr(ui_tema, "FILA_ALTERNA", "#EAF5D5")
    tabla.tag_configure("fila_par", background=ui_tema.BLANCO)
    tabla.tag_configure("fila_impar", background=color)

    if getattr(tabla, "_filas_alternadas_activadas", False):
        for indice, elemento in enumerate(tabla.get_children("")):
            tabla.item(
                elemento,
                tags=("fila_par" if indice % 2 == 0 else "fila_impar",),
            )
        return

    insertar_original = tabla.insert

    def insertar_con_filas(parent, index, iid=None, **opciones):
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

    for indice, elemento in enumerate(tabla.get_children("")):
        tabla.item(
            elemento,
            tags=("fila_par" if indice % 2 == 0 else "fila_impar",),
        )


def crear_tabla(d, contenedor, columnas):
    """
    Crea una tabla moderna.
    columnas: (clave, encabezado, ancho, alineacion).
    Devuelve (marco, tabla).
    """
    estilo = ttk.Style()
    estilo.configure(
        "Custom.Treeview",
        background=d.BLANCO,
        foreground=d.TEXTO,
        rowheight=40,
        fieldbackground=d.BLANCO,
        borderwidth=0,
        relief="flat",
        font=ui_tema.fuente_texto(10),
    )
    estilo.configure(
        "Custom.Treeview.Heading",
        background=d.VERDE_SUAVE,
        foreground=d.VERDE_OSCURO,
        font=ui_tema.fuente_titulo(9),
        borderwidth=0,
        relief="flat",
        padding=(12, 10),
    )
    estilo.map(
        "Custom.Treeview.Heading",
        background=[("active", getattr(d, "VERDE_ACTIVO", d.VERDE_SUAVE))],
    )
    estilo.map(
        "Custom.Treeview",
        background=[("selected", d.VERDE_ACTIVO)],
        foreground=[("selected", d.VERDE_OSCURO)],
    )

    marco = Tarjeta(contenedor, bg=d.BLANCO, padding=6)
    claves = [clave for clave, _, _, _ in columnas]

    tabla = ttk.Treeview(
        marco.cuerpo,
        columns=claves,
        show="headings",
        style="Custom.Treeview",
        selectmode="browse",
    )

    for clave, encabezado, ancho, alineacion in columnas:
        tabla.heading(clave, text=encabezado)
        tabla.column(clave, width=ancho, anchor=alineacion, minwidth=40)

    barra = ttk.Scrollbar(
        marco.cuerpo,
        orient="vertical",
        command=tabla.yview,
        style="Tema.Vertical.TScrollbar",
    )
    tabla.configure(yscrollcommand=barra.set)

    def ajustar_columnas(_evento=None):
        ancho_disponible = tabla.winfo_width()
        if ancho_disponible <= 1:
            return
        total = sum(int(tabla.column(clave, "width")) for clave in claves)
        if total > ancho_disponible:
            factor = ancho_disponible / total
            for clave in claves:
                original = int(tabla.column(clave, "width"))
                tabla.column(clave, width=max(40, int(original * factor)))

    tabla.bind("<Configure>", ajustar_columnas, add="+")

    barra.pack(side="right", fill="y", padx=(0, 2), pady=2)
    tabla.pack(side="left", fill="both", expand=True, padx=(2, 0), pady=2)

    activar_filas_alternadas(tabla)
    return marco, tabla


def crear_kpi(
    d,
    padre,
    titulo,
    valor=None,
    detalle="",
    color=None,
    variable=None,
):
    """Tarjeta KPI compatible con valores fijos o variables Tkinter."""
    color = color or d.VERDE_CLARO
    tarjeta = Tarjeta(padre, bg=d.BLANCO, padding=16)
    cuerpo = tarjeta.cuerpo

    tk.Frame(cuerpo, bg=color, height=4).pack(fill="x", pady=(0, 12))

    fila_titulo = tk.Frame(cuerpo, bg=d.BLANCO)
    fila_titulo.pack(fill="x")

    punto = tk.Canvas(
        fila_titulo,
        width=9,
        height=9,
        bg=d.BLANCO,
        highlightthickness=0,
        bd=0,
    )
    punto.create_oval(0, 0, 9, 9, fill=color, outline="")
    punto.pack(side="left", padx=(0, 8))

    tk.Label(
        fila_titulo,
        text=titulo,
        font=ui_tema.fuente_texto(9, "bold"),
        bg=d.BLANCO,
        fg=d.TEXTO_SECUNDARIO,
        anchor="w",
    ).pack(side="left", fill="x", expand=True)

    if variable is not None:
        etiqueta_valor = tk.Label(
            cuerpo,
            textvariable=variable,
            font=ui_tema.fuente_titulo(25),
            bg=d.BLANCO,
            fg=d.VERDE_OSCURO,
            anchor="w",
        )
    else:
        etiqueta_valor = tk.Label(
            cuerpo,
            text=valor if valor not in (None, "") else "—",
            font=ui_tema.fuente_titulo(25),
            bg=d.BLANCO,
            fg=d.VERDE_OSCURO,
            anchor="w",
        )
    etiqueta_valor.pack(anchor="w", pady=(10, 2))

    if detalle:
        tk.Label(
            cuerpo,
            text=detalle,
            font=ui_tema.fuente_texto(8),
            bg=d.BLANCO,
            fg=d.TEXTO_SECUNDARIO,
            anchor="w",
        ).pack(anchor="w")

    return tarjeta


def crear_tarjeta_resumen(d, padre, titulo, variable):
    """Nombre antiguo conservado para no romper las pantallas existentes."""
    return crear_kpi(d, padre, titulo, variable=variable)


MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
DIAS_SEMANA = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]


def leer_fecha(texto):
    """Convierte AAAA-MM-DD en date; devuelve None si no es válida."""
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

        inicial = leer_fecha(variable.get()) or date.today()
        self.seleccionada = leer_fecha(variable.get())
        self.anio = inicial.year
        self.mes = inicial.month

        self.title("Elegir fecha")
        self.configure(bg=d.BLANCO, highlightbackground=d.BORDE, highlightthickness=1)
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
        x = max(0, min(x, self.winfo_screenwidth() - self.winfo_reqwidth()))
        y = max(0, min(y, self.winfo_screenheight() - self.winfo_reqheight()))
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
            font=extra.pop("font", ui_tema.fuente_texto(10)),
            bg=extra.pop("bg", d.BLANCO),
            fg=extra.pop("fg", d.TEXTO),
            cursor="hand2",
            activebackground=d.VERDE_SUAVE,
            activeforeground=d.VERDE_OSCURO,
            highlightthickness=0,
            padx=5,
            pady=4,
            **extra,
        )

    def cambiar_mes(self, delta):
        nuevo = self.mes + delta
        self.anio += (nuevo - 1) // 12
        self.mes = (nuevo - 1) % 12 + 1
        self.dibujar()

    def dibujar(self):
        d = self.d
        for marco in (self.encabezado, self.cuadricula, self.pie):
            for hijo in marco.winfo_children():
                hijo.destroy()

        self.boton(
            self.encabezado, "‹", lambda: self.cambiar_mes(-1),
            width=3, font=ui_tema.fuente_titulo(14),
        ).pack(side="left")
        self.boton(
            self.encabezado, "›", lambda: self.cambiar_mes(1),
            width=3, font=ui_tema.fuente_titulo(14),
        ).pack(side="right")

        tk.Label(
            self.encabezado,
            text=f"{MESES[self.mes - 1]} {self.anio}",
            font=ui_tema.fuente_titulo(11),
            bg=d.BLANCO,
            fg=d.VERDE_OSCURO,
        ).pack(expand=True)

        for columna, nombre in enumerate(DIAS_SEMANA):
            tk.Label(
                self.cuadricula,
                text=nombre,
                width=4,
                font=ui_tema.fuente_texto(9, "bold"),
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
            font=ui_tema.fuente_texto(9, "bold"),
        ).pack(side="left")

        if self.permitir_vacio:
            self.boton(
                self.pie,
                "Borrar fecha",
                lambda: self.elegir(None),
                fg=d.TEXTO_SECUNDARIO,
                font=ui_tema.fuente_texto(9),
            ).pack(side="right")

    def elegir(self, fecha):
        self.variable.set(fecha.isoformat() if fecha else "")
        self.destroy()


def crear_campo_fecha(
    d,
    padre,
    variable,
    fuente=None,
    ancho=12,
    permitir_vacio=False,
):
    """Campo AAAA-MM-DD con entrada y botón para abrir el calendario."""
    fuente = fuente or ui_tema.fuente_texto(11)
    marco = tk.Frame(
        padre,
        bg=d.BLANCO,
        highlightbackground=d.BORDE,
        highlightcolor=d.VERDE_CLARO,
        highlightthickness=1,
    )

    entrada = ui_tema.entrada(
        marco,
        textvariable=variable,
        font=fuente,
        width=ancho,
    )
    entrada.pack(side="left", fill="x", expand=True, padx=(8, 0), ipady=4)

    boton_calendario = ui_tema.boton(
        marco,
        "▦",
        lambda: CalendarioFecha(d, marco, variable, permitir_vacio),
        fuente=ui_tema.fuente_texto(10, "bold"),
    )
    boton_calendario.pack(side="right", fill="y", padx=2, pady=2)

    marco.entrada = entrada
    marco.boton_calendario = boton_calendario
    return marco


# ----------------------------------------------------------------------
# Logo del negocio
# ----------------------------------------------------------------------
NOMBRES_LOGO = ("logo.png", "logo.jpg", "logo.jpeg", "logo.gif", "logo.webp")


def buscar_logo():
    """Busca un logo junto a main.py o en assets/, img/ e imagenes/."""
    raiz = pathlib.Path(__file__).resolve().parent
    for carpeta in (raiz, raiz / "assets", raiz / "img", raiz / "imagenes"):
        for nombre in NOMBRES_LOGO:
            ruta = carpeta / nombre
            if ruta.exists():
                return ruta
    return None


_CACHE_LOGOS = {}


def crear_logo(padre, bg, alto=44, texto="YOGUFRUT", fg=None):
    """Muestra el logo del negocio o el nombre como respaldo."""
    fg = fg or ui_tema.VERDE_OSCURO
    ruta = buscar_logo()
    if ruta:
        try:
            from PIL import Image, ImageTk

            clave = (str(ruta), alto)
            foto = _CACHE_LOGOS.get(clave)
            if foto is None:
                imagen = Image.open(ruta).convert("RGBA")
                ancho = max(1, round(imagen.width * alto / imagen.height))
                remuestreo = getattr(Image, "Resampling", Image).LANCZOS
                foto = ImageTk.PhotoImage(imagen.resize((ancho, alto), remuestreo))
                _CACHE_LOGOS[clave] = foto

            etiqueta = tk.Label(padre, image=foto, bg=bg, bd=0)
            etiqueta.image = foto
            return etiqueta
        except Exception:
            pass

    return tk.Label(
        padre,
        text=texto,
        font=ui_tema.fuente_titulo(15),
        bg=bg,
        fg=fg,
    )
