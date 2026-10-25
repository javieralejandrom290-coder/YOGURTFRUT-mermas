import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date

import ui_tema
from base_datos import obtener_conexion
from ui_comunes import Tarjeta, crear_kpi, crear_tabla
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

        header = tk.Frame(self.contenido, bg=self.FONDO_GENERAL, height=92)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_content = tk.Frame(header, bg=self.FONDO_GENERAL)
        header_content.pack(fill="both", expand=True, padx=32, pady=14)

        tk.Frame(
            header_content, bg=self.VERDE_MEDIO, width=4, height=48
        ).pack(side="left", padx=(0, 14))

        textos_header = tk.Frame(header_content, bg=self.FONDO_GENERAL)
        textos_header.pack(side="left", fill="y")

        tk.Label(
            textos_header, text="Historial de mermas",
            font=ui_tema.fuente_titulo(22),
            bg=self.FONDO_GENERAL, fg=self.VERDE_OSCURO, anchor="w"
        ).pack(anchor="w", pady=(4, 0))

        tk.Label(
            textos_header,
            text="Consulta, filtra y exporta las pérdidas registradas",
            font=ui_tema.fuente_texto(9),
            bg=self.FONDO_GENERAL, fg=self.TEXTO_MUTED, anchor="w"
        ).pack(anchor="w", pady=(3, 0))

        frame_kpis = tk.Frame(self.contenido, bg=self.FONDO_GENERAL)
        frame_kpis.pack(fill="x", padx=32, pady=(14, 14))

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
            self.var_kpi_promedio, ui_tema.ACENTO
        )

        card_filtros = Tarjeta(self.contenido, bg=self.BLANCO, padding=18)
        card_filtros.pack(fill="x", padx=32, pady=(0, 14))

        fila_titulo = tk.Frame(card_filtros.cuerpo, bg=self.BLANCO)
        fila_titulo.pack(fill="x", pady=(0, 10))

        punto = tk.Canvas(
            fila_titulo, width=10, height=10, bg=self.BLANCO,
            highlightthickness=0, bd=0,
        )
        punto.create_oval(0, 0, 10, 10, fill=self.VERDE_MEDIO, outline="")
        punto.pack(side="left", padx=(0, 8))

        tk.Label(
            fila_titulo, text="Filtros y búsqueda",
            font=ui_tema.fuente_titulo(14), bg=self.BLANCO,
            fg=self.VERDE_OSCURO
        ).pack(side="left")

        body_filtros = tk.Frame(card_filtros.cuerpo, bg=self.BLANCO)
        body_filtros.pack(fill="x")

        body_filtros.columnconfigure(1, weight=1)
        body_filtros.columnconfigure(3, weight=1)

        tk.Label(body_filtros, text="Desde:", font=ui_tema.fuente_texto(8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=0, column=0, sticky="w", pady=4, padx=(0, 6))
        entrada_desde = ui_tema.entrada(
            body_filtros, textvariable=self.var_desde,
            font=ui_tema.fuente_texto(9), width=12,
        )
        entrada_desde.grid(row=0, column=1, sticky="w", pady=4, padx=(0, 20))

        tk.Label(body_filtros, text="Hasta:", font=ui_tema.fuente_texto(8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=0, column=2, sticky="w", pady=4, padx=(0, 6))
        entrada_hasta = ui_tema.entrada(
            body_filtros, textvariable=self.var_hasta,
            font=ui_tema.fuente_texto(9), width=12,
        )
        entrada_hasta.grid(row=0, column=3, sticky="w", pady=4, padx=(0, 20))

        f_fechas_rapidas = tk.Frame(body_filtros, bg=self.BLANCO)
        f_fechas_rapidas.grid(row=0, column=4, sticky="w", pady=4)
        ui_tema.boton(
            f_fechas_rapidas, "Hoy", self.filtrar_hoy,
            fuente=ui_tema.fuente_texto(8, "bold"),
        ).pack(side="left", padx=(0, 6))
        ui_tema.boton(
            f_fechas_rapidas, "Este mes", self.filtrar_mes_actual,
            fuente=ui_tema.fuente_texto(8, "bold"),
        ).pack(side="left")

        tk.Label(body_filtros, text="Producto:", font=ui_tema.fuente_texto(8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=1, column=0, sticky="w", pady=4, padx=(0, 6))
        e_prod = ui_tema.entrada(
            body_filtros, textvariable=self.var_producto,
            font=ui_tema.fuente_texto(9), width=20,
        )
        e_prod.grid(row=1, column=1, sticky="w", pady=4, padx=(0, 20))
        e_prod.bind("<Return>", lambda e: self.cargar())

        tk.Label(body_filtros, text="Motivo:", font=ui_tema.fuente_texto(8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=1, column=2, sticky="w", pady=4, padx=(0, 6))
        combo_motivo = ttk.Combobox(body_filtros, textvariable=self.var_motivo, values=["Todos"] + MOTIVOS, state="readonly", width=18, font=ui_tema.fuente_texto(9),
            style="Tema.TCombobox")
        combo_motivo.grid(row=1, column=3, sticky="w", pady=4, padx=(0, 20))
        combo_motivo.bind("<<ComboboxSelected>>", lambda e: self.cargar())

        tk.Label(body_filtros, text="Tipo Merma:", font=ui_tema.fuente_texto(8, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).grid(row=2, column=0, sticky="w", pady=4, padx=(0, 6))
        combo_tipo = ttk.Combobox(body_filtros, textvariable=self.var_tipo, values=["Todos"] + consultar_tipos_merma(), state="readonly", width=18, font=ui_tema.fuente_texto(9),
            style="Tema.TCombobox")
        combo_tipo.grid(row=2, column=1, sticky="w", pady=4, padx=(0, 20))
        combo_tipo.bind("<<ComboboxSelected>>", lambda e: self.cargar())

        f_acciones = tk.Frame(body_filtros, bg=self.BLANCO)
        f_acciones.grid(row=2, column=2, columnspan=3, sticky="w", pady=4)

        ui_tema.boton(
            f_acciones, "Buscar", self.cargar, principal=True,
            fuente=ui_tema.fuente_texto(9, "bold")
        ).pack(side="left", padx=(0, 8))
        ui_tema.boton(
            f_acciones, "Limpiar", self.limpiar,
            fuente=ui_tema.fuente_texto(9, "bold")
        ).pack(side="left", padx=(0, 8))
        ui_tema.boton(
            f_acciones, "Exportar CSV", self.exportar_csv,
            fuente=ui_tema.fuente_texto(9, "bold")
        ).pack(side="left")

        card_tabla = Tarjeta(self.contenido, bg=self.BLANCO, padding=18)
        card_tabla.pack(fill="both", expand=True, padx=32, pady=(0, 24))

        marco, self.tabla = crear_tabla(d, card_tabla.cuerpo, [
            ("fecha", "Fecha y Hora", 120, "w"),
            ("producto", "Producto", 165, "w"),
            ("cantidad", "Cantidad", 85, "center"),
            ("tipo", "Tipo", 105, "w"),
            ("motivo", "Motivo", 135, "w"),
            ("empleado", "Empleado", 120, "w"),
            ("costo", "Costo Total", 95, "e"),
        ])
        tk.Label(
            card_tabla.cuerpo,
            text="Doble clic sobre un registro para ver la ficha detallada.",
            font=ui_tema.fuente_texto(8, "italic"), bg=self.BLANCO,
            fg=self.TEXTO_MUTED
        ).pack(side="bottom", anchor="w", pady=(10, 0))

        marco.pack(fill="both", expand=True)
        self.tabla.bind("<Double-1>", lambda e: self.ver_detalle())

        self.tabla.tag_configure("par", background=ui_tema.FILA_ALTERNA)
        self.tabla.tag_configure("impar", background=self.BLANCO)

        self.cargar()

    def _crear_kpi(self, padre, titulo, variable, color):
        tarjeta = crear_kpi(
            self.dashboard, padre, titulo, variable=variable, color=color,
        )
        tarjeta.pack(side="left", fill="both", expand=True, padx=6)
        return tarjeta

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

        top = tk.Toplevel(self.dashboard.root)
        top.title("Detalle de Merma - Yogufrut")
        top.geometry("500x560")
        top.config(bg=self.FONDO_GENERAL)
        top.transient(self.dashboard.root)
        top.grab_set()

        tarjeta = Tarjeta(top, bg=self.BLANCO, padding=22)
        tarjeta.pack(fill="both", expand=True, padx=22, pady=18)
        card = tarjeta.cuerpo

        tk.Label(
            card, text="Ficha detallada del registro",
            font=ui_tema.fuente_titulo(18), bg=self.BLANCO,
            fg=self.VERDE_OSCURO
        ).pack(anchor="w")

        tk.Frame(card, bg=self.VERDE_MEDIO, height=3, width=46).pack(
            anchor="w", pady=(6, 14)
        )

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
            row.pack(fill="x", pady=4)
            tk.Label(row, text=etiqueta, font=ui_tema.fuente_texto(9, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED, width=20, anchor="w").pack(side="left")
            tk.Label(row, text=str(valor), font=ui_tema.fuente_texto(9, "bold"), bg=self.BLANCO, fg=self.TEXTO_MAIN, anchor="w").pack(side="left", fill="x", expand=True)

        tk.Label(card, text="Observaciones / Notas:", font=ui_tema.fuente_texto(9, "bold"), bg=self.BLANCO, fg=self.TEXTO_MUTED).pack(anchor="w", pady=(12, 4))

        lbl_obs = tk.Label(
            card, text=f['observaciones'] or 'Sin observaciones registradas.',
            font=ui_tema.fuente_texto(9, "italic"), bg=ui_tema.CAMPO, fg=self.TEXTO_MAIN,
            padx=12, pady=10, justify="left", anchor="nw",
            wraplength=410
        )
        lbl_obs.pack(fill="both", expand=True)

        ui_tema.boton(
            top, "Cerrar ficha", top.destroy, principal=True,
            fuente=ui_tema.fuente_texto(9, "bold")
        ).pack(pady=(0, 18))