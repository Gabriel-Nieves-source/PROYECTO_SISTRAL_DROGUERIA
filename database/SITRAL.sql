/* =========================================================
   BASE DE DATOS SITRAL
   Sistema de Trazabilidad y Control por Lotes
   para Droguerías
   ========================================================= */

-- =========================================================
-- 1. CREAR BASE DE DATOS
-- =========================================================
CREATE DATABASE SITRAL
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE SITRAL;


-- =========================================================
-- 2. TABLA ROL
-- =========================================================

CREATE TABLE rol (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL UNIQUE,
    descripcion VARCHAR(150)
);


-- =========================================================
-- 3. TABLA USUARIO
-- =========================================================

CREATE TABLE usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    id_rol INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100),
    usuario VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    estado ENUM('ACTIVO', 'INACTIVO') NOT NULL DEFAULT 'ACTIVO',
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_usuario_rol
        FOREIGN KEY (id_rol)
        REFERENCES rol(id_rol)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


-- =========================================================
-- 4. TABLA PROVEEDOR
-- =========================================================

CREATE TABLE proveedor (
    id_proveedor INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    nit VARCHAR(30) UNIQUE,
    telefono VARCHAR(30),
    correo VARCHAR(100),
    direccion VARCHAR(200),
    estado ENUM('ACTIVO', 'INACTIVO') NOT NULL DEFAULT 'ACTIVO'
);


-- =========================================================
-- 5. TABLA MEDICAMENTO
-- =========================================================

CREATE TABLE medicamento (
    id_medicamento INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    presentacion VARCHAR(100),
    concentracion VARCHAR(50),
    codigo_barras VARCHAR(100) UNIQUE,
    precio DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    estado ENUM('ACTIVO', 'INACTIVO') NOT NULL DEFAULT 'ACTIVO',

    CONSTRAINT chk_medicamento_precio
        CHECK (precio >= 0)
);


-- =========================================================
-- 6. TABLA LOTE
-- =========================================================

CREATE TABLE lote (
    id_lote INT AUTO_INCREMENT PRIMARY KEY,

    id_medicamento INT NOT NULL,
    id_proveedor INT NOT NULL,

    numero_lote VARCHAR(100) NOT NULL,

    cantidad_inicial INT NOT NULL,
    cantidad_disponible INT NOT NULL,

    fecha_ingreso DATE NOT NULL,
    fecha_vencimiento DATE NOT NULL,

    estado ENUM(
        'VIGENTE',
        'PROXIMO_VENCER',
        'VENCIDO',
        'AGOTADO'
    ) NOT NULL DEFAULT 'VIGENTE',

    CONSTRAINT fk_lote_medicamento
        FOREIGN KEY (id_medicamento)
        REFERENCES medicamento(id_medicamento)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_lote_proveedor
        FOREIGN KEY (id_proveedor)
        REFERENCES proveedor(id_proveedor)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT uk_medicamento_lote
        UNIQUE (id_medicamento, numero_lote),

    CONSTRAINT chk_lote_cantidad_inicial
        CHECK (cantidad_inicial >= 0),

    CONSTRAINT chk_lote_cantidad_disponible
        CHECK (cantidad_disponible >= 0),

    CONSTRAINT chk_lote_fechas
        CHECK (fecha_vencimiento >= fecha_ingreso)
);


-- =========================================================
-- 7. TABLA FACTURA
-- =========================================================

CREATE TABLE factura (
    id_factura INT AUTO_INCREMENT PRIMARY KEY,

    id_usuario INT NOT NULL,
    id_proveedor INT NULL,

    numero_factura VARCHAR(50) NOT NULL,

    tipo ENUM(
        'ENTRADA',
        'SALIDA'
    ) NOT NULL,

    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    total DECIMAL(14,2) NOT NULL DEFAULT 0.00,

    estado ENUM(
        'ACTIVA',
        'ANULADA'
    ) NOT NULL DEFAULT 'ACTIVA',

    CONSTRAINT fk_factura_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_factura_proveedor
        FOREIGN KEY (id_proveedor)
        REFERENCES proveedor(id_proveedor)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_factura_total
        CHECK (total >= 0)
);


-- =========================================================
-- 8. TABLA DETALLE_FACTURA
-- =========================================================

