# 🛡️ Sistema Proactivo de Seguridad LAN - Guía de Instalación

## 📋 Requisitos Previos

- **Python 3.9+** instalado
- **Ubuntu Server 22.04+** con MySQL 8.0+
- **Acceso sudo** para captura de paquetes
- **Ollama** instalado y corriendo en `localhost:11434`

---

## 🚀 Paso 1: Preparación del Entorno Virtual

```bash
# Ir a tu directorio de trabajo
cd /ruta/del/proyecto

# Crear entorno virtual
python3 -m venv entorno_redes

# Activar entorno (bash/zsh)
source entorno_redes/bin/activate

# O si usas fish
source entorno_redes/bin/activate.fish
```

---

## 📦 Paso 2: Instalar Dependencias

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar todos los requisitos
pip install -r requirements.txt

# Si tienes problemas con Scapy:
pip install --upgrade scapy
```

---

## 🗄️ Paso 3: Configurar Base de Datos MySQL

### En el Ubuntu Server:

```bash
# Conectarse a MySQL
mysql -u root -p

# Ejecutar dentro de MySQL:
```

```sql
-- Crear base de datos
CREATE DATABASE sistema_monitoreo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear usuario (cambiar password)
CREATE USER 'joshua'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON sistema_monitoreo.* TO 'joshua'@'%';
FLUSH PRIVILEGES;

-- Salir
EXIT;
```

### Ejecutar script de configuración:

```bash
# Desde tu máquina local o el servidor
mysql -h 10.3.16.216 -u joshua -p sistema_monitoreo < setup_tickets.sql

# Ingresa la contraseña: password
```

---

## ⚙️ Paso 4: Configurar Credenciales

Edita `database.py` y actualiza:

```python
DB_HOST = '10.3.16.216'      # IP de tu Ubuntu Server
DB_USER = 'joshua'            # Usuario MySQL
DB_PASS = 'tu_password'       # Tu contraseña
DB_NAME = 'sistema_monitoreo' # Nombre de BD
```

---

## 🔌 Paso 5: Configurar Ollama (Local)

### Instalar Ollama:
```bash
# En macOS/Linux:
curl https://ollama.ai/install.sh | sh

# O descargar desde: https://ollama.ai
```

### Descargar modelo:
```bash
ollama pull phi3
```

### Ejecutar Ollama:
```bash
# En terminal separada
ollama serve
# Se ejecutará en: http://localhost:11434
```

---

## ✅ Paso 6: Pruebas de Conexión

### Probar conexión a BD:

```bash
# Ejecutar test
python3 database.py

# Deberías ver:
# ¡Conexión y Login EXITOSOS!
# Ticket #XXXX creado correctamente
```

### Probar Ollama:

```bash
curl http://localhost:11434/api/tags

# Deberías ver los modelos disponibles
```

---

## 🎯 Paso 7: Ejecutar la Aplicación

### Opción A: Login + Dashboard (Recomendado)

```bash
# Con sudo para captura de paquetes
sudo python3 login.py

# Credenciales de ejemplo: joshua / redes2026
# (Asegúrate que existan en la tabla 'usuarios' de MySQL)
```

### Opción B: Solo Dashboard (sin Login)

```bash
sudo python3 app.py
```

---

## 📊 Características Principales

### Panel de Control (Izquierda)
- ▶ **Iniciar Escaneo**: Comienza monitoreo de tráfico
- ⏹ **Detener Sistema**: Pausa el análisis
- 🔍 **Escaneo de Puertos**: Selecciona rango personalizado (1-65535)

### Dashboard (Centro-Derecha)
- **Semáforo (Arriba)**:
  - 🟢 Verde: Tráfico normal
  - 🟠 Naranja: Anomalía detectada
  - 🔴 Rojo: Alerta crítica

- **Consola (Centro)**: Logs en tiempo real de ejecución
  
- **Tickets (Abajo)**:
  - Lista de alertas generadas
  - Guardadas automáticamente en BD

### Gráficas (Pestañas)
- 📊 **Total/Día**: Cantidad de tickets por día (lunes-domingo)
- 📈 **Severidad/Día**: Desglose de críticos vs anomalías

---

## 🛠️ Solución de Problemas

### Error: "PermissionError - Ejecuta con sudo"
```bash
sudo python3 app.py
```

### Error: "No se encontró scapy"
```bash
pip install scapy requests
```

### Error: "No se puede conectar a MySQL"
- Verifica IP en `database.py`
- Comprueba que MySQL está corriendo: `mysql -h 10.3.16.216 -u joshua -p`
- Verifica firewall: `sudo ufw allow 3306`

### Error: "No se puede conectar a Ollama"
```bash
# Verifica que Ollama esté corriendo
curl http://localhost:11434/api/tags

# Si no responde, inicia en otra terminal:
ollama serve
```

### Error: "Tabla tickets no existe"
```bash
mysql -h 10.3.16.216 -u joshua -p sistema_monitoreo < setup_tickets.sql
```

---

## 📁 Estructura de Archivos

```
proyecto/
├── login.py                 # Pantalla de autenticación
├── app.py                   # Dashboard principal
├── analisis_ia.py          # Análisis con Scapy + IA
├── database.py             # Conexión y operaciones BD
├── port_scanner.py         # Escaneo de puertos
├── setup_tickets.sql       # Script de base de datos
├── requirements.txt        # Dependencias Python
├── GUIA_INSTALACION.md    # Este archivo
└── entorno_redes/         # Entorno virtual
```

---

## 🔐 Seguridad

1. **Nunca commits credenciales** en Git
2. **Crea `.gitignore`**:
   ```
   entorno_redes/
   __pycache__/
   *.pyc
   .DS_Store
   ```

3. **Usa contraseñas fuertes** en MySQL
4. **Restringe permisos BD**: `GRANT SELECT, INSERT ON...`

---

## 📞 Soporte

Para problemas:
1. Verifica los logs en la **Consola** de la app
2. Revisa `/var/log/mysql/` en el servidor Ubuntu
3. Comprueba `ollama serve` en terminal separada

---

## 🎓 Créditos

Sistema desarrollado para **UTCJ - Tópicos de Calidad para Diseño de Software**

Prof. Cepeda Gómez Yadira
