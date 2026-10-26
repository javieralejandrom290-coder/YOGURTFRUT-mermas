"""Sistema visual compartido de YOGUFRUT.

Toda la paleta, las tipografías y los estilos de componentes viven aquí.
Las pantallas solo consumen estas constantes/helpers para que el diseño se
pueda ajustar desde un único lugar.
"""

import ctypes
import os
import pathlib
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


# ----------------------------------------------------------------------
# Paleta verde pastel
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Paleta oficial YOGURFRUT
# ----------------------------------------------------------------------
# Verde de marca
VERDE_MARCA = "#8BC900"
VERDE_MARCA_HOVER = "#78AE00"
VERDE_MARCA_OSCURO = "#527A00"
VERDE_MARCA_CLARO = "#B6E65C"

# Fondos y superficies
FONDO = "#F7FAF1"
FONDO_SUAVE = "#EEF5E2"
SIDEBAR = "#F0F6E6"
BLANCO = "#FFFFFF"
SUPERFICIE = "#FFFFFF"
CAMPO = "#FBFDF7"
FILA_ALTERNA = "#F4F8EB"

# Compatibilidad con todas las pantallas existentes
VERDE_OSCURO = "#35520B"
VERDE_TEXTO = "#35520B"
VERDE_MEDIO = "#A4D64D"
VERDE_CLARO = "#B6E65C"
VERDE_PRIMARIO = "#8BC900"
VERDE_HOVER = "#78AE00"
VERDE_SUAVE = "#EAF5D5"
VERDE_ACTIVO = "#DDF0B8"
SIDEBAR_ACTIVO = "#E2F1C7"

# Bordes y textos
BORDE = "#E2EBCF"
BORDE_FUERTE = "#C9D9AB"
TEXTO = "#26351A"
TEXTO_SECUNDARIO = "#71805F"
ACENTO = "#8BC900"
ACENTO_LOGO = "#8BC900"

# Estados de la aplicación
PELIGRO = "#C62828"
PELIGRO_FONDO = "#FDECEC"
PELIGRO_BORDE = "#F3CACA"

EXITO_FONDO = "#E6F5D8"
EXITO_TEXTO = "#416D12"

AVISO_FONDO = "#FFF5D9"
AVISO_BORDE = "#F0DFA9"
AVISO_TEXTO = "#856404"

# Sombras y decoración
SOMBRA = "#E7EDD9"
SOMBRA_SUAVE = "#EDF1E5"
DECORACION_1 = "#E8F3D6"
DECORACION_2 = "#DDEDBF"

# Tonos para series de gráficas
PALETA_GRAFICAS = [
    "#8BC900",
    "#527A00",
    "#B6E65C",
    "#A4D64D",
    "#78AE00",
    "#C9E99A",
    "#709E24",
    "#E0F0C4",
]

# Espaciado, radios y medidas compartidas
RADIO_TARJETA = 16
RADIO_CAMPO = 12
RADIO_BOTON = 12
ESPACIO_XS = 4
ESPACIO_S = 8
ESPACIO_M = 16
ESPACIO_L = 24
ESPACIO_XL = 32


# ----------------------------------------------------------------------
# Tipografía
# ----------------------------------------------------------------------
FUENTE_TITULOS = "Segoe UI"
FUENTE_TEXTO = "Segoe UI"
FUENTE = FUENTE_TEXTO  # compatibilidad con el código existente

_FAMILIAS_RESUELTAS = False


def _cargar_fuentes_locales():
    """Carga .ttf/.otf de assets/fuentes sin dependencias externas.

    En Windows se registran solo para este proceso. Si los archivos no
    existen, la app sigue usando Segoe UI sin ningún problema.
    """
    if os.name != "nt":
        return

    carpeta = pathlib.Path(__file__).resolve().parent / "assets" / "fuentes"
    if not carpeta.is_dir():
        return

    try:
        add_font = ctypes.windll.gdi32.AddFontResourceExW
        for archivo in carpeta.iterdir():
            if archivo.suffix.lower() in (".ttf", ".otf"):
                add_font(str(archivo), 0x10, 0)
    except Exception:
        pass


_cargar_fuentes_locales()


def _elegir_familia(familias, preferidas, inicio):
    for nombre in preferidas:
        if nombre in familias:
            return nombre

    for familia in familias:
        if familia.lower().startswith(inicio):
            return familia

    return "Segoe UI"


