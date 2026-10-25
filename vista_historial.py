import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date

import ui_tema
from base_datos import obtener_conexion
from ui_comunes import crear_boton, crear_tabla
from vista_mermas import RegistrarMermaView

MOTIVOS = RegistrarMermaView.MOTIVOS


def parsear_fecha(texto):
    texto = texto.strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise ValueError(
            f"'{texto}' no es una fecha válida. Usa el formato AAAA-MM-DD."
        )


def consultar_tipos_merma():
    with obtener_conexion() as conexion:
        return [
            fila["nombre"]
            for fila in conexion.execute(
                "SELECT nombre FROM tipos_merma ORDER BY id"
            )
        ]


def consultar_historial(desde=None, hasta=None, motivo=None, producto="", tipo=None):
    condiciones = ["p.nombre LIKE ?"]
    parametros = [f"%{producto.strip()}%"]

    if tipo and tipo != "Todos":
        condiciones.append("t.nombre = ?")
        parametros.append(tipo)

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
                   COALESCE(u.nombre, 'Usuario eliminado') AS usuario,
                   COALESCE(t.nombre, 'Sin tipo') AS tipo,
                   COALESCE(e.nombre, 'Sin empleado') AS empleado
            FROM mermas m
            JOIN productos p ON p.id = m.producto_id
            LEFT JOIN usuarios u ON u.id = m.usuario_id
            LEFT JOIN tipos_merma t ON t.id = m.tipo_merma_id
            LEFT JOIN empleados e ON e.id = m.empleado_id
            WHERE {' AND '.join(condiciones)}
            ORDER BY m.fecha DESC, m.id DESC
            """,
            parametros
        ).fetchall()


class ModuloHistorial:

    VERDE_OSCURO = ui_tema.VERDE_OSCURO
    VERDE_MEDIO = ui_tema.VERDE_PRIMARIO
    VERDE_CLARO = ui_tema.VERDE_CLARO
    VERDE_SUAVE = ui_tema.VERDE_SUAVE
    VERDE_HOVER = ui_tema.VERDE_HOVER
    FONDO_GENERAL = ui_tema.FONDO
    BLANCO = ui_tema.BLANCO
    TEXTO_MAIN = ui_tema.TEXTO
    TEXTO_MUTED = ui_tema.TEXTO_SECUNDARIO
    GRIS_BORDE = ui_tema.BORDE
    AZUL_BTN = ui_tema.VERDE_PRIMARIO

    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.contenido = dashboard.contenido

        self.var_desde = tk.StringVar()
        self.var_hasta = tk.StringVar()
        self.var_motivo = tk.StringVar(value="Todos")
        self.var_tipo = tk.StringVar(value="Todos")
        self.var_producto = tk.StringVar()
        
        self.var_kpi_total = tk.StringVar(value="0")
        self.var_kpi_costo = tk.StringVar(value="$0.00")
        self.var_kpi_promedio = tk.StringVar(value="$0.00")
        
        self.registros = {}

    def mostrar(self):
        d = self.dashboard
        d.limpiar_contenido()
        self.contenido.config(bg=self.FONDO_GENERAL)

        header = tk.Frame(self.contenido, bg=self.VERDE_SUAVE, height=68)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_content = tk.Frame(header, bg=self.VERDE_SUAVE)
        header_content.pack(fill="both", expand=True, padx=25, pady=12)

        tk.Label(
            header_content, text="Historial de mermas",
            font=("Segoe UI", 15, "bold"),
            bg=self.VERDE_SUAVE, fg=self.VERDE_OSCURO
        ).pack(side="left")

        tk.Label(
            header_content,
            text="Consulta, filtra y exporta las pérdidas registradas",
            font=("Segoe UI", 9),
            bg=self.VERDE_SUAVE, fg=self.TEXTO_MUTED
        ).pack(side="right", padx=10)

        frame_kpis = tk.Frame(self.contenido, bg=self.FONDO_GENERAL)
        frame_kpis.pack(fill="x", padx=25, pady=(10, 10))

        self._crear_kpi(
            frame_kpis, "REGISTROS ENCONTRADOS",
            self.var_kpi_total, ui_tema.VERDE_CLARO
        )
        self._crear_kpi(
            frame_kpis, "COSTO TOTAL ACUMULADO",
            self.var_kpi_costo, ui_tema.VERDE_MEDIO
        )
        self._crear_kpi(
            frame_kpis, "PROMEDIO POR MERMA",
            self.var_kpi_promedio, "#B7DCC7"
        )

        card_filtros = tk.Frame(
            self.contenido, bg=self.BLANCO,
            highlightbackground=self.GRIS_BORDE, highlightthickness=1
        )
        card_filtros.pack(fill="x", padx=25, pady=(0, 10))

        tk.Frame(card_filtros, bg=self.VERDE_CLARO, height=3).pack(fill="x")

        header_card = tk.Frame(card_filtros, bg=self.BLANCO)
        header_card.pack(fill="x", padx=16, pady=(10, 4))
        tk.Label(
            header_card, text="Filtros y búsqueda",
            font=("Segoe UI", 11, "bold"), bg=self.BLANCO, fg=self.VERDE_OSCURO
        ).pack(anchor="w")

        body_filtros = tk.Frame(card_filtros, bg=self.BLANCO)
        body_filtros.pack(fill="x", padx=16, pady=(4, 12))

        body_filtros.columnconfigure(1, weight=1)
        body_filtros.columnconfigure(3, weight=1)

        tk.Label(body_filtros, text="Desde:", font=("Segoe UI", 8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=0, column=0, sticky="w", pady=4, padx=(0, 6))
        tk.Entry(body_filtros, textvariable=self.var_desde, font=("Segoe UI", 9), relief="flat", bd=0, bg="#F7FBF8",
                                     highlightthickness=1,
                                     highlightbackground=self.GRIS_BORDE,
                                     highlightcolor=self.VERDE_CLARO, width=14).grid(row=0, column=1, sticky="w", pady=4, padx=(0, 20))

        tk.Label(body_filtros, text="Hasta:", font=("Segoe UI", 8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=0, column=2, sticky="w", pady=4, padx=(0, 6))
        tk.Entry(body_filtros, textvariable=self.var_hasta, font=("Segoe UI", 9), relief="flat", bd=0, bg="#F7FBF8",
                                     highlightthickness=1,
                                     highlightbackground=self.GRIS_BORDE,
                                     highlightcolor=self.VERDE_CLARO, width=14).grid(row=0, column=3, sticky="w", pady=4, padx=(0, 20))

        f_fechas_rapidas = tk.Frame(body_filtros, bg=self.BLANCO)
        f_fechas_rapidas.grid(row=0, column=4, sticky="w", pady=4)
        tk.Button(f_fechas_rapidas, text="Hoy", font=("Segoe UI", 8, "bold"), bg=self.VERDE_SUAVE, fg=self.VERDE_OSCURO, activebackground=self.VERDE_SUAVE, relief="flat", cursor="hand2", command=self.filtrar_hoy).pack(side="left", padx=(0, 4), ipadx=6, ipady=2)
        tk.Button(f_fechas_rapidas, text="Este mes", font=("Segoe UI", 8, "bold"), bg=self.VERDE_SUAVE, fg=self.VERDE_OSCURO, relief="flat", cursor="hand2", command=self.filtrar_mes_actual).pack(side="left", ipadx=6, ipady=2)

        tk.Label(body_filtros, text="Producto:", font=("Segoe UI", 8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=1, column=0, sticky="w", pady=4, padx=(0, 6))
        e_prod = tk.Entry(body_filtros, textvariable=self.var_producto, font=("Segoe UI", 9), relief="flat", bd=0, bg="#F7FBF8",
                                     highlightthickness=1,
                                     highlightbackground=self.GRIS_BORDE,
                                     highlightcolor=self.VERDE_CLARO, width=22)
        e_prod.grid(row=1, column=1, sticky="w", pady=4, padx=(0, 20))
        e_prod.bind("<Return>", lambda e: self.cargar())

        tk.Label(body_filtros, text="Motivo:", font=("Segoe UI", 8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=1, column=2, sticky="w", pady=4, padx=(0, 6))
        combo_motivo = ttk.Combobox(body_filtros, textvariable=self.var_motivo, values=["Todos"] + MOTIVOS, state="readonly", width=18, font=("Segoe UI", 9),
            style="Tema.TCombobox")
        combo_motivo.grid(row=1, column=3, sticky="w", pady=4, padx=(0, 20))
        combo_motivo.bind("<<ComboboxSelected>>", lambda e: self.cargar())

        tk.Label(body_filtros, text="Tipo Merma:", font=("Segoe UI", 8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=2, column=0, sticky="w", pady=4, padx=(0, 6))
        combo_tipo = ttk.Combobox(body_filtros, textvariable=self.var_tipo, values=["Todos"] + consultar_tipos_merma(), state="readonly", width=18, font=("Segoe UI", 9),
            style="Tema.TCombobox")
        combo_tipo.grid(row=2, column=1, sticky="w", pady=4, padx=(0, 20))
        combo_tipo.bind("<<ComboboxSelected>>", lambda e: self.cargar())

        f_acciones = tk.Frame(body_filtros, bg=self.BLANCO)
        f_acciones.grid(row=2, column=2, columnspan=3, sticky="w", pady=4)

        ui_tema.boton(
            f_acciones, "Buscar", self.cargar, principal=True,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=(0, 8), ipadx=8, ipady=2)
        ui_tema.boton(
            f_acciones, "Limpiar", self.limpiar,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=(0, 8), ipadx=6, ipady=2)
        ui_tema.boton(
            f_acciones, "Exportar CSV", self.exportar_csv,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", ipadx=6, ipady=2)

        card_tabla = tk.Frame(
            self.contenido, bg=self.BLANCO,
            highlightbackground=self.GRIS_BORDE, highlightthickness=1
        )
        card_tabla.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        tk.Frame(card_tabla, bg=self.VERDE_CLARO, height=3).pack(fill="x")

        marco, self.tabla = crear_tabla(d, card_tabla, [
            ("fecha", "Fecha y Hora", 130, "w"),
            ("producto", "Producto", 170, "w"),
            ("cantidad", "Cantidad", 90, "center"),
            ("tipo", "Tipo", 110, "w"),
            ("motivo", "Motivo", 140, "w"),
            ("empleado", "Empleado", 130, "w"),
            ("costo", "Costo Total", 100, "e"),
        ])
        marco.configure(highlightthickness=0)
        marco.pack(fill="both", expand=True, padx=12, pady=8)
        self.tabla.bind("<Double-1>", lambda e: self.ver_detalle())

        self.tabla.tag_configure("par", background="#F7FCF9")
        self.tabla.tag_configure("impar", background=self.BLANCO)

        tk.Label(
            card_tabla,
            text="Doble clic sobre un registro para ver la ficha detallada.",
            font=("Segoe UI", 8, "italic"), bg=self.BLANCO, fg=self.TEXTO_MUTED
        ).pack(anchor="w", padx=16, pady=(0, 10))

        self.cargar()

    def _crear_kpi(self, padre, titulo, variable, color):
        card = tk.Frame(
            padre, bg=self.BLANCO,
            highlightbackground=self.GRIS_BORDE, highlightthickness=1
        )
        card.pack(side="left", fill="both", expand=True, padx=4)

        borde = tk.Frame(card, bg=color, width=4)
        borde.pack(side="left", fill="y")

        info = tk.Frame(card, bg=self.BLANCO)
        info.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        tk.Label(info, text=titulo, font=("Segoe UI", 8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).pack(anchor="w")
        tk.Label(info, textvariable=variable, font=("Segoe UI", 14, "bold"), bg=self.BLANCO, fg=self.TEXTO_MAIN).pack(anchor="w", pady=(3, 0))

    def filtrar_hoy(self):
        hoy = date.today().isoformat()
        self.var_desde.set(hoy)
        self.var_hasta.set(hoy)
        self.cargar()

    def filtrar_mes_actual(self):
        hoy = date.today()
        inicio_mes = hoy.replace(day=1).isoformat()
        self.var_desde.set(inicio_mes)
        self.var_hasta.set(hoy.isoformat())
        self.cargar()

    def limpiar(self):
        self.var_desde.set("")
        self.var_hasta.set("")
        self.var_producto.set("")
        self.var_motivo.set("Todos")
        self.var_tipo.set("Todos")
        self.cargar()

    def cargar(self):
        try:
            desde = parsear_fecha(self.var_desde.get())
            hasta = parsear_fecha(self.var_hasta.get())
        except ValueError as error:
            messagebox.showwarning("Fecha inválida", str(error))
            return

        if desde and hasta and desde > hasta:
            messagebox.showwarning("Rango inválido", "La fecha inicial no puede ser mayor que la final.")
            return

        filas = consultar_historial(desde, hasta, self.var_motivo.get(), self.var_producto.get(), self.var_tipo.get())

        self.tabla.delete(*self.tabla.get_children())
        self.registros = {}

        for idx, f in enumerate(filas):
            tag = "par" if idx % 2 == 0 else "impar"
            iid = self.tabla.insert("", "end", values=(
                f["fecha"][:16],
                f["producto"],
                f"{f['cantidad']:g} {f['unidad']}",
                f["tipo"],
                f["motivo"],
                f["empleado"],
                f"${f['costo_total']:,.2f}",
            ), tags=(tag,))
            self.registros[iid] = f

        total_items = len(filas)
        costo_sum = sum(f["costo_total"] for f in filas)
        promedio = (costo_sum / total_items) if total_items > 0 else 0.0

        self.var_kpi_total.set(f"{total_items:,}")
        self.var_kpi_costo.set(f"${costo_sum:,.2f}")
        self.var_kpi_promedio.set(f"${promedio:,.2f}")

    def exportar_csv(self):
        if not self.registros:
            messagebox.showwarning("Sin datos", "No hay registros disponibles para exportar.")
            return

        archivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivos CSV (Excel)", "*.csv"), ("Todos los archivos", "*.*")],
            title="Guardar Historial de Mermas"
        )
        if not archivo:
            return

        try:
            with open(archivo, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Fecha", "Producto", "Cantidad", "Unidad", "Tipo Merma", "Motivo", "Empleado Responsable", "Usuario Sistema", "Costo Total", "Observaciones"])
                for reg in self.registros.values():
                    writer.writerow([
                        reg["fecha"], reg["producto"], reg["cantidad"], reg["unidad"],
                        reg["tipo"], reg["motivo"], reg["empleado"], reg["usuario"],
                        reg["costo_total"], reg["observaciones"] or ""
                    ])
            messagebox.showinfo("Exportación Exitosa", f"El archivo fue generado correctamente:\n{archivo}")
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"No se pudo guardar el archivo:\n{e}")

    def ver_detalle(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        f = self.registros[seleccion[0]]

        top = tk.Toplevel(self.dashboard)
        top.title("Detalle de Merma - Yogufrut")
        top.geometry("480x520")
        top.config(bg=self.FONDO_GENERAL)
        top.transient(self.dashboard)
        top.grab_set()

        header = tk.Frame(top, bg=self.VERDE_SUAVE)
        header.pack(fill="x")
        tk.Label(header, text="Ficha detallada del registro", font=("Segoe UI", 12, "bold"), bg=self.VERDE_SUAVE, fg=self.VERDE_OSCURO).pack(pady=12)

        card = tk.Frame(
            top, bg=self.BLANCO,
            highlightbackground=self.GRIS_BORDE, highlightthickness=1
        )
        card.pack(fill="both", expand=True, padx=20, pady=15)

        detalles = [
            ("Fecha / Hora:", f['fecha'][:16]),
            ("Producto:", f['producto']),
            ("Cantidad Mermada:", f"{f['cantidad']:g} {f['unidad']}"),
            ("Tipo de Merma:", f['tipo']),
            ("Motivo:", f['motivo']),
            ("Costo Perdida Total:", f"${f['costo_total']:,.2f}"),
            ("Empleado Involucrado:", f['empleado']),
            ("Capturado por (Usuario):", f['usuario']),
        ]

        for etiqueta, valor in detalles:
            row = tk.Frame(card, bg=self.BLANCO)
            row.pack(fill="x", padx=15, pady=4)
            tk.Label(row, text=etiqueta, font=("Segoe UI", 9, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED, width=22, anchor="w").pack(side="left")
            tk.Label(row, text=str(valor), font=("Segoe UI", 9, "bold"), bg=self.BLANCO, fg=self.TEXTO_MAIN, anchor="w").pack(side="left", fill="x", expand=True)

        tk.Label(card, text="Observaciones / Notas:", font=("Segoe UI", 9, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).pack(anchor="w", padx=15, pady=(8, 2))
        
        lbl_obs = tk.Label(
            card, text=f['observaciones'] or 'Sin observaciones registradas.',
            font=("Segoe UI", 9, "italic"), bg="#F7FBF8", fg=self.TEXTO_MAIN,
            relief="flat", bd=0, padx=10, pady=8, justify="left", anchor="nw",
            wraplength=400, highlightthickness=1,
            highlightbackground=self.GRIS_BORDE
        )
        lbl_obs.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        ui_tema.boton(
            top, "Cerrar ficha", top.destroy, principal=True,
            font=("Segoe UI", 9, "bold")
        ).pack(pady=(0, 15), ipadx=20, ipady=3)