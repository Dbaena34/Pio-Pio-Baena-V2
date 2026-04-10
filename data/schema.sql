-- ============================================
-- SISTEMA DE GESTIÓN GRANJA PONEDORA
-- Esquema de Base de Datos SQLite
-- ============================================

-- Tabla de producción diaria
CREATE TABLE IF NOT EXISTS produccion_diaria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    tipo_c INTEGER DEFAULT 0,
    tipo_b INTEGER DEFAULT 0,
    tipo_a INTEGER DEFAULT 0,
    tipo_aa INTEGER DEFAULT 0,
    tipo_aaa INTEGER DEFAULT 0,
    tipo_jumbo INTEGER DEFAULT 0,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de stock actual de huevos
CREATE TABLE IF NOT EXISTS stock_huevos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    tipo_c INTEGER DEFAULT 0,
    tipo_b INTEGER DEFAULT 0,
    tipo_a INTEGER DEFAULT 0,
    tipo_aa INTEGER DEFAULT 0,
    tipo_aaa INTEGER DEFAULT 0,
    tipo_jumbo INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de registro de población de gallinas
CREATE TABLE IF NOT EXISTS poblacion_gallinas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    cantidad_gallinas INTEGER NOT NULL,
    descartes INTEGER DEFAULT 0,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de consumo de alimento diario
CREATE TABLE IF NOT EXISTS consumo_alimento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    consumo_por_gallina REAL NOT NULL,  -- en gramos
    cantidad_gallinas INTEGER NOT NULL,  -- snapshot de cuántas gallinas había ese día
    consumo_total REAL NOT NULL,  -- calculado automáticamente
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Tabla de precios históricos por categoría
CREATE TABLE IF NOT EXISTS precios_huevos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_vigencia DATE NOT NULL,
    precio_c REAL NOT NULL,
    precio_b REAL NOT NULL,
    precio_a REAL NOT NULL,
    precio_aa REAL NOT NULL,
    precio_aaa REAL NOT NULL,
    precio_jumbo REAL NOT NULL,
    activo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    contacto TEXT,
    activo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de trabajadores
CREATE TABLE IF NOT EXISTS trabajadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    cargo TEXT,
    activo BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de pedidos
-- Tabla de pedidos
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    canastillas_c INTEGER DEFAULT 0,
    canastillas_b INTEGER DEFAULT 0,
    canastillas_a INTEGER DEFAULT 0,
    canastillas_aa INTEGER DEFAULT 0,
    canastillas_aaa INTEGER DEFAULT 0,
    canastillas_jumbo INTEGER DEFAULT 0,
    precio_total REAL NOT NULL,
    estado TEXT DEFAULT 'pendiente' CHECK(estado IN ('pendiente', 'completado', 'cancelado')),
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- Tabla de despachos
CREATE TABLE IF NOT EXISTS despachos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    canastillas_c INTEGER DEFAULT 0,
    canastillas_b INTEGER DEFAULT 0,
    canastillas_a INTEGER DEFAULT 0,
    canastillas_aa INTEGER DEFAULT 0,
    canastillas_aaa INTEGER DEFAULT 0,
    canastillas_jumbo INTEGER DEFAULT 0,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
);

-- Tabla de insumos
CREATE TABLE IF NOT EXISTS insumos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL CHECK(categoria IN ('Alimento', 'Medicamento', 'Mantenimiento', 'Canstillas','Otros')),
    cantidad REAL NOT NULL,
    unidad TEXT NOT NULL CHECK(unidad IN ('kg', 'bultos', 'litros', 'unidades')),
    costo_unitario REAL NOT NULL,
    costo_total REAL NOT NULL,
    fecha_compra DATE NOT NULL,
    proveedor TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de stock de insumos
CREATE TABLE IF NOT EXISTS stock_insumos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insumo_id INTEGER NOT NULL,
    cantidad_actual REAL NOT NULL,
    stock_minimo REAL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (insumo_id) REFERENCES insumos(id)
);

