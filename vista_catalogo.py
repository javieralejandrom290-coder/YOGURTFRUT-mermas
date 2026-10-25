import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

import ui_tema
from base_datos import obtener_conexion
from ui_comunes import Tarjeta, crear_boton, crear_tabla


class ModuloCatalogo:
    """
    Apartado genérico para catálogos sencillos (Proveedores, Empleados...):
    listado con búsqueda, alta, edición y activación/desactivación.

    Las subclases definen:
      TITULO, DESCRIPCION, TABLA, NOMBRE_SINGULAR
      CAMPOS: lista de dicts con
          clave, etiqueta, ancho, obligatorio (bool),
          opciones (lista, opcional: muestra un Combobox)
      validar(datos) -> mensaje de error o None (opcional)
    """

    TITULO = ""
    DESCRIPCION = ""
    TABLA = ""
    NOMBRE_SINGULAR = ""
    CAMPOS = []

    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.root = dashboard.root
        self.contenido = dashboard.contenido

        self.busqueda = tk.StringVar()
        self.mostrar_inactivos = tk.BooleanVar(value=False)

    def validar(self, datos):
        return None


    def mostrar(self):
        d = self.dashboard
        d.limpiar_contenido()
        d.titulo_pagina(self.TITULO, self.DESCRIPCION)

        barra = tk.Frame(self.contenido, bg=d.FONDO)
        barra.pack(fill="x", padx=32, pady=(0, 14))

        tk.Label(
            barra, text="Buscar:", font=ui_tema.fuente_texto(10),
            bg=d.FONDO, fg=d.TEXTO
        ).pack(side="left")

        entrada = ui_tema.entrada(
            barra, textvariable=self.busqueda, font=ui_tema.fuente_texto(10),
            width=28
        )
        entrada.pack(side="left", padx=(8, 12), ipady=2)
        entrada.bind("<KeyRelease>", lambda evento: self.cargar())

        tk.Checkbutton(
            barra, text="Mostrar inactivos",
            variable=self.mostrar_inactivos, command=self.cargar,
            font=ui_tema.fuente_texto(10), bg=d.FONDO, fg=d.TEXTO,
            activebackground=d.FONDO, selectcolor=d.BLANCO,
            cursor="hand2", highlightthickness=0, bd=0
        ).pack(side="left")

        crear_boton(
            d, barra, "Activar / Desactivar", self.cambiar_estado
        ).pack(side="right")
        crear_boton(
            d, barra, "Editar", self.editar
        ).pack(side="right", padx=8)
        crear_boton(
            d, barra, f"Nuevo {self.NOMBRE_SINGULAR}", self.nuevo,
            principal=True
        ).pack(side="right")

        columnas = [
            (campo["clave"], campo["etiqueta"], campo["ancho"], "w")
            for campo in self.CAMPOS
        ] + [("estado", "Estado", 90, "center")]

        self.etiqueta_resumen = tk.Label(
            self.contenido, text="", font=ui_tema.fuente_texto(9),
            bg=d.FONDO, fg=d.TEXTO_SECUNDARIO
        )
        self.etiqueta_resumen.pack(
            side="bottom", anchor="w", padx=32, pady=(0, 22)
        )

        marco, self.tabla = crear_tabla(d, self.contenido, columnas)
        marco.pack(fill="both", expand=True, padx=32, pady=(0, 12))

        self.tabla.tag_configure("inactivo", foreground=d.TEXTO_SECUNDARIO)
        self.tabla.bind("<Double-1>", lambda evento: self.editar())

        self.cargar()

    def cargar(self):
        self.tabla.delete(*self.tabla.get_children())

        claves = [campo["clave"] for campo in self.CAMPOS]
        consulta = (
            f"SELECT id, {', '.join(claves)}, activo FROM {self.TABLA} "
            f"WHERE nombre LIKE ?"
        )
        if not self.mostrar_inactivos.get():
            consulta += " AND activo = 1"
        consulta += " ORDER BY nombre"

        try:
            with obtener_conexion() as conexion:
                filas = conexion.execute(
                    consulta, (f"%{self.busqueda.get().strip()}%",)
                ).fetchall()
        except sqlite3.Error as error:
            messagebox.showerror(
                "Error de base de datos",
                f"No se pudo cargar la información.\n\n{error}",
                parent=self.root
            )
            return

        for fila in filas:
            self.tabla.insert(
                "", "end",
                iid=str(fila["id"]),
                values=[fila[clave] or "" for clave in claves]
                + ["Activo" if fila["activo"] else "Inactivo"],
                tags=() if fila["activo"] else ("inactivo",)
            )

        self.etiqueta_resumen.configure(text=f"{len(filas)} registro(s)")

    def seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning(
                "Sin selección",
                f"Selecciona un {self.NOMBRE_SINGULAR} de la tabla.",
                parent=self.root
            )
            return None
        return int(seleccion[0])


    def nuevo(self):
        self.abrir_formulario()

    def editar(self):
        registro_id = self.seleccionado()
        if registro_id is None:
            return

        with obtener_conexion() as conexion:
            registro = conexion.execute(
                f"SELECT * FROM {self.TABLA} WHERE id = ?", (registro_id,)
            ).fetchone()

        if registro:
            self.abrir_formulario(registro)

    def cambiar_estado(self):
        registro_id = self.seleccionado()
        if registro_id is None:
            return

        with obtener_conexion() as conexion:
            registro = conexion.execute(
                f"SELECT nombre, activo FROM {self.TABLA} WHERE id = ?",
                (registro_id,)
            ).fetchone()

            accion = "desactivar" if registro["activo"] else "activar"
            if not messagebox.askyesno(
                "Confirmar",
                f"¿Deseas {accion} a \"{registro['nombre']}\"?",
                parent=self.root
            ):
                return

            conexion.execute(
                f"UPDATE {self.TABLA} SET activo = ? WHERE id = ?",
                (0 if registro["activo"] else 1, registro_id)
            )

        self.cargar()

    def abrir_formulario(self, registro=None):
        d = self.dashboard
        editando = registro is not None
        titulo = (
            f"Editar {self.NOMBRE_SINGULAR}" if editando
            else f"Nuevo {self.NOMBRE_SINGULAR}"
        )

        alto = 240 + 72 * len(self.CAMPOS)

        ventana = tk.Toplevel(self.root)
        ventana.title(titulo)
        ventana.resizable(False, False)
        ventana.configure(bg=d.FONDO)
        ventana.transient(self.root)
        ventana.grab_set()

        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() - 440) // 2
        y = (ventana.winfo_screenheight() - alto) // 2
        ventana.geometry(f"440x{alto}+{x}+{y}")

        tarjeta = Tarjeta(ventana, bg=d.BLANCO, padding=24)
        tarjeta.pack(fill="both", expand=True, padx=16, pady=16)
        cuerpo = tarjeta.cuerpo

        tk.Label(
            cuerpo, text=titulo, font=ui_tema.fuente_titulo(18),
            bg=d.BLANCO, fg=d.VERDE_OSCURO
        ).pack(anchor="w")

        tk.Frame(
            cuerpo, bg=ui_tema.VERDE_MEDIO, height=3, width=46
        ).pack(anchor="w", pady=(6, 16))

        entradas = {}
        for campo in self.CAMPOS:
            texto = campo["etiqueta"]
            if not campo.get("obligatorio"):
                texto += " (opcional)"

            tk.Label(
                cuerpo, text=texto, font=ui_tema.fuente_texto(10, "bold"),
                bg=d.BLANCO, fg=d.TEXTO
            ).pack(anchor="w")

            if campo.get("opciones"):
                entrada = ttk.Combobox(
                    cuerpo, values=campo["opciones"],
                    state="readonly", font=ui_tema.fuente_texto(10),
                    style="Tema.TCombobox"
                )
            else:
                entrada = ui_tema.entrada(
                    cuerpo, font=ui_tema.fuente_texto(10)
                )
            entrada.pack(fill="x", pady=(4, 10))

            if editando and registro[campo["clave"]]:
                if isinstance(entrada, ttk.Combobox):
                    entrada.set(registro[campo["clave"]])
                else:
                    entrada.insert(0, registro[campo["clave"]])

            entradas[campo["clave"]] = entrada

        entradas[self.CAMPOS[0]["clave"]].focus_set()

        def guardar():
            datos = {
                clave: entrada.get().strip()
                for clave, entrada in entradas.items()
            }

            for campo in self.CAMPOS:
                if campo.get("obligatorio") and not datos[campo["clave"]]:
                    messagebox.showwarning(
                        "Campos obligatorios",
                        f"El campo \"{campo['etiqueta']}\" es obligatorio.",
                        parent=ventana
                    )
                    return

            error = self.validar(datos)
            if error:
                messagebox.showwarning("Dato inválido", error, parent=ventana)
                return

            claves = list(datos.keys())
            valores = [datos[clave] or None for clave in claves]

            try:
                with obtener_conexion() as conexion:
                    if editando:
                        conexion.execute(
                            f"UPDATE {self.TABLA} SET "
                            + ", ".join(f"{clave} = ?" for clave in claves)
                            + " WHERE id = ?",
                            valores + [registro["id"]]
                        )
                    else:
                        conexion.execute(
                            f"INSERT INTO {self.TABLA} ({', '.join(claves)}) "
                            f"VALUES ({', '.join('?' for _ in claves)})",
                            valores
                        )
            except sqlite3.IntegrityError:
                messagebox.showerror(
                    "Error",
                    f"Ya existe un {self.NOMBRE_SINGULAR} con ese nombre.",
                    parent=ventana
                )
                return

            ventana.grab_release()
            ventana.destroy()
            self.cargar()

        ui_tema.boton(
            cuerpo,
            "GUARDAR CAMBIOS" if editando else "GUARDAR",
            guardar, principal=True
        ).pack(fill="x", pady=(12, 0))

        ventana.bind("<Return>", lambda evento: guardar())
