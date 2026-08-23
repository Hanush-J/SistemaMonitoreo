import customtkinter as ctk
import threading
import queue
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import analisis_ia
import database
import port_scanner
import theme

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def habilitar_scroll_rueda(frame_scrollable):
    """Hace que la rueda del mouse funcione dentro de un CTkScrollableFrame.

    customtkinter solo se suscribe al evento <MouseWheel> (Windows/Mac). En
    Linux/X11 el scroll llega como <Button-4>/<Button-5>, así que sin esto
    la rueda del mouse no hace nada dentro del frame.
    """
    canvas = frame_scrollable._parent_canvas

    def _subir(event):
        if frame_scrollable.check_if_master_is_canvas(event.widget):
            canvas.yview_scroll(-1, "units")

    def _bajar(event):
        if frame_scrollable.check_if_master_is_canvas(event.widget):
            canvas.yview_scroll(1, "units")

    frame_scrollable.bind_all("<Button-4>", _subir, add="+")
    frame_scrollable.bind_all("<Button-5>", _bajar, add="+")


class VentanaEditarTicket(ctk.CTkToplevel):
    """Ventana modal para editar un ticket existente."""

    def __init__(self, parent, ticket, on_guardar=None):
        super().__init__(parent)
        self.parent_app = parent
        self.ticket = ticket
        self.on_guardar = on_guardar
        self.id_ticket = ticket["id_ticket"]

        self.title(f"Ticket #{self.id_ticket}")
        self.geometry("650x640")
        self.minsize(650, 640)
        self.resizable(False, False)
        self.configure(fg_color=theme.BG)

        self.transient(parent)
        self.wait_visibility()
        self.grab_set()
        self.focus_force()

        self._construir_formulario()

    def _construir_formulario(self):
        ticket = self.ticket
        fecha = ticket.get("fecha_hora", "")
        if hasattr(fecha, "strftime"):
            fecha = fecha.strftime("%Y-%m-%d %H:%M:%S")

        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=0, pady=0)

        ctk.CTkLabel(
            contenedor,
            text=f"Ticket #{ticket['id_ticket']}",
            font=theme.fuente(18, "bold"),
            text_color=theme.TEXTO,
        ).pack(pady=(20, 5))

        info_frame = ctk.CTkFrame(contenedor, fg_color=theme.SURFACE, corner_radius=theme.RADIO_CHICO)
        info_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(
            info_frame,
            text=f"Fecha: {fecha}  ·  Interfaz: {ticket.get('interfaz') or 'N/A'}",
            font=theme.fuente(10),
            text_color=theme.TEXTO_SUAVE,
        ).pack(anchor="w", padx=12, pady=8)

        form = ctk.CTkScrollableFrame(contenedor, fg_color="transparent", height=380)
        form.pack(fill="both", expand=True, padx=20, pady=10)
        habilitar_scroll_rueda(form)

        ctk.CTkLabel(form, text="Severidad", font=theme.fuente(11, "bold"), text_color=theme.TEXTO_SUAVE).pack(anchor="w")
        self.combo_severidad = ctk.CTkComboBox(
            form, values=["CRITICO", "ANOMALIA", "NORMAL"], width=200
        )
        self.combo_severidad.set(ticket.get("severidad", "ANOMALIA"))
        self.combo_severidad.pack(anchor="w", pady=(2, 10))

        ctk.CTkLabel(form, text="Estado", font=theme.fuente(11, "bold"), text_color=theme.TEXTO_SUAVE).pack(anchor="w")
        self.combo_estado = ctk.CTkComboBox(
            form, values=["PENDIENTE", "RESUELTO", "IGNORADO"], width=200
        )
        self.combo_estado.set(ticket.get("estado", "PENDIENTE"))
        self.combo_estado.pack(anchor="w", pady=(2, 10))

        ctk.CTkLabel(form, text="IP origen", font=theme.fuente(11, "bold"), text_color=theme.TEXTO_SUAVE).pack(anchor="w")
        self.entrada_ip = ctk.CTkEntry(form, placeholder_text="ej: 192.168.1.100")
        self.entrada_ip.insert(0, ticket.get("ip_origen") or "")
        self.entrada_ip.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(form, text="Puertos involucrados", font=theme.fuente(11, "bold"), text_color=theme.TEXTO_SUAVE).pack(anchor="w")
        self.entrada_puertos = ctk.CTkEntry(form, placeholder_text="ej: 80,443,22")
        self.entrada_puertos.insert(0, ticket.get("puertos_involucrados") or "")
        self.entrada_puertos.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(form, text="Descripción", font=theme.fuente(11, "bold"), text_color=theme.TEXTO_SUAVE).pack(anchor="w")
        self.text_descripcion = ctk.CTkTextbox(form, height=150, font=theme.fuente_mono(10))
        self.text_descripcion.insert("1.0", ticket.get("descripcion", ""))
        self.text_descripcion.pack(fill="x", pady=(2, 10))

        footer = ctk.CTkFrame(contenedor, fg_color=theme.SURFACE, corner_radius=0)
        footer.pack(fill="x", side="bottom", padx=0, pady=0)

        self.label_estado_guardado = ctk.CTkLabel(footer, text="", font=theme.fuente(11, "bold"))
        self.label_estado_guardado.pack(pady=(12, 6))

        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.btn_guardar = ctk.CTkButton(
            btn_frame,
            text="Guardar cambios",
            width=180,
            height=36,
            font=theme.fuente(13, "bold"),
            fg_color=theme.ACENTO,
            hover_color=theme.ACENTO_HOVER,
            command=self._guardar,
        )
        self.btn_guardar.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Cerrar sin guardar",
            width=150,
            height=36,
            fg_color=theme.NEUTRO,
            hover_color=theme.NEUTRO_HOVER,
            command=self.destroy,
        ).pack(side="left")

    def _guardar(self):
        descripcion = self.text_descripcion.get("1.0", "end").strip()
        if not descripcion:
            self.label_estado_guardado.configure(
                text="La descripción no puede estar vacía", text_color=theme.ERROR,
            )
            return

        self.btn_guardar.configure(state="disabled", text="Guardando...")
        self.label_estado_guardado.configure(text="Guardando en base de datos...", text_color=theme.ACENTO)
        self.update_idletasks()

        ip = self.entrada_ip.get().strip() or None
        puertos = self.entrada_puertos.get().strip() or None

        exito = database.actualizar_ticket(
            self.id_ticket,
            severidad=self.combo_severidad.get(),
            estado=self.combo_estado.get(),
            descripcion=descripcion,
            ip_origen=ip,
            puertos_involucrados=puertos,
        )

        self.btn_guardar.configure(state="normal", text="Guardar cambios")

        if exito:
            self.label_estado_guardado.configure(
                text="Ticket guardado correctamente", text_color=theme.OK,
            )
            if hasattr(self.parent_app, "agregar_log"):
                self.parent_app.agregar_log("SUCCESS", f"Ticket #{self.id_ticket} actualizado y guardado")
            if self.on_guardar:
                self.on_guardar()
        else:
            self.label_estado_guardado.configure(
                text="No se pudo guardar. Verifica la conexión a la base de datos",
                text_color=theme.ERROR,
            )
            if hasattr(self.parent_app, "agregar_log"):
                self.parent_app.agregar_log("ERROR", f"No se pudo guardar el ticket #{self.id_ticket}")