def resolver_fuentes(root=None):
    """Detecta Poppins/Inter y deja Segoe UI como respaldo."""
    global FUENTE_TITULOS, FUENTE_TEXTO, FUENTE, _FAMILIAS_RESUELTAS

    if _FAMILIAS_RESUELTAS:
        return

    try:
        familias = set(tkfont.families(root))
    except Exception:
        familias = set()

    FUENTE_TITULOS = _elegir_familia(
        familias,
        ("Poppins", "Poppins SemiBold", "Poppins Medium"),
        "poppins",
    )
    FUENTE_TEXTO = _elegir_familia(
        familias,
        ("Inter", "Inter Medium", "Inter SemiBold"),
        "inter",
    )
    # Si una de las dos no existe, se usa la otra antes que Segoe UI.
    if FUENTE_TITULOS == "Segoe UI" and FUENTE_TEXTO != "Segoe UI":
        FUENTE_TITULOS = FUENTE_TEXTO
    if FUENTE_TEXTO == "Segoe UI" and FUENTE_TITULOS != "Segoe UI":
        FUENTE_TEXTO = FUENTE_TITULOS

    FUENTE = FUENTE_TEXTO
    _FAMILIAS_RESUELTAS = True


def fuente_titulo(tamano, peso="bold"):
    familia = FUENTE_TITULOS
    return (familia, tamano, peso) if peso else (familia, tamano)


def fuente_texto(tamano, peso="normal"):
    familia = FUENTE_TEXTO
    return (familia, tamano, peso) if peso and peso != "normal" else (familia, tamano)


def _color_padre(padre):
    try:
        color = padre.cget("bg")
        if isinstance(color, str) and color:
            return color
    except Exception:
        pass
    return FONDO


# ----------------------------------------------------------------------
# Dibujo de esquinas redondeadas
# ----------------------------------------------------------------------
def rectangulo_redondeado(canvas, x1, y1, x2, y2, radio=RADIO_TARJETA, **opciones):
    """Dibuja un rectángulo redondeado suave sobre un Canvas."""
    radio = max(0, min(radio, (x2 - x1) / 2, (y2 - y1) / 2))
    puntos = [
        x1 + radio, y1,
        x2 - radio, y1,
        x2, y1,
        x2, y1 + radio,
        x2, y2 - radio,
        x2, y2,
        x2 - radio, y2,
        x1 + radio, y2,
        x1, y2,
        x1, y2 - radio,
        x1, y1 + radio,
        x1, y1,
    ]
    return canvas.create_polygon(puntos, smooth=True, **opciones)


