
import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib
import hmac
import secrets

from base_datos import obtener_conexion, inicializar_base_datos


class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOGURTFRUT | Iniciar sesión")
        self.root.geometry("900x560")
        self.root.resizable(False, False)
        self.root.configure(bg="#F3F6F4")

        self.verificar_administrador()
        self.crear_interfaz()

    # --------------------------------------------------
    # SEGURIDAD DE CONTRASEÑAS
    # --------------------------------------------------
    @staticmethod
    def generar_hash(contrasena, salt=None):
        if salt is None:
            salt = secrets.token_hex(16)

        resultado = hashlib.pbkdf2_hmac(
            "sha256",
            contrasena.encode("utf-8"),
            bytes.fromhex(salt),
            600_000
        )

        return f"{salt}${resultado.hex()}"

    @staticmethod
    def verificar_hash(contrasena, hash_guardado):
        try:
            salt, hash_original = hash_guardado.split("$", 1)
            hash_nuevo = LoginApp.generar_hash(contrasena, salt)
            return hmac.compare_digest(
                hash_nuevo.split("$", 1)[1],
                hash_original
            )
        except (ValueError, TypeError):
            return False

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
        ventana.geometry("430x390")
        ventana.resizable(False, False)
        ventana.configure(bg="#FFFFFF")
        ventana.transient(self.root)
        ventana.grab_set()

        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() - 430) // 2
        y = (ventana.winfo_screenheight() - 390) // 2
        ventana.geometry(f"430x390+{x}+{y}")

        tk.Label(
            ventana,
            text="¡Bienvenido a YOGURTFRUT!",
            font=("Segoe UI", 17, "bold"),
            bg="#FFFFFF",
            fg="#173B32"
        ).pack(pady=(25, 5))

        tk.Label(
            ventana,
            text="Crea la cuenta del administrador inicial.",
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#607D8B"
        ).pack(pady=(0, 20))

        campos = {}

        for etiqueta, clave, ocultar in [
            ("Nombre completo", "nombre", False),
            ("Nombre de usuario", "usuario", False),
            ("Contraseña", "contrasena", True),
            ("Confirmar contraseña", "confirmar", True)
        ]:
            tk.Label(
                ventana,
                text=etiqueta,
                font=("Segoe UI", 10, "bold"),
                bg="#FFFFFF",
                fg="#263238"
            ).pack(anchor="w", padx=45)

            entrada = tk.Entry(
                ventana,
                font=("Segoe UI", 11),
                relief="solid",
                bd=1,
                show="*" if ocultar else ""
            )
            entrada.pack(fill="x", padx=45, pady=(4, 10))
            campos[clave] = entrada

        def guardar_administrador():
            nombre = campos["nombre"].get().strip()
            usuario = campos["usuario"].get().strip()
            contrasena = campos["contrasena"].get()
            confirmar = campos["confirmar"].get()

            if not nombre or not usuario or not contrasena:
                messagebox.showwarning(
                    "Campos obligatorios",
                    "Completa todos los campos.",
                    parent=ventana
                )
                return

            if len(contrasena) < 10:
                messagebox.showwarning(
                    "Contraseña insegura",
                    "La contraseña debe tener al menos 10 caracteres.",
                    parent=ventana
                )
                return

            if contrasena != confirmar:
                messagebox.showerror(
                    "Error",
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
                    "Configuración completada",
                    "Administrador creado correctamente.",
                    parent=ventana
                )
                ventana.grab_release()
                ventana.destroy()

            except sqlite3.IntegrityError:
                messagebox.showerror(
                    "Error",
                    "Ese nombre de usuario ya existe.",
                    parent=ventana
                )

        tk.Button(
            ventana,
            text="CREAR ADMINISTRADOR",
            command=guardar_administrador,
            font=("Segoe UI", 10, "bold"),
            bg="#7CB342",
            fg="#FFFFFF",
            activebackground="#689F38",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            pady=10
        ).pack(fill="x", padx=45, pady=(5, 20))

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
        panel_izquierdo = tk.Frame(
            self.root,
            bg="#173B32",
            width=390
        )
        panel_izquierdo.pack(side="left", fill="y")
        panel_izquierdo.pack_propagate(False)

        tk.Label(
            panel_izquierdo,
            text="YOGURTFRUT",
            font=("Segoe UI", 27, "bold"),
            bg="#173B32",
            fg="#FFFFFF"
        ).pack(pady=(125, 5))

        tk.Label(
            panel_izquierdo,
            text="CONTROL DE MERMAS",
            font=("Segoe UI", 12, "bold"),
            bg="#173B32",
            fg="#B9D8A5"
        ).pack(pady=5)

        tk.Label(
            panel_izquierdo,
            text="Controla tus productos.\nReduce las pérdidas.\nMejora tus resultados.",
            font=("Segoe UI", 12),
            bg="#173B32",
            fg="#E0EBE5",
            justify="center"
        ).pack(pady=30)

        panel_derecho = tk.Frame(
            self.root,
            bg="#FFFFFF"
        )
        panel_derecho.pack(
            side="right",
            fill="both",
            expand=True
        )

        tk.Label(
            panel_derecho,
            text="Iniciar sesión",
            font=("Segoe UI", 23, "bold"),
            bg="#FFFFFF",
            fg="#263238"
        ).pack(anchor="w", padx=55, pady=(105, 8))

        tk.Label(
            panel_derecho,
            text="Ingresa tus credenciales para continuar.",
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#78909C"
        ).pack(anchor="w", padx=55, pady=(0, 30))

        tk.Label(
            panel_derecho,
            text="USUARIO",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#37474F"
        ).pack(anchor="w", padx=55)

        self.entrada_usuario = tk.Entry(
            panel_derecho,
            font=("Segoe UI", 12),
            relief="solid",
            bd=1
        )
        self.entrada_usuario.pack(
            fill="x", padx=55, pady=(7, 20), ipady=8
        )

        tk.Label(
            panel_derecho,
            text="CONTRASEÑA",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#37474F"
        ).pack(anchor="w", padx=55)

        self.entrada_contrasena = tk.Entry(
            panel_derecho,
            font=("Segoe UI", 12),
            relief="solid",
            bd=1,
            show="*"
        )
        self.entrada_contrasena.pack(
            fill="x", padx=55, pady=(7, 25), ipady=8
        )

        self.entrada_usuario.bind(
            "<Return>",
            lambda evento: self.entrada_contrasena.focus_set()
        )
        self.entrada_contrasena.bind(
            "<Return>",
            lambda evento: self.iniciar_sesion()
        )

        tk.Button(
            panel_derecho,
            text="INICIAR SESIÓN",
            command=self.iniciar_sesion,
            font=("Segoe UI", 11, "bold"),
            bg="#7CB342",
            fg="#FFFFFF",
            activebackground="#689F38",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            pady=12
        ).pack(fill="x", padx=55)

        tk.Label(
            panel_derecho,
            text="YOGURTFRUT · Sistema de gestión",
            font=("Segoe UI", 9),
            bg="#FFFFFF",
            fg="#90A4AE"
        ).pack(side="bottom", pady=20)

        self.entrada_usuario.focus_set()

    # --------------------------------------------------
    # VALIDAR CREDENCIALES
    # --------------------------------------------------
    def iniciar_sesion(self):
        usuario = self.entrada_usuario.get().strip()
        contrasena = self.entrada_contrasena.get()

        if not usuario or not contrasena:
            messagebox.showwarning(
                "Campos obligatorios",
                "Ingresa tu usuario y contraseña.",
                parent=self.root
            )
            return

        with obtener_conexion() as conexion:
            registro = conexion.execute(
                """
                SELECT id, nombre, usuario, contrasena_hash, rol
                FROM usuarios
                WHERE usuario = ? AND activo = 1
                """,
                (usuario,)
            ).fetchone()

        if registro and self.verificar_hash(
            contrasena,
            registro["contrasena_hash"]
        ):
            self.root.destroy()

            # El dashboard se desarrollará en el siguiente paso.
            self.abrir_dashboard(
                registro["id"],
                registro["nombre"],
                registro["rol"]
            )
        else:
            messagebox.showerror(
                "Acceso denegado",
                "Usuario o contraseña incorrectos.",
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

            ventana = tk.Tk()
            DashboardApp(
                ventana,
                usuario_id=usuario_id,
                nombre=nombre,
                rol=rol
            )
            ventana.mainloop()

        except ImportError as error:
            messagebox.showerror(
                "Error",
                "El inicio de sesión fue correcto, pero todavía "
                "no se puede abrir el panel principal.\n\n"
                "Revisa el archivo vista_dashboard.py.\n\n"
                f"Detalle: {error}"
            )


if __name__ == "__main__":
    root = tk.Tk()
    LoginApp(root)
    root.mainloop()
