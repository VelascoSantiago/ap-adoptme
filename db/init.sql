-- Usar la base de datos del proyecto
USE adoptme_db;

-- ==========================================
-- 1. TABLA: usuarios
-- ==========================================
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    telefono VARCHAR(20),
    rol ENUM('adoptante', 'admin') DEFAULT 'adoptante',
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ==========================================
-- 2. TABLA: mascotas
-- ==========================================
CREATE TABLE IF NOT EXISTS mascotas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    especie VARCHAR(50) NOT NULL, -- Para filtros: Perro, Gato, etc.
    raza VARCHAR(50) DEFAULT 'Mestizo', -- Para filtros
    fecha_nacimiento_aprox DATE NOT NULL, -- Para calcular edad dinámicamente
    tamano ENUM('Pequeño', 'Mediano', 'Grande', 'Gigante') NOT NULL, -- Para filtros
    sexo ENUM('Macho', 'Hembra') NOT NULL, -- Para filtros (NUEVO)
    energia ENUM('Baja', 'Media', 'Alta') DEFAULT 'Media', -- Para filtros (NUEVO)
    salud VARCHAR(100) NOT NULL, 
    estado_adopcion ENUM('disponible', 'en_proceso', 'adoptado') DEFAULT 'disponible',
    notas_medicas TEXT,
    foto_url VARCHAR(255) DEFAULT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ==========================================
-- 3. TABLA: solicitudes (Formulario Complejo)
-- ==========================================
CREATE TABLE IF NOT EXISTS solicitudes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    mascota_id INT NOT NULL,
    estado ENUM('pendiente', 'en_revision', 'aprobada', 'rechazada', 'cancelada') DEFAULT 'pendiente',
    
    -- TOQUE PRO: Aquí se guardará todo el cuestionario gigante (vivienda, estilo de vida, etc.)
    -- en formato JSON nativo de MySQL. Esto evita tener una tabla con 40 columnas difíciles de mantener.
    datos_formulario JSON NOT NULL, 
    
    comentarios_admin TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE RESTRICT
);

-- ==========================================
-- 4. TABLA: citas (NUEVA)
-- ==========================================
CREATE TABLE IF NOT EXISTS citas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    mascota_id INT NOT NULL,
    fecha_hora DATETIME NOT NULL,
    estado ENUM('pendiente', 'confirmada', 'completada', 'cancelada') DEFAULT 'pendiente',
    google_calendar_event_id VARCHAR(255) DEFAULT NULL, -- Espacio reservado para la API de Google
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE CASCADE
);