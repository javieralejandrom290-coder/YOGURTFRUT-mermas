import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, timedelta

from base_datos import obtener_conexion
from ui_comunes import crear_boton, crear_tabla, crear_tarjeta_resumen
from vista_historial import consultar_historial

PERIODOS = ["Hoy", "Últimos 7 días", "Este mes", "Todo el historial"]


def rango_periodo(periodo, hoy=None):
    """Devuelve (desde, hasta) como texto AAAA-MM-DD; None = sin límite."""
    hoy = hoy or date.today()

    if periodo == "Hoy":
        return hoy.isoformat(), hoy.isoformat()
    if periodo == "Últimos 7 días":
        return (hoy - timedelta(days=6)).isoformat(), hoy.isoformat()
    if periodo == "Este mes":
        return hoy.replace(day=1).isoformat(), hoy.isoformat()
    return None, None


def filtro_fechas(columna, desde, hasta):
    """Arma la condición WHERE de un rango de fechas sobre una columna."""
    condiciones, parametros = ["1 = 1"], []
    if desde:
        condiciones.append(f"date({columna}) >= date(?)")
        parametros.append(desde)
    if hasta:
        condiciones.append(f"date({columna}) <= date(?)")
        parametros.append(hasta)
    return " AND ".join(condiciones), parametros


def agrupar_con_porcentaje(filas, clave, costo_total):
    return [
        {
            "nombre": f[clave],
            "registros": f["registros"],
            "costo": f["costo"],
            "porcentaje": (f["costo"] / costo_total * 100) if costo_total else 0,
        }
        for f in filas
    ]


def generar_reporte(desde=None, hasta=None):
    """Totales de mermas por motivo, tipo y producto, y comparación con compras."""
    donde, parametros = filtro_fechas("m.fecha", desde, hasta)
    donde_compras, parametros_compras = filtro_fechas("fecha", desde, hasta)

    with obtener_conexion() as conexion:
        total = conexion.execute(
            f"""
            SELECT COUNT(*) AS registros, COALESCE(SUM(m.costo_total), 0) AS costo
            FROM mermas m WHERE {donde}
            """,
            parametros
        ).fetchone()

        por_motivo = conexion.execute(
            f"""
            SELECT m.motivo, COUNT(*) AS registros, SUM(m.costo_total) AS costo
            FROM mermas m WHERE {donde}
            GROUP BY m.motivo ORDER BY costo DESC
            """,
            parametros
        ).fetchall()

        por_tipo = conexion.execute(
            f"""
            SELECT COALESCE(t.nombre, 'Sin tipo') AS tipo,
                   COUNT(*) AS registros, SUM(m.costo_total) AS costo
            FROM mermas m
            LEFT JOIN tipos_merma t ON t.id = m.tipo_merma_id
            WHERE {donde}
            GROUP BY tipo ORDER BY costo DESC
            """,
            parametros
        ).fetchall()

        total_compras = conexion.execute(
            f"""
            SELECT COALESCE(SUM(total), 0) FROM compras
            WHERE {donde_compras}
            """,
            parametros_compras
        ).fetchone()[0]

        por_producto = conexion.execute(
            f"""
            SELECT p.nombre, p.unidad, COUNT(*) AS registros,
                   SUM(m.cantidad) AS cantidad, SUM(m.costo_total) AS costo
            FROM mermas m JOIN productos p ON p.id = m.producto_id
            WHERE {donde}
            GROUP BY p.id ORDER BY costo DESC LIMIT 10
            """,
            parametros
        ).fetchall()

    costo_total = total["costo"]
    return {
        "registros": total["registros"],
        "costo_total": costo_total,
        "total_compras": total_compras,
        # Indicador clave: qué parte de lo comprado se perdió como merma
        "porcentaje_merma": (
            costo_total / total_compras * 100 if total_compras else None
        ),
        "por_motivo": agrupar_con_porcentaje(por_motivo, "motivo", costo_total),
        "por_tipo": agrupar_con_porcentaje(por_tipo, "tipo", costo_total),
        "por_producto": [dict(f) for f in por_producto],
    }


def exportar_csv(ruta, filas):
    """Guarda las mermas en un CSV que Excel abre sin problemas."""
    with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow([
            "Fecha", "Producto", "Cantidad", "Unidad",
            "Tipo de merma", "Motivo", "Costo total", "Empleado",
            "Capturó", "Observaciones"
        ])
        for f in filas:
            escritor.writerow([
                f["fecha"], f["producto"], f["cantidad"], f["unidad"],
                f["tipo"], f["motivo"], f["costo_total"], f["empleado"],
                f["usuario"],
                f["observaciones"] or ""
            ])


