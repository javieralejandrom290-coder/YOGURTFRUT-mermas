import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from base_datos import obtener_conexion
from ui_comunes import crear_boton, crear_tabla
from vista_mermas import RegistrarMermaView

MOTIVOS = RegistrarMermaView.MOTIVOS


def parsear_fecha(texto):
    """Convierte 'AAAA-MM-DD' en texto normalizado. Vacío = sin filtro."""
    texto = texto.strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ValueError(
            f"'{texto}' no es una fecha válida. Usa el formato AAAA-MM-DD."
        )


def consultar_historial(desde=None, hasta=None, motivo=None, producto=""):
    """Mermas filtradas por rango de fechas, motivo y nombre de producto."""
    condiciones = ["p.nombre LIKE ?"]
    parametros = [f"%{producto.strip()}%"]

    if desde:
        condiciones.append("date(m.fecha) >= date(?)")
        parametros.append(desde)
    if hasta:
        condiciones.append("date(m.fecha) <= date(?)")
        parametros.append(hasta)
    if motivo and motivo != "Todos":
        condiciones.append("m.motivo = ?")
        parametros.append(motivo)

    with obtener_conexion() as conexion:
        return conexion.execute(
            f"""
            SELECT m.id, m.fecha, p.nombre AS producto, p.unidad, m.cantidad,
                   m.motivo, m.costo_total, m.observaciones,
                   COALESCE(u.nombre, 'Usuario eliminado') AS usuario
            FROM mermas m
            JOIN productos p ON p.id = m.producto_id
            LEFT JOIN usuarios u ON u.id = m.usuario_id
            WHERE {' AND '.join(condiciones)}
            ORDER BY m.fecha DESC, m.id DESC
            """,
            parametros
        ).fetchall()


class ModuloHistorial:
    """Apartado Historial: consulta de mermas con filtros."""

    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.contenido = dashboard.contenido

        self.var_desde = tk.StringVar()
        self.var_hasta = tk.StringVar()
        self.var_motivo = tk.StringVar(value="Todos")
        self.var_producto = tk.StringVar()
        self.var_resumen = tk.StringVar()
        self.registros = {}

    def mostrar(self):
        d = self.dashboard
        d.limpiar_contenido()
        d.titulo_pagina(
            "Historial",
            "Consulta las mermas registradas anteriormente."
        )

        barra = tk.Frame(self.contenido, bg=d.FONDO)
        barra.pack(fill="x", padx=30, pady=(0, 8))
        barra2 = tk.Frame(self.contenido, bg=d.FONDO)
        barra2.pack(fill="x", padx=30, pady=(0, 6))

        def campo(texto, variable, ancho):
            tk.Label(
                barra, text=texto, font=("Segoe UI", 10),
                bg=d.FONDO, fg=d.TEXTO
            ).pack(side="left", padx=(0, 6))
            entrada = tk.Entry(
                barra, textvariable=variable, font=("Segoe UI", 10),
                relief="solid", bd=1, width=ancho
            )
            entrada.pack(side="left", padx=(0, 14), ipady=4)
            return entrada

        campo("Desde:", self.var_desde, 12)
        campo("Hasta:", self.var_hasta, 12)
        campo("Producto:", self.var_producto, 18).bind(
            "<Return>", lambda e: self.cargar()
        )

        tk.Label(
            barra2, text="Motivo:", font=("Segoe UI", 10),
            bg=d.FONDO, fg=d.TEXTO
        ).pack(side="left", padx=(0, 6))
        combo = ttk.Combobox(
            barra2, textvariable=self.var_motivo,
            values=["Todos"] + MOTIVOS, state="readonly",
            width=18, font=("Segoe UI", 10)
        )
        combo.pack(side="left", padx=(0, 14))
        combo.bind("<<ComboboxSelected>>", lambda e: self.cargar())

        crear_boton(d, barra2, "Buscar", self.cargar, principal=True).pack(side="left")
        crear_boton(d, barra2, "Limpiar", self.limpiar).pack(side="left", padx=8)

        tk.Label(
            self.contenido,
            text="Fechas en formato AAAA-MM-DD (por ejemplo 2026-10-14). "
                 "Doble clic en una fila para ver los detalles.",
            font=("Segoe UI", 9), bg=d.FONDO, fg=d.TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=30, pady=(0, 10))

        marco, self.tabla = crear_tabla(d, self.contenido, [
            ("fecha", "Fecha", 135, "w"),
            ("producto", "Producto", 170, "w"),
            ("cantidad", "Cantidad", 90, "center"),
            ("motivo", "Motivo", 150, "w"),
            ("usuario", "Registró", 130, "w"),
            ("costo", "Costo", 100, "e"),
        ])
        marco.pack(fill="both", expand=True, padx=30, pady=(0, 6))
        self.tabla.bind("<Double-1>", lambda e: self.ver_detalle())

        tk.Label(
            self.contenido, textvariable=self.var_resumen,
            font=("Segoe UI", 10, "bold"), bg=d.FONDO, fg=d.VERDE_OSCURO
        ).pack(anchor="w", padx=30, pady=(0, 20))

        self.cargar()

    def limpiar(self):
        self.var_desde.set("")
        self.var_hasta.set("")
        self.var_producto.set("")
        self.var_motivo.set("Todos")
        self.cargar()

    def cargar(self):
        try:
            desde = parsear_fecha(self.var_desde.get())
            hasta = parsear_fecha(self.var_hasta.get())
        except ValueError as error:
            messagebox.showwarning("Fecha inválida", str(error))
            return

        if desde and hasta and desde > hasta:
            messagebox.showwarning(
                "Rango inválido",
                "La fecha inicial no puede ser mayor que la final."
            )
            return

        filas = consultar_historial(
            desde, hasta, self.var_motivo.get(), self.var_producto.get()
        )

        self.tabla.delete(*self.tabla.get_children())
        self.registros = {}

        for f in filas:
            iid = self.tabla.insert("", "end", values=(
                f["fecha"][:16],
                f["producto"],
                f"{f['cantidad']:g} {f['unidad']}",
                f["motivo"],
                f["usuario"],
                f"${f['costo_total']:,.2f}",
            ))
            self.registros[iid] = f

        total = sum(f["costo_total"] for f in filas)
        self.var_resumen.set(
            f"{len(filas)} merma(s)  ·  Costo total: ${total:,.2f}"
        )

    def ver_detalle(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        f = self.registros[seleccion[0]]
        messagebox.showinfo(
            "Detalle de la merma",
            f"Fecha: {f['fecha'][:16]}\n"
            f"Producto: {f['producto']}\n"
            f"Cantidad: {f['cantidad']:g} {f['unidad']}\n"
            f"Motivo: {f['motivo']}\n"
            f"Costo: ${f['costo_total']:,.2f}\n"
            f"Registró: {f['usuario']}\n\n"
            f"Observaciones: {f['observaciones'] or 'Sin observaciones'}"
        )
