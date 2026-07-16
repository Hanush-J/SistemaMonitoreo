import customtkinter as ctk
import threading
from tkinter import messagebox
import database
import app

# Configuración visual
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🔐 Sistema Proactivo de Seguridad LAN - Login")
        self.geometry("500x600")
        self.resizable(False, False)
        
        # Variables
        self.validando = False
        self.dashboard = None

        # --- FRAME PRINCIPAL ---
        self.frame_principal = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_principal.pack(fill="both", expand=True, padx=40, pady=40)

        # Logo/Título
        self.label_logo = ctk.CTkLabel(
            self.frame_principal,
            text="🛡️",
            font=("Arial", 80)
        )
        self.label_logo.pack(pady=(20, 10))

        self.label_titulo = ctk.CTkLabel(
            self.frame_principal,
            text="Sistema de Seguridad LAN",
            font=("Arial", 24, "bold")
        )
        self.label_titulo.pack(pady=(0, 5))

        self.label_subtitulo = ctk.CTkLabel(
            self.frame_principal,
            text="Acceso Autenticado",
            font=("Arial", 14),
            text_color="gray"
        )
        self.label_subtitulo.pack(pady=(0, 40))

        # --- CAMPO DE USUARIO ---
        self.label_usuario = ctk.CTkLabel(
            self.frame_principal,
            text="👤 Usuario",
            font=("Arial", 12, "bold"),
            text_color="white"
        )
        self.label_usuario.pack(anchor="w", pady=(10, 5))

        self.entrada_usuario = ctk.CTkEntry(
            self.frame_principal,
            placeholder_text="Ingresa tu usuario",
            height=40,
            font=("Arial", 12),
            border_width=2,
            border_color="blue"
        )
        self.entrada_usuario.pack(fill="x", pady=(0, 15))

        # --- CAMPO DE CONTRASEÑA ---
        self.label_password = ctk.CTkLabel(
            self.frame_principal,
            text="🔑 Contraseña",
            font=("Arial", 12, "bold"),
            text_color="white"
        )
        self.label_password.pack(anchor="w", pady=(10, 5))

        self.entrada_password = ctk.CTkEntry(
            self.frame_principal,
            placeholder_text="Ingresa tu contraseña",
            show="•",
            height=40,
            font=("Arial", 12),
            border_width=2,
            border_color="blue"
        )
        self.entrada_password.pack(fill="x", pady=(0, 25))

        # Bind para Enter
        self.entrada_password.bind("<Return>", lambda e: self.verificar_credenciales())

        # --- MENSAJE DE ERROR ---
        self.label_error = ctk.CTkLabel(
            self.frame_principal,
            text="",
            text_color="red",
            font=("Arial", 11),
            wraplength=400
        )
        self.label_error.pack(pady=10, padx=10)

        # --- BOTÓN DE LOGIN ---
        self.boton_login = ctk.CTkButton(
            self.frame_principal,
            text="▶ Entrar al Sistema",
            command=self.verificar_credenciales,
            height=45,
            font=("Arial", 13, "bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.boton_login.pack(fill="x", pady=15)

        # --- PROGRESO ---
        self.progreso_login = ctk.CTkProgressBar(self.frame_principal)
        self.progreso_login.pack(fill="x", pady=10)
        self.progreso_login.set(0)

        # --- PIE DE PÁGINA ---
        self.label_footer = ctk.CTkLabel(
            self.frame_principal,
            text="UTCJ - Tópicos de Calidad para Diseño de Software",
            font=("Arial", 9),
            text_color="gray"
        )
        self.label_footer.pack(side="bottom", pady=20)

        self.label_version = ctk.CTkLabel(
            self.frame_principal,
            text="v1.0.0",
            font=("Arial", 8),
            text_color="gray"
        )
        self.label_version.pack(side="bottom", pady=(0, 5))

    def verificar_credenciales(self):
        """Valida usuario y contraseña de forma asincrónica."""
        if self.validando:
            return

        # Capturar inputs
        usuario = self.entrada_usuario.get().strip()
        contraseña = self.entrada_password.get().strip()

        # Validación básica
        if not usuario or not contraseña:
            self.label_error.configure(
                text="⚠️ Por favor, ingresa usuario y contraseña"
            )
            return

        # Desactivar botón y mostrar progreso
        self.validando = True
        self.boton_login.configure(state="disabled", text="⏳ Validando...")
        self.label_error.configure(text="")
        self.progreso_login.set(0.3)

        # Ejecutar validación en hilo separado
        hilo_validacion = threading.Thread(
            target=self._validar_en_hilo,
            args=(usuario, contraseña),
            daemon=True
        )
        hilo_validacion.start()

    def _validar_en_hilo(self, usuario, contraseña):
        """Valida credenciales sin bloquear la UI."""
        try:
            self.after(100, self.progreso_login.set, 0.6)
            
            # Consultar BD
            resultado = database.validar_login(usuario, contraseña)
            
            self.after(100, self.progreso_login.set, 0.9)
            
            if resultado:
                self.after(0, self._login_exitoso)
            else:
                self.after(0, self._login_fallido)
                
        except Exception as e:
            self.after(0, self._error_conexion, str(e))

    def _login_exitoso(self):
        """Maneja login exitoso."""
        self.label_error.configure(
            text="✅ ¡Acceso concedido! Abriendo dashboard...",
            text_color="green"
        )
        self.progreso_login.set(1.0)
        self.boton_login.configure(text="✓ Acceso concedido")
        
        # Abrir dashboard después de 500ms
        self.after(500, self.abrir_dashboard)

    def _login_fallido(self):
        """Maneja login fallido."""
        self.label_error.configure(
            text="❌ Usuario o contraseña incorrectos",
            text_color="red"
        )
        self.progreso_login.set(0)
        self.boton_login.configure(state="normal", text="▶ Entrar al Sistema")
        self.validando = False
        
        # Limpiar campo de contraseña
        self.entrada_password.delete(0, "end")
        self.entrada_usuario.focus()

    def _error_conexion(self, error):
        """Maneja error de conexión."""
        self.label_error.configure(
            text=f"⚠️ Error de conexión: {error[:50]}...",
            text_color="red"
        )
        self.progreso_login.set(0)
        self.boton_login.configure(state="normal", text="▶ Entrar al Sistema")
        self.validando = False

    def abrir_dashboard(self):
        """Abre la aplicación principal."""
        try:
            # Ocultar ventana de login
            self.withdraw()
            
            # Crear y ejecutar dashboard
            self.dashboard = app.AplicacionMonitor()
            
            # Si cierra dashboard, volver al login
            self.dashboard.protocol("WM_DELETE_WINDOW", self._on_dashboard_close)
            
            self.dashboard.mainloop()
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir el dashboard:\n{str(e)}"
            )
            self._reset_login()

    def _on_dashboard_close(self):
        """Maneja cierre del dashboard."""
        if self.dashboard:
            self.dashboard.destroy()
        
        # Resetear login y mostrar
        self._reset_login()

    def _reset_login(self):
        """Reinicia la pantalla de login."""
        self.entrada_usuario.delete(0, "end")
        self.entrada_password.delete(0, "end")
        self.label_error.configure(text="")
        self.progreso_login.set(0)
        self.boton_login.configure(state="normal", text="▶ Entrar al Sistema")
        self.validando = False
        self.deiconify()  # Mostrar ventana
        self.entrada_usuario.focus()


if __name__ == "__main__":
    app_login = LoginApp()
    app_login.mainloop()