class BotonPastel(tk.Canvas):
    """Botón plano con esquinas redondeadas y hover suave.

    Mantiene una API compatible con los botones anteriores: se puede usar
    con pack/grid/place, `command`, `.configure(bg=..., fg=...)`, etc.
    """

    def __init__(
        self,
        padre,
        texto,
        comando,
        principal=False,
        peligro=False,
        fuente=None,
        **extra,
    ):
        self._texto = texto
        self._comando = comando
        self._principal = principal
        self._peligro = peligro
        self._fuente = fuente or fuente_texto(10, "bold")
        self._estado = extra.pop("state", "normal")
        self._hover = False
        self._presionado = False

        self._padx = extra.pop("padx", 18)
        self._pady = extra.pop("pady", 10)
        self._radio = extra.pop("radio", RADIO_BOTON)

        # Opciones que no aplican a un Canvas o que controlamos aparte.
        for clave in (
            "activebackground", "activeforeground", "highlightbackground",
            "highlightcolor", "highlightthickness", "bd", "relief",
        ):
            extra.pop(clave, None)

        self._fuente_padre = _color_padre(padre)
        ancho, alto = self._medidas()
        ancho = extra.pop("width", ancho)
        alto = extra.pop("height", alto)

        super().__init__(
            padre,
            width=ancho,
            height=alto,
            bg=self._fuente_padre,
            highlightthickness=0,
            bd=0,
            cursor="hand2" if self._estado != "disabled" else "arrow",
            takefocus=1,
            **extra,
        )

        self._definir_colores()
        self.bind("<Configure>", lambda evento: self._redibujar())
        self.bind("<Enter>", self._al_entrar)
        self.bind("<Leave>", self._al_salir)
        self.bind("<ButtonPress-1>", self._al_presionar)
        self.bind("<ButtonRelease-1>", self._al_soltar)
        self.bind("<Return>", lambda evento: self.invoke())
        self.bind("<space>", lambda evento: self.invoke())
        self._redibujar()

    def _medidas(self):
        fuente = tkfont.Font(font=self._fuente)
        ancho = fuente.measure(self._texto) + (self._padx * 2)
        alto = fuente.metrics("linespace") + (self._pady * 2)
        return max(60, ancho), max(32, alto)

    def _definir_colores(self):
        if self._peligro:
            self._fondo = PELIGRO_FONDO
            self._fondo_hover = "#F7DEDE"
            self._color_texto = PELIGRO
            self._borde = PELIGRO_BORDE
        elif self._principal:
            self._fondo = VERDE_PRIMARIO
            self._fondo_hover = VERDE_HOVER
            self._color_texto = "#244C3C"
            self._borde = VERDE_PRIMARIO
        else:
            self._fondo = BLANCO
            self._fondo_hover = VERDE_SUAVE
            self._color_texto = VERDE_OSCURO
            self._borde = BORDE_FUERTE

    def _color_actual(self):
        if self._estado == "disabled":
            return BORDE
        if self._presionado:
            return self._fondo_hover
        if self._hover:
            return self._fondo_hover
        return self._fondo

    def _redibujar(self):
        self.delete("all")
        ancho = max(1, self.winfo_width())
        alto = max(1, self.winfo_height())

        # Sombra ligera
        if self._estado != "disabled":
            rectangulo_redondeado(
                self, 1, 3, ancho - 1, alto - 1,
                radio=self._radio, fill=SOMBRA_SUAVE, outline="",
            )

        borde = self._borde if self._estado != "disabled" else BORDE
        color_texto = (
            self._color_texto if self._estado != "disabled" else TEXTO_SECUNDARIO
        )

        rectangulo_redondeado(
            self, 1, 1, ancho - 1, alto - 3,
            radio=self._radio,
            fill=self._color_actual(),
            outline=borde,
            width=1,
        )
        self.create_text(
            ancho / 2,
            (alto - 2) / 2,
            text=self._texto,
            fill=color_texto,
            font=self._fuente,
        )

    def _al_entrar(self, _evento=None):
        if self._estado == "disabled":
            return
        self._hover = True
        self._redibujar()

    def _al_salir(self, _evento=None):
        self._hover = False
        self._presionado = False
        self._redibujar()

    def _al_presionar(self, _evento=None):
        if self._estado == "disabled":
            return
        self._presionado = True
        self.focus_set()
        self._redibujar()

    def _al_soltar(self, evento=None):
        if self._estado == "disabled":
            return
        self._presionado = False
        self._redibujar()
        if evento is not None and not (
            0 <= evento.x <= self.winfo_width()
            and 0 <= evento.y <= self.winfo_height()
        ):
            return
        self.invoke()

    def invoke(self):
        if self._estado != "disabled" and callable(self._comando):
            return self._comando()

    def configure(self, **opciones):
        if "bg" in opciones:
            self._fondo = opciones.pop("bg")
            self._fondo_hover = self._fondo
        if "fg" in opciones:
            self._color_texto = opciones.pop("fg")
        if "text" in opciones:
            self._texto = opciones.pop("text")
        if "font" in opciones:
            self._fuente = opciones.pop("font")
        if "state" in opciones:
            self._estado = opciones.pop("state")
            super().configure(
                cursor="hand2" if self._estado != "disabled" else "arrow"
            )
        if "command" in opciones:
            self._comando = opciones.pop("command")

        for clave in (
            "highlightthickness", "highlightbackground", "highlightcolor",
            "bd", "relief", "activebackground", "activeforeground",
        ):
            opciones.pop(clave, None)

        if opciones:
            super().configure(**opciones)

        self._redibujar()
        return self

    config = configure

    def cget(self, clave):
        if clave == "bg":
            return self._fondo
        if clave == "fg":
            return self._color_texto
        return super().cget(clave)


