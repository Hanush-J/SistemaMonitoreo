"""Paleta y tokens visuales compartidos por login.py y app.py.

Un solo lugar para los colores evita que cada pantalla invente los suyos
(antes había rojo/verde/naranja/cian/amarillo/lima compitiendo entre sí).
"""

# Fondo
BG = "#111318"
SURFACE = "#1a1d24"
SURFACE_ALT = "#20242c"
BORDE = "#2a2e38"

# Texto
TEXTO = "#e8e9ed"
TEXTO_SUAVE = "#8b8f99"

# Acento de marca: el único color "vivo" para acciones primarias
ACENTO = "#5b8cff"
ACENTO_HOVER = "#4a76e0"

# Estados semánticos: se usan SOLO para transmitir estado, nunca como decoración
OK = "#3ecf8e"
OK_HOVER = "#33b37b"
WARN = "#e8a33d"
WARN_HOVER = "#d1922f"
ERROR = "#e5484d"
ERROR_HOVER = "#cc3f44"
NEUTRO = "#6b7280"
NEUTRO_HOVER = "#565c68"

FUENTE = "Arial"
FUENTE_MONO = "Courier"

RADIO = 12
RADIO_CHICO = 8

COLORES_SEVERIDAD = {
    "CRITICO": (ERROR, ERROR),
    "ANOMALIA": (WARN, WARN),
    "NORMAL": (OK, OK),
}

COLORES_ESTADO = {
    "PENDIENTE": WARN,
    "RESUELTO": OK,
    "IGNORADO": NEUTRO,
}


def fuente(tamano, peso="normal"):
    return (FUENTE, tamano, peso) if peso != "normal" else (FUENTE, tamano)


def fuente_mono(tamano, peso="normal"):
    return (FUENTE_MONO, tamano, peso) if peso != "normal" else (FUENTE_MONO, tamano)
