import tkinter as tk
from tkinter import messagebox
import sqlite3

import seguridad
import ui_tema
from base_datos import obtener_conexion, inicializar_base_datos
from ui_comunes import Tarjeta, crear_logo


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
        ventana.geometry("470x600")
        ventana.resizable(False, False)
        ventana.configure(bg=ui_tema.FONDO)
        ventana.transient(self.root)
        ventana.grab_set()

        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() - 470) // 2
        y = (ventana.winfo_screenheight() - 600) // 2
        ventana.geometry(f"470x600+{x}+{y}")

        tarjeta = Tarjeta(ventana, bg=ui_tema.BLANCO, padding=24)
        tarjeta.pack(fill="both", expand=True, padx=16, pady=16)
        cuerpo = tarjeta.cuerpo

        crear_logo(cuerpo, bg=ui_tema.BLANCO, alto=56).pack(
            anchor="w", pady=(0, 10)
        )

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
                show="*" if ocultar else "",
            )
            entrada.pack(fill="x", pady=(3, 8))
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
            cuerpo, "CREAR ADMINISTRADOR", guardar_administrador,
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
        # Panel de marca (izquierda)
        panel_izquierdo = tk.Frame(
            self.root, width=430, bg=ui_tema.SIDEBAR
        )
        panel_izquierdo.pack(side="left", fill="y")
        panel_izquierdo.pack_propagate(False)

        # Detalles decorativos suaves
        fondo = tk.Canvas(
            panel_izquierdo,
            bg=ui_tema.SIDEBAR,
            highlightthickness=0,
        )
        fondo.place(x=0, y=0, relwidth=1, relheight=1)
        fondo.create_oval(
            -120, -140, 230, 210,
            fill=ui_tema.DECORACION_1, outline=""
        )
        fondo.create_oval(
            260, 430, 540, 710,
            fill=ui_tema.DECORACION_2, outline=""
        )

        marca = Tarjeta(panel_izquierdo, bg=ui_tema.BLANCO, padding=14)
        marca.place(relx=0.5, y=48, anchor="n", width=282, height=198)

        crear_logo(marca.cuerpo, bg=ui_tema.BLANCO, alto=108).pack(
            expand=True, pady=(4, 0)
        )
        tk.Label(
            marca.cuerpo,
            text="CONTROL DE MERMAS",
            font=ui_tema.fuente_texto(8, "bold"),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO_SECUNDARIO,
        ).pack(pady=(0, 8))

        tk.Frame(
            marca.cuerpo, bg=ui_tema.ACENTO, height=3, width=46
        ).pack()

        tk.Label(
            panel_izquierdo,
            text="Un control simple para\ncuidar cada insumo.",
            font=ui_tema.fuente_titulo(21),
            bg=ui_tema.SIDEBAR,
            fg=ui_tema.VERDE_OSCURO,
            justify="center",
        ).place(relx=0.5, y=286, anchor="n")

        tarjeta = Tarjeta(panel_izquierdo, bg=ui_tema.BLANCO, padding=14)
        tarjeta.place(relx=0.5, y=400, anchor="n", width=342, height=174)

        for numero, titulo, detalle in [
            ("01", "Inventario en tiempo real", "Existencias siempre al día"),
            ("02", "Menos pérdidas", "Detecta mermas a tiempo"),
            ("03", "Decisiones claras", "Reportes fáciles de leer"),
        ]:
            self._caracteristica(tarjeta.cuerpo, numero, titulo, detalle)

        tk.Label(
            panel_izquierdo,
            text="YOGUFRUT © 2026",
            font=ui_tema.fuente_texto(8),
            bg=ui_tema.SIDEBAR,
            fg=ui_tema.TEXTO_SECUNDARIO,
        ).place(relx=0.5, rely=0.97, anchor="s")

        # Panel del formulario (derecha)
        area_derecha = tk.Frame(self.root, bg=ui_tema.FONDO)
        area_derecha.pack(side="right", fill="both", expand=True)

        card_login = Tarjeta(area_derecha, bg=ui_tema.BLANCO, padding=2)
        card_login.place(
            relx=0.5, rely=0.5, anchor="center", width=430, height=500
        )
        cuerpo = card_login.cuerpo

        tk.Label(
            cuerpo,
            text="Iniciar sesión",
            font=ui_tema.fuente_titulo(24),
            bg=ui_tema.BLANCO,
            fg=ui_tema.VERDE_OSCURO,
        ).pack(anchor="w", padx=34, pady=(26, 2))

        tk.Label(
            cuerpo,
            text="Ingresa tus credenciales para continuar.",
            font=ui_tema.fuente_texto(9),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=34)

        tk.Frame(cuerpo, bg=ui_tema.BORDE, height=1).pack(
            fill="x", padx=34, pady=(18, 18)
        )

        tk.Label(
            cuerpo,
            text="Usuario",
            font=ui_tema.fuente_texto(9, "bold"),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO,
        ).pack(anchor="w", padx=34)

        self.entrada_usuario = ui_tema.entrada(
            cuerpo,
            font=ui_tema.fuente_texto(11),
        )
        self.entrada_usuario.pack(
            fill="x", padx=34, pady=(5, 14)
        )

        tk.Label(
            cuerpo,
            text="Contraseña",
            font=ui_tema.fuente_texto(9, "bold"),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO,
        ).pack(anchor="w", padx=34)

        self.entrada_contrasena = ui_tema.entrada(
            cuerpo,
            font=ui_tema.fuente_texto(11),
            show="•",
        )
        self.entrada_contrasena.pack(
            fill="x", padx=34, pady=(5, 18)
        )

        self.entrada_usuario.bind(
            "<Return>", lambda e: self.entrada_contrasena.focus_set()
        )
        self.entrada_contrasena.bind(
            "<Return>", lambda e: self.iniciar_sesion()
        )

        self.btn_ingresar = ui_tema.boton(
            cuerpo,
            "INGRESAR AL SISTEMA",
            self.iniciar_sesion,
            principal=True,
            fuente=ui_tema.fuente_texto(10, "bold"),
            height=46,
        )
        self.btn_ingresar.pack(fill="x", padx=34)

        tk.Frame(cuerpo, bg=ui_tema.BORDE, height=1).pack(
            fill="x", padx=34, pady=(22, 14)
        )

        tk.Label(
            cuerpo,
            text="Sistema de control de mermas",
            font=ui_tema.fuente_texto(8),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=34)

        tk.Label(
            cuerpo,
            text="Acceso exclusivo para personal autorizado",
            font=ui_tema.fuente_texto(8),
            bg=ui_tema.BLANCO,
            fg=ui_tema.TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=34, pady=(2, 0))

        self.entrada_usuario.focus_set()

    def _caracteristica(self, padre, numero, titulo, detalle):
        fila = tk.Frame(padre, bg=ui_tema.BLANCO)
        fila.pack(fill="x", pady=5)

        circulo = tk.Canvas(
            fila, width=30, height=30,
            bg=ui_tema.BLANCO, highlightthickness=0
        )
        circulo.pack(side="left", padx=(0, 10))
        circulo.create_oval(
            0, 0, 30, 30, fill=ui_tema.VERDE_SUAVE, outline=""
        )
        circulo.create_text(
            15, 15, text=numero,
            fill=ui_tema.VERDE_OSCURO,
            font=ui_tema.fuente_texto(8, "bold")
        )

        textos = tk.Frame(fila, bg=ui_tema.BLANCO)
        textos.pack(side="left", fill="x", expand=True)

        tk.Label(
            textos, text=titulo,
            font=ui_tema.fuente_texto(9, "bold"),
            bg=ui_tema.BLANCO, fg=ui_tema.VERDE_OSCURO,
            anchor="w"
        ).pack(anchor="w")

        tk.Label(
            textos, text=detalle,
            font=ui_tema.fuente_texto(8),
            bg=ui_tema.BLANCO, fg=ui_tema.TEXTO_SECUNDARIO,
            anchor="w"
        ).pack(anchor="w")

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