-- Tabla de pagos a trabajadores
CREATE TABLE IF NOT EXISTS pagos_trabajadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trabajador_id INTEGER NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    monto REAL NOT NULL,
    concepto TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trabajador_id) REFERENCES trabajadores(id)
);

-- Tabla de movimientos financieros
CREATE TABLE IF NOT EXISTS movimientos_financieros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('ingreso', 'egreso')),
    categoria TEXT NOT NULL,
    monto REAL NOT NULL,
    descripcion TEXT,
    referencia_id INTEGER,
    referencia_tabla TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- ÍNDICES PARA OPTIMIZAR CONSULTAS
-- ============================================

CREATE INDEX idx_produccion_fecha ON produccion_diaria(fecha);
CREATE INDEX idx_pedidos_cliente ON pedidos(cliente_id);
CREATE INDEX idx_pedidos_estado ON pedidos(estado);
CREATE INDEX idx_pedidos_fecha ON pedidos(fecha);
CREATE INDEX idx_despachos_pedido ON despachos(pedido_id);
CREATE INDEX idx_movimientos_fecha ON movimientos_financieros(fecha);
CREATE INDEX idx_movimientos_tipo ON movimientos_financieros(tipo);
CREATE INDEX idx_precios_activo ON precios_huevos(activo);
CREATE INDEX idx_poblacion_fecha ON poblacion_gallinas(fecha);
CREATE INDEX idx_consumo_fecha ON consumo_alimento(fecha);
-- ============================================
-- TRIGGERS AUTOMÁTICOS
-- ============================================

-- Trigger: Actualizar stock cuando se registra producción
CREATE TRIGGER IF NOT EXISTS update_stock_after_produccion
AFTER INSERT ON produccion_diaria
BEGIN
    UPDATE stock_huevos 
    SET 
        tipo_c = tipo_c + NEW.tipo_c,
        tipo_b = tipo_b + NEW.tipo_b,
        tipo_a = tipo_a + NEW.tipo_a,
        tipo_aa = tipo_aa + NEW.tipo_aa,
        tipo_aaa = tipo_aaa + NEW.tipo_aaa,
        tipo_jumbo = tipo_jumbo + NEW.tipo_jumbo,
        fecha = NEW.fecha,
        hora = NEW.hora,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = 1;
END;

-- Trigger: Descontar stock cuando se completa un despacho (REEMPLAZAR el existente)
DROP TRIGGER IF EXISTS update_stock_after_despacho;

CREATE TRIGGER update_stock_after_despacho
AFTER INSERT ON despachos
BEGIN
    UPDATE stock_huevos 
    SET 
        tipo_c = tipo_c - (NEW.canastillas_c * 30),
        tipo_b = tipo_b - (NEW.canastillas_b * 30),
        tipo_a = tipo_a - (NEW.canastillas_a * 30),
        tipo_aa = tipo_aa - (NEW.canastillas_aa * 30),
        tipo_aaa = tipo_aaa - (NEW.canastillas_aaa * 30),
        tipo_jumbo = tipo_jumbo - (NEW.canastillas_jumbo * 30),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = 1;
    
    -- Actualizar estado del pedido a completado
    UPDATE pedidos 
    SET estado = 'completado'
    WHERE id = NEW.pedido_id;
END;

-- Trigger: Registrar ingreso cuando se completa un pedido
CREATE TRIGGER IF NOT EXISTS register_ingreso_after_despacho
AFTER INSERT ON despachos
BEGIN
    INSERT INTO movimientos_financieros (fecha, tipo, categoria, monto, descripcion, referencia_id, referencia_tabla)
    SELECT 
        NEW.fecha,
        'ingreso',
        'Venta de huevos',
        p.precio_total,
        'Venta pedido #' || NEW.pedido_id || ' - ' || c.nombre,
        NEW.pedido_id,
        'pedidos'
    FROM pedidos p
    JOIN clientes c ON p.cliente_id = c.id
    WHERE p.id = NEW.pedido_id;
END;

