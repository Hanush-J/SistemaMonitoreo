import customtkinter as ctk
import threading
from tkinter import messagebox

import database
import app
import theme

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SPS — Acceso")
        self.geometry("420x520")
        self.resizable(False, False)
        self.configure(fg_color=theme.BG)

        self.validando = False
        self.dashboard = None

        tarjeta = ctk.CTkFrame(
            self, fg_color=theme.SURFACE, corner_radius=theme.RADIO,
            border_width=1, border_color=theme.BORDE,
        )
        tarjeta.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.82, relheight=0.86)

        contenido = ctk.CTkFrame(tarjeta, fg_color="transparent")
        contenido.pack(fill="both", expand=True, padx=32, pady=32)

        ctk.CTkLabel(contenido, text="🛡", font=theme.fuente(36)).pack(pady=(4, 8))
        ctk.CTkLabel(
            contenido, text="SPS", font=theme.fuente(22, "bold"), text_color=theme.TEXTO
        ).pack()
        ctk.CTkLabel(
            contenido, text="Sistema Proactivo de Seguridad",
            font=theme.fuente(11), text_color=theme.TEXTO_SUAVE,
        ).pack(pady=(0, 28))

        ctk.CTkLabel(
            contenido, text="Usuario", font=theme.fuente(11), text_color=theme.TEXTO_SUAVE,
        ).pack(anchor="w")
        self.entrada_usuario = ctk.CTkEntry(
            contenido, placeholder_text="usuario", height=38,
            fg_color=theme.SURFACE_ALT, border_color=theme.BORDE, border_width=1,
        )
        self.entrada_usuario.pack(fill="x", pady=(4, 16))

        ctk.CTkLabel(
            contenido, text="Contraseña", font=theme.fuente(11), text_color=theme.TEXTO_SUAVE,
        ).pack(anchor="w")
        self.entrada_password = ctk.CTkEntry(
            contenido, placeholder_text="contraseña", show="•", height=38,
            fg_color=theme.SURFACE_ALT, border_color=theme.BORDE, border_width=1,
        )
        self.entrada_password.pack(fill="x", pady=(4, 8))
        self.entrada_password.bind("<Return>", lambda e: self.verificar_credenciales())

        self.label_error = ctk.CTkLabel(
            contenido, text="", font=theme.fuente(10), text_color=theme.ERROR, wraplength=300,
        )
        self.label_error.pack(pady=(4, 8))

        self.boton_login = ctk.CTkButton(
            contenido, text="Entrar", command=self.verificar_credenciales,
            height=40, font=theme.fuente(13, "bold"),
            fg_color=theme.ACENTO, hover_color=theme.ACENTO_HOVER,
        )
        self.boton_login.pack(fill="x", pady=(8, 12))

        self.progreso_login = ctk.CTkProgressBar(contenido, progress_color=theme.ACENTO)
        self.progreso_login.pack(fill="x")
        self.progreso_login.set(0)

        ctk.CTkLabel(
            contenido, text="UTCJ · Tópicos de Calidad para Diseño de Software",
            font=theme.fuente(8), text_color=theme.TEXTO_SUAVE,
        ).pack(side="bottom", pady=(16, 0))

    def verificar_credenciales(self):
        """Valida usuario y contraseña de forma asincrónica."""
        if self.validando:
            return

        usuario = self.entrada_usuario.get().strip()
        contraseña = self.entrada_password.get().strip()

        if not usuario or not contraseña:
            self.label_error.configure(text="Ingresa usuario y contraseña")
            return

        self.validando = True
        self.boton_login.configure(state="disabled", text="Validando...")
        self.label_error.configure(text="")
        self.progreso_login.set(0.3)

        hilo_validacion = threading.Thread(
            target=self._validar_en_hilo, args=(usuario, contraseña), daemon=True
        )
        hilo_validacion.start()

    def _validar_en_hilo(self, usuario, contraseña):
        """Valida credenciales sin bloquear la UI."""
        try:
            self.after(100, self.progreso_login.set, 0.6)
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
        self.label_error.configure(text="Acceso concedido", text_color=theme.OK)
        self.progreso_login.set(1.0)
        self.boton_login.configure(text="Listo")
        self.after(400, self.abrir_dashboard)

    def _login_fallido(self):
        """Maneja login fallido."""
        self.label_error.configure(text="Usuario o contraseña incorrectos", text_color=theme.ERROR)
        self.progreso_login.set(0)
        self.boton_login.configure(state="normal", text="Entrar")
        self.validando = False
        self.entrada_password.delete(0, "end")
        self.entrada_usuario.focus()

    def _error_conexion(self, error):
        """Maneja error de conexión."""
        self.label_error.configure(text=f"Error de conexión: {error[:50]}", text_color=theme.ERROR)
        self.progreso_login.set(0)
        self.boton_login.configure(state="normal", text="Entrar")
        self.validando = False

    def abrir_dashboard(self):
        """Abre la aplicación principal."""
        try:
            self.withdraw()
            self.dashboard = app.AplicacionMonitor()
            self.dashboard.protocol("WM_DELETE_WINDOW", self._on_dashboard_close)
            self.dashboard.mainloop()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el dashboard:\n{str(e)}")
            self._reset_login()

    def _on_dashboard_close(self):
        """Maneja cierre del dashboard."""
        if self.dashboard:
            self.dashboard.destroy()
        self._reset_login()

    def _reset_login(self):
        """Reinicia la pantalla de login."""
        self.entrada_usuario.delete(0, "end")
        self.entrada_password.delete(0, "end")
        self.label_error.configure(text="")
        self.progreso_login.set(0)
        self.boton_login.configure(state="normal", text="Entrar")
        self.validando = False
        self.deiconify()
        self.entrada_usuario.focus()


if __name__ == "__main__":
    app_login = LoginApp()
    app_login.mainloop()
