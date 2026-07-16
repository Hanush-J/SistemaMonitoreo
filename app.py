import customtkinter as ctk
import threading
import time
import queue
from datetime import datetime
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import sys

# Importamos nuestros módulos
import analisis_ia
import database
import port_scanner

# Configuración visual
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORES_SEVERIDAD = {
    "CRITICO": ("red", "red"),
    "ANOMALIA": ("orange", "orange"),
    "NORMAL": ("green", "lime"),
}
COLORES_ESTADO = {
    "PENDIENTE": "yellow",
    "RESUELTO": "lime",
    "IGNORADO": "gray",
}


class VentanaEditarTicket(ctk.CTkToplevel):
    """Ventana modal para editar un ticket existente."""

    def __init__(self, parent, ticket, on_guardar=None):
        super().__init__(parent)
        self.parent_app = parent
        self.ticket = ticket
        self.on_guardar = on_guardar
        self.id_ticket = ticket["id_ticket"]

        self.title(f"Editar Ticket #{self.id_ticket}")
        self.geometry("650x640")
        self.minsize(650, 640)
        self.resizable(False, False)
        self.configure(fg_color="#1a1a1a")

        self.transient(parent)
        self.wait_visibility()
        self.grab_set()
        self.focus_force()

        self._construir_formulario()
        ctk.CTkLabel(self.frame_controles, text="Modo de Escaneo:", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(5, 0))
        self.combo_modo_escaneo = ctk.CTkComboBox(
            self.frame_controles, 
            values=["Rango Completo", "Puertos Comunes VIP"]
        )
        self.combo_modo_escaneo.pack(pady=5, padx=15, fill="x")
        self.combo_modo_escaneo.set("Puertos Comunes VIP") # Opción por defecto

    def _construir_formulario(self):
        ticket = self.ticket
        fecha = ticket.get("fecha_hora", "")
        if hasattr(fecha, "strftime"):
            fecha = fecha.strftime("%Y-%m-%d %H:%M:%S")

        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=0, pady=0)

        ctk.CTkLabel(
            contenedor,
            text=f"🎫 Ticket #{ticket['id_ticket']}",
            font=("Arial", 18, "bold"),
            text_color="cyan",
        ).pack(pady=(15, 5))

        info_frame = ctk.CTkFrame(contenedor, fg_color="#2b2b2b")
        info_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(
            info_frame,
            text=f"Fecha: {fecha}  |  Interfaz: {ticket.get('interfaz') or 'N/A'}",
            font=("Arial", 10),
            text_color="gray",
        ).pack(anchor="w", padx=12, pady=8)

        form = ctk.CTkScrollableFrame(contenedor, fg_color="transparent", height=380)
        form.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(form, text="Severidad:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.combo_severidad = ctk.CTkComboBox(
            form, values=["CRITICO", "ANOMALIA", "NORMAL"], width=200
        )
        self.combo_severidad.set(ticket.get("severidad", "ANOMALIA"))
        self.combo_severidad.pack(anchor="w", pady=(2, 10))

        ctk.CTkLabel(form, text="Estado:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.combo_estado = ctk.CTkComboBox(
            form, values=["PENDIENTE", "RESUELTO", "IGNORADO"], width=200
        )
        self.combo_estado.set(ticket.get("estado", "PENDIENTE"))
        self.combo_estado.pack(anchor="w", pady=(2, 10))

        ctk.CTkLabel(form, text="IP Origen:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.entrada_ip = ctk.CTkEntry(form, placeholder_text="ej: 192.168.1.100")
        self.entrada_ip.insert(0, ticket.get("ip_origen") or "")
        self.entrada_ip.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(form, text="Puertos involucrados:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.entrada_puertos = ctk.CTkEntry(form, placeholder_text="ej: 80,443,22")
        self.entrada_puertos.insert(0, ticket.get("puertos_involucrados") or "")
        self.entrada_puertos.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(form, text="Descripción:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.text_descripcion = ctk.CTkTextbox(form, height=150, font=("Courier", 10))
        self.text_descripcion.insert("1.0", ticket.get("descripcion", ""))
        self.text_descripcion.pack(fill="x", pady=(2, 10))

        footer = ctk.CTkFrame(contenedor, fg_color="#2b2b2b", corner_radius=0)
        footer.pack(fill="x", side="bottom", padx=0, pady=0)

        self.label_estado_guardado = ctk.CTkLabel(
            footer, text="", font=("Arial", 11, "bold")
        )
        self.label_estado_guardado.pack(pady=(12, 6))

        btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.btn_guardar = ctk.CTkButton(
            btn_frame,
            text="💾 Guardar cambios",
            width=180,
            height=36,
            font=("Arial", 13, "bold"),
            fg_color="green",
            hover_color="darkgreen",
            command=self._guardar,
        )
        self.btn_guardar.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Cerrar sin guardar",
            width=150,
            height=36,
            fg_color="gray",
            hover_color="#555555",
            command=self.destroy,
        ).pack(side="left")

    def _guardar(self):
        descripcion = self.text_descripcion.get("1.0", "end").strip()
        if not descripcion:
            self.label_estado_guardado.configure(
                text="✗ La descripción no puede estar vacía",
                text_color="red",
            )
            return

        self.btn_guardar.configure(state="disabled", text="Guardando...")
        self.label_estado_guardado.configure(text="Guardando en base de datos...", text_color="cyan")
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

        self.btn_guardar.configure(state="normal", text="💾 Guardar cambios")

        if exito:
            self.label_estado_guardado.configure(
                text="✓ Ticket guardado correctamente en la base de datos",
                text_color="lime",
            )
            if hasattr(self.parent_app, "agregar_log"):
                self.parent_app.agregar_log(
                    "SUCCESS",
                    f"Ticket #{self.id_ticket} actualizado y guardado",
                )
            if self.on_guardar:
                self.on_guardar()
        else:
            self.label_estado_guardado.configure(
                text="✗ No se pudo guardar. Verifica la conexión a la base de datos",
                text_color="red",
            )
            if hasattr(self.parent_app, "agregar_log"):
                self.parent_app.agregar_log(
                    "ERROR",
                    f"No se pudo guardar el ticket #{self.id_ticket}",
                )


class AplicacionMonitor(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sistema Proactivo de Seguridad LAN - Integradora")
        self.geometry("1400x900")
        
        # Variables de control
        self.monitoreando = False
        self.buzon_reportes = queue.Queue() 
        self.logs_buffer = deque(maxlen=100)  # Últimos 100 logs
        self.ventanas_editor_abiertas = {}
        
        # Configuración de escaneo de puertos
        self.puertos_inicio = 1
        self.puertos_fin = 1000
        self.modo_escaneo = "rango"  # 'rango' o 'comunes'

        # --- PANEL IZQUIERDO (Controles) ---
        self.frame_controles = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color="#1a1a1a")
        self.frame_controles.pack(side="left", fill="y", padx=0, pady=0)
        
        self.etiqueta_titulo = ctk.CTkLabel(
            self.frame_controles, 
            text="🛡️ Panel de Control", 
            font=("Arial", 18, "bold")
        )
        self.etiqueta_titulo.pack(pady=20, padx=15)

        # --- Sección de Análisis de Tráfico ---
        self.label_trafico = ctk.CTkLabel(
            self.frame_controles, 
            text="Análisis de Tráfico", 
            font=("Arial", 12, "bold"),
            text_color="cyan"
        )
        self.label_trafico.pack(pady=(15, 10), padx=15)

        self.btn_iniciar = ctk.CTkButton(
            self.frame_controles, 
            text="▶ Iniciar Escaneo", 
            fg_color="green", 
            hover_color="darkgreen", 
            command=self.arrancar_sistema
        )
        self.btn_iniciar.pack(pady=8, padx=15, fill="x")

        self.btn_detener = ctk.CTkButton(
            self.frame_controles, 
            text="⏹ Detener Sistema", 
            fg_color="red", 
            hover_color="darkred", 
            state="disabled", 
            command=self.detener_sistema
        )
        self.btn_detener.pack(pady=8, padx=15, fill="x")

        # --- Sección de Escaneo de Puertos ---
        self.label_puertos = ctk.CTkLabel(
            self.frame_controles, 
            text="Escaneo de Puertos", 
            font=("Arial", 12, "bold"),
            text_color="orange"
        )
        self.label_puertos.pack(pady=(20, 10), padx=15)

        # --- Sección de Escaneo de Puertos ---
        self.label_puertos = ctk.CTkLabel(
            self.frame_controles, 
            text="Escaneo de Puertos", 
            font=("Arial", 12, "bold"),
            text_color="orange"
        )
        self.label_puertos.pack(pady=(20, 10), padx=15)

        # 1. Entrada de Red / Host
        ctk.CTkLabel(self.frame_controles, text="Red / Host (IP):", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(5, 0))
        self.entrada_host = ctk.CTkEntry(
            self.frame_controles, 
            placeholder_text="ej: 192.168.1.1 o 127.0.0.1"
        )
        self.entrada_host.pack(pady=5, padx=15, fill="x")

        # 2. Contenedor Scrollable para los Checkboxes
        ctk.CTkLabel(self.frame_controles, text="Selecciona puertos a auditar:", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(10, 0))
        self.frame_checkboxes = ctk.CTkScrollableFrame(self.frame_controles, height=160, fg_color="#1a1a1a")
        self.frame_checkboxes.pack(pady=5, padx=15, fill="x")

        # Lista de puertos VIP y diccionario para guardar su estado (Seleccionado o no)
        self.puertos_disponibles = [
            (21, "TCP", "FTP"), (22, "TCP", "SSH"), (23, "TCP", "Telnet"),
            (25, "TCP", "SMTP"), (53, "UDP", "DNS"), (67, "UDP", "DHCP"),
            (69, "UDP", "TFTP"), (80, "TCP", "HTTP"), (443, "TCP", "HTTPS"),
            (3306, "TCP", "MySQL"), (3389, "TCP", "RDP")
        ]
        self.variables_checkbox = {}

        # Generar los checkboxes dinámicamente
        for puerto, protocolo, servicio in self.puertos_disponibles:
            var = ctk.BooleanVar(value=False)
            self.variables_checkbox[(puerto, protocolo)] = var
            chk = ctk.CTkCheckBox(
                self.frame_checkboxes,
                text=f"{puerto} ({servicio})",
                variable=var,
                font=("Arial", 11),
                checkbox_height=18,
                checkbox_width=18
            )
            chk.pack(anchor="w", pady=4, padx=5)
        
        # Botón de escaneo
        self.btn_escaneo_puertos = ctk.CTkButton(
            self.frame_controles,
            text="🔍 Escanear Puertos",
            fg_color="#FF6B00",
            hover_color="#FF8C00",
            command=self.iniciar_escaneo_puertos
        )
        self.btn_escaneo_puertos.pack(pady=8, padx=15, fill="x")

        # Progreso escaneo
        self.progreso_escaneo = ctk.CTkProgressBar(self.frame_controles)
        self.progreso_escaneo.pack(pady=8, padx=15, fill="x")
        self.progreso_escaneo.set(0)

        self.label_progreso = ctk.CTkLabel(
            self.frame_controles, 
            text="", 
            font=("Arial", 9)
        )
        self.label_progreso.pack(pady=2, padx=15)

        # Estado del sistema
        self.etiqueta_estado_sistema = ctk.CTkLabel(
            self.frame_controles, 
            text="⚫ Motor: APAGADO", 
            text_color="gray",
            font=("Arial", 11, "bold")
        )
        self.etiqueta_estado_sistema.pack(side="bottom", pady=20)

        # --- PANEL PRINCIPAL (Centro y Abajo) ---
        self.frame_principal = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_principal.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        # --- PANEL SUPERIOR: Semáforo ---
        self.frame_semaforo = ctk.CTkFrame(self.frame_principal, fg_color="#2b2b2b", corner_radius=10)
        self.frame_semaforo.pack(fill="x", pady=(0, 10))

        self.etiqueta_semaforo = ctk.CTkLabel(
            self.frame_semaforo,
            text="🔴 ESTADO: EN ESPERA",
            font=("Arial", 32, "bold"),
            text_color="gray"
        )
        self.etiqueta_semaforo.pack(pady=15)

        # --- PANEL CENTRAL: Consola de ejecución ---
        self.frame_consola = ctk.CTkFrame(self.frame_principal, fg_color="#1a1a1a", corner_radius=10)
        self.frame_consola.pack(fill="both", expand=True, pady=(0, 10))

        self.label_consola = ctk.CTkLabel(
            self.frame_consola,
            text="📋 Consola de Ejecución",
            font=("Arial", 13, "bold"),
            text_color="lime"
        )
        self.label_consola.pack(anchor="w", padx=15, pady=(10, 5))

        self.textbox_consola = ctk.CTkTextbox(
            self.frame_consola,
            fg_color="#0a0a0a",
            text_color="lime",
            font=("Courier", 9)
        )
        self.textbox_consola.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.textbox_consola.configure(state="disabled")

        # --- PANEL INFERIOR: Tickets ---
        self.frame_tickets_section = ctk.CTkFrame(self.frame_principal, fg_color="#2b2b2b", corner_radius=10)
        self.frame_tickets_section.pack(fill="both", expand=False, pady=0)

        # Tabs para tickets y gráficas
        self.tabview = ctk.CTkTabview(self.frame_tickets_section, fg_color="#2b2b2b", height=280)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: Tickets en vivo
        self.tab_tickets = self.tabview.add("🎫 Tickets Activos")
        self.frame_tickets = ctk.CTkScrollableFrame(
            self.tab_tickets,
            fg_color="#1a1a1a",
            label_text=""
        )
        self.frame_tickets.pack(fill="both", expand=True, padx=0, pady=0)

        # Tab 2: Gestión de tickets (desde BD)
        self.tab_gestion = self.tabview.add("📋 Gestión de Tickets")
        self._construir_tab_gestion()

        # Tab 3: Gráficas (pestañas internas)
        self.tab_graficas = self.tabview.add("📊 Estadísticas Semanales")
        self.tabview_graficas = ctk.CTkTabview(self.tab_graficas, fg_color="#1a1a1a")
        self.tabview_graficas.pack(fill="both", expand=True, padx=0, pady=0)

        # Sub-tab: Total tickets por día
        self.tab_total = self.tabview_graficas.add("Total Tickets/Día")
        self.canvas_total = None

        # Sub-tab: Tickets por severidad
        self.tab_severidad = self.tabview_graficas.add("Severidad/Día")
        self.canvas_severidad = None

        self.cargar_tickets_gestion()

    def _construir_tab_gestion(self):
        """Construye la pestaña de gestión de tickets."""
        header = ctk.CTkFrame(self.tab_gestion, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=(5, 0))

        ctk.CTkLabel(
            header,
            text="Historial completo de tickets",
            font=("Arial", 12, "bold"),
            text_color="cyan",
        ).pack(side="left")

        self.label_total_tickets = ctk.CTkLabel(
            header, text="0 tickets", font=("Arial", 10), text_color="gray"
        )
        self.label_total_tickets.pack(side="left", padx=15)

        ctk.CTkButton(
            header,
            text="🔄 Actualizar",
            width=100,
            command=self.cargar_tickets_gestion,
        ).pack(side="right", padx=5)

        filtros = ctk.CTkFrame(self.tab_gestion, fg_color="transparent")
        filtros.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(filtros, text="Filtrar por estado:", font=("Arial", 10)).pack(side="left", padx=(0, 5))
        self.filtro_estado = ctk.CTkComboBox(
            filtros,
            values=["TODOS", "PENDIENTE", "RESUELTO", "IGNORADO"],
            width=140,
            command=lambda _: self.cargar_tickets_gestion(),
        )
        self.filtro_estado.set("TODOS")
        self.filtro_estado.pack(side="left")

        self.frame_gestion_lista = ctk.CTkScrollableFrame(
            self.tab_gestion,
            fg_color="#1a1a1a",
            label_text="",
        )
        self.frame_gestion_lista.pack(fill="both", expand=True, padx=0, pady=5)

    def _obtener_colores_severidad(self, severidad):
        return COLORES_SEVERIDAD.get(severidad, ("gray", "white"))

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
                self.frame_gestion_lista,
                text="No hay tickets registrados",
                font=("Arial", 11),
                text_color="gray",
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
        color_estado = COLORES_ESTADO.get(estado, "white")

        fila = ctk.CTkFrame(
            self.frame_gestion_lista,
            border_width=1,
            border_color=color_borde,
            fg_color="#2b2b2b",
            corner_radius=6,
        )
        fila.pack(fill="x", padx=6, pady=4)

        contenido = ctk.CTkFrame(fila, fg_color="transparent")
        contenido.pack(fill="x", padx=10, pady=8)

        cabecera = ctk.CTkFrame(contenido, fg_color="transparent")
        cabecera.pack(fill="x")

        ctk.CTkLabel(
            cabecera,
            text=f"#{id_ticket:04d} | {self._formatear_fecha(ticket.get('fecha_hora'))}",
            font=("Arial", 10, "bold"),
            text_color=color_texto,
        ).pack(side="left")

        ctk.CTkLabel(
            cabecera,
            text=f"[{severidad}]",
            font=("Arial", 10, "bold"),
            text_color=color_texto,
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            cabecera,
            text=f"Estado: {estado}",
            font=("Arial", 10),
            text_color=color_estado,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            cabecera,
            text="✏️ Editar",
            width=80,
            height=24,
            font=("Arial", 10),
            command=lambda tid=id_ticket: self._abrir_editor_ticket(tid),
        ).pack(side="right")

        descripcion = ticket.get("descripcion", "")
        if len(descripcion) > 120:
            descripcion = descripcion[:120] + "..."

        ctk.CTkLabel(
            contenido,
            text=descripcion,
            font=("Courier", 9),
            justify="left",
            anchor="w",
            text_color="white",
        ).pack(fill="x", pady=(4, 0))

        extras = []
        if ticket.get("ip_origen"):
            extras.append(f"IP: {ticket['ip_origen']}")
        if ticket.get("puertos_involucrados"):
            extras.append(f"Puertos: {ticket['puertos_involucrados']}")
        if extras:
            ctk.CTkLabel(
                contenido,
                text=" | ".join(extras),
                font=("Arial", 9),
                text_color="gray",
            ).pack(anchor="w", pady=(2, 0))

    def agregar_log(self, tipo, mensaje):
        """Agrega un mensaje a la consola en tiempo real."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Colores según tipo
        colores = {
            "INFO": "[azul]",
            "SUCCESS": "[verde]",
            "WARNING": "[amarillo]",
            "ERROR": "[rojo]"
        }
        
        log_mensaje = f"[{timestamp}] {tipo}: {mensaje}\n"
        self.logs_buffer.append((tipo, mensaje, timestamp))
        
        # Actualizar textbox de forma segura
        self.after(0, self._actualizar_consola, log_mensaje)
        
        # Guardar en BD
        database.registrar_log(tipo, mensaje)

    def _actualizar_consola(self, mensaje):
        """Actualiza la consola (debe ser llamado desde el hilo principal)."""
        # --- NUEVA LÍNEA DE PROTECCIÓN ---
        if not hasattr(self, 'textbox_consola') or not self.textbox_consola.winfo_exists():
            return
            
        self.textbox_consola.configure(state="normal")
        self.textbox_consola.insert("end", mensaje)
        self.textbox_consola.see("end")
        self.textbox_consola.configure(state="disabled")

    def actualizar_semaforo(self, texto, color):
        """Actualiza el semáforo de forma segura."""
        # --- NUEVA LÍNEA DE PROTECCIÓN ---
        if not hasattr(self, 'etiqueta_semaforo') or not self.etiqueta_semaforo.winfo_exists():
            return
            
        emojis = {"green": "🟢", "red": "🔴", "orange": "🟠", "gray": "⚫", "cyan": "🔵"}
        emoji = emojis.get(color, "⚫")
        self.etiqueta_semaforo.configure(text=f"{emoji} {texto}", text_color=color)

    def crear_ticket(self, severidad, descripcion, ip_origen=None, puertos=None):
        """Genera un nuevo ticket y lo guarda en BD."""
        hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        interfaz = analisis_ia.detectar_interfaz_automatica()
        id_ticket = database.crear_ticket(
            severidad=severidad,
            descripcion=descripcion,
            interfaz=interfaz,
            ip_origen=ip_origen,
            puertos=puertos,
        )

        if not id_ticket:
            self.agregar_log("ERROR", "No se pudo guardar el ticket en BD")
            return

        color_borde, color_texto = self._obtener_colores_severidad(severidad)

        ticket_frame = ctk.CTkFrame(
            self.frame_tickets,
            border_width=2,
            border_color=color_borde,
            fg_color="#2b2b2b",
            corner_radius=8,
        )
        ticket_frame.pack(fill="x", padx=8, pady=6)

        cabecera_frame = ctk.CTkFrame(ticket_frame, fg_color="transparent")
        cabecera_frame.pack(fill="x", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            cabecera_frame,
            text=f"#{id_ticket:04d} | {hora_actual} | [{severidad}]",
            font=("Arial", 11, "bold"),
            text_color=color_texto,
        ).pack(side="left")

        ctk.CTkButton(
            cabecera_frame,
            text="✏️",
            width=30,
            height=22,
            font=("Arial", 10),
            command=lambda tid=id_ticket: self._abrir_editor_ticket(tid),
        ).pack(side="right")

        ctk.CTkLabel(
            ticket_frame,
            text=descripcion,
            font=("Courier", 9),
            justify="left",
            wraplength=500,
            text_color="white",
        ).pack(anchor="w", padx=12, pady=(0, 8))

        self.after(100, self.refrescar_graficas)
        self.after(100, self.cargar_tickets_gestion)

    def arrancar_sistema(self):
        """Inicia el monitoreo de tráfico."""
        self.monitoreando = True
        self.btn_iniciar.configure(state="disabled")
        self.btn_detener.configure(state="normal")
        self.etiqueta_estado_sistema.configure(text="🟢 Motor: ESCANEANDO...", text_color="green")
        self.actualizar_semaforo("ESTADO: ANALIZANDO RED", "green")
        
        self.agregar_log("INFO", "Sistema iniciado - Escaneando tráfico de red")
        
        hilo_captura = threading.Thread(target=self.trabajador_sniffer, daemon=True)
        hilo_captura.start()

        hilo_ia = threading.Thread(target=self.trabajador_inteligencia, daemon=True)
        hilo_ia.start()

    def detener_sistema(self):
        """Detiene el monitoreo."""
        self.monitoreando = False
        self.btn_detener.configure(state="disabled")
        self.etiqueta_estado_sistema.configure(text="🟠 Motor: DETENIENDO...", text_color="orange")
        self.actualizar_semaforo("ESTADO: APAGANDO", "orange")
        self.agregar_log("INFO", "Sistema detenido por el usuario")

    def trabajador_sniffer(self):
        """HILO 1: Captura tráfico en vivo."""
        interfaz = analisis_ia.detectar_interfaz_automatica()
        if not interfaz:
            self.after(0, self.actualizar_semaforo, "ERROR: SIN TARJETA RED", "red")
            self.after(0, self.agregar_log, "ERROR", "No se detectó interfaz de red")
            return

        self.after(0, self.agregar_log, "SUCCESS", f"Interfaz detectada: {interfaz}")

        while self.monitoreando:
            reporte = analisis_ia.capturar_trafico_vivo(interfaz, tiempo_ventana=5)

            if not self.monitoreando:
                break
            
            if reporte:
                self.after(0, self.agregar_log, "INFO", f"Tráfico capturado - Analizando...")
                self.buzon_reportes.put(reporte)
            else:
                self.after(0, self.agregar_log, "WARNING", "Sin tráfico IP detectado")

        self.after(0, self.restaurar_botones)

    def trabajador_inteligencia(self):
        """HILO 2: Procesa reportes y consulta IA."""
        while self.monitoreando:
            try:
                reporte_nuevo = self.buzon_reportes.get(timeout=2)
                
                self.after(0, self.actualizar_semaforo, "IA ANALIZANDO...", "cyan")
                self.after(0, self.agregar_log, "INFO", "Consultando IA para análisis...")
                
                veredicto = analisis_ia.consultar_ia_local(reporte_nuevo, modelo="phi3")
                
                if veredicto:
                    # Convertimos todo a mayúsculas para comparar más fácil
                    veredicto_mayus = veredicto.upper()
                    self.after(0, self.agregar_log, "INFO", f"IA: {veredicto[:80]}...")
                    
                    # 🟢 TRÁFICO NORMAL (Buscamos con acento y sin acento por si la IA se equivoca)
                    if "[TRÁFICO NORMAL]" in veredicto_mayus or "[TRAFICO NORMAL]" in veredicto_mayus:
                        self.after(0, self.actualizar_semaforo, "ESTADO: NORMAL", "green")
                        self.after(0, self.agregar_log, "SUCCESS", "Tráfico normal detectado")
                        # 🚫 No llamamos a self.crear_ticket aquí. La lista se queda limpia.
                    
                    # 🔴 ALERTA CRÍTICA
                    elif "[ALERTA CRITICA DETECTADA]" in veredicto_mayus or "[ALERTA CRÍTICA" in veredicto_mayus:
                        self.after(0, self.actualizar_semaforo, "ESTADO: ⚠️ CRÍTICO", "red")
                        self.after(0, self.crear_ticket, "CRITICO", veredicto, None, None)
                        self.after(0, self.agregar_log, "ERROR", "ALERTA CRÍTICA CREADA")
                    
                    # 🟠 ANOMALÍA
                    elif "[ANOMALIA]" in veredicto_mayus or "[ANOMALÍA]" in veredicto_mayus:
                        self.after(0, self.actualizar_semaforo, "ESTADO: ANOMALÍA", "orange")
                        self.after(0, self.crear_ticket, "ANOMALIA", veredicto, None, None)
                        self.after(0, self.agregar_log, "WARNING", "Anomalía detectada - Ticket creado")
                        
                    # CASO DESCONOCIDO (Si la IA responde algo que no está en las reglas)
                    else:
                        self.after(0, self.actualizar_semaforo, "ESTADO: DESCONOCIDO", "orange")
                        self.after(0, self.crear_ticket, "ANOMALIA", veredicto, None, None)
                        
            except queue.Empty:
                continue

    def iniciar_escaneo_puertos(self):
        """Inicia escaneo de puertos en hilo separado."""
        host = self.entrada_host.get().strip()
        
        if not host:
            self.agregar_log("ERROR", "Ingresa un host válido (IP)")
            return
        
        try:
            puerto_inicio = int(self.entrada_puerto_inicio.get() or "1")
            puerto_fin = int(self.entrada_puerto_fin.get() or "1000")
            
            if puerto_inicio < 1 or puerto_fin > 65535 or puerto_inicio > puerto_fin:
                self.agregar_log("ERROR", "Rango de puertos inválido")
                return
        except ValueError:
            self.agregar_log("ERROR", "Los puertos deben ser números")
            return

        self.btn_escaneo_puertos.configure(state="disabled")
        self.agregar_log("INFO", f"Iniciando escaneo de puertos {puerto_inicio}-{puerto_fin} en {host}")

        def callback_progreso(actual, total):
            porcentaje = actual / total
            self.after(0, self.progreso_escaneo.set, porcentaje)
            self.after(0, self.label_progreso.configure, {"text": f"{actual}/{total} puertos"})

        def callback_resultado(puerto, estado):
            self.after(0, self.agregar_log, "SUCCESS", f"Puerto {puerto}: {estado}")

        hilo_escaneo = threading.Thread(
            target=self._ejecutar_escaneo,
            args=(host, puerto_inicio, puerto_fin, callback_progreso, callback_resultado),
            daemon=True
        )
        hilo_escaneo.start()

    def _ejecutar_escaneo(self, host, inicio, fin, callback_prog, callback_res):
        """Ejecuta el escaneo en hilo separado."""
        
        modo = self.combo_modo_escaneo.get()
        
        if modo == "Puertos Comunes VIP":
            resultado = port_scanner.escanear_puertos_predeterminados(host, callback_prog, callback_res)
        else:
            # Modo rango
            resultado = port_scanner.escanear_puertos(host, inicio, fin, callback_prog, callback_res)
            
        if resultado:
            self.after(0, self.agregar_log, "SUCCESS", 
                f"Escaneo completado: {resultado['total_abiertos']} puertos abiertos")
        # ... resto del código sin tocar ...

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
        self.etiqueta_estado_sistema.configure(text="⚫ Motor: EN REPOSO", text_color="gray")
        self.actualizar_semaforo("ESTADO: EN ESPERA", "gray")

    def refrescar_graficas(self):
        """Actualiza las gráficas con datos de la BD."""
        estadisticas = database.obtener_estadisticas_semana()
        
        if not estadisticas or not estadisticas.get('tickets_por_dia'):
            return
        
        # Gráfica 1: Total de tickets por día
        self._dibujar_grafica_total(estadisticas)
        
        # Gráfica 2: Tickets por severidad
        self._dibujar_grafica_severidad(estadisticas)

    def _dibujar_grafica_total(self, estadisticas):
        """Dibuja gráfica de total de tickets por día."""
        # Limpiar canvas anterior
        if self.canvas_total:
            self.canvas_total.get_tk_widget().destroy()

        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        tickets = [estadisticas['tickets_por_dia'].get(dia, 0) for dia in dias]

        fig = Figure(figsize=(10, 3.5), dpi=80, facecolor='#1a1a1a', edgecolor='none')
        ax = fig.add_subplot(111, facecolor='#2b2b2b')

        bars = ax.bar(dias, tickets, color='#00FFFF', edgecolor='white', linewidth=1.5)
        
        # Colores dinámicos
        for i, bar in enumerate(bars):
            if tickets[i] > 0:
                bar.set_color('#FFD700')  # Oro si hay tickets
        
        ax.set_ylabel('Cantidad de Tickets', color='white', fontsize=10)
        ax.set_xlabel('Día de la Semana', color='white', fontsize=10)
        ax.set_title('Tickets Detectados (Última Semana)', color='white', fontsize=12, fontweight='bold')
        ax.tick_params(axis='both', colors='white')
        ax.grid(axis='y', alpha=0.3, color='white')

        self.canvas_total = FigureCanvasTkAgg(fig, master=self.tab_total)
        self.canvas_total.draw()
        self.canvas_total.get_tk_widget().pack(fill="both", expand=True)

    def _dibujar_grafica_severidad(self, estadisticas):
        """Dibuja gráfica de tickets por severidad."""
        if self.canvas_severidad:
            self.canvas_severidad.get_tk_widget().destroy()

        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        criticos = []
        anomalias = []
        normales = []

        for dia in dias:
            sev = estadisticas['severidad_por_dia'].get(dia, {})
            criticos.append(sev.get('criticos', 0))
            anomalias.append(sev.get('anomalias', 0))
            normales.append(sev.get('normales', 0))

        fig = Figure(figsize=(10, 3.5), dpi=80, facecolor='#1a1a1a', edgecolor='none')
        ax = fig.add_subplot(111, facecolor='#2b2b2b')

        x = range(len(dias))
        width = 0.25

        ax.bar([i - width for i in x], criticos, width, label='Críticos', color='#FF4444', edgecolor='white')
        ax.bar(x, anomalias, width, label='Anomalías', color='#FF8800', edgecolor='white')
        ax.bar([i + width for i in x], normales, width, label='Normales', color='#44FF44', edgecolor='white')

        ax.set_ylabel('Cantidad', color='white', fontsize=10)
        ax.set_xlabel('Día de la Semana', color='white', fontsize=10)
        ax.set_title('Tickets por Severidad (Última Semana)', color='white', fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(dias)
        ax.tick_params(axis='both', colors='white')
        ax.legend(facecolor='#2b2b2b', edgecolor='white', labelcolor='white')
        ax.grid(axis='y', alpha=0.3, color='white')

        self.canvas_severidad = FigureCanvasTkAgg(fig, master=self.tab_severidad)
        self.canvas_severidad.draw()
        self.canvas_severidad.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    app = AplicacionMonitor()
    app.mainloop()
