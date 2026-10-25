import tkinter as tk
from tkinter import messagebox
import sqlite3

import seguridad
import ui_tema
from base_datos import obtener_conexion, inicializar_base_datos
from ui_comunes import crear_logo


class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOGUFRUT | Control de Mermas")
        self.root.geometry("1000x640")
        self.root.resizable(False, False)
        self.root.configure(bg=ui_tema.FONDO)

        # Centrar la ventana en la pantalla
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 1000) // 2
        y = (self.root.winfo_screenheight() - 640) // 2
        self.root.geometry(f"1000x640+{x}+{y}")

        ui_tema.aplicar_tema(self.root)

        self.verificar_administrador()
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
        ventana.geometry("470x520")
        ventana.resizable(False, False)
        ventana.configure(bg=ui_tema.BLANCO)
        ventana.transient(self.root)
        ventana.grab_set()

        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() - 470) // 2
        y = (ventana.winfo_screenheight() - 520) // 2
        ventana.geometry(f"470x520+{x}+{y}")

        crear_logo(ventana, bg=ui_tema.BLANCO, alto=58).pack(
            pady=(22, 8)
        )

        tk.Label(
            ventana,
            text="Configuración inicial",
            font=("Segoe UI", 18, "bold"),
            bg=ui_tema.BLANCO,
            fg=ui_tema.VERDE_OSCURO
        ).pack(pady=(0, 4))

        tk.Label(
            ventana,
            text="Crea la cuenta del primer administrador",
            font=("Segoe UI", 9),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO_SECUNDARIO
        ).pack(pady=(0, 16))

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
                font=("Segoe UI", 9, "bold"),
                bg=ui_tema.BLANCO,
                fg=ui_tema.TEXTO
            ).pack(anchor="w", padx=45)

            entrada = ui_tema.entrada(
                ventana,
                font=("Segoe UI", 10),
                show="*" if ocultar else "",
            )
            entrada.pack(fill="x", padx=45, pady=(3, 8), ipady=5)
            campos[clave] = entrada

        def guardar_administrador():
            nombre = campos["nombre"].get().strip()
            usuario = campos["usuario"].get().strip()
            contrasena = campos["contrasena"].get()
            confirmar = campos["confirmar"].get()

            if not nombre or not usuario or not contrasena:
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

        ui_tema.boton(
            ventana, "CREAR ADMINISTRADOR", guardar_administrador
        ).pack(fill="x", padx=45, pady=(10, 20))

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
        # Panel de marca (izquierda)
        panel_izquierdo = tk.Frame(
            self.root, width=430, bg=ui_tema.FONDO_SUAVE
        )
        panel_izquierdo.pack(side="left", fill="y")
        panel_izquierdo.pack_propagate(False)

        # Detalles decorativos suaves
        fondo = tk.Canvas(
            panel_izquierdo,
            bg=ui_tema.FONDO_SUAVE,
            highlightthickness=0,
        )
        fondo.place(x=0, y=0, relwidth=1, relheight=1)
        fondo.create_oval(
            -120, -140, 230, 210,
            fill="#E1F2E8", outline=""
        )
        fondo.create_oval(
            260, 430, 540, 710,
            fill="#DFF1E7", outline=""
        )

        marca = tk.Frame(
            panel_izquierdo,
            bg=ui_tema.BLANCO,
            highlightbackground=ui_tema.BORDE,
            highlightthickness=1,
        )
        marca.place(relx=0.5, y=58, anchor="n", width=270, height=210)
        marca.pack_propagate(False)

        crear_logo(marca, bg=ui_tema.BLANCO, alto=118).pack(
            expand=True, pady=(16, 0)
        )
        tk.Label(
            marca,
            text="CONTROL DE MERMAS",
            font=("Segoe UI", 8, "bold"),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO_SECUNDARIO,
        ).pack(pady=(0, 16))

        tk.Label(
            panel_izquierdo,
            text="Un control simple para\ncuidar cada insumo.",
            font=("Segoe UI", 20, "bold"),
            bg=ui_tema.FONDO_SUAVE,
            fg=ui_tema.VERDE_OSCURO,
            justify="center",
        ).place(relx=0.5, y=320, anchor="n")

        tarjeta = tk.Frame(
            panel_izquierdo,
            bg=ui_tema.BLANCO,
            highlightbackground=ui_tema.BORDE,
            highlightthickness=1,
        )
        tarjeta.place(relx=0.5, y=418, anchor="n", width=330, height=160)

        for numero, titulo, detalle in [
            ("01", "Inventario en tiempo real", "Existencias siempre al día"),
            ("02", "Menos pérdidas", "Detecta mermas a tiempo"),
            ("03", "Decisiones claras", "Reportes fáciles de leer"),
        ]:
            self._caracteristica(tarjeta, numero, titulo, detalle)

        tk.Label(
            panel_izquierdo,
            text="YOGUFRUT © 2026",
            font=("Segoe UI", 8),
            bg=ui_tema.FONDO_SUAVE,
            fg=ui_tema.TEXTO_SECUNDARIO,
        ).place(relx=0.5, rely=0.97, anchor="s")

        # Panel del formulario (derecha)
        area_derecha = tk.Frame(self.root, bg=ui_tema.FONDO)
        area_derecha.pack(side="right", fill="both", expand=True)

        card_width, card_height = 430, 500
        card_login = tk.Frame(
            area_derecha,
            width=card_width,
            height=card_height,
            bg=ui_tema.BLANCO,
            highlightbackground=ui_tema.BORDE,
            highlightthickness=1,
            bd=0,
        )
        card_login.place(relx=0.5, rely=0.5, anchor="center")
        card_login.pack_propagate(False)

        tk.Label(
            card_login,
            text="Iniciar sesión",
            font=("Segoe UI", 22, "bold"),
            bg=ui_tema.BLANCO,
            fg=ui_tema.VERDE_OSCURO,
        ).place(x=44, y=40)

        tk.Label(
            card_login,
            text="Ingresa tus credenciales para continuar.",
            font=("Segoe UI", 9),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO_SECUNDARIO,
        ).place(x=44, y=78)

        tk.Frame(card_login, bg=ui_tema.BORDE, height=1).place(
            x=44, y=112, width=342
        )

        tk.Label(
            card_login,
            text="Usuario",
            font=("Segoe UI", 9, "bold"),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO,
        ).place(x=44, y=138)

        canvas_usr = tk.Canvas(
            card_login, bg=ui_tema.BLANCO,
            highlightthickness=0, height=44
        )
        canvas_usr.place(x=44, y=162, width=342, height=44)
        self._crear_rounded_rect(
            canvas_usr, 0, 0, 342, 44, radius=14,
            fill="#F7FBF8", outline=ui_tema.BORDE_FUERTE
        )

        self.entrada_usuario = tk.Entry(
            canvas_usr,
            font=("Segoe UI", 11),
            relief="flat",
            bd=0,
            bg="#F7FBF8",
            fg=ui_tema.TEXTO,
            insertbackground=ui_tema.VERDE_OSCURO,
            highlightthickness=0,
        )
        canvas_usr.create_window(
            171, 22, window=self.entrada_usuario, width=310, height=28
        )

        tk.Label(
            card_login,
            text="Contraseña",
            font=("Segoe UI", 9, "bold"),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO,
        ).place(x=44, y=228)

        canvas_pwd = tk.Canvas(
            card_login, bg=ui_tema.BLANCO,
            highlightthickness=0, height=44
        )
        canvas_pwd.place(x=44, y=252, width=342, height=44)
        self._crear_rounded_rect(
            canvas_pwd, 0, 0, 342, 44, radius=14,
            fill="#F7FBF8", outline=ui_tema.BORDE_FUERTE
        )

        self.entrada_contrasena = tk.Entry(
            canvas_pwd,
            font=("Segoe UI", 11),
            relief="flat",
            bd=0,
            bg="#F7FBF8",
            fg=ui_tema.TEXTO,
            show="•",
            insertbackground=ui_tema.VERDE_OSCURO,
            highlightthickness=0,
        )
        canvas_pwd.create_window(
            171, 22, window=self.entrada_contrasena, width=310, height=28
        )

        self.entrada_usuario.bind(
            "<Return>", lambda e: self.entrada_contrasena.focus_set()
        )
        self.entrada_contrasena.bind(
            "<Return>", lambda e: self.iniciar_sesion()
        )

        self.btn_ingresar = ui_tema.boton(
            card_login,
            "INGRESAR AL SISTEMA",
            self.iniciar_sesion,
            principal=True,
            font=("Segoe UI", 10, "bold"),
        )
        self.btn_ingresar.place(x=44, y=330, width=342, height=46)

        def on_enter(_evento):
            self.btn_ingresar.config(bg=ui_tema.VERDE_HOVER)

        def on_leave(_evento):
            self.btn_ingresar.config(bg=ui_tema.VERDE_PRIMARIO)

        self.btn_ingresar.bind("<Enter>", on_enter)
        self.btn_ingresar.bind("<Leave>", on_leave)

        tk.Frame(card_login, bg=ui_tema.BORDE, height=1).place(
            x=44, y=410, width=342
        )

        tk.Label(
            card_login,
            text="Sistema de control de mermas",
            font=("Segoe UI", 8),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO_SECUNDARIO,
        ).place(x=44, y=432)

        tk.Label(
            card_login,
            text="Acceso exclusivo para personal autorizado",
            font=("Segoe UI", 8),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO_SECUNDARIO,
        ).place(x=44, y=452)

        self.entrada_usuario.focus_set()

    def _caracteristica(self, padre, numero, titulo, detalle):
        fila = tk.Frame(padre, bg=ui_tema.BLANCO)
        fila.pack(fill="x", padx=14, pady=5)

        circulo = tk.Canvas(
            fila, width=28, height=28,
            bg=ui_tema.BLANCO, highlightthickness=0
        )
        circulo.pack(side="left", padx=(0, 9))
        circulo.create_oval(
            0, 0, 28, 28, fill=ui_tema.VERDE_SUAVE, outline=""
        )
        circulo.create_text(
            14, 14, text=numero,
            fill=ui_tema.VERDE_OSCURO,
            font=("Segoe UI", 7, "bold")
        )

        textos = tk.Frame(fila, bg=ui_tema.BLANCO)
        textos.pack(side="left", fill="x", expand=True)

        tk.Label(
            textos, text=titulo,
            font=("Segoe UI", 9, "bold"),
            bg=ui_tema.BLANCO, fg=ui_tema.VERDE_OSCURO,
            anchor="w"
        ).pack(anchor="w")

        tk.Label(
            textos, text=detalle,
            font=("Segoe UI", 8),
            bg=ui_tema.BLANCO, fg=ui_tema.TEXTO_SECUNDARIO,
            anchor="w"
        ).pack(anchor="w")

    # Método auxiliar para dibujar rectángulos con esquinas redondeadas
    def _crear_rounded_rect(self, canvas, x1, y1, x2, y2, radius=25, **kwargs):
        points = [
            x1 + radius, y1,
            x1 + radius, y1,
            x2 - radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1 + radius,
            x1, y1
        ]
        return canvas.create_polygon(points, **kwargs, smooth=True)

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
