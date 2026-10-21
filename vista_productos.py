
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

from base_datos import obtener_conexion, registrar_movimiento_inventario


UNIDADES = ["kg", "g", "L", "ml", "pza", "caja", "bolsa"]


class ModuloProductos:
    """Apartado de Productos: alta, edición y desactivación del catálogo."""

    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.root = dashboard.root
        self.contenido = dashboard.contenido

        self.busqueda = tk.StringVar()
        self.mostrar_inactivos = tk.BooleanVar(value=False)


    def mostrar(self):
        self.dashboard.limpiar_contenido()
        self.dashboard.titulo_pagina(
            "Productos",
            "Administra los productos y sus costos."
        )

        self.crear_barra_acciones()
        self.crear_tabla()
        self.cargar_productos()

    def crear_boton(self, contenedor, texto, comando, principal=False):
        d = self.dashboard

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

    def crear_barra_acciones(self):
        d = self.dashboard

        barra = tk.Frame(self.contenido, bg=d.FONDO)
        barra.pack(fill="x", padx=30, pady=(0, 12))

        tk.Label(
            barra,
            text="Buscar:",
            font=("Segoe UI", 10),
            bg=d.FONDO,
            fg=d.TEXTO
        ).pack(side="left")

        entrada = tk.Entry(
            barra,
            textvariable=self.busqueda,
            font=("Segoe UI", 11),
            relief="solid",
            bd=1,
            width=28
        )
        entrada.pack(side="left", padx=(8, 12), ipady=4)
        entrada.bind("<KeyRelease>", lambda evento: self.cargar_productos())

        tk.Checkbutton(
            barra,
            text="Mostrar inactivos",
            variable=self.mostrar_inactivos,
            command=self.cargar_productos,
            font=("Segoe UI", 10),
            bg=d.FONDO,
            fg=d.TEXTO,
            activebackground=d.FONDO,
            cursor="hand2"
        ).pack(side="left")

        self.crear_boton(
            barra, "Activar / Desactivar", self.cambiar_estado
        ).pack(side="right")

        self.crear_boton(
            barra, "Editar", self.editar_producto
        ).pack(side="right", padx=8)

        self.crear_boton(
            barra, "＋ Nuevo producto", self.nuevo_producto, principal=True
        ).pack(side="right")

    def crear_tabla(self):
        d = self.dashboard

        tabla_frame = tk.Frame(
            self.contenido,
            bg=d.BLANCO,
            highlightbackground=d.BORDE,
            highlightthickness=1
        )
        tabla_frame.pack(fill="both", expand=True, padx=30, pady=(0, 10))

        columnas = (
            "nombre", "categoria", "unidad", "costo",
            "existencia", "stock_minimo", "estado"
        )

        self.tabla = ttk.Treeview(
            tabla_frame,
            columns=columnas,
            show="headings",
            style="Mermas.Treeview",
            selectmode="browse"
        )

        encabezados = {
            "nombre": "Producto",
            "categoria": "Categoría",
            "unidad": "Unidad",
            "costo": "Costo unitario",
            "existencia": "Existencia",
            "stock_minimo": "Stock mínimo",
            "estado": "Estado"
        }

        anchos = {
            "nombre": 200,
            "categoria": 150,
            "unidad": 80,
            "costo": 120,
            "existencia": 100,
            "stock_minimo": 110,
            "estado": 90
        }

        for columna in columnas:
            self.tabla.heading(columna, text=encabezados[columna])
            self.tabla.column(
                columna,
                width=anchos[columna],
                anchor="w" if columna == "nombre" else "center"
            )

        self.tabla.tag_configure("stock_bajo", background="#FDECEA")
        self.tabla.tag_configure("inactivo", foreground=d.TEXTO_SECUNDARIO)

        barra = ttk.Scrollbar(
            tabla_frame,
            orient="vertical",
            command=self.tabla.yview
        )
        self.tabla.configure(yscrollcommand=barra.set)

        self.tabla.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        barra.pack(side="right", fill="y", padx=(0, 8), pady=8)

        self.tabla.bind("<Double-1>", lambda evento: self.editar_producto())

        self.etiqueta_resumen = tk.Label(
            self.contenido,
            text="",
            font=("Segoe UI", 9),
            bg=d.FONDO,
            fg=d.TEXTO_SECUNDARIO
        )
        self.etiqueta_resumen.pack(anchor="w", padx=30, pady=(0, 20))


    def cargar_productos(self):
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        consulta = """
            SELECT
                p.id,
                p.nombre,
                COALESCE(c.nombre, 'Sin categoría') AS categoria,
                p.unidad,
                p.costo_unitario,
                p.existencia,
                p.stock_minimo,
                p.activo
            FROM productos p
            LEFT JOIN categorias c ON c.id = p.categoria_id
            WHERE p.nombre LIKE ?
        """

        if not self.mostrar_inactivos.get():
            consulta += " AND p.activo = 1"

        consulta += " ORDER BY p.nombre"

        try:
            with obtener_conexion() as conexion:
                productos = conexion.execute(
                    consulta,
                    (f"%{self.busqueda.get().strip()}%",)
                ).fetchall()
        except sqlite3.Error as error:
            messagebox.showerror(
                "Error de base de datos",
                f"No se pudieron cargar los productos.\n\n{error}",
                parent=self.root
            )
            return

        stock_bajo = 0

        for producto in productos:
            etiquetas = []

            if not producto["activo"]:
                etiquetas.append("inactivo")
            elif producto["existencia"] <= producto["stock_minimo"]:
                etiquetas.append("stock_bajo")
                stock_bajo += 1

            self.tabla.insert(
                "",
                "end",
                iid=str(producto["id"]),
                values=(
                    producto["nombre"],
                    producto["categoria"],
                    producto["unidad"],
                    f"${producto['costo_unitario']:,.2f}",
                    f"{producto['existencia']:g}",
                    f"{producto['stock_minimo']:g}",
                    "Activo" if producto["activo"] else "Inactivo"
                ),
                tags=etiquetas
            )

        resumen = f"{len(productos)} producto(s)"
        if stock_bajo:
            resumen += f"  ·  {stock_bajo} con stock bajo (marcados en rojo)"
        self.etiqueta_resumen.configure(text=resumen)

    def producto_seleccionado(self):
        seleccion = self.tabla.selection()

        if not seleccion:
            messagebox.showwarning(
                "Sin selección",
                "Selecciona un producto de la tabla.",
                parent=self.root
            )
            return None

        return int(seleccion[0])

    def obtener_categorias(self):
        with obtener_conexion() as conexion:
            return [
                fila["nombre"]
                for fila in conexion.execute(
                    "SELECT nombre FROM categorias ORDER BY nombre"
                ).fetchall()
            ]


    def nuevo_producto(self):
        self.abrir_formulario()

    def editar_producto(self):
        producto_id = self.producto_seleccionado()
        if producto_id is None:
            return

        with obtener_conexion() as conexion:
            producto = conexion.execute(
                """
                SELECT p.*, c.nombre AS categoria
                FROM productos p
                LEFT JOIN categorias c ON c.id = p.categoria_id
                WHERE p.id = ?
                """,
                (producto_id,)
            ).fetchone()

        if producto:
            self.abrir_formulario(producto)

    def cambiar_estado(self):
        producto_id = self.producto_seleccionado()
        if producto_id is None:
            return

        with obtener_conexion() as conexion:
            producto = conexion.execute(
                "SELECT nombre, activo FROM productos WHERE id = ?",
                (producto_id,)
            ).fetchone()

            accion = "desactivar" if producto["activo"] else "activar"

            if not messagebox.askyesno(
                "Confirmar",
                f"¿Deseas {accion} el producto \"{producto['nombre']}\"?",
                parent=self.root
            ):
                return

            conexion.execute(
                "UPDATE productos SET activo = ? WHERE id = ?",
                (0 if producto["activo"] else 1, producto_id)
            )

        self.cargar_productos()

    def abrir_formulario(self, producto=None):
        d = self.dashboard
        editando = producto is not None

        ventana = tk.Toplevel(self.root)
        ventana.title("Editar producto" if editando else "Nuevo producto")
        ventana.resizable(False, False)
        ventana.configure(bg=d.BLANCO)
        ventana.transient(self.root)
        ventana.grab_set()

        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() - 430) // 2
        y = (ventana.winfo_screenheight() - 560) // 2
        ventana.geometry(f"430x560+{x}+{y}")

        tk.Label(
            ventana,
            text="Editar producto" if editando else "Nuevo producto",
            font=("Segoe UI", 17, "bold"),
            bg=d.BLANCO,
            fg=d.VERDE_OSCURO
        ).pack(pady=(22, 16))

        campos = {}

        def etiqueta(texto):
            tk.Label(
                ventana,
                text=texto,
                font=("Segoe UI", 10, "bold"),
                bg=d.BLANCO,
                fg=d.TEXTO
            ).pack(anchor="w", padx=45)

        etiqueta("Nombre del producto")
        campos["nombre"] = tk.Entry(
            ventana, font=("Segoe UI", 11), relief="solid", bd=1
        )
        campos["nombre"].pack(fill="x", padx=45, pady=(4, 10))

        etiqueta("Categoría (elige una o escribe una nueva)")
        campos["categoria"] = ttk.Combobox(
            ventana,
            values=self.obtener_categorias(),
            font=("Segoe UI", 11)
        )
        campos["categoria"].pack(fill="x", padx=45, pady=(4, 10))

        etiqueta("Unidad")
        campos["unidad"] = ttk.Combobox(
            ventana,
            values=UNIDADES,
            font=("Segoe UI", 11)
        )
        campos["unidad"].pack(fill="x", padx=45, pady=(4, 10))

        for texto, clave in [
            ("Costo unitario ($)", "costo_unitario"),
            ("Existencia", "existencia"),
            ("Stock mínimo", "stock_minimo")
        ]:
            etiqueta(texto)
            campos[clave] = tk.Entry(
                ventana, font=("Segoe UI", 11), relief="solid", bd=1
            )
            campos[clave].pack(fill="x", padx=45, pady=(4, 10))

        if editando:
            campos["nombre"].insert(0, producto["nombre"])
            campos["categoria"].set(producto["categoria"] or "")
            campos["unidad"].set(producto["unidad"])
            campos["costo_unitario"].insert(0, f"{producto['costo_unitario']:g}")
            campos["existencia"].insert(0, f"{producto['existencia']:g}")
            campos["stock_minimo"].insert(0, f"{producto['stock_minimo']:g}")
        else:
            campos["unidad"].set("kg")
            for clave in ("costo_unitario", "existencia", "stock_minimo"):
                campos[clave].insert(0, "0")

        campos["nombre"].focus_set()

        def guardar():
            nombre = campos["nombre"].get().strip()
            categoria = campos["categoria"].get().strip()
            unidad = campos["unidad"].get().strip()

            if not nombre or not unidad:
                messagebox.showwarning(
                    "Campos obligatorios",
                    "El nombre y la unidad son obligatorios.",
                    parent=ventana
                )
                return

            numeros = {}
            for clave, texto in [
                ("costo_unitario", "costo unitario"),
                ("existencia", "existencia"),
                ("stock_minimo", "stock mínimo")
            ]:
                try:
                    valor = float(campos[clave].get().strip() or 0)
                except ValueError:
                    valor = -1

                if valor < 0:
                    messagebox.showwarning(
                        "Dato inválido",
                        f"El {texto} debe ser un número mayor o igual a 0.",
                        parent=ventana
                    )
                    return

                numeros[clave] = valor

            try:
                with obtener_conexion() as conexion:
                    categoria_id = None

                    if categoria:
                        fila = conexion.execute(
                            "SELECT id FROM categorias WHERE nombre = ?",
                            (categoria,)
                        ).fetchone()

                        if fila:
                            categoria_id = fila["id"]
                        else:
                            categoria_id = conexion.execute(
                                "INSERT INTO categorias (nombre) VALUES (?)",
                                (categoria,)
                            ).lastrowid

                    datos = (
                        nombre,
                        categoria_id,
                        unidad,
                        numeros["costo_unitario"],
                        numeros["existencia"],
                        numeros["stock_minimo"]
                    )

                    if editando:
                        existencia_anterior = conexion.execute(
                            "SELECT existencia FROM productos WHERE id = ?",
                            (producto["id"],)
                        ).fetchone()[0]

                        conexion.execute(
                            """
                            UPDATE productos
                            SET nombre = ?, categoria_id = ?, unidad = ?,
                                costo_unitario = ?, existencia = ?,
                                stock_minimo = ?
                            WHERE id = ?
                            """,
                            datos + (producto["id"],)
                        )
                        producto_id = producto["id"]
                    else:
                        existencia_anterior = 0
                        producto_id = conexion.execute(
                            """
                            INSERT INTO productos
                                (nombre, categoria_id, unidad,
                                 costo_unitario, existencia, stock_minimo)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            datos
                        ).lastrowid

                    # Un ajuste manual de existencia también es un
                    # movimiento de inventario (entrada o salida)
                    diferencia = numeros["existencia"] - existencia_anterior
                    if diferencia:
                        registrar_movimiento_inventario(
                            conexion,
                            producto_id,
                            entrada=max(diferencia, 0),
                            salida=max(-diferencia, 0)
                        )

            except sqlite3.IntegrityError:
                messagebox.showerror(
                    "Error",
                    "Ya existe un producto con ese nombre.",
                    parent=ventana
                )
                return

            ventana.grab_release()
            ventana.destroy()
            self.cargar_productos()

        tk.Button(
            ventana,
            text="GUARDAR CAMBIOS" if editando else "GUARDAR PRODUCTO",
            command=guardar,
            font=("Segoe UI", 10, "bold"),
            bg=d.VERDE_CLARO,
            fg=d.BLANCO,
            activebackground="#689F38",
            activeforeground=d.BLANCO,
            relief="flat",
            cursor="hand2",
            pady=10
        ).pack(fill="x", padx=45, pady=(8, 20))

        ventana.bind("<Return>", lambda evento: guardar())
