import time
from scapy.all import IP, TCP, UDP, sr1, conf
from collections import Counter

# Configurar timeout de Scapy para escaneo más rápido
conf.verb = 0  # Sin verbosidad

def escanear_puertos(host, puerto_inicio, puerto_fin, callback_progreso=None, callback_resultado=None):
    """
    Escanea un rango de puertos TCP en un host específico.
    
    Args:
        host: IP a escanear
        puerto_inicio: Puerto inicial del rango
        puerto_fin: Puerto final del rango
        callback_progreso: Función que recibe (puerto_actual, total_puertos) para actualizar UI
        callback_resultado: Función que recibe (puerto, estado) cuando encuentra un puerto abierto
    
    Returns:
        dict con puertos abiertos y cerrados
    """
    puertos_abiertos = []
    puertos_cerrados = []
    total_puertos = puerto_fin - puerto_inicio + 1
    
    print(f"\n[ESCANEO] Iniciando escaneo de {host} puertos {puerto_inicio}-{puerto_fin}")
    print(f"[ESCANEO] Total de puertos a verificar: {total_puertos}")
    
    try:
        for puerto in range(puerto_inicio, puerto_fin + 1):
            # Crear paquete SYN (TCP)
            paquete = IP(dst=host) / TCP(dport=puerto, flags="S")
            
            # Enviar y esperar respuesta con timeout corto
            respuesta = sr1(paquete, timeout=0.5, verbose=False)
            
            if respuesta is not None:
                # Verificar si es SYN-ACK (puerto abierto)
                if respuesta.haslayer(TCP) and respuesta[TCP].flags == "SA":
                    puertos_abiertos.append(puerto)
                    if callback_resultado:
                        callback_resultado(puerto, "ABIERTO (TCP)")
                else:
                    puertos_cerrados.append(puerto)
            else:
                puertos_cerrados.append(puerto)
            
            # Llamar callback de progreso
            if callback_progreso:
                progreso = puerto - puerto_inicio + 1
                callback_progreso(progreso, total_puertos)
            
            # Pequeña pausa para no saturar la red local
            time.sleep(0.01)
    
    except PermissionError:
        print("\n[ERROR] Requiere permisos de administrador (sudo)")
        return None
    except Exception as e:
        print(f"\n[ERROR ESCANEO] {str(e)}")
        return None
    
    resultado = {
        "host": host,
        "puertos_abiertos": puertos_abiertos,
        "puertos_cerrados": puertos_cerrados,
        "total_abiertos": len(puertos_abiertos),
        "total_cerrados": len(puertos_cerrados)
    }
    
    return resultado


def escanear_puertos_predeterminados(host, callback_progreso=None, callback_resultado=None):
    """Escanea puertos conocidos comúnmente (TCP y UDP clave para la infraestructura)."""
    
    # Formato de la tupla: (Puerto, "Protocolo")
    puertos_comunes = [
        (20, "TCP"), (21, "TCP"),      # FTP
        (22, "TCP"),                   # SSH
        (23, "TCP"),                   # Telnet
        (25, "TCP"), (465, "TCP"),     # SMTP
        (53, "TCP"), (53, "UDP"),      # DNS (Soporta ambos)
        (67, "UDP"), (68, "UDP"),      # DHCP (Servidor y Cliente)
        (69, "UDP"),                   # TFTP
        (80, "TCP"), (443, "TCP"),     # HTTP/HTTPS
        (110, "TCP"), (143, "TCP"),    # POP3/IMAP
        (445, "TCP"),                  # SMB
        (3306, "TCP"),                 # MySQL
        (3389, "TCP"),                 # RDP
        (8080, "TCP"), (8443, "TCP")   # Web alternativos
    ]
    
    puertos_abiertos = []
    
    print(f"\n[ESCANEO] Escaneando {len(puertos_comunes)} puertos conocidos VIP en {host}")
    
    try:
        for idx, (puerto, protocolo) in enumerate(puertos_comunes):
            if protocolo == "TCP":
                paquete = IP(dst=host) / TCP(dport=puerto, flags="S")
            else:
                # Si el protocolo en la lista es UDP, armamos un paquete UDP (Para DHCP, TFTP, etc)
                paquete = IP(dst=host) / UDP(dport=puerto)
                
            respuesta = sr1(paquete, timeout=0.5, verbose=False)
            
            if respuesta is not None:
                # Si es TCP, verificamos la bandera SYN-ACK
                if protocolo == "TCP" and respuesta.haslayer(TCP) and respuesta[TCP].flags == "SA":
                    puertos_abiertos.append(puerto)
                    if callback_resultado:
                        callback_resultado(puerto, f"ABIERTO ({protocolo})")
                        
                # Si es UDP y obtenemos cualquier respuesta directa en la capa UDP, lo damos por activo
                elif protocolo == "UDP" and respuesta.haslayer(UDP):
                    puertos_abiertos.append(puerto)
                    if callback_resultado:
                        callback_resultado(puerto, f"ABIERTO ({protocolo})")
            
            if callback_progreso:
                callback_progreso(idx + 1, len(puertos_comunes))
            
            time.sleep(0.01)
            
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return None
        
    return {
        "host": host,
        "puertos_abiertos": puertos_abiertos,
        "total_abiertos": len(puertos_abiertos)
    }


def obtener_servicios_por_puerto(puertos):
    """Retorna nombres de servicios comunes para mostrar en la interfaz gráfica."""
    servicios = {
        20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "Telnet",
        25: "SMTP", 53: "DNS", 67: "DHCP Server", 68: "DHCP Client",
        69: "TFTP", 80: "HTTP", 110: "POP3", 143: "IMAP",
        443: "HTTPS", 445: "SMB", 465: "SMTP Seguro",
        587: "SMTP Alternativo", 993: "IMAPS", 995: "POP3S",
        3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
        8080: "HTTP Alternativo", 8443: "HTTPS Alternativo",
        27017: "MongoDB", 6379: "Redis"
    }
    
    return {puerto: servicios.get(puerto, "Desconocido") for puerto in puertos}


def escanear_puertos_personalizados(host, lista_puertos, callback_progreso=None, callback_resultado=None):
    """
    Escanea una lista específica de puertos y protocolos seleccionados por el usuario.
    """
    puertos_abiertos = []
    total_puertos = len(lista_puertos)
    
    print(f"\n[ESCANEO] Auditando {total_puertos} puertos personalizados en {host}")
    
    try:
        for idx, (puerto, protocolo) in enumerate(lista_puertos):
            if protocolo == "TCP":
                paquete = IP(dst=host) / TCP(dport=puerto, flags="S")
            else:
                paquete = IP(dst=host) / UDP(dport=puerto)
                
            respuesta = sr1(paquete, timeout=0.5, verbose=False)
            
            if respuesta is not None:
                if protocolo == "TCP" and respuesta.haslayer(TCP) and respuesta[TCP].flags == "SA":
                    puertos_abiertos.append(puerto)
                    if callback_resultado:
                        callback_resultado(puerto, f"ABIERTO ({protocolo})")
                        
                elif protocolo == "UDP" and respuesta.haslayer(UDP):
                    puertos_abiertos.append(puerto)
                    if callback_resultado:
                        callback_resultado(puerto, f"ABIERTO ({protocolo})")
            
            if callback_progreso:
                callback_progreso(idx + 1, total_puertos)
            
            time.sleep(0.01)
            
    except PermissionError:
        print("\n[ERROR] Requiere permisos de administrador (sudo)")
        return None
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return None
        
    return {
        "host": host,
        "puertos_abiertos": puertos_abiertos,
        "total_abiertos": len(puertos_abiertos)
    }