class EntradaRedondeada(tk.Frame):
    """Campo de texto con contenedor redondeado y borde de foco verde.

    Expone el Entry real en `.entrada` y delega get/insert/delete/bind/focus
    para que el código existente siga funcionando sin cambios.
    """

    def __init__(
        self,
        padre,
        textvariable=None,
        show="",
        font=None,
        width=None,
        **extra,
    ):
        self._fuente_padre = _color_padre(padre)
        super().__init__(
            padre,
            bg=self._fuente_padre,
            highlightthickness=0,
            bd=0,
        )

        self._fuente = font or fuente_texto(10)
        self._ancho_caracteres = width
        self._enfocado = False

        self._canvas = tk.Canvas(
            self,
            bg=self._fuente_padre,
            highlightthickness=0,
            bd=0,
            height=44,
            # Un ancho solicitado pequeño permite que los gestores de
            # geometría (pack/grid) estiren el campo según el espacio real.
            width=140,
        )
        self._canvas.pack(fill="both", expand=True)

        self.entrada = tk.Entry(
            self._canvas,
            textvariable=textvariable,
            show=show or "",
            font=self._fuente,
            relief="flat",
            bd=0,
            bg=CAMPO,
            fg=TEXTO,
            insertbackground=VERDE_OSCURO,
            highlightthickness=0,
        )

        self._item = self._canvas.create_window(
            14, 22, window=self.entrada, anchor="w", width=100, height=28
        )
        self._canvas.bind("<Configure>", self._acomodar)
        self._canvas.bind("<Button-1>", lambda evento: self.entrada.focus_set())
        self.entrada.bind("<FocusIn>", self._al_enfocar, add="+")
        self.entrada.bind("<FocusOut>", self._al_desenfoCar, add="+")

        if width:
            fuente = tkfont.Font(font=self._fuente)
            self._canvas.configure(width=fuente.measure("0" * int(width)) + 30)

        # Opciones de Entry que lleguen desde los formularios.
        opciones_entrada = {}
        for clave in (
            "fg", "bg", "insertbackground", "justify", "state",
            "selectbackground", "selectforeground", "validate",
            "validatecommand", "readonlybackground", "disabledbackground",
            "disabledforeground",
        ):
            if clave in extra:
                opciones_entrada[clave] = extra.pop(clave)
        if opciones_entrada:
            self.entrada.configure(**opciones_entrada)

        self._redibujar()

    def _acomodar(self, evento):
        alto = max(1, evento.height)
        self._canvas.coords(self._item, 14, alto / 2)
        self._canvas.itemconfigure(
            self._item,
            width=max(10, evento.width - 28),
            height=max(20, alto - 16),
        )
        self._redibujar()

    def _al_enfocar(self, _evento=None):
        self._enfocado = True
        self._redibujar()

    def _al_desenfoCar(self, _evento=None):
        self._enfocado = False
        self._redibujar()

    def _redibujar(self):
        self._canvas.delete("fondo")
        ancho = max(1, self._canvas.winfo_width())
        alto = max(1, self._canvas.winfo_height())
        borde = VERDE_PRIMARIO if self._enfocado else BORDE_FUERTE
        rectangulo_redondeado(
            self._canvas,
            1, 1, ancho - 1, alto - 1,
            radio=RADIO_CAMPO,
            fill=CAMPO,
            outline=borde,
            width=1,
            tags="fondo",
        )
        self._canvas.tag_lower("fondo")

    def bind(self, secuencia=None, funcion=None, add=None):
        if getattr(self, "entrada", None) is not None:
            return self.entrada.bind(secuencia, funcion, add)
        return super().bind(secuencia, funcion, add)

    def focus_set(self):
        if getattr(self, "entrada", None) is not None:
            return self.entrada.focus_set()
        return super().focus_set()

    def configure(self, **opciones):
        opciones_entrada = {}
        for clave in (
            "textvariable", "show", "state", "fg", "bg", "insertbackground",
            "justify", "selectbackground", "selectforeground", "validate",
            "validatecommand", "readonlybackground", "disabledbackground",
            "disabledforeground",
        ):
            if clave in opciones:
                opciones_entrada[clave] = opciones.pop(clave)

        if "font" in opciones:
            self._fuente = opciones.pop("font")
            opciones_entrada["font"] = self._fuente

        if "width" in opciones:
            self._ancho_caracteres = opciones.pop("width")
            if self._ancho_caracteres:
                fuente = tkfont.Font(font=self._fuente)
                self._canvas.configure(
                    width=fuente.measure("0" * int(self._ancho_caracteres)) + 30
                )

        for clave in (
            "highlightthickness", "highlightbackground", "highlightcolor",
            "bd", "relief",
        ):
            opciones.pop(clave, None)

        if opciones_entrada:
            self.entrada.configure(**opciones_entrada)

        if opciones:
            super().configure(**opciones)

        self._redibujar()
        return self

    config = configure

    def cget(self, clave):
        try:
            return self.entrada.cget(clave)
        except Exception:
            return super().cget(clave)

    def __getattr__(self, nombre):
        entrada = self.__dict__.get("entrada")
        if entrada is not None:
            return getattr(entrada, nombre)
        raise AttributeError(nombre)


