import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

import seguridad
import ui_tema
from base_datos import obtener_conexion
from ui_comunes import Tarjeta, crear_boton, crear_tabla


ROLES = ["Administrador", "Gerente", "Empleado"]
LARGO_MINIMO_CONTRASENA = 4


def contar_administradores_activos(conexion, excepto_id=None):
    """Cuántos administradores activos quedan sin contar a excepto_id."""
    return conexion.execute(
        """
        SELECT COUNT(*) FROM usuarios
        WHERE rol = 'Administrador' AND activo = 1 AND id != ?
        """,
        (excepto_id or 0,)
    ).fetchone()[0]


def validar_contrasena(contrasena, confirmar):
    if len(contrasena) < LARGO_MINIMO_CONTRASENA:
        return (
            f"La contraseña debe tener al menos "
            f"{LARGO_MINIMO_CONTRASENA} caracteres."
        )
    if contrasena != confirmar:
        return "Las contraseñas no coinciden."
    return None


class ModuloUsuarios:
    """Apartado Usuarios (solo administradores): cuentas para entrar al sistema."""

    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.root = dashboard.root
        self.contenido = dashboard.contenido


    def mostrar(self):
        d = self.dashboard
        d.limpiar_contenido()
        d.titulo_pagina(
            "Usuarios",
            "Administra las cuentas para entrar al sistema y su rol."
        )

        barra = tk.Frame(self.contenido, bg=d.FONDO)
        barra.pack(fill="x", padx=32, pady=(0, 14))

        crear_boton(
            d, barra, "Nuevo usuario", self.nuevo, principal=True
        ).pack(side="left")
        crear_boton(d, barra, "Editar", self.editar).pack(side="left", padx=8)
        crear_boton(
            d, barra, "Cambiar contraseña", self.cambiar_contrasena
        ).pack(side="left")
        crear_boton(
            d, barra, "Activar / Desactivar", self.cambiar_estado
        ).pack(side="left", padx=8)

        crear_boton(
            d, barra, "Mi cuenta", self.mi_cuenta, principal=True
        ).pack(side="right")

        tk.Label(
            self.contenido,
            text="Tu cuenta aparece en negritas. Los usuarios inactivos "
                 "no pueden iniciar sesión.",
            font=ui_tema.fuente_texto(9), bg=d.FONDO, fg=d.TEXTO_SECUNDARIO
        ).pack(side="bottom", anchor="w", padx=32, pady=(0, 22))

        marco, self.tabla = crear_tabla(d, self.contenido, [
            ("nombre", "Nombre", 220, "w"),
            ("usuario", "Usuario", 160, "w"),
            ("rol", "Rol", 140, "center"),
            ("estado", "Estado", 100, "center"),
            ("creado", "Creado", 150, "center"),
        ])
        marco.pack(fill="both", expand=True, padx=32, pady=(0, 12))

        self.tabla.tag_configure("inactivo", foreground=d.TEXTO_SECUNDARIO)
        self.tabla.tag_configure("yo", font=ui_tema.fuente_texto(10, "bold"))
        self.tabla.bind("<Double-1>", lambda evento: self.editar())

        self.cargar()

    def cargar(self):
        self.tabla.delete(*self.tabla.get_children())

        with obtener_conexion() as conexion:
            usuarios = conexion.execute(
                """
                SELECT id, nombre, usuario, rol, activo, fecha_creacion
                FROM usuarios
                ORDER BY activo DESC, nombre
                """
            ).fetchall()

        for u in usuarios:
            etiquetas = []
            if not u["activo"]:
                etiquetas.append("inactivo")
            if u["id"] == self.dashboard.usuario_id:
                etiquetas.append("yo")

            self.tabla.insert(
                "", "end", iid=str(u["id"]), tags=etiquetas,
                values=(
                    u["nombre"],
                    u["usuario"],
                    u["rol"],
                    "Activo" if u["activo"] else "Inactivo",
                    (u["fecha_creacion"] or "")[:16],
                )
            )

    def seleccionado(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning(
                "Sin selección", "Selecciona un usuario de la tabla.",
                parent=self.root
            )
            return None
        return int(seleccion[0])

    def obtener_usuario(self, usuario_id):
        with obtener_conexion() as conexion:
            return conexion.execute(
                "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
            ).fetchone()


    def abrir_ventana(self, titulo, campos, al_guardar, texto_boton="GUARDAR"):
        """
        Ventana de formulario. campos: lista de
        (clave, etiqueta, tipo, valor_inicial) con tipo "texto",
        "contrasena" u opciones (lista para un Combobox).
        al_guardar(datos, ventana) devuelve True si se guardó.
        """
        d = self.dashboard
        alto = 230 + 76 * len(campos)

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
        for clave, etiqueta, tipo, inicial in campos:
            tk.Label(
                cuerpo, text=etiqueta, font=ui_tema.fuente_texto(10, "bold"),
                bg=d.BLANCO, fg=d.TEXTO
            ).pack(anchor="w")

            if isinstance(tipo, list):
                entrada = ttk.Combobox(
                    cuerpo, values=tipo, state="readonly",
                    font=ui_tema.fuente_texto(10), style="Tema.TCombobox"
                )
                entrada.set(inicial or tipo[-1])
            else:
                entrada = ui_tema.entrada(
                    cuerpo, font=ui_tema.fuente_texto(10),
                    show="*" if tipo == "contrasena" else ""
                )
                if inicial:
                    entrada.insert(0, inicial)
            entrada.pack(fill="x", pady=(4, 10))
            entradas[clave] = entrada

        entradas[campos[0][0]].focus_set()

        def guardar():
            datos = {}
            for clave, _, tipo, _ in campos:
                valor = entradas[clave].get()
                # Las contraseñas no se recortan: los espacios cuentan
                datos[clave] = valor if tipo == "contrasena" else valor.strip()

            if al_guardar(datos, ventana):
                ventana.grab_release()
                ventana.destroy()
                self.cargar()

        ui_tema.boton(
            cuerpo, texto_boton, guardar, principal=True
        ).pack(fill="x", pady=(14, 0))

        ventana.bind("<Return>", lambda evento: guardar())
        return ventana

    def aviso(self, ventana, titulo, texto):
        messagebox.showwarning(titulo, texto, parent=ventana)
        return False


    def nuevo(self):
        def guardar(datos, ventana):
            if not datos["nombre"] or not datos["usuario"]:
                return self.aviso(
                    ventana, "Campos obligatorios",
                    "El nombre y el usuario son obligatorios."
                )

            error = validar_contrasena(datos["contrasena"], datos["confirmar"])
            if error:
                return self.aviso(ventana, "Contraseña inválida", error)

            try:
                with obtener_conexion() as conexion:
                    conexion.execute(
                        """
                        INSERT INTO usuarios
                            (nombre, usuario, contrasena_hash, rol)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            datos["nombre"],
                            datos["usuario"],
                            seguridad.generar_hash(datos["contrasena"]),
                            datos["rol"],
                        )
                    )
            except sqlite3.IntegrityError:
                return self.aviso(
                    ventana, "Usuario repetido", "Ese nombre de usuario ya existe."
                )
            return True

        self.abrir_ventana("Nuevo usuario", [
            ("nombre", "Nombre completo", "texto", ""),
            ("usuario", "Usuario", "texto", ""),
            ("rol", "Rol", ROLES, "Empleado"),
            ("contrasena", "Contraseña", "contrasena", ""),
            ("confirmar", "Confirmar contraseña", "contrasena", ""),
        ], guardar)

    def editar(self):
        usuario_id = self.seleccionado()
        if usuario_id is None:
            return
        actual = self.obtener_usuario(usuario_id)

        def guardar(datos, ventana):
            if not datos["nombre"] or not datos["usuario"]:
                return self.aviso(
                    ventana, "Campos obligatorios",
                    "El nombre y el usuario son obligatorios."
                )

            try:
                with obtener_conexion() as conexion:
                    deja_de_ser_admin = (
                        actual["rol"] == "Administrador"
                        and datos["rol"] != "Administrador"
                        and actual["activo"]
                    )
                    if deja_de_ser_admin and contar_administradores_activos(
                        conexion, excepto_id=usuario_id
                    ) == 0:
                        return self.aviso(
                            ventana, "No permitido",
                            "Debe quedar al menos un administrador activo."
                        )

                    conexion.execute(
                        """
                        UPDATE usuarios SET nombre = ?, usuario = ?, rol = ?
                        WHERE id = ?
                        """,
                        (datos["nombre"], datos["usuario"], datos["rol"],
                         usuario_id)
                    )
            except sqlite3.IntegrityError:
                return self.aviso(
                    ventana, "Usuario repetido", "Ese nombre de usuario ya existe."
                )

            if usuario_id == self.dashboard.usuario_id:
                self.aviso_sesion_actual()
            return True

        self.abrir_ventana("Editar usuario", [
            ("nombre", "Nombre completo", "texto", actual["nombre"]),
            ("usuario", "Usuario", "texto", actual["usuario"]),
            ("rol", "Rol", ROLES, actual["rol"]),
        ], guardar, "GUARDAR CAMBIOS")

    def cambiar_contrasena(self):
        usuario_id = self.seleccionado()
        if usuario_id is None:
            return
        actual = self.obtener_usuario(usuario_id)

        def guardar(datos, ventana):
            error = validar_contrasena(datos["contrasena"], datos["confirmar"])
            if error:
                return self.aviso(ventana, "Contraseña inválida", error)

            with obtener_conexion() as conexion:
                conexion.execute(
                    "UPDATE usuarios SET contrasena_hash = ? WHERE id = ?",
                    (seguridad.generar_hash(datos["contrasena"]), usuario_id)
                )

            messagebox.showinfo(
                "Contraseña actualizada",
                f"Se cambió la contraseña de {actual['usuario']}.",
                parent=self.root
            )
            return True

        self.abrir_ventana(f"Contraseña de {actual['usuario']}", [
            ("contrasena", "Nueva contraseña", "contrasena", ""),
            ("confirmar", "Confirmar contraseña", "contrasena", ""),
        ], guardar)

    def cambiar_estado(self):
        usuario_id = self.seleccionado()
        if usuario_id is None:
            return

        if usuario_id == self.dashboard.usuario_id:
            messagebox.showwarning(
                "No permitido", "No puedes desactivar tu propia cuenta.",
                parent=self.root
            )
            return

        actual = self.obtener_usuario(usuario_id)

        with obtener_conexion() as conexion:
            if (
                actual["activo"] and actual["rol"] == "Administrador"
                and contar_administradores_activos(
                    conexion, excepto_id=usuario_id
                ) == 0
            ):
                messagebox.showwarning(
                    "No permitido",
                    "Debe quedar al menos un administrador activo.",
                    parent=self.root
                )
                return

            accion = "desactivar" if actual["activo"] else "activar"
            if not messagebox.askyesno(
                "Confirmar",
                f"¿Deseas {accion} al usuario \"{actual['usuario']}\"?",
                parent=self.root
            ):
                return

            conexion.execute(
                "UPDATE usuarios SET activo = ? WHERE id = ?",
                (0 if actual["activo"] else 1, usuario_id)
            )

        self.cargar()

    def mi_cuenta(self):
        actual = self.obtener_usuario(self.dashboard.usuario_id)

        def guardar(datos, ventana):
            if not seguridad.verificar_hash(
                datos["actual"], actual["contrasena_hash"]
            ):
                return self.aviso(
                    ventana, "Contraseña incorrecta",
                    "La contraseña actual no es correcta."
                )

            if not datos["usuario"]:
                return self.aviso(
                    ventana, "Campo obligatorio", "El usuario es obligatorio."
                )

            nuevo_hash = actual["contrasena_hash"]
            if datos["nueva"] or datos["confirmar"]:
                error = validar_contrasena(datos["nueva"], datos["confirmar"])
                if error:
                    return self.aviso(ventana, "Contraseña inválida", error)
                nuevo_hash = seguridad.generar_hash(datos["nueva"])

            try:
                with obtener_conexion() as conexion:
                    conexion.execute(
                        """
                        UPDATE usuarios SET usuario = ?, contrasena_hash = ?
                        WHERE id = ?
                        """,
                        (datos["usuario"], nuevo_hash, actual["id"])
                    )
            except sqlite3.IntegrityError:
                return self.aviso(
                    ventana, "Usuario repetido", "Ese nombre de usuario ya existe."
                )

            messagebox.showinfo(
                "Cuenta actualizada",
                "Tus datos se guardaron. Úsalos la próxima vez que inicies "
                "sesión.",
                parent=self.root
            )
            return True

        self.abrir_ventana("Mi cuenta", [
            ("usuario", "Usuario", "texto", actual["usuario"]),
            ("actual", "Contraseña actual (obligatoria)", "contrasena", ""),
            ("nueva", "Nueva contraseña (vacío = no cambiar)", "contrasena", ""),
            ("confirmar", "Confirmar nueva contraseña", "contrasena", ""),
        ], guardar, "GUARDAR MI CUENTA")

    def aviso_sesion_actual(self):
        messagebox.showinfo(
            "Tu cuenta",
            "Cambiaste tu propia cuenta. Los cambios de nombre o rol se verán "
            "la próxima vez que inicies sesión.",
            parent=self.root
        )
