-- Script para crear la tabla de tickets en MySQL
-- Ejecutar en el Ubuntu Server: mysql -u joshua -p sistema_monitoreo < setup_tickets.sql

CREATE TABLE IF NOT EXISTS tickets (
    id_ticket INT AUTO_INCREMENT PRIMARY KEY,
    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    severidad ENUM('NORMAL', 'ANOMALIA', 'CRITICO') NOT NULL,
    descripcion LONGTEXT NOT NULL,
    interfaz VARCHAR(50),
    ip_origen VARCHAR(15),
    puertos_involucrados VARCHAR(255),
    estado ENUM('PENDIENTE', 'RESUELTO', 'IGNORADO') DEFAULT 'PENDIENTE',
    INDEX idx_fecha (fecha_hora),
    INDEX idx_severidad (severidad),
    INDEX idx_estado (estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla adicional para estadísticas diarias (opcional, para gráficas más rápidas)
CREATE TABLE IF NOT EXISTS tickets_estadisticas (
    id_estadistica INT AUTO_INCREMENT PRIMARY KEY,
    fecha_date DATE NOT NULL,
    dia_semana VARCHAR(15),
    total_tickets INT DEFAULT 0,
    tickets_criticos INT DEFAULT 0,
    tickets_anomalias INT DEFAULT 0,
    tickets_normales INT DEFAULT 0,
    UNIQUE KEY unique_date (fecha_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla para logs de ejecución (consola en tiempo real)
CREATE TABLE IF NOT EXISTS logs_ejecucion (
    id_log INT AUTO_INCREMENT PRIMARY KEY,
    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    tipo_log ENUM('INFO', 'WARNING', 'ERROR', 'SUCCESS') DEFAULT 'INFO',
    mensaje TEXT NOT NULL,
    INDEX idx_fecha_log (fecha_hora)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
