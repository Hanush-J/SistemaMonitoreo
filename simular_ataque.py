"""
Reproduce un archivo .pcap en la interfaz de red activa, para probar el
Sistema Proactivo de Seguridad LAN con tráfico de ataque real capturado
previamente (carpeta "capturas_pcap/").

Uso solo en tu propia máquina/lab de pruebas.

Uso:
    sudo ./entorno/bin/python simular_ataque.py "capturas_pcap/ataque_nmap.pcap"
"""
import sys
import time

from scapy.all import rdpcap, sendp, Ether, conf


def main():
    if len(sys.argv) != 2:
        print("Uso: sudo python simular_ataque.py <archivo.pcap>")
        sys.exit(1)

    archivo = sys.argv[1]
    interfaz, _, _ = conf.route.route("0.0.0.0")

    print(f"[INFO] Interfaz de salida: {interfaz}")
    print(f"[INFO] Cargando paquetes de: {archivo}")
    paquetes = rdpcap(archivo)
    print(f"[INFO] {len(paquetes)} paquetes cargados. Reproduciendo...")

    for pkt in paquetes:
        salida = pkt if pkt.haslayer(Ether) else Ether() / pkt
        try:
            sendp(salida, iface=interfaz, verbose=False)
        except Exception as e:
            print(f"[WARN] No se pudo enviar un paquete: {e}")
        time.sleep(0.01)

    print("[INFO] Reproducción terminada.")


if __name__ == "__main__":
    main()