CREATE TABLE detalle_factura (
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,

    id_factura INT NOT NULL,
    id_medicamento INT NOT NULL,
    id_lote INT NOT NULL,

    cantidad INT NOT NULL,

    precio_unitario DECIMAL(12,2) NOT NULL,

    subtotal DECIMAL(14,2) NOT NULL,

    CONSTRAINT fk_detalle_factura
        FOREIGN KEY (id_factura)
        REFERENCES factura(id_factura)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_detalle_medicamento
        FOREIGN KEY (id_medicamento)
        REFERENCES medicamento(id_medicamento)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_detalle_lote
        FOREIGN KEY (id_lote)
        REFERENCES lote(id_lote)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_detalle_cantidad
        CHECK (cantidad > 0),

    CONSTRAINT chk_detalle_precio
        CHECK (precio_unitario >= 0),

    CONSTRAINT chk_detalle_subtotal
        CHECK (subtotal >= 0)
);


-- =========================================================
-- 9. TABLA MOVIMIENTO_INVENTARIO
-- =========================================================

CREATE TABLE movimiento_inventario (
    id_movimiento INT AUTO_INCREMENT PRIMARY KEY,

    id_lote INT NOT NULL,
    id_usuario INT NOT NULL,
    id_factura INT NULL,

    tipo_movimiento ENUM(
        'ENTRADA',
        'SALIDA',
        'AJUSTE',
        'VENCIMIENTO'
    ) NOT NULL,

    cantidad INT NOT NULL,

    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    descripcion VARCHAR(255),

    CONSTRAINT fk_movimiento_lote
        FOREIGN KEY (id_lote)
        REFERENCES lote(id_lote)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_movimiento_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_movimiento_factura
        FOREIGN KEY (id_factura)
        REFERENCES factura(id_factura)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT chk_movimiento_cantidad
        CHECK (cantidad > 0)
);


-- =========================================================
-- 10. TABLA ALERTA
-- =========================================================

