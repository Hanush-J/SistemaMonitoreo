"""
Prueba de extremo a extremo para UN pcap: reproduce el archivo mientras el
propio sistema (analisis_ia.capturar_trafico_vivo) escucha en vivo, y luego
manda ese reporte a la IA local para ver qué veredicto da.

No usa la GUI (app.py) ni requiere tener login.py corriendo aparte; llama
directo a las mismas funciones que usa el sistema real.

Uso:
    sudo ./entorno/bin/python test_pcap_veredicto.py "capturas_pcap/ataque_nmap.pcap"
"""
import sys
import threading
import time

from scapy.all import rdpcap, sendp, Ether, conf

from analisis_ia import capturar_trafico_vivo, consultar_ia_local, detectar_interfaz_automatica


def reproducir(archivo, interfaz, espera=1.5):
    time.sleep(espera)
    paquetes = rdpcap(archivo)
    print(f"[REPLAY] Enviando {len(paquetes)} paquetes de '{archivo}' por '{interfaz}'...")
    for pkt in paquetes:
        salida = pkt if pkt.haslayer(Ether) else Ether() / pkt
        try:
            sendp(salida, iface=interfaz, verbose=False)
        except Exception as e:
            print(f"[REPLAY][WARN] {e}")
        time.sleep(0.01)
    print("[REPLAY] Terminado.")


def main():
    if len(sys.argv) != 2:
        print('Uso: sudo ./entorno/bin/python test_pcap_veredicto.py "capturas_pcap/archivo.pcap"')
        sys.exit(1)

    archivo = sys.argv[1]
    interfaz = detectar_interfaz_automatica()
    if not interfaz:
        sys.exit(1)

    hilo = threading.Thread(target=reproducir, args=(archivo, interfaz))
    hilo.start()

    reporte = capturar_trafico_vivo(interfaz, tiempo_ventana=12)
    hilo.join()

    if not reporte:
        print("[INFO] No se capturó tráfico suficiente durante la ventana. Prueba subir tiempo_ventana o revisa la interfaz.")
        return

    print("\n=== REPORTE ESTADÍSTICO ===")
    print(reporte)

    print("=== CONSULTANDO IA LOCAL (Ollama) ===")
    veredicto = consultar_ia_local(reporte)

    print("\n=== VEREDICTO ===")
    print(veredicto)


if __name__ == "__main__":
    main()
