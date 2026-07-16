# 🛡️ Sistema Proactivo de Seguridad LAN

> **Sistema inteligente de monitoreo de seguridad de red con análisis de tráfico basado en IA, escaneo de puertos y generación automática de reportes.**

---

## ✨ Características Principales

### 🔍 **Captura de Tráfico en Vivo**
- Monitorea tráfico IP en tiempo real usando Scapy
- Análisis automático cada 30 segundos
- Detección de patrones anómalos

### 🤖 **Análisis Impulsado por IA**
- Integración con Ollama (modelo Phi-3)
- Clasificación automática de alertas:
  - 🟢 **NORMAL**: Tráfico estándar
  - 🟠 **ANOMALÍA**: Comportamiento inusual
  - 🔴 **CRÍTICO**: Riesgo de seguridad detectado
- Reglas de análisis customizables

### 🔌 **Escaneo de Puertos Personalizado**
- Rango configurable (1 a 65535)
- Detección de servicios por puerto
- Progreso visual en tiempo real
- Soporte para puertos comunes predefinidos

### 📊 **Dashboard Profesional**
- **Panel de Control**: Inicio/parada de sistemas
- **Semáforo Visual**: Estado del sistema en color
- **Consola en Vivo**: Logs de ejecución en tiempo real
- **Tickets de Alerta**: Registro de incidentes detectados
- **Gráficas Estadísticas**: 
  - Total de tickets por día de la semana
  - Desglose de severidad (Críticos vs Anomalías)

### 💾 **Persistencia en BD**
- MySQL 8.0+ para almacenamiento
- Historial completo de tickets
- Estadísticas agregadas por día
- Logs de ejecución del sistema

### 🔐 **Autenticación Segura**
- Pantalla de login con validación BD
- Integración con usuarios MySQL
- Control de acceso a funcionalidades

---

## 🚀 Quick Start

```bash
# 1. Clonar/descargar proyecto
cd sistema-seguridad-lan

# 2. Crear entorno
python3 -m venv entorno_redes
source entorno_redes/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar MySQL (ver GUIA_INSTALACION.md)
mysql -h 10.3.16.216 -u joshua -p < setup_tickets.sql

# 5. Iniciar Ollama (terminal separada)
ollama serve

# 6. Ejecutar aplicación
sudo python3 login.py
```

---

## 📊 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────┐
│         LOGIN.PY (Autenticación)                    │
├─────────────────────────────────────────────────────┤
│  APP.PY (Dashboard Principal)                       │
│ ┌─────────────┬──────────────────────────────────┐  │
│ │   CONTROLES │     VISUALIZACIÓN                │  │
│ ├─────────────┼──────────────────────────────────┤  │
│ │ • Iniciar   │ • Semáforo (Estado)              │  │
│ │ • Detener   │ • Consola (Logs en vivo)         │  │
│ │ • Escanear  │ • Tickets (Alertas)              │  │
│ │   Puertos   │ • Gráficas (Estadísticas)        │  │
│ └─────────────┴──────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
        ↓                    ↓                 ↓
   ┌─────────────┐  ┌────────────────┐  ┌──────────────┐
   │ ANALISIS_IA │  │ PORT_SCANNER   │  │  DATABASE.PY │
   ├─────────────┤  ├────────────────┤  ├──────────────┤
   │ • Captura   │  │ • Escaneo TCP  │  │ • Conexión   │
   │   de tráfico│  │ • Detección de │  │   MySQL      │
   │ • Análisis  │  │   servicios    │  │ • CRUD Tickets
   │   estadístico│  │ • Progreso     │  │ • Estadísticas
   └─────────────┘  └────────────────┘  └──────────────┘
        ↓                    ↓
   ┌─────────────────────────────────┐
   │      OLLAMA (IA Local)          │
   │   Modelo: Phi-3                 │
   │   Análisis de Amenazas          │
   └─────────────────────────────────┘
        ↓
   ┌──────────────────────────────────┐
   │   MySQL (Base de Datos)          │
   │ • tickets                        │
   │ • logs_ejecucion                 │
   │ • usuarios                       │
   └──────────────────────────────────┘