class AplicacionMonitor(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SPS — Sistema Proactivo de Seguridad")
        self.geometry("1400x900")
        self.configure(fg_color=theme.BG)

        # Variables de control
        self.monitoreando = False
        self.buzon_reportes = queue.Queue(maxsize=1)
        self.ventanas_editor_abiertas = {}

        # --- PANEL IZQUIERDO (Controles) ---
        self.frame_controles = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=theme.SURFACE)
        self.frame_controles.pack(side="left", fill="y", padx=0, pady=0)

        ctk.CTkLabel(self.frame_controles, text="🛡", font=theme.fuente(28)).pack(pady=(24, 0))
        ctk.CTkLabel(
            self.frame_controles, text="SPS", font=theme.fuente(16, "bold"), text_color=theme.TEXTO,
        ).pack()
        ctk.CTkLabel(
            self.frame_controles, text="Panel de control", font=theme.fuente(10), text_color=theme.TEXTO_SUAVE,
        ).pack(pady=(0, 20))

        # --- Sección de Análisis de Tráfico ---
        ctk.CTkLabel(
            self.frame_controles, text="ANÁLISIS DE TRÁFICO",
            font=theme.fuente(10, "bold"), text_color=theme.TEXTO_SUAVE,
        ).pack(anchor="w", padx=15, pady=(5, 8))

        self.btn_iniciar = ctk.CTkButton(
            self.frame_controles,
            text="Iniciar monitoreo",
            fg_color=theme.ACENTO,
            hover_color=theme.ACENTO_HOVER,
            command=self.arrancar_sistema,
        )
        self.btn_iniciar.pack(pady=4, padx=15, fill="x")

        self.btn_detener = ctk.CTkButton(
            self.frame_controles,
            text="Detener",
            fg_color=theme.ERROR,
            hover_color=theme.ERROR_HOVER,
            state="disabled",
            command=self.detener_sistema,
        )
        self.btn_detener.pack(pady=4, padx=15, fill="x")

        # --- Sección de Escaneo de Puertos ---
        ctk.CTkLabel(
            self.frame_controles, text="ESCANEO DE PUERTOS",
            font=theme.fuente(10, "bold"), text_color=theme.TEXTO_SUAVE,
        ).pack(anchor="w", padx=15, pady=(20, 8))

        ctk.CTkLabel(self.frame_controles, text="Red / host (IP)", font=theme.fuente(10), text_color=theme.TEXTO_SUAVE).pack(anchor="w", padx=15)
        self.entrada_host = ctk.CTkEntry(
            self.frame_controles,
            placeholder_text="ej: 192.168.1.1",
            fg_color=theme.SURFACE_ALT, border_color=theme.BORDE,
        )
        self.entrada_host.pack(pady=(4, 10), padx=15, fill="x")

        # Modo de escaneo: decide si se usan los campos de rango o las
        # checkboxes de abajo (ver _actualizar_visibilidad_modo).
        ctk.CTkLabel(self.frame_controles, text="Modo de escaneo", font=theme.fuente(10), text_color=theme.TEXTO_SUAVE).pack(anchor="w", padx=15)
        self.combo_modo_escaneo = ctk.CTkComboBox(
            self.frame_controles,
            values=["Rango Completo", "Puertos Comunes VIP", "Personalizado"],
            command=lambda _: self._actualizar_visibilidad_modo(),
        )
        self.combo_modo_escaneo.pack(pady=(4, 10), padx=15, fill="x")
        self.combo_modo_escaneo.set("Puertos Comunes VIP")

        # Rango de puertos: solo visible/relevante en modo "Rango Completo"
        self.frame_rango = ctk.CTkFrame(self.frame_controles, fg_color="transparent")
        self.frame_rango.pack(pady=(0, 10), padx=15, fill="x")

        ctk.CTkLabel(self.frame_rango, text="Desde", font=theme.fuente(10), text_color=theme.TEXTO_SUAVE).pack(side="left")
        self.entrada_puerto_inicio = ctk.CTkEntry(self.frame_rango, width=65, placeholder_text="1")
        self.entrada_puerto_inicio.pack(side="left", padx=5)

        ctk.CTkLabel(self.frame_rango, text="Hasta", font=theme.fuente(10), text_color=theme.TEXTO_SUAVE).pack(side="left")
        self.entrada_puerto_fin = ctk.CTkEntry(self.frame_rango, width=65, placeholder_text="1000")
        self.entrada_puerto_fin.pack(side="left", padx=5)

        # Checkboxes de puertos VIP: solo se usan en modo "Personalizado",
        # pero se dejan visibles siempre para que el usuario pueda armar su
        # selección antes de cambiar de modo.
        ctk.CTkLabel(self.frame_controles, text="Puertos a auditar", font=theme.fuente(10), text_color=theme.TEXTO_SUAVE).pack(anchor="w", padx=15, pady=(0, 4))

        self.var_todos_puertos = ctk.BooleanVar(value=False)
        self.chk_todos = ctk.CTkCheckBox(
            self.frame_controles,
            text="Seleccionar todos",
            variable=self.var_todos_puertos,
            command=self.toggle_todos_puertos,
            font=theme.fuente(11, "bold"),
            text_color=theme.TEXTO,
        )
        self.chk_todos.pack(anchor="w", padx=15, pady=(0, 5))

        self.frame_checkboxes = ctk.CTkScrollableFrame(self.frame_controles, height=150, fg_color=theme.SURFACE_ALT)
        self.frame_checkboxes.pack(pady=(0, 10), padx=15, fill="x")
        habilitar_scroll_rueda(self.frame_checkboxes)

        # Puertos VIP ofrecidos para escaneo "Personalizado" (distinto del
        # listado interno de port_scanner.escanear_puertos_predeterminados,
        # que es fijo y no editable desde la interfaz).
        self.puertos_disponibles = [
            (21, "TCP", "FTP"), (22, "TCP", "SSH"), (23, "TCP", "Telnet"),
            (25, "TCP", "SMTP"), (53, "UDP", "DNS"), (67, "UDP", "DHCP"),
            (69, "UDP", "TFTP"), (80, "TCP", "HTTP"), (443, "TCP", "HTTPS"),
            (3306, "TCP", "MySQL"), (3389, "TCP", "RDP"),
        ]
        self.variables_checkbox = {}

        for puerto, protocolo, nombre in self.puertos_disponibles:
            var = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(
                self.frame_checkboxes,
                text=f"{puerto} ({protocolo}) · {nombre}",
                variable=var,
                font=theme.fuente(10),
            ).pack(anchor="w", padx=5, pady=2)
            self.variables_checkbox[(puerto, protocolo)] = var

        self._actualizar_visibilidad_modo()

        self.btn_escaneo_puertos = ctk.CTkButton(
            self.frame_controles,
            text="Escanear puertos",
            fg_color=theme.ACENTO,
            hover_color=theme.ACENTO_HOVER,
            command=self.iniciar_escaneo_puertos,
        )
        self.btn_escaneo_puertos.pack(pady=4, padx=15, fill="x")

        self.progreso_escaneo = ctk.CTkProgressBar(self.frame_controles, progress_color=theme.ACENTO)
        self.progreso_escaneo.pack(pady=(10, 4), padx=15, fill="x")
        self.progreso_escaneo.set(0)

        self.label_progreso = ctk.CTkLabel(self.frame_controles, text="", font=theme.fuente(9), text_color=theme.TEXTO_SUAVE)
        self.label_progreso.pack(pady=2, padx=15)

        self.etiqueta_estado_sistema = ctk.CTkLabel(
            self.frame_controles, text="●  Motor en reposo",
            text_color=theme.NEUTRO, font=theme.fuente(11, "bold"),
        )
        self.etiqueta_estado_sistema.pack(side="bottom", pady=20)

        # --- PANEL PRINCIPAL (Centro y Abajo) ---
        self.frame_principal = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_principal.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        # --- PANEL SUPERIOR: Semáforo ---
        self.frame_semaforo = ctk.CTkFrame(self.frame_principal, fg_color=theme.SURFACE, corner_radius=theme.RADIO)
        self.frame_semaforo.pack(fill="x", pady=(0, 10))

        self.etiqueta_semaforo = ctk.CTkLabel(
            self.frame_semaforo,
            text="●  En espera",
            font=theme.fuente(28, "bold"),
            text_color=theme.NEUTRO,
        )
        self.etiqueta_semaforo.pack(pady=15)

        # --- PANEL CENTRAL: Consola de ejecución ---
        self.frame_consola = ctk.CTkFrame(self.frame_principal, fg_color=theme.SURFACE, corner_radius=theme.RADIO)
        self.frame_consola.pack(fill="both", expand=True, pady=(0, 10))

        ctk.CTkLabel(
            self.frame_consola, text="CONSOLA",
            font=theme.fuente(11, "bold"), text_color=theme.TEXTO_SUAVE,
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.textbox_consola = ctk.CTkTextbox(
            self.frame_consola,
            fg_color=theme.SURFACE_ALT,
            text_color=theme.TEXTO,
            font=theme.fuente_mono(14),
        )
        self.textbox_consola.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.textbox_consola.configure(state="disabled")

        # --- PANEL INFERIOR: Tickets ---
        self.frame_tickets_section = ctk.CTkFrame(self.frame_principal, fg_color=theme.SURFACE, corner_radius=theme.RADIO)
        self.frame_tickets_section.pack(fill="both", expand=False, pady=0)

        self.tabview = ctk.CTkTabview(self.frame_tickets_section, fg_color=theme.SURFACE, height=280)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_tickets = self.tabview.add("Tickets activos")

        header_tickets_activos = ctk.CTkFrame(self.tab_tickets, fg_color="transparent")
        header_tickets_activos.pack(fill="x", padx=5, pady=(5, 0))

        ctk.CTkButton(
            header_tickets_activos, text="Limpiar pantalla", width=120,
            fg_color=theme.NEUTRO, hover_color=theme.NEUTRO_HOVER,
            command=self.limpiar_tickets_activos,
        ).pack(side="right", padx=5)

        self.frame_tickets = ctk.CTkScrollableFrame(self.tab_tickets, fg_color=theme.SURFACE_ALT, label_text="")
        self.frame_tickets.pack(fill="both", expand=True, padx=0, pady=(5, 0))
        habilitar_scroll_rueda(self.frame_tickets)

        self.tab_gestion = self.tabview.add("Gestión de tickets")
        self._construir_tab_gestion()

        self.tab_graficas = self.tabview.add("Estadísticas")
        self.tabview_graficas = ctk.CTkTabview(self.tab_graficas, fg_color=theme.SURFACE_ALT)
        self.tabview_graficas.pack(fill="both", expand=True, padx=0, pady=0)

        self.tab_total = self.tabview_graficas.add("Total por día")
        self.canvas_total = None

        self.tab_severidad = self.tabview_graficas.add("Severidad por día")
        self.canvas_severidad = None

        self.cargar_tickets_gestion()

    def _construir_tab_gestion(self):
        """Construye la pestaña de gestión de tickets."""
        header = ctk.CTkFrame(self.tab_gestion, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=(5, 0))

        ctk.CTkLabel(
            header, text="Historial completo de tickets",
            font=theme.fuente(12, "bold"), text_color=theme.TEXTO,
        ).pack(side="left")

        self.label_total_tickets = ctk.CTkLabel(
            header, text="0 tickets", font=theme.fuente(10), text_color=theme.TEXTO_SUAVE,
        )
        self.label_total_tickets.pack(side="left", padx=15)

        ctk.CTkButton(
            header, text="Actualizar", width=100,
            fg_color=theme.NEUTRO, hover_color=theme.NEUTRO_HOVER,
            command=self.cargar_tickets_gestion,
        ).pack(side="right", padx=5)

        filtros = ctk.CTkFrame(self.tab_gestion, fg_color="transparent")
        filtros.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(filtros, text="Filtrar por estado:", font=theme.fuente(10), text_color=theme.TEXTO_SUAVE).pack(side="left", padx=(0, 5))
        self.filtro_estado = ctk.CTkComboBox(
            filtros,
            values=["TODOS", "PENDIENTE", "RESUELTO", "IGNORADO"],
            width=140,
            command=lambda _: self.cargar_tickets_gestion(),
        )
        self.filtro_estado.set("TODOS")
        self.filtro_estado.pack(side="left")

        self.frame_gestion_lista = ctk.CTkScrollableFrame(self.tab_gestion, fg_color=theme.SURFACE_ALT, label_text="")
        self.frame_gestion_lista.pack(fill="both", expand=True, padx=0, pady=5)
        habilitar_scroll_rueda(self.frame_gestion_lista)

    def _obtener_colores_severidad(self, severidad):
        return theme.COLORES_SEVERIDAD.get(severidad, (theme.NEUTRO, theme.TEXTO))

    def _formatear_fecha(self, fecha):
        if hasattr(fecha, "strftime"):
            return fecha.strftime("%Y-%m-%d %H:%M:%S")
        return str(fecha)

    def _abrir_editor_ticket(self, id_ticket):
        """Abre la ventana de edición para un ticket."""
        if id_ticket in self.ventanas_editor_abiertas:
            ventana = self.ventanas_editor_abiertas[id_ticket]
            if ventana.winfo_exists():
                ventana.focus_force()
                return

        ticket = database.obtener_ticket_por_id(id_ticket)
        if not ticket:
            self.agregar_log("ERROR", f"No se encontró el ticket #{id_ticket}")
            return

        def on_guardar():
            self.cargar_tickets_gestion()
            self.refrescar_graficas()

        ventana = VentanaEditarTicket(self, ticket, on_guardar=on_guardar)
        self.ventanas_editor_abiertas[id_ticket] = ventana
        ventana.protocol("WM_DELETE_WINDOW", lambda: self._cerrar_editor(id_ticket))

    def _cerrar_editor(self, id_ticket):
        ventana = self.ventanas_editor_abiertas.pop(id_ticket, None)
        if ventana and ventana.winfo_exists():
            ventana.destroy()

    def cargar_tickets_gestion(self):
        """Carga y muestra todos los tickets desde la base de datos."""
        for widget in self.frame_gestion_lista.winfo_children():
            widget.destroy()

        tickets = database.obtener_tickets_recientes(100)
        filtro = self.filtro_estado.get()

        if filtro != "TODOS":
            tickets = [t for t in tickets if t.get("estado") == filtro]

        self.label_total_tickets.configure(text=f"{len(tickets)} tickets")

        if not tickets:
            ctk.CTkLabel(
                self.frame_gestion_lista, text="No hay tickets registrados",
                font=theme.fuente(11), text_color=theme.TEXTO_SUAVE,
            ).pack(pady=20)
            return

        for ticket in tickets:
            self._crear_fila_gestion(ticket)

    def _crear_fila_gestion(self, ticket):
        """Crea una fila en la pestaña de gestión."""
        id_ticket = ticket["id_ticket"]
        severidad = ticket.get("severidad", "ANOMALIA")
        estado = ticket.get("estado", "PENDIENTE")
        color_borde, color_texto = self._obtener_colores_severidad(severidad)
        color_estado = theme.COLORES_ESTADO.get(estado, theme.TEXTO)

        fila = ctk.CTkFrame(
            self.frame_gestion_lista,
            border_width=1,
            border_color=color_borde,
            fg_color=theme.SURFACE,
            corner_radius=theme.RADIO_CHICO,
        )
        fila.pack(fill="x", padx=6, pady=4)

        contenido = ctk.CTkFrame(fila, fg_color="transparent")
        contenido.pack(fill="x", padx=10, pady=8)

        cabecera = ctk.CTkFrame(contenido, fg_color="transparent")
        cabecera.pack(fill="x")

        ctk.CTkLabel(
            cabecera,
            text=f"#{id_ticket:04d}  ·  {self._formatear_fecha(ticket.get('fecha_hora'))}",
            font=theme.fuente(10, "bold"),
            text_color=color_texto,
        ).pack(side="left")

        ctk.CTkLabel(
            cabecera, text=f"[{severidad}]", font=theme.fuente(10, "bold"), text_color=color_texto,
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            cabecera, text=f"Estado: {estado}", font=theme.fuente(10), text_color=color_estado,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            cabecera, text="Editar", width=70, height=24, font=theme.fuente(10),
            fg_color=theme.NEUTRO, hover_color=theme.NEUTRO_HOVER,
            command=lambda tid=id_ticket: self._abrir_editor_ticket(tid),
        ).pack(side="right")

        descripcion = ticket.get("descripcion", "")
        if len(descripcion) > 120:
            descripcion = descripcion[:120] + "..."

        ctk.CTkLabel(
            contenido, text=descripcion, font=theme.fuente_mono(9),
            justify="left", anchor="w", text_color=theme.TEXTO,
        ).pack(fill="x", pady=(4, 0))

        extras = []
        if ticket.get("ip_origen"):
            extras.append(f"IP: {ticket['ip_origen']}")
        if ticket.get("puertos_involucrados"):
            extras.append(f"Puertos: {ticket['puertos_involucrados']}")
        if extras:
            ctk.CTkLabel(
                contenido, text=" · ".join(extras), font=theme.fuente(9), text_color=theme.TEXTO_SUAVE,
            ).pack(anchor="w", pady=(2, 0))

    def agregar_log(self, tipo, mensaje):
        """Agrega un mensaje a la consola en tiempo real."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_mensaje = f"[{timestamp}] {tipo}: {mensaje}\n"

        self.after(0, self._actualizar_consola, log_mensaje)
        database.registrar_log(tipo, mensaje)

    def _actualizar_consola(self, mensaje):
        """Actualiza la consola (debe ser llamado desde el hilo principal)."""
        if not hasattr(self, 'textbox_consola') or not self.textbox_consola.winfo_exists():
            return

        self.textbox_consola.configure(state="normal")
        self.textbox_consola.insert("end", mensaje)
        self.textbox_consola.see("end")
        self.textbox_consola.configure(state="disabled")

    def actualizar_semaforo(self, texto, color):
        """Actualiza el semáforo de forma segura."""
        if not hasattr(self, 'etiqueta_semaforo') or not self.etiqueta_semaforo.winfo_exists():
            return
        self.etiqueta_semaforo.configure(text=f"●  {texto}", text_color=color)

    def crear_ticket(self, severidad, descripcion, ip_origen=None, puertos=None):
        """Genera un nuevo ticket y lo guarda en BD."""
        hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        interfaz = analisis_ia.detectar_interfaz_automatica()
        id_ticket = database.crear_ticket(
            severidad=severidad, descripcion=descripcion, interfaz=interfaz,
            ip_origen=ip_origen, puertos=puertos,
        )

        if not id_ticket:
            self.agregar_log("ERROR", "No se pudo guardar el ticket en BD")
            return

        color_borde, color_texto = self._obtener_colores_severidad(severidad)

        tickets_previos = self.frame_tickets.winfo_children()

        ticket_frame = ctk.CTkFrame(
            self.frame_tickets, border_width=2, border_color=color_borde,
            fg_color=theme.SURFACE, corner_radius=theme.RADIO_CHICO,
        )
        if tickets_previos:
            ticket_frame.pack(fill="x", padx=8, pady=6, before=tickets_previos[0])
        else:
            ticket_frame.pack(fill="x", padx=8, pady=6)

        cabecera_frame = ctk.CTkFrame(ticket_frame, fg_color="transparent")
        cabecera_frame.pack(fill="x", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            cabecera_frame,
            text=f"#{id_ticket:04d}  ·  {hora_actual}  ·  [{severidad}]",
            font=theme.fuente(11, "bold"),
            text_color=color_texto,
        ).pack(side="left")

        ctk.CTkButton(
            cabecera_frame, text="Editar", width=60, height=22, font=theme.fuente(10),
            fg_color=theme.NEUTRO, hover_color=theme.NEUTRO_HOVER,
            command=lambda tid=id_ticket: self._abrir_editor_ticket(tid),
        ).pack(side="right")

        ctk.CTkLabel(
            ticket_frame, text=descripcion, font=theme.fuente_mono(9),
            justify="left", wraplength=500, text_color=theme.TEXTO,
        ).pack(anchor="w", padx=12, pady=(0, 8))

        self.after(100, self.refrescar_graficas)
        self.after(100, self.cargar_tickets_gestion)

    def limpiar_tickets_activos(self):
        """Borra solo las tarjetas visuales de 'Tickets activos'.

        No toca la base de datos: los tickets siguen intactos y visibles
        en la pestaña 'Gestión de tickets'.
        """
        for widget in self.frame_tickets.winfo_children():
            widget.destroy()

    def arrancar_sistema(self):
        """Inicia el monitoreo de tráfico."""
        self.monitoreando = True
        self.btn_iniciar.configure(state="disabled")
        self.btn_detener.configure(state="normal")
        self.etiqueta_estado_sistema.configure(text="●  Motor escaneando", text_color=theme.OK)
        self.actualizar_semaforo("Analizando red", theme.OK)

        self.agregar_log("INFO", "Sistema iniciado - Escaneando tráfico de red")

        hilo_captura = threading.Thread(target=self.trabajador_sniffer, daemon=True)
        hilo_captura.start()

        hilo_ia = threading.Thread(target=self.trabajador_inteligencia, daemon=True)
        hilo_ia.start()

    def detener_sistema(self):
        """Detiene el monitoreo."""
        self.monitoreando = False
        self.btn_detener.configure(state="disabled")
        self.etiqueta_estado_sistema.configure(text="●  Motor deteniéndose", text_color=theme.WARN)
        self.actualizar_semaforo("Apagando", theme.WARN)
        self.agregar_log("INFO", "Sistema detenido por el usuario")

    def trabajador_sniffer(self):
        """HILO 1: Captura tráfico en vivo."""
        interfaz = analisis_ia.detectar_interfaz_automatica()
        if not interfaz:
            self.after(0, self.actualizar_semaforo, "Sin tarjeta de red", theme.ERROR)
            self.after(0, self.agregar_log, "ERROR", "No se detectó interfaz de red")
            return

        self.after(0, self.agregar_log, "SUCCESS", f"Interfaz detectada: {interfaz}")

        while self.monitoreando:
            reporte = analisis_ia.capturar_trafico_vivo(interfaz, tiempo_ventana=5)

            if not self.monitoreando:
                break

            if reporte:
                self.after(0, self.agregar_log, "INFO", "Tráfico capturado - Analizando...")
                # Si la IA sigue ocupada con el reporte anterior, lo descartamos
                # y nos quedamos solo con el más reciente (evita acumular atrasos).
                if self.buzon_reportes.full():
                    try:
                        self.buzon_reportes.get_nowait()
                    except queue.Empty:
                        pass
                self.buzon_reportes.put(reporte)
            else:
                self.after(0, self.agregar_log, "WARNING", "Sin tráfico IP detectado")

        self.after(0, self.restaurar_botones)

    def trabajador_inteligencia(self):
        """HILO 2: Procesa reportes y consulta IA."""
        while self.monitoreando:
            try:
                reporte_nuevo = self.buzon_reportes.get(timeout=2)

                self.after(0, self.actualizar_semaforo, "IA analizando...", theme.ACENTO)
                self.after(0, self.agregar_log, "INFO", "Consultando IA para análisis...")

                veredicto = analisis_ia.consultar_ia_local(reporte_nuevo, modelo="qwen2.5-coder:7b")

                if veredicto:
                    veredicto_mayus = veredicto.upper()
                    self.after(0, self.agregar_log, "INFO", f"IA: {veredicto[:80]}...")

                    if "[TRÁFICO NORMAL]" in veredicto_mayus or "[TRAFICO NORMAL]" in veredicto_mayus:
                        self.after(0, self.actualizar_semaforo, "Tráfico normal", theme.OK)
                        self.after(0, self.agregar_log, "SUCCESS", "Tráfico normal detectado")
                        # No creamos ticket aquí: el tráfico normal no se registra.

                    elif "[ALERTA CRITICA DETECTADA]" in veredicto_mayus or "[ALERTA CRÍTICA" in veredicto_mayus:
                        self.after(0, self.actualizar_semaforo, "Crítico", theme.ERROR)
                        self.after(0, self.crear_ticket, "CRITICO", veredicto, None, None)
                        self.after(0, self.agregar_log, "ERROR", "ALERTA CRÍTICA CREADA")

                    elif "[ANOMALIA]" in veredicto_mayus or "[ANOMALÍA]" in veredicto_mayus:
                        self.after(0, self.actualizar_semaforo, "Anomalía", theme.WARN)
                        self.after(0, self.crear_ticket, "ANOMALIA", veredicto, None, None)
                        self.after(0, self.agregar_log, "WARNING", "Anomalía detectada - Ticket creado")

                    elif "[OMITIR]" in veredicto_mayus:
                        # Timeout/error de infraestructura de Ollama: no es una
                        # alerta de red, así que no genera ticket.
                        self.after(0, self.actualizar_semaforo, "Analizando red", theme.ACENTO)
                        self.after(0, self.agregar_log, "WARNING", veredicto)

                    else:
                        self.after(0, self.actualizar_semaforo, "Desconocido", theme.WARN)
                        self.after(0, self.crear_ticket, "ANOMALIA", veredicto, None, None)

            except queue.Empty:
                continue

    def _actualizar_visibilidad_modo(self):
        """Muestra solo los controles relevantes al modo de escaneo elegido."""
        modo = self.combo_modo_escaneo.get()

        if modo == "Rango Completo":
            self.frame_rango.pack(pady=(0, 10), padx=15, fill="x")
        else:
            self.frame_rango.pack_forget()

    def toggle_todos_puertos(self):
        """Marca/desmarca todos los checkboxes de puertos VIP a la vez."""
        estado = self.var_todos_puertos.get()
        for var in self.variables_checkbox.values():
            var.set(estado)

    def iniciar_escaneo_puertos(self):
        """Inicia escaneo de puertos en hilo separado."""
        host = self.entrada_host.get().strip()

        if not host:
            self.agregar_log("ERROR", "Ingresa un host válido (IP)")
            return

        modo = self.combo_modo_escaneo.get()
        puerto_inicio, puerto_fin = 1, 1000
        lista_puertos = None

        if modo == "Rango Completo":
            try:
                puerto_inicio = int(self.entrada_puerto_inicio.get() or "1")
                puerto_fin = int(self.entrada_puerto_fin.get() or "1000")

                if puerto_inicio < 1 or puerto_fin > 65535 or puerto_inicio > puerto_fin:
                    self.agregar_log("ERROR", "Rango de puertos inválido")
                    return
            except ValueError:
                self.agregar_log("ERROR", "Los puertos deben ser números")
                return
        elif modo == "Personalizado":
            lista_puertos = [puerto_proto for puerto_proto, var in self.variables_checkbox.items() if var.get()]
            if not lista_puertos:
                self.agregar_log("ERROR", "Selecciona al menos un puerto para auditar")
                return

        self.btn_escaneo_puertos.configure(state="disabled")
        self.progreso_escaneo.set(0)
        self.agregar_log("INFO", f"Iniciando escaneo ({modo}) en {host}")

        def callback_progreso(actual, total):
            porcentaje = actual / total
            self.after(0, self.progreso_escaneo.set, porcentaje)
            self.after(0, lambda: self.label_progreso.configure(text=f"{actual}/{total} puertos"))

        def callback_resultado(puerto, estado):
            self.after(0, self.agregar_log, "SUCCESS", f"Puerto {puerto}: {estado}")

        hilo_escaneo = threading.Thread(
            target=self._ejecutar_escaneo,
            args=(host, modo, puerto_inicio, puerto_fin, lista_puertos, callback_progreso, callback_resultado),
            daemon=True,
        )
        hilo_escaneo.start()

    def _ejecutar_escaneo(self, host, modo, inicio, fin, lista_puertos, callback_prog, callback_res):
        """Ejecuta el escaneo en hilo separado."""
        if modo == "Puertos Comunes VIP":
            resultado = port_scanner.escanear_puertos_predeterminados(host, callback_prog, callback_res)
        elif modo == "Personalizado":
            resultado = port_scanner.escanear_puertos_personalizados(host, lista_puertos, callback_prog, callback_res)
        else:
            resultado = port_scanner.escanear_puertos(host, inicio, fin, callback_prog, callback_res)

        self.after(0, lambda: self.btn_escaneo_puertos.configure(state="normal"))

        if resultado:
            self.after(0, self.agregar_log, "SUCCESS",
                f"Escaneo completado: {resultado['total_abiertos']} puertos abiertos")
            if resultado["total_abiertos"] > 0:
                self.after(0, self._mostrar_resultados_escaneo, resultado)
        else:
            self.after(0, self.agregar_log, "ERROR", "El escaneo falló (revisa permisos/conexión)")

    def _mostrar_resultados_escaneo(self, resultado):
        """Muestra resultados del escaneo."""
        puertos_abiertos = resultado['puertos_abiertos']
        servicios = port_scanner.obtener_servicios_por_puerto(puertos_abiertos)

        mensaje = f"Puertos abiertos: {', '.join([f'{p}({servicios[p]})' for p in puertos_abiertos[:10]])}"
        if len(puertos_abiertos) > 10:
            mensaje += f"... y {len(puertos_abiertos) - 10} más"

        self.agregar_log("INFO", mensaje)

    def restaurar_botones(self):
        """Restaura estado de los botones al detener."""
        self.btn_iniciar.configure(state="normal")
        self.etiqueta_estado_sistema.configure(text="●  Motor en reposo", text_color=theme.NEUTRO)
        self.actualizar_semaforo("En espera", theme.NEUTRO)

    def refrescar_graficas(self):
        """Actualiza las gráficas con datos de la BD."""
        estadisticas = database.obtener_estadisticas_semana()

        if not estadisticas or not estadisticas.get('tickets_por_dia'):
            return

        self._dibujar_grafica_total(estadisticas)
        self._dibujar_grafica_severidad(estadisticas)

    def _dibujar_grafica_total(self, estadisticas):
        """Dibuja gráfica de total de tickets por día."""
        if self.canvas_total:
            self.canvas_total.get_tk_widget().destroy()

        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        tickets = [estadisticas['tickets_por_dia'].get(dia, 0) for dia in dias]

        fig = Figure(figsize=(10, 3.5), dpi=80, facecolor=theme.SURFACE_ALT, edgecolor='none')
        ax = fig.add_subplot(111, facecolor=theme.SURFACE_ALT)

        colores_barras = [theme.ACENTO if t > 0 else theme.BORDE for t in tickets]
        ax.bar(dias, tickets, color=colores_barras)

        ax.set_ylabel('Tickets', color=theme.TEXTO_SUAVE, fontsize=10)
        ax.set_title('Tickets detectados (última semana)', color=theme.TEXTO, fontsize=12, fontweight='bold')
        ax.tick_params(axis='both', colors=theme.TEXTO_SUAVE)
        ax.grid(axis='y', alpha=0.15, color=theme.TEXTO_SUAVE)
        for spine in ax.spines.values():
            spine.set_color(theme.BORDE)

        self.canvas_total = FigureCanvasTkAgg(fig, master=self.tab_total)
        self.canvas_total.draw()
        self.canvas_total.get_tk_widget().pack(fill="both", expand=True)

    def _dibujar_grafica_severidad(self, estadisticas):
        """Dibuja gráfica de tickets por severidad."""
        if self.canvas_severidad:
            self.canvas_severidad.get_tk_widget().destroy()

        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        criticos, anomalias, normales = [], [], []

        for dia in dias:
            sev = estadisticas['severidad_por_dia'].get(dia, {})
            criticos.append(sev.get('criticos', 0))
            anomalias.append(sev.get('anomalias', 0))
            normales.append(sev.get('normales', 0))

        fig = Figure(figsize=(10, 3.5), dpi=80, facecolor=theme.SURFACE_ALT, edgecolor='none')
        ax = fig.add_subplot(111, facecolor=theme.SURFACE_ALT)

        x = range(len(dias))
        width = 0.25

        ax.bar([i - width for i in x], criticos, width, label='Críticos', color=theme.ERROR)
        ax.bar(x, anomalias, width, label='Anomalías', color=theme.WARN)
        ax.bar([i + width for i in x], normales, width, label='Normales', color=theme.OK)

        ax.set_ylabel('Cantidad', color=theme.TEXTO_SUAVE, fontsize=10)
        ax.set_title('Tickets por severidad (última semana)', color=theme.TEXTO, fontsize=12, fontweight='bold')
        ax.set_xticks(list(x))
        ax.set_xticklabels(dias)
        ax.tick_params(axis='both', colors=theme.TEXTO_SUAVE)
        ax.legend(facecolor=theme.SURFACE_ALT, edgecolor=theme.BORDE, labelcolor=theme.TEXTO)
        ax.grid(axis='y', alpha=0.15, color=theme.TEXTO_SUAVE)
        for spine in ax.spines.values():
            spine.set_color(theme.BORDE)

        self.canvas_severidad = FigureCanvasTkAgg(fig, master=self.tab_severidad)
        self.canvas_severidad.draw()
        self.canvas_severidad.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    app = AplicacionMonitor()
    app.mainloop()
