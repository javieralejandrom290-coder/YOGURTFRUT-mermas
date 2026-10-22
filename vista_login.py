import tkinter as tk
from tkinter import messagebox
import sqlite3
import os
from PIL import Image, ImageTk, ImageEnhance, ImageDraw, ImageFont

import seguridad
from base_datos import obtener_conexion, inicializar_base_datos


class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOGUFRUT | Control de Mermas")
        self.root.geometry("980x620")
        self.root.resizable(False, False)

        # Centrar la ventana en la pantalla
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 980) // 2
        y = (self.root.winfo_screenheight() - 620) // 2
        self.root.geometry(f"980x620+{x}+{y}")

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
        ventana.title("Configuración Inicial")
        ventana.geometry("450x420")
        ventana.resizable(False, False)
        ventana.configure(bg="#FFFFFF")
        ventana.transient(self.root)
        ventana.grab_set()

        ventana.update_idletasks()
        x = (ventana.winfo_screenwidth() - 450) // 2
        y = (ventana.winfo_screenheight() - 420) // 2
        ventana.geometry(f"450x420+{x}+{y}")

        tk.Label(
            ventana,
            text="¡Bienvenido a YOGUFRUT!",
            font=("Segoe UI", 18, "bold"),
            bg="#FFFFFF",
            fg="#1B4332"
        ).pack(pady=(25, 5))

        tk.Label(
            ventana,
            text="Crea la cuenta del primer administrador.",
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#52796F"
        ).pack(pady=(0, 15))

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
                bg="#FFFFFF",
                fg="#2D3748"
            ).pack(anchor="w", padx=45)

            entrada = tk.Entry(
                ventana,
                font=("Segoe UI", 10),
                relief="flat",
                bg="#F7FAFC",
                highlightthickness=1,
                highlightbackground="#CBD5E0",
                highlightcolor="#2D6A4F"
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
                    "Éxito",
                    "Administrador creado correctamente.",
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

        btn_guardar = tk.Button(
            ventana,
            text="CREAR ADMINISTRADOR",
            command=guardar_administrador,
            font=("Segoe UI", 10, "bold"),
            bg="#2D6A4F",
            fg="#FFFFFF",
            activebackground="#1B4332",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            pady=8
        )
        btn_guardar.pack(fill="x", padx=45, pady=(10, 20))

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
        # 1. Panel Lateral Izquierdo (Verde vivo: #38A169)
        panel_izquierdo = tk.Frame(self.root, width=400, bg="#38A169")
        panel_izquierdo.pack(side="left", fill="y")
        panel_izquierdo.pack_propagate(False)

        frame_brand = tk.Frame(panel_izquierdo, bg="#38A169")
        frame_brand.place(relx=0.5, rely=0.5, anchor="center", width=340, height=420)

        tk.Label(
            frame_brand,
            text="🌿",
            font=("Segoe UI Emoji", 40),
            bg="#38A169",
            fg="#FFFFFF"
        ).pack(pady=(10, 0))

        tk.Label(
            frame_brand,
            text="YOGUFRUT",
            font=("Segoe UI", 30, "bold"),
            bg="#38A169",
            fg="#FFFFFF"
        ).pack(pady=(5, 5))

        # Texto "SISTEMA DE CONTROL DE MERMAS" sin recuadro de fondo, más grande y en negrita
        tk.Label(
            frame_brand,
            text="SISTEMA DE CONTROL DE MERMAS",
            font=("Segoe UI", 10, "bold"),
            bg="#38A169",
            fg="#FFFFFF"
        ).pack(pady=(0, 25))

        # Viñetas informativas con texto en negrita para resaltar más
        tk.Label(
            frame_brand,
            text="• Control de inventario en tiempo real\n\n• Reducción efectiva de pérdidas\n\n• Optimización de insumos y materia prima",
            font=("Segoe UI", 10, "bold"),
            bg="#38A169",
            fg="#FFFFFF",
            justify="center"
        ).pack(pady=10)

        # 2. Área Principal Derecha (Contiene la foto nítida de fondo)
        area_derecha = tk.Frame(self.root, width=580)
        area_derecha.pack(side="right", fill="both", expand=True)
        area_derecha.pack_propagate(False)

        ruta_base = os.path.dirname(os.path.abspath(__file__))
        imagen_cargada = False
        img_final_pil = None

        try:
            for archivo in os.listdir(ruta_base):
                if archivo.lower().endswith(('.jpg', '.jpeg', '.png', '.avif', '.jfif')):
                    ruta_imagen = os.path.join(ruta_base, archivo)
                    try:
                        img_original = Image.open(ruta_imagen)
                        img_redimensionada = img_original.resize((580, 620), Image.Resampling.LANCZOS)
                        
                        img_final_pil = img_redimensionada
                        
                        # Brillo natural y luminoso
                        enhancer = ImageEnhance.Brightness(img_final_pil)
                        img_final_pil = enhancer.enhance(0.90)

                        self.bg_image_derecha = ImageTk.PhotoImage(img_final_pil)
                        lbl_bg_der = tk.Label(area_derecha, image=self.bg_image_derecha, bd=0)
                        lbl_bg_der.place(x=0, y=0, relwidth=1, relheight=1)
                        imagen_cargada = True
                        break
                    except Exception as img_err:
                        print(f"Error procesando imagen {archivo}: {img_err}")
        except Exception as e:
            print(f"Error leyendo carpeta: {e}")

        if not imagen_cargada:
            area_derecha.configure(bg="#E8ECEF")

        # 3. TARJETA FLOTANTE CON EFECTO TRANSLÚCIDO (SIN RECUADROS BLANCOS)
        card_width, card_height = 460, 480
        card_x = (580 - card_width) // 2
        card_y = (620 - card_height) // 2

        card_login = tk.Frame(area_derecha, width=card_width, height=card_height, bd=0)
        card_login.place(x=card_x, y=card_y)
        card_login.pack_propagate(False)

        if imagen_cargada and img_final_pil:
            region_fondo = img_final_pil.crop((card_x, card_y, card_x + card_width, card_y + card_height))
            capa_blanca = Image.new("RGB", (card_width, card_height), "#FFFFFF")
            card_glass_pil = Image.blend(region_fondo, capa_blanca, alpha=0.32)
            
            draw = ImageDraw.Draw(card_glass_pil)
            try:
                font_titulo = ImageFont.truetype("arialbd.ttf", 22)
                font_sub = ImageFont.truetype("arial.ttf", 11)
                font_label = ImageFont.truetype("arialbd.ttf", 10)
            except:
                font_titulo = ImageFont.load_default()
                font_sub = ImageFont.load_default()
                font_label = ImageFont.load_default()

            draw.text((45, 30), "Iniciar Sesión", fill="#1B4332", font=font_titulo)
            draw.text((45, 62), "Ingresa tus credenciales para continuar", fill="#4A5568", font=font_sub)
            
            draw.text((45, 105), "USUARIO", fill="#2D3748", font=font_label)
            draw.text((45, 185), "CONTRASEÑA", fill="#2D3748", font=font_label)

            self.card_bg_img = ImageTk.PhotoImage(card_glass_pil)
            lbl_card_bg = tk.Label(card_login, image=self.card_bg_img, bd=0)
            lbl_card_bg.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            card_login.configure(bg="#FFFFFF")
            tk.Label(card_login, text="Iniciar Sesión", font=("Segoe UI", 22, "bold"), bg="#FFFFFF", fg="#1B4332").pack(anchor="w", padx=45, pady=(30, 2))
            tk.Label(card_login, text="Ingresa tus credenciales para continuar", font=("Segoe UI", 10), bg="#FFFFFF", fg="#718096").pack(anchor="w", padx=45, pady=(0, 20))
            tk.Label(card_login, text="USUARIO", font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#2D3748").pack(anchor="w", padx=45)

        # --- CAMPO USUARIO CON DISEÑO REDONDEADO ---
        canvas_usr = tk.Canvas(card_login, bg="#F0F4F4", highlightthickness=0, height=40)
        canvas_usr.place(x=45, y=125, width=370, height=40)
        self._crear_rounded_rect(canvas_usr, 0, 0, 370, 40, radius=18, fill="#F0F4F4", outline="#CBD5E0")
        
        self.entrada_usuario = tk.Entry(
            canvas_usr,
            font=("Segoe UI", 11),
            relief="flat",
            bg="#F0F4F4",
            fg="#2D3748",
            insertbackground="#1B4332"
        )
        canvas_usr.create_window(185, 20, window=self.entrada_usuario, width=340, height=28)

        # --- CAMPO CONTRASEÑA CON DISEÑO REDONDEADO ---
        canvas_pwd = tk.Canvas(card_login, bg="#F0F4F4", highlightthickness=0, height=40)
        canvas_pwd.place(x=45, y=205, width=370, height=40)
        self._crear_rounded_rect(canvas_pwd, 0, 0, 370, 40, radius=18, fill="#F0F4F4", outline="#CBD5E0")

        self.entrada_contrasena = tk.Entry(
            canvas_pwd,
            font=("Segoe UI", 11),
            relief="flat",
            bg="#F0F4F4",
            fg="#2D3748",
            show="•",
            insertbackground="#1B4332"
        )
        canvas_pwd.create_window(185, 20, window=self.entrada_contrasena, width=340, height=28)

        # Eventos de teclado
        self.entrada_usuario.bind(
            "<Return>",
            lambda e: self.entrada_contrasena.focus_set()
        )
        self.entrada_contrasena.bind(
            "<Return>",
            lambda e: self.iniciar_sesion()
        )

        # 4. BOTÓN ESTILIZADO CON HOVER DINÁMICO
        self.btn_ingresar = tk.Button(
            card_login,
            text="INGRESAR AL SISTEMA",
            command=self.iniciar_sesion,
            font=("Segoe UI", 10, "bold"),
            bg="#38A169",
            fg="#FFFFFF",
            activebackground="#2F855A",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
            pady=10
        )
        self.btn_ingresar.place(x=45, y=275, width=370, height=44)

        # Efecto Hover interactivo
        def on_enter(e):
            self.btn_ingresar.config(bg="#2F855A")

        def on_leave(e):
            self.btn_ingresar.config(bg="#38A169")

        self.btn_ingresar.bind("<Enter>", on_enter)
        self.btn_ingresar.bind("<Leave>", on_leave)

        # Footer inferior flotante sobre la derecha
        tk.Label(
            area_derecha,
            text="YOGUFRUT © 2026 · Sistema de Control de Mermas",
            font=("Segoe UI", 8, "bold"),
            bg="#276749",
            fg="#FFFFFF",
            padx=10,
            pady=3
        ).place(relx=0.5, rely=0.95, anchor="center")

        self.entrada_usuario.focus_set()

    # Método auxiliar para dibujar rectángulos con esquinas redondeadas en Canvas
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