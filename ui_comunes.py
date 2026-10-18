import tkinter as tk
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

    return marco, tabla


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
