import sys
from collections import Counter

# Tratamos de importar Scapy de forma segura
try:
    import scapy.all as scapy
except ModuleNotFoundError:
    print("\n[ERROR DE DEPENDENCIAS] No se encontró el módulo 'scapy'.")
    print("-> Asegúrate de activar tu entorno con: source entorno/bin/activate.fish")
    print("-> E instala las librerías con: pip install scapy requests\n")
    sys.exit(1)

try:
    import requests
except ModuleNotFoundError:
    print("\n[ERROR DE DEPENDENCIAS] No se encontró el módulo 'requests'.")
    print("-> Instálalo ejecutando: pip install requests\n")
    sys.exit(1)

import database


def detectar_interfaz_automatica():
    """Detecta automáticamente la interfaz de red que usa la ruta por defecto (la que tiene salida a Internet)."""
    try:
        interfaz, _ip_local, _gateway = scapy.conf.route.route("0.0.0.0")
        print(f"[SISTEMA] Interfaz detectada automáticamente: {interfaz}")
        return interfaz
    except Exception as e:
        print(f"[ERROR] No se pudo detectar la interfaz automáticamente: {str(e)}")
        return None


def capturar_trafico_vivo(interfaz, tiempo_ventana=30):
    """Escucha tráfico en vivo durante un tiempo determinado y extrae estadísticas."""
    print(f"\n[FASE 1] Escuchando tráfico en vivo en '{interfaz}' por {tiempo_ventana}s...")
    
    # Excluimos el tráfico hacia nuestra propia base de datos: si no, el sistema
    # se termina marcando a sí mismo como sospechoso (sus propias conexiones a
    # MySQL en el puerto 3306 se ven como "puerto sensible" en cada ventana).
    filtro_captura = f"tcp and not host {database.DB_HOST}"

    # Un escaneo hacia la propia IP de la máquina (ej. probar el sistema contra
    # sí mismo) nunca sale por la tarjeta física: Linux lo enruta por "lo". Por
    # eso escuchamos también loopback además de la interfaz detectada.
    interfaces_escucha = [interfaz] if interfaz == "lo" else [interfaz, "lo"]

    try:
        paquetes = scapy.sniff(iface=interfaces_escucha, timeout=tiempo_ventana, filter=filtro_captura)
    except PermissionError:
        print("\n[ERROR DE PERMISOS] Ejecuta el script con sudo: sudo python app.py")
        return None
    except Exception as e:
        print(f"\n[ERROR DE CAPTURA] {str(e)}")
        return None

    if not paquetes:
        return None

    ips_origen = []
    puertos_destino = []
    protocolos = []
    total_bytes = 0
    ips_destino = []

    for pkt in paquetes:
        if pkt.haslayer(scapy.IP):
            ips_origen.append(pkt[scapy.IP].src)
            ips_destino.append(pkt[scapy.IP].dst)
            total_bytes += len(pkt)
            
            if pkt.haslayer(scapy.TCP):
                if pkt[scapy.TCP].dport < 10000:
                    puertos_destino.append(pkt[scapy.TCP].dport)
                protocolos.append("TCP")
            elif pkt.haslayer(scapy.UDP):
                if pkt[scapy.UDP].dport < 10000:
                    puertos_destino.append(pkt[scapy.UDP].dport)
                protocolos.append("UDP")
            elif pkt.haslayer(scapy.ICMP):
                protocolos.append("ICMP")

    if not ips_origen:
        return None

    # Construir reporte detallado
    top_ips = Counter(ips_origen).most_common(3)
    top_puertos = Counter(puertos_destino).most_common(5)
    top_protocolos = Counter(protocolos).most_common()
    puertos_unicos = set(puertos_destino)

    puertos_sensibles = {21, 22, 23, 25, 69, 135, 139, 445, 1433, 3306, 3389, 5900}
    sensibles_detectados = sorted(puertos_unicos & puertos_sensibles)

    reporte_resumen = (
        f"- Total paquetes: {len(ips_origen)}\n"
        f"- Tráfico: {total_bytes / 1024:.2f} KB\n"
        f"- Top IPs origen: {top_ips}\n"
        f"- Top Puertos (por frecuencia): {top_puertos}\n"
        f"- Cantidad de puertos DISTINTOS contactados: {len(puertos_unicos)}\n"
        f"- Puertos sensibles detectados entre todos los contactados: {sensibles_detectados or 'ninguno'}\n"
        f"- Protocolos: {top_protocolos}\n"
        f"- IPs destino únicas: {len(set(ips_destino))}\n"
    )
    return reporte_resumen


def consultar_ia_local(reporte_estadistico, modelo="qwen2.5-coder:7b"):
    """Envía el resumen estadístico a Ollama para análisis."""
    url_api = "http://localhost:11434/api/generate"
    
    prompt_ingenieria = (
        f"Actúa como un experto analista de ciberseguridad (SOC) de Nivel 3.\n"
        f"Analiza este reporte de tráfico de red capturado recientemente:\n{reporte_estadistico}\n\n"
        "REGLAS ESTRICTAS DE ANÁLISIS:\n"
        "1. EL PUERTO 443 (HTTPS) Y 53 (DNS) SON RUIDO DE FONDO. Si ves una alta cantidad de tráfico TCP en el puerto 443 o UDP en el 53, considéralo [TRÁFICO NORMAL] al 100%. Las computadoras modernas sincronizan datos en segundo plano constantemente. NO lo marques como anomalía.\n"
        "2. Revisa el campo 'Puertos sensibles detectados': si NO dice 'ninguno', es un fuerte indicio de [ANOMALIA] o [ALERTA CRITICA DETECTADA] (ej. 22 SSH, 21 FTP, 3306 MySQL, 445 SMB, 3389 RDP).\n"
        "3. Revisa el campo 'Cantidad de puertos DISTINTOS contactados': si es un número alto (más de 15-20) hacia una sola IP destino, es un escaneo de puertos y debes marcarlo como [ANOMALIA] o [ALERTA CRITICA DETECTADA], aunque los puertos individuales parezcan comunes.\n"
        "4. Tu respuesta DEBE empezar obligatoriamente con una de estas tres etiquetas: [TRÁFICO NORMAL], [ANOMALIA] o [ALERTA CRITICA DETECTADA].\n"
        "5. Sé directo, máximo 3 líneas de explicación."
    )

    datos_json = {
        "model": modelo,
        "prompt": prompt_ingenieria,
        "stream": False,
        "keep_alive": "30m",
        "options": {"temperature": 0.0, "top_p": 0.9, "num_predict": 150, "repeat_penalty": 1.15}
    }

    try:
        respuesta = requests.post(url_api, json=datos_json, timeout=90)
        if respuesta.status_code == 200:
            resultado = respuesta.json().get("response", "Error: Respuesta vacía.")
            return resultado.strip()
        return f"Error Ollama: {respuesta.status_code}"
    except requests.exceptions.ConnectionError:
        return "[ALERTA CRITICA DETECTADA] Error: No se pudo conectar a Ollama. Verifica que esté ejecutándose en localhost:11434"
    except requests.exceptions.Timeout:
        return "[OMITIR] Ollama tardó demasiado en responder (timeout). El modelo puede estar sobrecargado."
    except Exception as e:
        return f"Error conectando IA: {str(e)}"
