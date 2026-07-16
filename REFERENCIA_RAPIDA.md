# ⚡ Referencia Rápida - Sistema Proactivo de Seguridad LAN

## 🚀 Iniciar Rápidamente

```bash
# Terminal 1: Ollama (déjalo corriendo)
ollama serve

# Terminal 2: Aplicación
cd /ruta/proyecto
source entorno_redes/bin/activate
sudo python3 login.py
```

**Login de ejemplo**: 
- Usuario: `joshua`
- Contraseña: `redes2026`

---

## 🎮 Cómo Usar el Dashboard

### Panel Izquierdo (Controles)

| Control | Función |
|---------|---------|
| **▶ Iniciar Escaneo** | Empieza captura de tráfico en vivo |
| **⏹ Detener Sistema** | Pausa el análisis |
| **Host** | IP a escanear (ej: 192.168.1.100) |
| **Puerto Inicio** | Primer puerto (ej: 1) |
| **Puerto Fin** | Último puerto (ej: 1000) |
| **🔍 Escanear Puertos** | Inicia escaneo TCP |

### Panel Superior (Semáforo)

```
🟢 ESTADO: NORMAL        → Tráfico seguro, sin amenazas
🟠 ESTADO: ANOMALÍA      → Comportamiento inusual detectado
🔴 ESTADO: CRÍTICO       → ⚠️ Amenaza de seguridad activa
⚫ ESTADO: EN ESPERA      → Sistema pausado o inicializando
🔵 IA PENSANDO...        → Analizando con modelo Ollama
```

### Panel Centro (Consola)

Logs en tiempo real con timestamps:
```
[14:35:20] SUCCESS: Interfaz detectada: eth0
[14:35:21] INFO: Tráfico capturado - Analizando...
[14:35:22] WARNING: Sin tráfico IP detectado
[14:35:23] ERROR: ALERTA CRÍTICA CREADA
```

### Panel Abajo (Tickets + Gráficas)

**Pestaña 1 - Tickets Activos**
- Recuadros coloreados con alertas
- Cada ticket tiene:
  - ID único
  - Hora de creación
  - Severidad [NORMAL/ANOMALIA/CRITICO]
  - Descripción del problema

**Pestaña 2 - Estadísticas Semanales**
- Gráfica 1: Total de tickets por día (lunes-domingo)
- Gráfica 2: Desglose por severidad

---

## 🔌 Escaneo de Puertos - Paso a Paso

### 1. Completar formulario
```
Host:           192.168.1.1
Puerto Inicio:  80
Puerto Fin:     1000
```

### 2. Hacer clic en "🔍 Escanear Puertos"

### 3. Esperar barra de progreso
- Muestra: "X/1000 puertos"
- Tiempo estimado: 1-2 minutos para 1000 puertos

### 4. Ver resultados
- En **Consola**: Puerto abierto + Servicio detectado
- En **Tickets**: Cambio de estado si es crítico

### Servicios comunes
```
80    → HTTP (Web)
443   → HTTPS (Web Seguro)
22    → SSH (Acceso Remoto)
3306  → MySQL (Base de Datos)
5432  → PostgreSQL (Base de Datos)
8080  → HTTP Alternativo
3389  → RDP (Escritorio Remoto)
```

---

## 📊 Interpretando las Gráficas

### Gráfica 1: Total Tickets/Día
```
Lunes    Martes   Miércoles   ...   Domingo
 ___     ___        ___              ___
|   |   |   |      |   |            |   |
|___|___|___|______|___|____________|___|
        Cantidad de tickets por día
```
🟡 Barras más altas = Más incidentes ese día

### Gráfica 2: Severidad/Día
```
Por cada día hay 3 barras:
🔴 Rojo   = Críticos
🟠 Naranja = Anomalías
🟢 Verde  = Normales

Miércoles (ejemplo):
|   |  ← Críticos (2)
|   |  ← Anomalías (3)
|___|  ← Normales (1)
```

---

## 🐛 Solución Rápida de Problemas

### Problema: "PermissionError"
```bash
# Solución: Ejecutar con sudo
sudo python3 login.py
```

### Problema: "No se conecta a MySQL"
```bash
# Verificar conexión
mysql -h 10.3.16.216 -u joshua -p

# Verificar que existan las tablas
SHOW TABLES;
```

