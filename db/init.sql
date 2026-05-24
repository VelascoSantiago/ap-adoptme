-- Usar la base de datos
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
-- Incluimos los campos base de tu interfaz: nombre, especie, tamaño, salud[cite: 199, 200, 202, 203].
CREATE TABLE IF NOT EXISTS mascotas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    especie VARCHAR(50) NOT NULL, 
    raza VARCHAR(50) DEFAULT 'Mestizo',
    fecha_nacimiento_aprox DATE, -- Reemplaza a la edad estática 
    tamano ENUM('Pequeño', 'Mediano', 'Grande', 'Gigante') NOT NULL, 
    salud VARCHAR(100) NOT NULL, 
    estado_adopcion ENUM('disponible', 'en_proceso', 'adoptado') DEFAULT 'disponible',
    notas_medicas TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ==========================================
-- 3. TABLA: solicitudes (Flujo Operativo)
-- ==========================================
CREATE TABLE IF NOT EXISTS solicitudes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    mascota_id INT NOT NULL,
    estado ENUM('pendiente', 'en_revision', 'aprobada', 'rechazada', 'cancelada') DEFAULT 'pendiente',
    comentarios_admin TEXT, -- Por qué se rechazó o notas de la entrevista
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Llaves foráneas
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE RESTRICT
);
