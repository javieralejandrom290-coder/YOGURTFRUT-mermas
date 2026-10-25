"""Paleta de colores y estilos compartidos de YOGUFRUT.

Un solo lugar para mantener el aspecto visual pastel del sistema. Todas las
pantallas toman sus colores de aquí para que el diseño se sienta uniforme.
"""

import tkinter as tk
from tkinter import ttk


# ----------------------------------------------------------------------
# Paleta verde pastel
# ----------------------------------------------------------------------
FONDO = "#F3F9F5"
FONDO_SUAVE = "#EAF6EF"
BLANCO = "#FFFFFF"

VERDE_OSCURO = "#2E5D4B"
VERDE_TEXTO = "#355C4B"
VERDE_MEDIO = "#79B896"
VERDE_CLARO = "#9FCFB4"
VERDE_PRIMARIO = "#8CC7A6"
VERDE_HOVER = "#7AB995"
VERDE_SUAVE = "#E2F2E9"
VERDE_ACTIVO = "#D8EEE2"

BORDE = "#D9E9E0"
BORDE_FUERTE = "#C5DDD0"
TEXTO = "#2A3A33"
TEXTO_SECUNDARIO = "#6D8177"
ACENTO = "#A1C534"

PELIGRO = "#B85C5C"
PELIGRO_FONDO = "#FBECEC"
PELIGRO_BORDE = "#F0CFCF"

AVISO_FONDO = "#FDF7E7"
AVISO_BORDE = "#EFDFB4"
AVISO_TEXTO = "#8A6B2F"

FUENTE = "Segoe UI"


# ----------------------------------------------------------------------
# Estilos ttk
# ----------------------------------------------------------------------
def aplicar_tema(root=None):
    """Aplica el tema plano y pastel a todos los widgets ttk."""
    estilo = ttk.Style(root)
    if "clam" in estilo.theme_names():
        estilo.theme_use("clam")

    for nombre in ("Tema.Treeview", "Custom.Treeview", "Mermas.Treeview"):
        estilo.configure(
            nombre,
            background=BLANCO,
            foreground=TEXTO,
            fieldbackground=BLANCO,
            rowheight=40,
            borderwidth=0,
            font=(FUENTE, 10),
        )
        estilo.configure(
            f"{nombre}.Heading",
            background=VERDE_SUAVE,
            foreground=VERDE_OSCURO,
            font=(FUENTE, 10, "bold"),
            borderwidth=0,
            relief="flat",
            padding=(10, 10),
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
            background=VERDE_SUAVE,
            troughcolor=FONDO,
            bordercolor=FONDO,
            arrowcolor=VERDE_OSCURO,
            borderwidth=0,
            relief="flat",
        )
        estilo.map(nombre, background=[("active", VERDE_CLARO)])

    estilo.configure(
        "Tema.TCombobox",
        fieldbackground="#F7FBF8",
        background=BLANCO,
        foreground=TEXTO,
        bordercolor=BORDE_FUERTE,
        lightcolor=BORDE_FUERTE,
        darkcolor=BORDE_FUERTE,
        arrowcolor=VERDE_OSCURO,
        padding=5,
        relief="flat",
    )
    estilo.map(
        "Tema.TCombobox",
        fieldbackground=[("readonly", "#F7FBF8")],
        foreground=[("readonly", TEXTO)],
        bordercolor=[("focus", VERDE_CLARO)],
    )

    estilo.configure(
        "Tema.TCheckbutton",
        background=FONDO,
        foreground=TEXTO,
        font=(FUENTE, 10),
    )
    estilo.map(
        "Tema.TCheckbutton",
        background=[("active", FONDO)],
        indicatorcolor=[("selected", VERDE_PRIMARIO), ("!selected", BLANCO)],
    )

    return estilo


# ----------------------------------------------------------------------
# Botones
# ----------------------------------------------------------------------
def boton(
    padre,
    texto,
    comando,
    principal=False,
    peligro=False,
    fuente=(FUENTE, 10, "bold"),
    **extra
):
    """Botón plano: pastel para la acción principal y blanco para el resto."""
    if peligro:
        fondo, color = PELIGRO_FONDO, PELIGRO
        activo, color_activo = PELIGRO_BORDE, PELIGRO
        borde = PELIGRO_BORDE
    elif principal:
        fondo, color = VERDE_PRIMARIO, VERDE_OSCURO
        activo, color_activo = VERDE_HOVER, VERDE_OSCURO
        borde = VERDE_PRIMARIO
    else:
        fondo, color = BLANCO, VERDE_OSCURO
        activo, color_activo = VERDE_SUAVE, VERDE_OSCURO
        borde = BORDE_FUERTE

    opciones = dict(
        text=texto,
        command=comando,
        font=fuente,
        bg=fondo,
        fg=color,
        activebackground=activo,
        activeforeground=color_activo,
        relief="flat",
        bd=0,
        highlightbackground=borde,
        highlightthickness=0 if principal or peligro else 1,
        cursor="hand2",
        padx=15,
        pady=8,
    )
    opciones.update(extra)
    return tk.Button(padre, **opciones)


def entrada(padre, **extra):
    """Entrada plana con fondo suave y borde pastel."""
    opciones = dict(
        font=(FUENTE, 10),
        relief="flat",
        bd=0,
        bg="#F7FBF8",
        fg=TEXTO,
        insertbackground=VERDE_OSCURO,
        highlightthickness=1,
        highlightbackground=BORDE_FUERTE,
        highlightcolor=VERDE_CLARO,
    )
    opciones.update(extra)
    return tk.Entry(padre, **opciones)
