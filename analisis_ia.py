import os
import sys
from collections import Counter

# Tratamos de importar Scapy de forma segura
try:
    import scapy.all as scapy
except ModuleNotFoundError:
    print("\n[ERROR DE DEPENDENCIAS] No se encontró el módulo 'scapy'.")
    print("-> Asegúrate de activar tu entorno con: source entorno_redes/bin/activate.fish")
    print("-> E instala las librerías con: pip install scapy requests\n")
    sys.exit(1)

try:
    import requests
except ModuleNotFoundError:
    print("\n[ERROR DE DEPENDENCIAS] No se encontró el módulo 'requests'.")
    print("-> Instálalo ejecutando: pip install requests\n")
    sys.exit(1)


def detectar_interfaz_automatica():
    """Detecta automáticamente las tarjetas de red activas."""
    try:
        interfaces_objetivo = ["wlan0", "lo", "vmnet8"]
        
        print(f"[SISTEMA] Escuchando múltiples interfaces: {interfaces_objetivo}")
        return interfaces_objetivo
    except Exception as e:
        print(f"[ERROR] No se pudo configurar las interfaces: {str(e)}")
        return "wlan0"


def capturar_trafico_vivo(interfaz, tiempo_ventana=30):
    """Escucha tráfico en vivo durante un tiempo determinado y extrae estadísticas."""
    print(f"\n[FASE 1] Escuchando tráfico en vivo en '{interfaz}' por {tiempo_ventana}s...")
    
    try:
        paquetes = scapy.sniff(iface=interfaz, timeout=tiempo_ventana, filter="tcp")
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

    reporte_resumen = (
        f"- Total paquetes: {len(ips_origen)}\n"
        f"- Tráfico: {total_bytes / 1024:.2f} KB\n"
        f"- Top IPs origen: {top_ips}\n"
        f"- Top Puertos: {top_puertos}\n"
        f"- Protocolos: {top_protocolos}\n"
        f"- IPs destino únicas: {len(set(ips_destino))}\n"
    )
    return reporte_resumen


def consultar_ia_local(reporte_estadistico, modelo="phi3"):
    """Envía el resumen estadístico a Ollama para análisis."""
    url_api = "http://localhost:11434/api/generate"
    
    prompt_ingenieria = (
        f"Actúa como un experto analista de ciberseguridad (SOC) de Nivel 3.\n"
        f"Analiza este reporte de tráfico de red capturado en los últimos 30 segundos:\n{reporte_estadistico}\n\n"
        "REGLAS ESTRICTAS DE ANÁLISIS:\n"
        "1. EL PUERTO 443 (HTTPS) Y 53 (DNS) SON RUIDO DE FONDO. Si ves una alta cantidad de tráfico TCP en el puerto 443 o UDP en el 53, considéralo [TRÁFICO NORMAL] al 100%. Las computadoras modernas sincronizan datos en segundo plano constantemente. NO lo marques como anomalía.\n"
        "2. Solo debes alertar si detectas puertos inusuales (ej. 22 SSH, 21 FTP, 3306 MySQL, 445 SMB) o demasiados puertos distintos escaneados a la vez.\n"
        "3. Tu respuesta DEBE empezar obligatoriamente con una de estas tres etiquetas: [TRÁFICO NORMAL], [ANOMALIA] o [ALERTA CRITICA DETECTADA].\n"
        "4. Sé directo, máximo 3 líneas de explicación."
    )

    datos_json = {
        "model": modelo,
        "prompt": prompt_ingenieria,
        "stream": False,
        "options": {"temperature": 0.0, "top_p": 0.9}
    }

    try:
        respuesta = requests.post(url_api, json=datos_json, timeout=40)
        if respuesta.status_code == 200:
            resultado = respuesta.json().get("response", "Error: Respuesta vacía.")
            return resultado.strip()
        return f"Error Ollama: {respuesta.status_code}"
    except requests.exceptions.ConnectionError:
        return "[ALERTA CRITICA DETECTADA] Error: No se pudo conectar a Ollama. Verifica que esté ejecutándose en localhost:11434"
    except Exception as e:
        return f"Error conectando IA: {str(e)}"


def iniciar_monitoreo_continuo(interfaz):
    """Bucle principal de monitoreo (versión legacy, se usa desde app.py)."""
    print(f"\nIniciando Sistema Proactivo en {interfaz}...")
    try:
        while True:
            reporte = capturar_trafico_vivo(interfaz, tiempo_ventana=30)
            if reporte:
                veredicto = consultar_ia_local(reporte)
                print(f"\n>> DIAGNÓSTICO:\n{veredicto}")
            else:
                print("[INFO] Sin tráfico IP para analizar.")
    except KeyboardInterrupt:
        print("\n[PROCESO DETENIDO]")


if __name__ == "__main__":
    interfaz_activa = detectar_interfaz_automatica()
    if interfaz_activa:
        iniciar_monitoreo_continuo(interfaz_activa)