### Problema: "Ollama no responde"
```bash
# En otra terminal
ollama serve

# Verificar que funciona
curl http://localhost:11434/api/tags
```

### Problema: "No se capturan paquetes"
```bash
# Verificar interfaz de red
ip addr show

# Cambiar en código si es diferente a eth0
# En: analisis_ia.py, línea ~25
```

### Problema: "Gráficas vacías"
- Espera 5 minutos a que se generen tickets
- O crea un ticket de prueba en MySQL:
```sql
INSERT INTO tickets VALUES 
(NULL, NOW(), 'ANOMALIA', 'Prueba', 'eth0', '192.168.1.100', '80,443', 'PENDIENTE');
```

---

## 📱 Comandos Útiles

### MySQL
```bash
# Conectar
mysql -h 10.3.16.216 -u joshua -p sistema_monitoreo

# Ver tickets recientes
SELECT id_ticket, fecha_hora, severidad, estado FROM tickets ORDER BY fecha_hora DESC LIMIT 10;

# Contar por severidad
SELECT severidad, COUNT(*) FROM tickets GROUP BY severidad;

# Estadísticas hoy
SELECT DATE(fecha_hora), COUNT(*) FROM tickets WHERE DATE(fecha_hora) = CURDATE() GROUP BY DATE(fecha_hora);

# Limpiar tickets antiguos (30 días)
DELETE FROM tickets WHERE fecha_hora < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

### Ollama
```bash
# Ver modelos disponibles
ollama list

# Descargar modelo
ollama pull phi3

# Probar IA directamente
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"phi3","prompt":"Hola","stream":false}'
```

### Red
```bash
# Ver interfaz activa
ip addr show

# Escaneo rápido con nmap (alternativa)
sudo nmap -p 1-1000 192.168.1.1

# Ver conexiones activas
sudo netstat -tln | grep LISTEN
```

---

## 🎯 Escenarios de Uso

### Escenario 1: Monitoreo Continuo
1. Click en "▶ Iniciar Escaneo"
2. Dejar corriendo 24/7
3. Revisar dashboard periódicamente
4. Actuar si hay alertas críticas (🔴)

### Escenario 2: Auditoría de Host
1. Ingresar IP a auditar en "Host"
2. Seleccionar rango de puertos
3. Click "🔍 Escanear Puertos"
4. Analizar resultados en Consola
5. Exportar datos si es necesario

### Escenario 3: Investigación de Incidente
1. Localizar ticket en panel inferior
2. Nota la hora exacta del evento
3. Revisar logs en BD:
   ```sql
   SELECT * FROM logs_ejecucion 
   WHERE fecha_hora BETWEEN '2024-01-15 10:00' AND '2024-01-15 10:05';
   ```
4. Exportar reporte completo

---

## ⚙️ Configuraciones Útiles

### Cambiar tiempo de captura (más corto = menos datos)
En `app.py`, línea ~480:
```python
reporte = analisis_ia.capturar_trafico_vivo(interfaz, tiempo_ventana=15)  # 15 segundos en vez de 30
```

### Cambiar modelo de IA
En `analisis_ia.py`, línea ~95:
```python
consultar_ia_local(reporte, modelo="mistral")  # Cambiar de phi3 a otro
```

### Agregar más puertos "comunes"
En `port_scanner.py`, línea ~70:
```python
puertos_comunes = [20, 21, 22, ..., 9999]  # Agregar más números
```

---

## 📞 Contactos de Soporte

**Para problemas técnicos:**
1. Revisar logs en la Consola
2. Verificar tabla `logs_ejecucion` en BD
3. Consultar `CAMBIOS_REALIZADOS.md`
4. Ver `GUIA_INSTALACION.md` para detalles

**Información de Proyecto:**
- Universidad: UTCJ
- Materia: Tópicos de Calidad para Diseño de Software
- Profesor: Cepeda Gómez Yadira
- Estudiante: Josh

---

## 🎓 Conceptos Clave

**Tráfico Normal**: HTTP, HTTPS, DNS, SSH esperado
**Anomalía**: Comportamiento inusual pero no necesariamente malicioso
**Crítico**: Escaneo masivo de puertos, intentos de acceso no autorizado
**Ticket**: Registro automático de cada incidente en BD

---

**¡Listo para operar el sistema!** 🚀
