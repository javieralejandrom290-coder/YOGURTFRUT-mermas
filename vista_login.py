
import tkinter as tk
from tkinter import messagebox
import sqlite3
import os

from PIL import Image, ImageTk, ImageOps, ImageEnhance

import seguridad
import ui_tema

from base_datos import obtener_conexion, inicializar_base_datos
from ui_comunes import Tarjeta, crear_logo


class LoginApp:

    def __init__(self, root):
        self.root = root
        self.imagen_fondo_login = None

        self.root.title("YOGUFRUT | Control de Mermas")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        self.root.configure(bg=ui_tema.FONDO)

        # Centrar la ventana.
        self.root.update_idletasks()

        x = (self.root.winfo_screenwidth() - 1000) // 2
        y = (self.root.winfo_screenheight() - 700) // 2

        self.root.geometry(f"1000x700+{x}+{y}")

        ui_tema.aplicar_tema(self.root)

        self.verificar_administrador()

        if self.root.winfo_exists():
            self.crear_interfaz()

    # --------------------------------------------------
    # SEGURIDAD DE CONTRASEÑAS
    # --------------------------------------------------

    generar_hash = staticmethod(seguridad.generar_hash)
    verificar_hash = staticmethod(seguridad.verificar_hash)

    # --------------------------------------------------
    # CREAR EL PRIMER ADMINISTRADOR
    # --------------------------------------------------

    def verificar_administrador(self):
        inicializar_base_datos()

        with obtener_conexion() as conexion:
            resultado = conexion.execute(
                "SELECT COUNT(*) FROM usuarios"
            ).fetchone()

        if resultado[0] == 0:
            self.crear_primer_administrador()

    def crear_primer_administrador(self):
        ventana = tk.Toplevel(self.root)

        ventana.title("Configuración inicial")
        ventana.geometry("470x600")
        ventana.resizable(False, False)
        ventana.configure(bg=ui_tema.FONDO)
        ventana.transient(self.root)
        ventana.grab_set()

        ventana.update_idletasks()

        x = (ventana.winfo_screenwidth() - 470) // 2
        y = (ventana.winfo_screenheight() - 600) // 2

        ventana.geometry(f"470x600+{x}+{y}")

        tarjeta = Tarjeta(
            ventana,
            bg=ui_tema.BLANCO,
            padding=24
        )
        tarjeta.pack(fill="both", expand=True, padx=16, pady=16)

        cuerpo = tarjeta.cuerpo

        crear_logo(
            cuerpo,
            bg=ui_tema.BLANCO,
            alto=56
        ).pack(anchor="w", pady=(0, 10))

        tk.Label(
            cuerpo,
            text="Configuración inicial",
            font=ui_tema.fuente_titulo(20),
            bg=ui_tema.BLANCO,
            fg=ui_tema.VERDE_OSCURO
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            cuerpo,
            text="Crea la cuenta del primer administrador",
            font=ui_tema.fuente_texto(9),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO_SECUNDARIO
        ).pack(anchor="w", pady=(0, 12))

        campos = {}

        for etiqueta, clave, ocultar in [
            ("Nombre completo", "nombre", False),
            ("Nombre de usuario", "usuario", False),
            ("Contraseña", "contrasena", True),
            ("Confirmar contraseña", "confirmar", True)
        ]:
            tk.Label(
                cuerpo,
                text=etiqueta,
                font=ui_tema.fuente_texto(9, "bold"),
                bg=ui_tema.BLANCO,
                fg=ui_tema.TEXTO
            ).pack(anchor="w")

            entrada = ui_tema.entrada(
                cuerpo,
                font=ui_tema.fuente_texto(10),
                show="*" if ocultar else ""
            )
            entrada.pack(fill="x", pady=(3, 8))

            campos[clave] = entrada

        def guardar_administrador():
            nombre = campos["nombre"].get().strip()
            usuario = campos["usuario"].get().strip()
            contrasena = campos["contrasena"].get()
            confirmar = campos["confirmar"].get()

            if not nombre or not usuario or not contrasena or not confirmar:
                messagebox.showwarning(
                    "Campos obligatorios",
                    "Completa todos los campos para continuar.",
                    parent=ventana
                )
                return

            if len(contrasena) < 10:
                messagebox.showwarning(
                    "Contraseña corta",
                    "La contraseña debe tener al menos 10 caracteres.",
                    parent=ventana
                )
                return

            if contrasena != confirmar:
                messagebox.showerror(
                    "Error de coincidencia",
                    "Las contraseñas no coinciden.",
                    parent=ventana
                )
                return

            hash_seguro = self.generar_hash(contrasena)

            try:
                with obtener_conexion() as conexion:
                    conexion.execute(
                        """
                        INSERT INTO usuarios
                            (nombre, usuario, contrasena_hash, rol)
                        VALUES (?, ?, ?, 'Administrador')
                        """,
                        (nombre, usuario, hash_seguro)
                    )

                messagebox.showinfo(
                    "Administrador creado",
                    "La cuenta se creó correctamente.",
                    parent=ventana
                )

                ventana.grab_release()
                ventana.destroy()

            except sqlite3.IntegrityError:
                messagebox.showerror(
                    "Usuario duplicado",
                    "Ese nombre de usuario ya existe.",
                    parent=ventana
                )

            except sqlite3.Error as error:
                messagebox.showerror(
                    "Error de base de datos",
                    f"No se pudo crear el administrador.\n\n{error}",
                    parent=ventana
                )

        ui_tema.boton(
            cuerpo,
            "CREAR ADMINISTRADOR",
            guardar_administrador,
            principal=True
        ).pack(fill="x", pady=(12, 0))

        ventana.protocol(
            "WM_DELETE_WINDOW",
            lambda: self.cerrar_configuracion(ventana)
        )

        ventana.wait_window()

    def cerrar_configuracion(self, ventana):
        ventana.grab_release()
        ventana.destroy()

        with obtener_conexion() as conexion:
            cantidad = conexion.execute(
                "SELECT COUNT(*) FROM usuarios"
            ).fetchone()[0]

        if cantidad == 0:
            self.root.destroy()

    # --------------------------------------------------
    # INTERFAZ DEL LOGIN
    # --------------------------------------------------

    def crear_interfaz(self):
        """Construye el login con una fotografía a la izquierda."""

        ancho_izquierdo = 440

        panel_izquierdo = tk.Frame(
            self.root,
            width=ancho_izquierdo,
            bg=ui_tema.VERDE_OSCURO
        )
        panel_izquierdo.pack(side="left", fill="y")
        panel_izquierdo.pack_propagate(False)

        ruta_imagen = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "Imagenes",
            "yogurthfrut.jpeg"
        )

        lienzo = tk.Canvas(
            panel_izquierdo,
            width=ancho_izquierdo,
            height=700,
            bd=0,
            highlightthickness=0,
            bg="#2F7D32"
        )
        lienzo.pack(fill="both", expand=True)

        try:
            with Image.open(ruta_imagen) as imagen_archivo:
                imagen_original = imagen_archivo.convert("RGB")

            imagen_fondo = ImageOps.fit(
                imagen_original,
                (ancho_izquierdo, 700),
                method=Image.Resampling.LANCZOS,
                centering=(0.52, 0.5)
            )

            imagen_fondo = ImageEnhance.Brightness(
                imagen_fondo
            ).enhance(0.66)

            self.imagen_fondo_login = ImageTk.PhotoImage(
                imagen_fondo
            )

            lienzo.create_image(
                0,
                0,
                image=self.imagen_fondo_login,
                anchor="nw"
            )

        except (OSError, ValueError) as error:
            print(f"No se pudo cargar la imagen del login: {error}")
            lienzo.configure(bg="#2F7D32")

        # Textos superpuestos sobre la fotografía.

        lienzo.create_text(
            28, 42,
            text="YOGUFRUT",
            anchor="nw",
            font=("Arial", 16, "bold"),
            fill="white"
        )

        lienzo.create_text(
            30, 405,
            text="YOGUFRUT",
            anchor="w",
            font=("Arial", 34, "bold"),
            fill="white"
        )

        lienzo.create_text(
            32, 452,
            text="Sistema de Control de Mermas",
            anchor="w",
            font=("Arial", 13, "bold"),
            fill="white"
        )

        lienzo.create_text(
            32, 482,
            text="Cuida cada insumo. Reduce las pérdidas.",
            anchor="w",
            font=("Arial", 10),
            fill="#F1F8E9"
        )

        lienzo.create_text(
            22, 672,
            text="© 2026 YOGUFRUT",
            anchor="sw",
            font=("Arial", 9),
            fill="white"
        )

        # Panel derecho: formulario de acceso.

        area_derecha = tk.Frame(
            self.root,
            bg="#F5F7EF"
        )
        area_derecha.pack(side="right", fill="both", expand=True)

        card_login = Tarjeta(
            area_derecha,
            bg=ui_tema.BLANCO,
            padding=24
        )
        card_login.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            width=430,
            height=510
        )

        cuerpo = card_login.cuerpo

        tk.Label(
            cuerpo,
            text="¡Bienvenido!",
            font=ui_tema.fuente_titulo(25),
            bg=ui_tema.BLANCO,
            fg=ui_tema.VERDE_OSCURO
        ).pack(anchor="center", pady=(28, 4))

        tk.Label(
            cuerpo,
            text="Ingresa tus credenciales para continuar",
            font=ui_tema.fuente_texto(9),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO_SECUNDARIO
        ).pack(anchor="center", pady=(0, 20))

        tk.Frame(
            cuerpo,
            bg=ui_tema.BORDE,
            height=1
        ).pack(fill="x", padx=24, pady=(0, 22))

        tk.Label(
            cuerpo,
            text="Usuario",
            font=ui_tema.fuente_texto(9, "bold"),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO
        ).pack(anchor="w", padx=24, pady=(0, 5))

        self.entrada_usuario = ui_tema.entrada(
            cuerpo,
            font=ui_tema.fuente_texto(11)
        )
        self.entrada_usuario.pack(
            fill="x",
            padx=24,
            pady=(0, 18),
            ipady=4
        )

        tk.Label(
            cuerpo,
            text="Contraseña",
            font=ui_tema.fuente_texto(9, "bold"),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO
        ).pack(anchor="w", padx=24, pady=(0, 5))

        self.entrada_contrasena = ui_tema.entrada(
            cuerpo,
            font=ui_tema.fuente_texto(11),
            show="*"
        )
        self.entrada_contrasena.pack(
            fill="x",
            padx=24,
            pady=(0, 22),
            ipady=4
        )

        self.entrada_usuario.bind(
            "<Return>",
            lambda evento: self.entrada_contrasena.focus_set()
        )

        self.entrada_contrasena.bind(
            "<Return>",
            lambda evento: self.iniciar_sesion()
        )

        self.btn_ingresar = ui_tema.boton(
            cuerpo,
            "INGRESAR AL SISTEMA",
            self.iniciar_sesion,
            principal=True,
            fuente=ui_tema.fuente_texto(10, "bold"),
            height=46
        )
        self.btn_ingresar.pack(fill="x", padx=24)

        tk.Frame(
            cuerpo,
            bg=ui_tema.BORDE,
            height=1
        ).pack(fill="x", padx=24, pady=(24, 16))

        tk.Label(
            cuerpo,
            text="Sistema de control de mermas",
            font=ui_tema.fuente_texto(8),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO_SECUNDARIO
        ).pack(anchor="center")

        tk.Label(
            cuerpo,
            text="Acceso exclusivo para personal autorizado",
            font=ui_tema.fuente_texto(8),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO_SECUNDARIO
        ).pack(anchor="center", pady=(3, 0))

        self.entrada_usuario.focus_set()

    # --------------------------------------------------
    # VALIDAR CREDENCIALES
    # --------------------------------------------------

    def iniciar_sesion(self):
        usuario = self.entrada_usuario.get().strip()
        contrasena = self.entrada_contrasena.get()

        if not usuario or not contrasena:
            messagebox.showwarning(
                "Campos vacíos",
                "Ingresa tu usuario y contraseña.",
                parent=self.root
            )
            return

        try:
            with obtener_conexion() as conexion:
                registro = conexion.execute(
                    """
                    SELECT id, nombre, usuario, contrasena_hash, rol
                    FROM usuarios
                    WHERE usuario = ? AND activo = 1
                    """,
                    (usuario,)
                ).fetchone()

        except sqlite3.Error as error:
            messagebox.showerror(
                "Error de base de datos",
                f"No se pudieron consultar los usuarios.\n\n{error}",
                parent=self.root
            )
            return

        if registro and self.verificar_hash(
            contrasena,
            registro["contrasena_hash"]
        ):
            self.abrir_dashboard(
                registro["id"],
                registro["nombre"],
                registro["rol"]
            )
        else:
            messagebox.showerror(
                "Acceso denegado",
                "Usuario o contraseña incorrectos, o la cuenta está inactiva.",
                parent=self.root
            )

            self.entrada_contrasena.delete(0, tk.END)
            self.entrada_contrasena.focus_set()

    # --------------------------------------------------
    # ABRIR EL PANEL PRINCIPAL
    # --------------------------------------------------

    def abrir_dashboard(self, usuario_id, nombre, rol):
        try:
            from vista_dashboard import DashboardApp

            # Eliminar todos los widgets del login.
            for widget in self.root.winfo_children():
                widget.destroy()

            # Liberar la referencia de la fotografía.
            self.imagen_fondo_login = None

            # Ajustar la ventana del sistema principal.
            self.root.state("normal")
            self.root.geometry("1240x760")
            self.root.minsize(1040, 660)

            # Crear el dashboard en la misma ventana.
            DashboardApp(
                self.root,
                usuario_id=usuario_id,
                nombre=nombre,
                rol=rol
            )

        except Exception as error:
            import traceback
            traceback.print_exc()

            messagebox.showerror(
                "Error al abrir el sistema",
                "No se pudo abrir el panel principal.\n\n"
                f"Detalle: {error}\n\n"
                "Revisa la terminal de VS Code.",
                parent=self.root
            )


if __name__ == "__main__":
    root = tk.Tk()
    LoginApp(root)
    root.mainloop()