class ModuloReportes:
    """Apartado Reportes: resumen de pérdidas por periodo."""

    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.contenido = dashboard.contenido

        self.var_periodo = tk.StringVar(value="Este mes")
        self.var_registros = tk.StringVar(value="0")
        self.var_costo = tk.StringVar(value="$0.00")
        self.var_principal = tk.StringVar(value="—")
        self.var_porcentaje = tk.StringVar(value="—")
        self.var_agrupar = tk.StringVar(value="Motivo")

    def mostrar(self):
        d = self.dashboard
        d.limpiar_contenido()
        d.titulo_pagina(
            "Reportes",
            "Analiza los costos y las pérdidas de productos."
        )

        barra = tk.Frame(self.contenido, bg=d.FONDO)
        barra.pack(fill="x", padx=30, pady=(0, 12))

        tk.Label(
            barra, text="Periodo:", font=("Segoe UI", 10),
            bg=d.FONDO, fg=d.TEXTO
        ).pack(side="left", padx=(0, 8))

        combo = ttk.Combobox(
            barra, textvariable=self.var_periodo, values=PERIODOS,
            state="readonly", width=20, font=("Segoe UI", 10)
        )
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda e: self.cargar())

        crear_boton(
            d, barra, "Exportar a CSV (Excel)", self.exportar
        ).pack(side="right")

        tarjetas = tk.Frame(self.contenido, bg=d.FONDO)
        tarjetas.pack(fill="x", padx=30, pady=(0, 14))
        for i in range(4):
            tarjetas.columnconfigure(i, weight=1, uniform="t")

        crear_tarjeta_resumen(
            d, tarjetas, "MERMAS REGISTRADAS", self.var_registros
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        crear_tarjeta_resumen(
            d, tarjetas, "COSTO TOTAL PERDIDO", self.var_costo
        ).grid(row=0, column=1, sticky="ew", padx=8)
        crear_tarjeta_resumen(
            d, tarjetas, "% MERMA VS COMPRAS", self.var_porcentaje
        ).grid(row=0, column=2, sticky="ew", padx=8)
        crear_tarjeta_resumen(
            d, tarjetas, "MOTIVO PRINCIPAL", self.var_principal
        ).grid(row=0, column=3, sticky="ew", padx=(8, 0))

        cuerpo = tk.Frame(self.contenido, bg=d.FONDO)
        cuerpo.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        cuerpo.columnconfigure(0, weight=1, uniform="c")
        cuerpo.columnconfigure(1, weight=1, uniform="c")
        cuerpo.rowconfigure(1, weight=1)

        encabezado = tk.Frame(cuerpo, bg=d.FONDO)
        encabezado.grid(row=0, column=0, sticky="w", pady=(0, 6))
        tk.Label(
            encabezado, text="Pérdidas por", font=("Segoe UI", 12, "bold"),
            bg=d.FONDO, fg=d.VERDE_OSCURO
        ).pack(side="left", padx=(0, 8))
        combo_agrupar = ttk.Combobox(
            encabezado, textvariable=self.var_agrupar,
            values=["Motivo", "Tipo de merma"], state="readonly",
            width=14, font=("Segoe UI", 10)
        )
        combo_agrupar.pack(side="left")
        combo_agrupar.bind("<<ComboboxSelected>>", lambda e: self.cargar())

        tk.Label(
            cuerpo, text="Productos con más pérdidas",
            font=("Segoe UI", 12, "bold"), bg=d.FONDO, fg=d.VERDE_OSCURO
        ).grid(row=0, column=1, sticky="w", pady=(0, 6))

        marco_m, self.tabla_motivo = crear_tabla(d, cuerpo, [
            ("motivo", "Concepto", 125, "w"),
            ("registros", "No.", 60, "center"),
            ("costo", "Costo", 85, "e"),
            ("grafica", "%", 105, "w"),
        ])
        marco_m.grid(row=1, column=0, sticky="nsew", padx=(0, 8))

        marco_p, self.tabla_producto = crear_tabla(d, cuerpo, [
            ("producto", "Producto", 140, "w"),
            ("cantidad", "Cantidad", 90, "center"),
            ("costo", "Costo", 90, "e"),
        ])
        marco_p.grid(row=1, column=1, sticky="nsew", padx=(8, 0))

        self.cargar()

    def cargar(self):
        desde, hasta = rango_periodo(self.var_periodo.get())
        reporte = generar_reporte(desde, hasta)

        self.var_registros.set(str(reporte["registros"]))
        self.var_costo.set(f"${reporte['costo_total']:,.2f}")
        self.var_principal.set(
            reporte["por_motivo"][0]["nombre"] if reporte["por_motivo"] else "—"
        )
        porcentaje = reporte["porcentaje_merma"]
        self.var_porcentaje.set(
            f"{porcentaje:.1f}%" if porcentaje is not None else "Sin compras"
        )

        grupos = (
            reporte["por_tipo"] if self.var_agrupar.get() == "Tipo de merma"
            else reporte["por_motivo"]
        )

        self.tabla_motivo.delete(*self.tabla_motivo.get_children())
        for m in grupos:
            barra = "█" * max(1, round(m["porcentaje"] / 20))
            self.tabla_motivo.insert("", "end", values=(
                m["nombre"],
                m["registros"],
                f"${m['costo']:,.2f}",
                f"{barra} {m['porcentaje']:.0f}%",
            ))

        self.tabla_producto.delete(*self.tabla_producto.get_children())
        for p in reporte["por_producto"]:
            self.tabla_producto.insert("", "end", values=(
                p["nombre"],
                f"{p['cantidad']:g} {p['unidad']}",
                f"${p['costo']:,.2f}",
            ))

    def exportar(self):
        desde, hasta = rango_periodo(self.var_periodo.get())
        filas = consultar_historial(desde, hasta)

        if not filas:
            messagebox.showinfo(
                "Sin datos", "No hay mermas en el periodo seleccionado."
            )
            return

        ruta = filedialog.asksaveasfilename(
            title="Guardar reporte",
            defaultextension=".csv",
            initialfile=f"reporte_mermas_{date.today().isoformat()}.csv",
            filetypes=[("Archivo CSV", "*.csv")]
        )
        if not ruta:
            return

        try:
            exportar_csv(ruta, filas)
        except OSError as error:
            messagebox.showerror(
                "Error", f"No se pudo guardar el archivo:\n{error}"
            )
            return

        messagebox.showinfo("Reporte exportado", f"Archivo guardado en:\n{ruta}")
