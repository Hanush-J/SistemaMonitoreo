import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import json

# Cambia estos datos por los de tu servidor Ubuntu
DB_HOST = '192.168.68.105'  
DB_USER = 'joshua'   # El usuario de MySQL
DB_PASS = 'password'
DB_NAME = 'sistema_monitoreo'

def conectar_bd():
    """Establece la conexión física con el Ubuntu Server."""
    try:
        conexion = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"[ERROR DE CONEXIÓN] No se pudo conectar a MySQL: {e}")
        return None

def validar_login(username, password):
    """Consulta a la base de datos si el usuario y contraseña coinciden."""
    conexion = conectar_bd()
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            consulta = "SELECT * FROM usuarios WHERE username = %s AND password = %s"
            cursor.execute(consulta, (username, password))
            
            usuario_encontrado = cursor.fetchone()
            
            cursor.close()
            conexion.close()
            
            if usuario_encontrado:
                return True 
            else:
                return False
        except Error as e:
            print(f"[ERROR SQL] Falla al consultar: {e}")
            return False
    return False

# ===== NUEVAS FUNCIONES PARA TICKETS =====

def crear_ticket(severidad, descripcion, interfaz=None, ip_origen=None, puertos=None):
    """
    Crea un nuevo ticket en la base de datos.
    
    Args:
        severidad: 'NORMAL', 'ANOMALIA', 'CRITICO'
        descripcion: Texto del veredicto de la IA
        interfaz: Interfaz de red detectada
        ip_origen: IP origen del tráfico detectado
        puertos: Puertos involucrados (string separado por comas)
    
    Returns:
        id del ticket creado o None si falla
    """
    conexion = conectar_bd()
    if not conexion:
        return None
    
    try:
        cursor = conexion.cursor()
        consulta = """
            INSERT INTO tickets 
            (fecha_hora, severidad, descripcion, interfaz, ip_origen, puertos_involucrados, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        valores = (
            datetime.now(),
            severidad,
            descripcion,
            interfaz,
            ip_origen,
            puertos,
            'PENDIENTE'
        )
        
        cursor.execute(consulta, valores)
        conexion.commit()
        
        id_ticket = cursor.lastrowid
        cursor.close()
        conexion.close()
        
        print(f"[BD] Ticket #{id_ticket} creado exitosamente")
        return id_ticket
        
    except Error as e:
        print(f"[ERROR BD] No se pudo crear ticket: {e}")
        return None

def obtener_tickets_recientes(cantidad=50):
    """Obtiene los últimos N tickets creados."""
    conexion = conectar_bd()
    if not conexion:
        return []
    
    try:
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT * FROM tickets 
            ORDER BY fecha_hora DESC 
            LIMIT %s
        """
        cursor.execute(consulta, (cantidad,))
        tickets = cursor.fetchall()
        cursor.close()
        conexion.close()
        
        return tickets
    except Error as e:
        print(f"[ERROR BD] No se pudieron leer tickets: {e}")
        return []

def obtener_estadisticas_semana():
    """Obtiene estadísticas de tickets para los últimos 7 días (lunes a domingo)."""
    conexion = conectar_bd()
    if not conexion:
        return {}
    
    try:
        cursor = conexion.cursor(dictionary=True)
        
        # Consulta para obtener tickets agrupados por día de la semana
        consulta = """
            SELECT 
                DAYNAME(fecha_hora) as dia_nombre,
                DAYOFWEEK(fecha_hora) as dia_numero,
                COUNT(*) as total_tickets,
                SUM(CASE WHEN severidad='CRITICO' THEN 1 ELSE 0 END) as criticos,
                SUM(CASE WHEN severidad='ANOMALIA' THEN 1 ELSE 0 END) as anomalias,
                SUM(CASE WHEN severidad='NORMAL' THEN 1 ELSE 0 END) as normales
            FROM tickets
            WHERE fecha_hora >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
            GROUP BY DAYOFWEEK(fecha_hora), DAYNAME(fecha_hora)
            ORDER BY dia_numero
        """
        
        cursor.execute(consulta)
        resultados = cursor.fetchall()
        cursor.close()
        conexion.close()
        
        # Formatear resultados
        dias_semana = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dias_esp = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        
        estadisticas = {
            'tickets_por_dia': {},
            'severidad_por_dia': {},
            'total_general': 0
        }
        
        for row in resultados:
            dia_nombre = dias_esp[row['dia_numero'] - 1]
            estadisticas['tickets_por_dia'][dia_nombre] = row['total_tickets']
            estadisticas['severidad_por_dia'][dia_nombre] = {
                'criticos': row['criticos'] or 0,
                'anomalias': row['anomalias'] or 0,
                'normales': row['normales'] or 0
            }
            estadisticas['total_general'] += row['total_tickets']
        
        return estadisticas
        
    except Error as e:
        print(f"[ERROR BD] Error en estadísticas: {e}")
        return {}