-- Trigger: Registrar egreso cuando se compra insumo
CREATE TRIGGER IF NOT EXISTS register_egreso_after_insumo
AFTER INSERT ON insumos
BEGIN
    INSERT INTO movimientos_financieros (fecha, tipo, categoria, monto, descripcion, referencia_id, referencia_tabla)
    VALUES (
        NEW.fecha_compra,
        'egreso',
        'Compra de ' || NEW.categoria,
        NEW.costo_total,
        NEW.nombre || ' - ' || NEW.cantidad || ' ' || NEW.unidad,
        NEW.id,
        'insumos'
    );
    
    -- Actualizar o crear registro en stock_insumos
    INSERT OR REPLACE INTO stock_insumos (id, insumo_id, cantidad_actual, stock_minimo)
    VALUES (
        (SELECT id FROM stock_insumos WHERE insumo_id = NEW.id),
        NEW.id,
        COALESCE((SELECT cantidad_actual FROM stock_insumos WHERE insumo_id = NEW.id), 0) + NEW.cantidad,
        COALESCE((SELECT stock_minimo FROM stock_insumos WHERE insumo_id = NEW.id), 0)
    );
END;

-- Trigger: Registrar egreso cuando se paga a trabajador
CREATE TRIGGER IF NOT EXISTS register_egreso_after_pago
AFTER INSERT ON pagos_trabajadores
BEGIN
    INSERT INTO movimientos_financieros (fecha, tipo, categoria, monto, descripcion, referencia_id, referencia_tabla)
    SELECT 
        NEW.fecha,
        'egreso',
        'Pago a trabajador',
        NEW.monto,
        'Pago a ' || t.nombre || ' - ' || COALESCE(NEW.concepto, 'Sin concepto'),
        NEW.id,
        'pagos_trabajadores'
    FROM trabajadores t
    WHERE t.id = NEW.trabajador_id;
END;

-- Trigger: Desactivar precio anterior cuando se crea uno nuevo
CREATE TRIGGER IF NOT EXISTS deactivate_old_prices
AFTER INSERT ON precios_huevos
WHEN NEW.activo = 1
BEGIN
    UPDATE precios_huevos 
    SET activo = 0
    WHERE id != NEW.id AND activo = 1;
END;

-- Tabla de ajustes de stock de huevos
CREATE TABLE IF NOT EXISTS ajustes_stock_huevos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    tipo_ajuste TEXT NOT NULL CHECK(tipo_ajuste IN ('merma', 'correccion')),
    tipo_c INTEGER DEFAULT 0,
    tipo_b INTEGER DEFAULT 0,
    tipo_a INTEGER DEFAULT 0,
    tipo_aa INTEGER DEFAULT 0,
    tipo_aaa INTEGER DEFAULT 0,
    tipo_jumbo INTEGER DEFAULT 0,
    motivo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de movimientos de insumos
CREATE TABLE IF NOT EXISTS movimientos_insumos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    insumo_id INTEGER NOT NULL,
    tipo_movimiento TEXT NOT NULL CHECK(tipo_movimiento IN ('entrada', 'salida')),
    cantidad REAL NOT NULL,
    motivo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (insumo_id) REFERENCES insumos(id)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_ajustes_fecha ON ajustes_stock_huevos(fecha);
CREATE INDEX IF NOT EXISTS idx_movimientos_insumos_fecha ON movimientos_insumos(fecha);


-- ============================================
-- DATOS INICIALES
-- ============================================

-- Inicializar stock de huevos en 0
INSERT OR IGNORE INTO stock_huevos (id, fecha, hora, tipo_c, tipo_b, tipo_a, tipo_aa, tipo_aaa, tipo_jumbo)
VALUES (1, date('now'), time('now'), 0, 0, 0, 0, 0, 0);

-- Precio inicial (ajustar según necesidad)
INSERT OR IGNORE INTO precios_huevos (fecha_vigencia, precio_c, precio_b, precio_a, precio_aa, precio_aaa, precio_jumbo, activo)
VALUES (date('now'), 300, 350, 400, 450, 500, 550, 1);