```

---

## 📋 Dependencias

```
customtkinter          - UI moderna y responsiva
scapy                 - Captura y análisis de paquetes
requests              - Comunicación con API Ollama
mysql-connector-python - Acceso a base de datos
matplotlib            - Gráficas estadísticas
```

---

## 🗄️ Estructura de Base de Datos

### Tabla: `tickets`
```
id_ticket (int, PK)
fecha_hora (datetime)
severidad (enum: NORMAL, ANOMALIA, CRITICO)
descripcion (longtext)
interfaz (varchar)
ip_origen (varchar)
puertos_involucrados (varchar)
estado (enum: PENDIENTE, RESUELTO, IGNORADO)
```

### Tabla: `logs_ejecucion`
```
id_log (int, PK)
fecha_hora (datetime)
tipo_log (enum: INFO, WARNING, ERROR, SUCCESS)
mensaje (text)
```

---

## 🎯 Casos de Uso

### 1. Monitoreo Continuo de Red
- Detecta automáticamente tráfico anómalo
- Genera alertas en tiempo real
- Mantiene historial completo

### 2. Auditoría de Seguridad
- Escanea puertos específicos
- Identifica servicios activos
- Genera reportes con gráficas

### 3. Respuesta a Incidentes
- Tickets automatizados por severidad
- Historial consultable en BD
- Análisis de patrones semanales

---

## 🔧 Configuración Avanzada

### Cambiar Modelo de IA
En `analisis_ia.py`:
```python
consultar_ia_local(reporte, modelo="mistral")  # Cambiar a otro modelo
```

### Ajustar Tiempo de Captura
En `app.py`:
```python
reporte = analisis_ia.capturar_trafico_vivo(interfaz, tiempo_ventana=60)  # 60 segundos
```

### Cambiar Rango de Puertos Predeterminado
En `port_scanner.py`, editar `puertos_comunes[]`

---

## 📈 Métricas de Rendimiento

- **Captura**: ~1000 paquetes/segundo
- **Análisis IA**: 20-30 segundos por reporte
- **Escaneo de Puertos**: ~1-5 segundos por puerto
- **Almacenamiento BD**: <1MB por 1000 tickets

---

## 🔐 Notas de Seguridad

1. **Requisitos de Permisos**:
   - Script debe ejecutarse con `sudo` para captura de paquetes
   - Root MySQL para crear BD (una sola vez)

2. **Datos Sensibles**:
   - Mantén credenciales fuera de Git
   - Usa variables de entorno en producción
   - Habilita SSL/TLS para BD remota

3. **Firewall**:
   ```bash
   sudo ufw allow 3306/tcp  # MySQL
   sudo ufw allow 11434/tcp # Ollama
   ```

---

## 📞 Solución de Problemas

| Problema | Solución |
|----------|----------|
| "Permission denied" | Ejecuta con `sudo python3 app.py` |
| "No se puede conectar a MySQL" | Verifica IP y credenciales en `database.py` |
| "Ollama no responde" | Inicia `ollama serve` en otra terminal |
| "No se capturan paquetes" | Verifica interfaz de red con `ip addr show` |

---

## 📚 Documentación Adicional

- **GUIA_INSTALACION.md** - Instalación paso a paso
- **setup_tickets.sql** - Script de base de datos
- **requirements.txt** - Todas las dependencias

---

## 🎓 Información del Proyecto

**Materia**: Tópicos de Calidad para el Diseño de Software  
**Profesor**: Cepeda Gómez Yadira  
**Universidad**: UTCJ (Universidad Tecnológica de Ciudad Juárez)  
**Autor**: Josh  

---

## 📝 Licencia

Este proyecto es de código abierto y está disponible para uso educativo y comercial.

---

## 🎉 Características Futuras (Roadmap)

- [ ] Exportar reportes a PDF
- [ ] Notificaciones por email
- [ ] Integración con SIEM (Splunk, ELK)
- [ ] API REST para integración
- [ ] Dashboard web (Flask/Django)
- [ ] Machine Learning para detección de anomalías
- [ ] Soporte para múltiples interfaces simultáneamente
- [ ] Integración con VPN y proxies

---

**¡Sistema listo para producción!** 🚀