# ----------------------------------------------------------------------
# Estilos ttk
# ----------------------------------------------------------------------
def aplicar_tema(root=None):
    """Aplica el tema plano y pastel a todos los widgets ttk."""
    resolver_fuentes(root)
    estilo = ttk.Style(root)
    if "clam" in estilo.theme_names():
        estilo.theme_use("clam")

    for nombre in (
        "Tema.Treeview", "Custom.Treeview", "Mermas.Treeview",
    ):
        estilo.configure(
            nombre,
            background=BLANCO,
            foreground=TEXTO,
            fieldbackground=BLANCO,
            rowheight=44,
            borderwidth=0,
            relief="flat",
            lightcolor=BLANCO,
            darkcolor=BLANCO,
            bordercolor=BLANCO,
            font=fuente_texto(10),
        )
        estilo.configure(
            f"{nombre}.Heading",
            background=VERDE_SUAVE,
            foreground=VERDE_OSCURO,
            font=fuente_titulo(9),
            borderwidth=0,
            relief="flat",
            padding=(12, 12),
        )
        estilo.map(
            nombre,
            background=[("selected", VERDE_ACTIVO)],
            foreground=[("selected", VERDE_OSCURO)],
        )
        estilo.map(
            f"{nombre}.Heading",
            background=[("active", VERDE_ACTIVO)],
        )

    for nombre in ("Tema.Vertical.TScrollbar", "Tema.Horizontal.TScrollbar"):
        estilo.configure(
            nombre,
            background=VERDE_CLARO,
            troughcolor=FONDO,
            bordercolor=FONDO,
            lightcolor=VERDE_CLARO,
            darkcolor=VERDE_CLARO,
            arrowcolor=VERDE_OSCURO,
            borderwidth=0,
            relief="flat",
            width=8,
            arrowsize=8,
        )
        estilo.map(
            nombre,
            background=[("active", VERDE_PRIMARIO), ("pressed", VERDE_HOVER)],
        )

    for nombre in ("Tema.TCombobox", "Modern.TCombobox"):
        estilo.configure(
            nombre,
            fieldbackground=CAMPO,
            background=BLANCO,
            foreground=TEXTO,
            bordercolor=BORDE_FUERTE,
            lightcolor=BORDE_FUERTE,
            darkcolor=BORDE_FUERTE,
            arrowcolor=VERDE_OSCURO,
            padding=(8, 6),
            relief="flat",
        )
        estilo.map(
            nombre,
            fieldbackground=[("readonly", CAMPO)],
            foreground=[("readonly", TEXTO)],
            bordercolor=[("focus", VERDE_PRIMARIO)],
            background=[("active", BLANCO)],
        )

    estilo.configure(
        "Tema.TCheckbutton",
        background=FONDO,
        foreground=TEXTO,
        font=fuente_texto(10),
        focuscolor=FONDO,
    )
    estilo.map(
        "Tema.TCheckbutton",
        background=[("active", FONDO)],
        indicatorcolor=[("selected", VERDE_PRIMARIO), ("!selected", BLANCO)],
    )

    estilo.configure(
        "Tema.TButton",
        font=fuente_texto(10, "bold"),
        padding=(14, 9),
        background=VERDE_PRIMARIO,
        foreground=VERDE_OSCURO,
        borderwidth=0,
    )
    estilo.map(
        "Tema.TButton",
        background=[("active", VERDE_HOVER)],
    )

    return estilo


# ----------------------------------------------------------------------
# Helpers de componentes
# ----------------------------------------------------------------------
def boton(
    padre,
    texto,
    comando,
    principal=False,
    peligro=False,
    fuente=None,
    **extra,
):
    """Botón pastel redondeado (principal), blanco (secundario) o suave (peligro)."""
    return BotonPastel(
        padre,
        texto,
        comando,
        principal=principal,
        peligro=peligro,
        fuente=fuente,
        **extra,
    )


def entrada(padre, **extra):
    """Campo de texto redondeado con fondo claro y borde de foco verde."""
    return EntradaRedondeada(padre, **extra)
