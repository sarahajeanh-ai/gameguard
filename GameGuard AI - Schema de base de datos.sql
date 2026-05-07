#GameGuard AI - Schema de base de datos
#Proyecto: Detección de amenazas en juegos online

CREATE DATABASE IF NOT EXISTS gameguard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE gameguard;

#Tabla 1: Usuarios del juego

CREATE TABLE IF NOT EXISTS usuarios (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50) NOT NULL UNIQUE,
    email           VARCHAR(120),
    ip_registro     VARCHAR(45),
    pais            VARCHAR(60),
    fecha_registro  DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado          ENUM('activo', 'suspendido', 'baneado') DEFAULT 'activo',
    score_riesgo    FLOAT DEFAULT 0.0,
    nivel_riesgo    ENUM('normal', 'medio', 'alto', 'critico') DEFAULT 'normal',
    revisado_por_ia TINYINT(1) DEFAULT 0,
    INDEX idx_nivel_riesgo (nivel_riesgo),
    INDEX idx_score (score_riesgo)
);

#Tabla 2: Sesiones de juego

CREATE TABLE IF NOT EXISTS sesiones (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id      INT NOT NULL,
    ip_sesion       VARCHAR(45),
    inicio          DATETIME NOT NULL,
    fin             DATETIME,
    duracion_min    INT GENERATED ALWAYS AS (TIMESTAMPDIFF(MINUTE, inicio, fin)) STORED,
    acciones_total  INT DEFAULT 0,
    dispositivo     VARCHAR(100),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_inicio (inicio)
);

#Tabla 3: Eventos de comportamiento
#Cada acción relevante dentro de una sesión

CREATE TABLE IF NOT EXISTS eventos_comportamiento (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    sesion_id       INT NOT NULL,
    usuario_id      INT NOT NULL,
    tipo_evento     ENUM(
                        'login', 'logout',
                        'accion_juego', 'chat_enviado',
                        'compra', 'transferencia_item',
                        'cambio_ip', 'velocidad_anormal',
                        'patron_repetitivo', 'acceso_off_hours'
                    ) NOT NULL,
    valor_metrica   FLOAT,           #Ej: tiempo_respuesta en ms, velocidad de acciones/min
    descripcion     VARCHAR(255),
    timestamp_evento DATETIME DEFAULT CURRENT_TIMESTAMP,
    es_anomalia     TINYINT(1) DEFAULT 0,
    FOREIGN KEY (sesion_id) REFERENCES sesiones(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_sesion (sesion_id),
    INDEX idx_tipo (tipo_evento),
    INDEX idx_anomalia (es_anomalia)
);


#Tabla 4: Alertas generadas por la IA

CREATE TABLE IF NOT EXISTS alertas (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id      INT NOT NULL,
    tipo_amenaza    ENUM(
                        'bot_detectado',
                        'multicuenta',
                        'velocidad_anomala',
                        'ip_sospechosa',
                        'patron_sospechoso',
                        'acceso_inusual'
                    ) NOT NULL,
    score_ia        FLOAT NOT NULL,          #0 a 100, dado por la IA
    descripcion_ia  TEXT,                    #Explicación generada por la IA
    estado          ENUM('pendiente', 'revisada', 'falso_positivo', 'confirmada') DEFAULT 'pendiente',
    fecha_creacion  DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_revision  DATETIME,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_estado (estado),
    INDEX idx_score_ia (score_ia),
    INDEX idx_fecha (fecha_creacion)
);

#Tabla 5: IPs en lista de riesgo

CREATE TABLE IF NOT EXISTS ips_riesgo (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    ip              VARCHAR(45) NOT NULL UNIQUE,
    motivo          ENUM('vpn', 'proxy', 'tor', 'reportada', 'datacenter') NOT NULL,
    nivel_riesgo    ENUM('bajo', 'medio', 'alto') DEFAULT 'medio',
    fecha_agregada  DATETIME DEFAULT CURRENT_TIMESTAMP
);

#Vista: Resumen de usuarios de alto riesgo
#Útil para el dashboard

CREATE OR REPLACE VIEW vista_usuarios_riesgo AS
SELECT
    u.id,
    u.username,
    u.nivel_riesgo,
    u.score_riesgo,
    u.estado,
    COUNT(DISTINCT s.id)          AS total_sesiones,
    COUNT(DISTINCT a.id)          AS total_alertas,
    MAX(a.fecha_creacion)         AS ultima_alerta,
    MAX(s.inicio)                 AS ultima_sesion
FROM usuarios u
LEFT JOIN sesiones s        ON s.usuario_id = u.id
LEFT JOIN alertas a         ON a.usuario_id = u.id
WHERE u.nivel_riesgo IN ('alto', 'critico')
GROUP BY u.id
ORDER BY u.score_riesgo DESC;

CREATE USER 'gameguard_user'@'localhost' IDENTIFIED BY 'una_clave_segura';
GRANT ALL PRIVILEGES ON gameguard.* TO 'gameguard_user'@'localhost';
FLUSH PRIVILEGES;