def obtener_estadisticas_por_hora():
    """Obtiene estadísticas de tickets por hora del día en la última semana."""
    conexion = conectar_bd()
    if not conexion:
        return {}
    
    try:
        cursor = conexion.cursor(dictionary=True)
        
        consulta = """
            SELECT 
                HOUR(fecha_hora) as hora,
                COUNT(*) as total_tickets,
                SUM(CASE WHEN severidad='CRITICO' THEN 1 ELSE 0 END) as criticos
            FROM tickets
            WHERE fecha_hora >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY HOUR(fecha_hora)
            ORDER BY hora
        """
        
        cursor.execute(consulta)
        resultados = cursor.fetchall()
        cursor.close()
        conexion.close()
        
        estadisticas = {}
        for row in resultados:
            hora_formateada = f"{row['hora']:02d}:00"
            estadisticas[hora_formateada] = {
                'total': row['total_tickets'],
                'criticos': row['criticos'] or 0
            }
        
        return estadisticas
        
    except Error as e:
        print(f"[ERROR BD] Error en estadísticas por hora: {e}")
        return {}

def obtener_ticket_por_id(id_ticket):
    """Obtiene un ticket por su ID."""
    conexion = conectar_bd()
    if not conexion:
        return None

    try:
        cursor = conexion.cursor(dictionary=True)
        consulta = "SELECT * FROM tickets WHERE id_ticket = %s"
        cursor.execute(consulta, (id_ticket,))
        ticket = cursor.fetchone()
        cursor.close()
        conexion.close()
        return ticket
    except Error as e:
        print(f"[ERROR BD] No se pudo obtener ticket: {e}")
        return None

def actualizar_estado_ticket(id_ticket, nuevo_estado):
    """Actualiza el estado de un ticket (PENDIENTE, RESUELTO, IGNORADO)."""
    return actualizar_ticket(id_ticket, estado=nuevo_estado)

def actualizar_ticket(id_ticket, severidad=None, descripcion=None, estado=None,
                      ip_origen=None, puertos_involucrados=None):
    """Actualiza los campos editables de un ticket."""
    campos = {
        'severidad': severidad,
        'descripcion': descripcion,
        'estado': estado,
        'ip_origen': ip_origen,
        'puertos_involucrados': puertos_involucrados,
    }
    campos = {k: v for k, v in campos.items() if v is not None}

    if not campos:
        return False

    conexion = conectar_bd()
    if not conexion:
        return False

    try:
        set_clause = ", ".join(f"{campo} = %s" for campo in campos)
        consulta = f"UPDATE tickets SET {set_clause} WHERE id_ticket = %s"
        valores = list(campos.values()) + [id_ticket]

        cursor = conexion.cursor()
        cursor.execute(consulta, valores)
        conexion.commit()
        cursor.close()
        conexion.close()

        print(f"[BD] Ticket #{id_ticket} actualizado")
        return True
    except Error as e:
        print(f"[ERROR BD] No se pudo actualizar ticket: {e}")
        return False

def registrar_log(tipo_log, mensaje):
    """Registra un evento en la tabla de logs para la consola."""
    conexion = conectar_bd()
    if not conexion:
        return None
    
    try:
        cursor = conexion.cursor()
        consulta = """
            INSERT INTO logs_ejecucion (tipo_log, mensaje)
            VALUES (%s, %s)
        """
        cursor.execute(consulta, (tipo_log, mensaje))
        conexion.commit()
        cursor.close()
        conexion.close()
        
        return True
    except Error as e:
        print(f"[ERROR BD] No se pudo registrar log: {e}")
        return False

def obtener_logs_recientes(cantidad=100):
    """Obtiene los últimos logs de ejecución."""
    conexion = conectar_bd()
    if not conexion:
        return []
    
    try:
        cursor = conexion.cursor(dictionary=True)
        consulta = """
            SELECT * FROM logs_ejecucion 
            ORDER BY fecha_hora DESC 
            LIMIT %s
        """
        cursor.execute(consulta, (cantidad,))
        logs = cursor.fetchall()
        cursor.close()
        conexion.close()
        
        return logs
    except Error as e:
        print(f"[ERROR BD] No se pudieron leer logs: {e}")
        return []

# ----- PRUEBA RÁPIDA -----
if __name__ == "__main__":
    print("Probando conexión al Ubuntu Server...")
    # Cambia por un usuario real
    if validar_login("joshua", "redes2026"):
        print("¡Conexión y Login EXITOSOS!")
        
        # Crear un ticket de prueba
        print("\nCreando ticket de prueba...")
        id_ticket = crear_ticket(
            severidad='CRITICO',
            descripcion='[ALERTA CRITICA DETECTADA] Escaneo masivo de puertos en 192.168.1.100',
            interfaz='eth0',
            ip_origen='192.168.1.100',
            puertos='80,443,22,3306'
        )
        
        if id_ticket:
            print(f"Ticket #{id_ticket} creado correctamente")
            
            # Obtener tickets recientes
            print("\nÚltimos tickets:")
            tickets = obtener_tickets_recientes(5)
            for t in tickets:
                print(f"  - Ticket #{t['id_ticket']}: {t['severidad']} - {t['fecha_hora']}")
            
            # Estadísticas de la semana
            print("\nEstadísticas de la semana:")
            stats = obtener_estadisticas_semana()
            print(f"  Total de tickets: {stats.get('total_general', 0)}")
    else:
        print("Fallo el login: Usuario incorrecto o sin conexión.")
