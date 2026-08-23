"""
Genera una ráfaga de paquetes SYN hacia UN SOLO puerto, para probar un
patrón distinto al de un escaneo: mucho volumen concentrado en un solo
destino, en vez de tocar muchos puertos distintos.

Uso solo en tu propia máquina/lab de pruebas.

Uso:
    sudo ./entorno/bin/python simular_flood.py <IP_objetivo> [puerto=80] [cantidad=500]
"""
import sys

from scapy.all import IP, TCP, RandShort, send, conf


def main():
    if len(sys.argv) < 2:
        print("Uso: sudo python simular_flood.py <IP_objetivo> [puerto=80] [cantidad=500]")
        sys.exit(1)

    destino = sys.argv[1]
    puerto = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    cantidad = int(sys.argv[3]) if len(sys.argv) > 3 else 500

    interfaz, _, _ = conf.route.route("0.0.0.0")
    print(f"[INFO] Enviando {cantidad} paquetes SYN a {destino}:{puerto} por '{interfaz}'...")

    paquete = IP(dst=destino) / TCP(sport=RandShort(), dport=puerto, flags="S")
    send(paquete, count=cantidad, iface=interfaz, verbose=False)

    print("[INFO] Envío terminado.")


if __name__ == "__main__":
    main()