CREATE TABLE alerta (
    id_alerta INT AUTO_INCREMENT PRIMARY KEY,

    id_lote INT NOT NULL,

    tipo VARCHAR(50) NOT NULL,

    mensaje VARCHAR(255) NOT NULL,

    dias_restantes INT,

    fecha_generacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    estado ENUM(
        'PENDIENTE',
        'VISTA',
        'ATENDIDA'
    ) NOT NULL DEFAULT 'PENDIENTE',

    CONSTRAINT fk_alerta_lote
        FOREIGN KEY (id_lote)
        REFERENCES lote(id_lote)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- =========================================================
-- 11. TABLA CONFIGURACION_ALERTA
-- =========================================================

CREATE TABLE configuracion_alerta (
    id_configuracion INT AUTO_INCREMENT PRIMARY KEY,

    dias_anticipacion INT NOT NULL DEFAULT 30,

    fecha_actualizacion DATETIME
        NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    estado ENUM(
        'ACTIVA',
        'INACTIVA'
    ) NOT NULL DEFAULT 'ACTIVA',

    CONSTRAINT chk_dias_anticipacion
        CHECK (dias_anticipacion >= 0)
);


-- =========================================================
-- 12. ÍNDICES
-- =========================================================

CREATE INDEX idx_usuario_rol
ON usuario(id_rol);

CREATE INDEX idx_usuario_estado
ON usuario(estado);

CREATE INDEX idx_proveedor_nombre
ON proveedor(nombre);

CREATE INDEX idx_medicamento_nombre
ON medicamento(nombre);

CREATE INDEX idx_medicamento_codigo
ON medicamento(codigo_barras);

CREATE INDEX idx_lote_numero
ON lote(numero_lote);

CREATE INDEX idx_lote_vencimiento
ON lote(fecha_vencimiento);

CREATE INDEX idx_lote_estado
ON lote(estado);

CREATE INDEX idx_factura_fecha
ON factura(fecha);

CREATE INDEX idx_factura_tipo
ON factura(tipo);

CREATE INDEX idx_detalle_factura
ON detalle_factura(id_factura);

CREATE INDEX idx_movimiento_lote
ON movimiento_inventario(id_lote);

CREATE INDEX idx_movimiento_fecha
ON movimiento_inventario(fecha);

CREATE INDEX idx_alerta_estado
ON alerta(estado);

CREATE INDEX idx_alerta_lote
ON alerta(id_lote);


-- =========================================================
-- 13. DATOS INICIALES - ROLES
-- =========================================================

INSERT INTO rol (
    nombre,
    descripcion
)
VALUES
(
    'ADMINISTRADOR',
    'Administrador general de la drogueria'
),
(
    'FARMACEUTA',
    'Usuario encargado de las operaciones de la drogueria'
);


-- =========================================================
-- 14. CONFIGURACION INICIAL DE ALERTAS
-- =========================================================

INSERT INTO configuracion_alerta (
    dias_anticipacion,
    estado
)
VALUES (
    30,
    'ACTIVA'
);


-- =========================================================
-- 15. USUARIOS DE PRUEBA
-- =========================================================
-- NOTA:
-- Las contraseñas aqui son solamente para pruebas.
-- Cuando conectemos la API utilizaremos contraseñas
-- almacenadas mediante hash.

INSERT INTO usuario (
    id_rol,
    nombre,
    apellido,
    usuario,
    password,
    estado
)
VALUES
(
    1,
    'Administrador',
    'SITRAL',
    'admin',
    'admin123',
    'ACTIVO'
),
(
    2,
    'Carlos',
    'Perez',
    'farmaceuta',
    'farm123',
    'ACTIVO'
);


-- =========================================================
-- 16. PROVEEDORES DE PRUEBA
-- =========================================================

INSERT INTO proveedor (
    nombre,
    nit,
    telefono,
    correo,
    direccion,
    estado
)
VALUES
(
    'Distribuciones Farmaceuticas ABC',
    '900123456-1',
    '3001234567',
    'ventas@abc.com',
    'Bogota',
    'ACTIVO'
),
(
    'Drogas y Medicamentos SAS',
    '901987654-2',
    '3019876543',
    'contacto@drogasymedicamentos.com',
    'Bogota',
    'ACTIVO'
);


-- =========================================================
-- 17. MEDICAMENTOS DE PRUEBA
-- =========================================================

INSERT INTO medicamento (
    nombre,
    presentacion,
    concentracion,
    codigo_barras,
    precio,
    estado
)
VALUES
(
    'Acetaminofen',
    'Tabletas',
    '500 mg',
    '7701234567890',
    5000,
    'ACTIVO'
),
(
    'Ibuprofeno',
    'Tabletas',
    '400 mg',
    '7709876543210',
    6500,
    'ACTIVO'
),
(
    'Loratadina',
    'Tabletas',
    '10 mg',
    '7701112223334',
    4500,
    'ACTIVO'
);


-- =========================================================
-- 18. LOTES DE PRUEBA
-- =========================================================

INSERT INTO lote (
    id_medicamento,
    id_proveedor,
    numero_lote,
    cantidad_inicial,
    cantidad_disponible,
    fecha_ingreso,
    fecha_vencimiento,
    estado
)
VALUES
(
    1,
    1,
    'LOT-ACE-001',
    100,
    100,
    '2026-09-16',
    '2027-09-16',
    'VIGENTE'
),
(
    1,
    2,
    'LOT-ACE-002',
    50,
    50,
    '2026-09-16',
    '2026-10-10',
    'PROXIMO_VENCER'
),
(
    2,
    1,
    'LOT-IBU-001',
    80,
    80,
    '2026-09-16',
    '2028-01-20',
    'VIGENTE'
),
(
    3,
    2,
    'LOT-LOR-001',
    60,
    60,
    '2026-09-16',
    '2027-05-15',
    'VIGENTE'
);


-- =========================================================
-- 19. VISTA DE INVENTARIO
-- =========================================================

CREATE VIEW vista_inventario AS
SELECT
    l.id_lote,
    m.id_medicamento,
    m.nombre AS medicamento,
    m.presentacion,
    m.concentracion,
    m.codigo_barras,

    l.numero_lote,

    p.id_proveedor,
    p.nombre AS proveedor,

    l.cantidad_inicial,
    l.cantidad_disponible,

    l.fecha_ingreso,
    l.fecha_vencimiento,

    DATEDIFF(
        l.fecha_vencimiento,
        CURDATE()
    ) AS dias_para_vencer,

    l.estado

FROM lote l

INNER JOIN medicamento m
    ON l.id_medicamento = m.id_medicamento

INNER JOIN proveedor p
    ON l.id_proveedor = p.id_proveedor;


-- =========================================================
-- 20. VISTA DE TRAZABILIDAD
-- =========================================================

CREATE VIEW vista_trazabilidad AS
SELECT

    l.id_lote,
    l.numero_lote,

    m.id_medicamento,
    m.nombre AS medicamento,
    m.presentacion,
    m.concentracion,
    m.codigo_barras,

    p.id_proveedor,
    p.nombre AS proveedor,

    l.cantidad_inicial,
    l.cantidad_disponible,

    l.fecha_ingreso,
    l.fecha_vencimiento,
    l.estado AS estado_lote,

    f.id_factura,
    f.numero_factura,
    f.tipo AS tipo_factura,
    f.fecha AS fecha_factura,

    df.cantidad,
    df.precio_unitario,
    df.subtotal,

    mi.id_movimiento,
    mi.tipo_movimiento,
    mi.cantidad AS cantidad_movimiento,
    mi.fecha AS fecha_movimiento,
    mi.descripcion

FROM lote l

INNER JOIN medicamento m
    ON l.id_medicamento = m.id_medicamento

INNER JOIN proveedor p
    ON l.id_proveedor = p.id_proveedor

LEFT JOIN detalle_factura df
    ON l.id_lote = df.id_lote

LEFT JOIN factura f
    ON df.id_factura = f.id_factura

LEFT JOIN movimiento_inventario mi
    ON l.id_lote = mi.id_lote;


-- =========================================================
-- 21. VISTA DE ALERTAS DE VENCIMIENTO
-- =========================================================

CREATE VIEW vista_alertas_vencimiento AS
SELECT

    l.id_lote,
    l.numero_lote,

    m.id_medicamento,
    m.nombre AS medicamento,

    p.nombre AS proveedor,

    l.cantidad_disponible,

    l.fecha_vencimiento,

    DATEDIFF(
        l.fecha_vencimiento,
        CURDATE()
    ) AS dias_restantes,

    CASE

        WHEN DATEDIFF(
            l.fecha_vencimiento,
            CURDATE()
        ) < 0
        THEN 'VENCIDO'

        WHEN DATEDIFF(
            l.fecha_vencimiento,
            CURDATE()
        ) <= ca.dias_anticipacion
        THEN 'PROXIMO_VENCER'

        ELSE 'VIGENTE'

    END AS nivel_alerta

FROM lote l

INNER JOIN medicamento m
    ON l.id_medicamento = m.id_medicamento

INNER JOIN proveedor p
    ON l.id_proveedor = p.id_proveedor

CROSS JOIN configuracion_alerta ca

WHERE ca.estado = 'ACTIVA';


-- =========================================================
-- 22. VISTA PARA DASHBOARD
-- =========================================================

CREATE VIEW vista_dashboard AS

SELECT

    (
        SELECT COUNT(*)
        FROM medicamento
        WHERE estado = 'ACTIVO'
    ) AS total_medicamentos,

    (
        SELECT COALESCE(
            SUM(cantidad_disponible),
            0
        )
        FROM lote
        WHERE estado <> 'VENCIDO'
    ) AS unidades_disponibles,

    (
        SELECT COUNT(*)
        FROM lote l
        CROSS JOIN configuracion_alerta ca
        WHERE
            ca.estado = 'ACTIVA'
            AND DATEDIFF(
                l.fecha_vencimiento,
                CURDATE()
            ) BETWEEN 0 AND ca.dias_anticipacion
    ) AS lotes_proximos_vencer,

    (
        SELECT COUNT(*)
        FROM lote
        WHERE fecha_vencimiento < CURDATE()
    ) AS lotes_vencidos,

    (
        SELECT COUNT(*)
        FROM proveedor
        WHERE estado = 'ACTIVO'
    ) AS proveedores_activos;


-- =========================================================
-- 23. CONSULTAS DE VERIFICACION
-- =========================================================

-- Ver tablas
SHOW TABLES;

-- Ver roles
SELECT * FROM rol;

-- Ver usuarios
SELECT
    u.id_usuario,
    u.nombre,
    u.apellido,
    u.usuario,
    r.nombre AS rol,
    u.estado
FROM usuario u
INNER JOIN rol r
    ON u.id_rol = r.id_rol;

-- Ver medicamentos
SELECT * FROM medicamento;

-- Ver proveedores
SELECT * FROM proveedor;

-- Ver lotes
SELECT * FROM lote;

-- Ver inventario
SELECT * FROM vista_inventario;

-- Ver alertas
SELECT * FROM vista_alertas_vencimiento;

-- Ver dashboard
SELECT * FROM vista_dashboard;