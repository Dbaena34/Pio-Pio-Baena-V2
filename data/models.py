"""
Modelos de repositorio para acceso a datos.
Cada clase Repository maneja las operaciones CRUD de una tabla específica.
"""

from datetime import datetime, date
from typing import List, Dict, Optional


class ProduccionRepository:
    """Repositorio para gestionar la producción diaria de huevos"""
    
    def __init__(self, db):
        self.db = db
    
    def registrar_produccion(self, fecha: date, hora: str, 
                            tipo_c: int, tipo_b: int, tipo_a: int,
                            tipo_aa: int, tipo_aaa: int, tipo_jumbo: int,
                            observaciones: str = None) -> int:
        """
        Registra la producción diaria.
        El trigger automáticamente actualiza el stock.
        
        Args:
            hora: Hora en formato string "HH:MM:SS"
        
        Returns:
            int: ID del registro creado
        """
        query = """
            INSERT INTO produccion_diaria 
            (fecha, hora, tipo_c, tipo_b, tipo_a, tipo_aa, tipo_aaa, tipo_jumbo, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.db.execute_insert(query, (
            fecha, hora, tipo_c, tipo_b, tipo_a, tipo_aa, tipo_aaa, tipo_jumbo, observaciones
        ))
    
    def obtener_produccion_por_fecha(self, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """Obtiene la producción entre dos fechas"""
        query = """
            SELECT * FROM produccion_diaria
            WHERE fecha BETWEEN ? AND ?
            ORDER BY fecha DESC, hora DESC
        """
        return self.db.execute_query(query, (fecha_inicio, fecha_fin))
    
    def obtener_produccion_del_dia(self, fecha: date) -> List[Dict]:
        """Obtiene la producción de un día específico"""
        query = "SELECT * FROM produccion_diaria WHERE fecha = ? ORDER BY hora DESC"
        return self.db.execute_query(query, (fecha,))
    
    def obtener_total_produccion_periodo(self, fecha_inicio: date, fecha_fin: date) -> Dict:
        """Obtiene el total de producción en un período"""
        query = """
            SELECT 
                SUM(tipo_c) as total_c,
                SUM(tipo_b) as total_b,
                SUM(tipo_a) as total_a,
                SUM(tipo_aa) as total_aa,
                SUM(tipo_aaa) as total_aaa,
                SUM(tipo_jumbo) as total_jumbo,
                COUNT(*) as dias_registrados
            FROM produccion_diaria
            WHERE fecha BETWEEN ? AND ?
        """
        result = self.db.execute_query(query, (fecha_inicio, fecha_fin))
        return result[0] if result else {}


class StockRepository:
    """Repositorio para gestionar el stock de huevos e insumos"""
    
    def __init__(self, db):
        self.db = db
    
    def obtener_stock_actual(self) -> Dict:
        """Obtiene el stock actual de huevos"""
        query = "SELECT * FROM stock_huevos WHERE id = 1"
        result = self.db.execute_query(query)
        return result[0] if result else {}
    
    def ajustar_stock_manual(self, tipo_c: int = 0, tipo_b: int = 0, 
                            tipo_a: int = 0, tipo_aa: int = 0,
                            tipo_aaa: int = 0, tipo_jumbo: int = 0,
                            razon: str = "Ajuste manual") -> int:
        """
        Ajusta el stock manualmente (para mermas, roturas, etc.)
        Valores negativos descuentan, positivos suman.
        """
        query = """
            UPDATE stock_huevos 
            SET tipo_c = tipo_c + ?,
                tipo_b = tipo_b + ?,
                tipo_a = tipo_a + ?,
                tipo_aa = tipo_aa + ?,
                tipo_aaa = tipo_aaa + ?,
                tipo_jumbo = tipo_jumbo + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """
        return self.db.execute_update(query, (tipo_c, tipo_b, tipo_a, tipo_aa, tipo_aaa, tipo_jumbo))
    
    def obtener_stock_insumos(self) -> List[Dict]:
        """Obtiene el stock de todos los insumos"""
        query = """
            SELECT 
                si.id,
                si.insumo_id,
                i.nombre,
                i.categoria,
                i.unidad,
                si.cantidad_actual,
                si.stock_minimo,
                CASE 
                    WHEN si.cantidad_actual <= si.stock_minimo THEN 1
                    ELSE 0
                END as alerta_stock
            FROM stock_insumos si
            JOIN insumos i ON si.insumo_id = i.id
            ORDER BY i.categoria, i.nombre
        """
        return self.db.execute_query(query)
    
    def obtener_alertas_stock(self) -> List[Dict]:
        """Obtiene insumos con stock bajo"""
        query = """
            SELECT 
                si.id,
                i.nombre,
                i.categoria,
                si.cantidad_actual,
                si.stock_minimo,
                i.unidad
            FROM stock_insumos si
            JOIN insumos i ON si.insumo_id = i.id
            WHERE si.cantidad_actual <= si.stock_minimo
            ORDER BY i.categoria, i.nombre
        """
        return self.db.execute_query(query)
    
    def registrar_ajuste_huevos(self, tipo_ajuste: str, tipo_c: int = 0, tipo_b: int = 0,
                                tipo_a: int = 0, tipo_aa: int = 0, tipo_aaa: int = 0,
                                tipo_jumbo: int = 0, motivo: str = None) -> int:
        """
        Registra un ajuste de stock de huevos y lo aplica.
        
        Args:
            tipo_ajuste: 'merma' o 'correccion'
            Los valores pueden ser positivos (corrección al alza) o negativos (mermas)
        """
        # Primero ajustar el stock
        self.ajustar_stock_manual(tipo_c, tipo_b, tipo_a, tipo_aa, tipo_aaa, tipo_jumbo, motivo)
        
        # Registrar el ajuste en una tabla de historial
        query = """
            INSERT INTO ajustes_stock_huevos 
            (fecha, hora, tipo_ajuste, tipo_c, tipo_b, tipo_a, tipo_aa, tipo_aaa, tipo_jumbo, motivo)
            VALUES (date('now'), time('now'), ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.db.execute_insert(query, (tipo_ajuste, tipo_c, tipo_b, tipo_a, tipo_aa, tipo_aaa, tipo_jumbo, motivo))
    
    def obtener_historial_ajustes_huevos(self, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """Obtiene el historial de ajustes de stock de huevos"""
        query = """
            SELECT * FROM ajustes_stock_huevos
            WHERE fecha BETWEEN ? AND ?
            ORDER BY fecha DESC, hora DESC
        """
        return self.db.execute_query(query, (fecha_inicio, fecha_fin))
    
    def registrar_consumo_insumo(self, insumo_id: int, cantidad: float, motivo: str = None) -> int:
        """
        Registra un consumo/salida de insumo y descuenta del stock.
        Cantidad debe ser positiva (se descuenta automáticamente).
        """
        # Descontar del stock
        query_update = """
            UPDATE stock_insumos 
            SET cantidad_actual = cantidad_actual - ?
            WHERE insumo_id = ?
        """
        self.db.execute_update(query_update, (cantidad, insumo_id))
        
        # Registrar el movimiento
        query_insert = """
            INSERT INTO movimientos_insumos 
            (fecha, hora, insumo_id, tipo_movimiento, cantidad, motivo)
            VALUES (date('now'), time('now'), ?, 'salida', ?, ?)
        """
        return self.db.execute_insert(query_insert, (insumo_id, cantidad, motivo))
    
    def obtener_historial_movimientos_insumos(self, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """Obtiene el historial de movimientos de insumos"""
        query = """
            SELECT 
                m.*,
                i.nombre as insumo_nombre,
                i.categoria,
                i.unidad
            FROM movimientos_insumos m
            JOIN insumos i ON m.insumo_id = i.id
            WHERE m.fecha BETWEEN ? AND ?
            ORDER BY m.fecha DESC, m.hora DESC
        """
        return self.db.execute_query(query, (fecha_inicio, fecha_fin))
    
    def ajustar_stock_insumo(self, insumo_id: int, nueva_cantidad: float, motivo: str = "Ajuste manual") -> int:
        """Ajusta el stock de un insumo a una cantidad específica"""
        query = """
            UPDATE stock_insumos 
            SET cantidad_actual = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE insumo_id = ?
        """
        return self.db.execute_update(query, (nueva_cantidad, insumo_id))
    
    def actualizar_stock_minimo(self, insumo_id: int, stock_minimo: float) -> int:
        """Actualiza el stock mínimo de un insumo"""
        query = """
            UPDATE stock_insumos 
            SET stock_minimo = ?
            WHERE insumo_id = ?
        """
        return self.db.execute_update(query, (stock_minimo, insumo_id))


class ClientesRepository:
    """Repositorio para gestionar clientes"""
    
    def __init__(self, db):
        self.db = db
    
    def crear_cliente(self, nombre: str, contacto: str = None) -> int:
        """Crea un nuevo cliente"""
        query = "INSERT INTO clientes (nombre, contacto) VALUES (?, ?)"
        return self.db.execute_insert(query, (nombre, contacto))
    
    def obtener_clientes_activos(self) -> List[Dict]:
        """Obtiene todos los clientes activos"""
        query = "SELECT * FROM clientes WHERE activo = 1 ORDER BY nombre"
        return self.db.execute_query(query)
    
    def obtener_cliente(self, cliente_id: int) -> Dict:
        """Obtiene un cliente específico"""
        query = "SELECT * FROM clientes WHERE id = ?"
        result = self.db.execute_query(query, (cliente_id,))
        return result[0] if result else {}
    
    def actualizar_cliente(self, cliente_id: int, nombre: str, contacto: str = None) -> int:
        """Actualiza los datos de un cliente"""
        query = "UPDATE clientes SET nombre = ?, contacto = ? WHERE id = ?"
        return self.db.execute_update(query, (nombre, contacto, cliente_id))
    
    def desactivar_cliente(self, cliente_id: int) -> int:
        """Desactiva un cliente (no lo elimina)"""
        query = "UPDATE clientes SET activo = 0 WHERE id = ?"
        return self.db.execute_update(query, (cliente_id,))
    
    def obtener_historial_cliente(self, cliente_id: int) -> List[Dict]:
        """Obtiene el historial de pedidos de un cliente"""
        query = """
            SELECT 
                p.*,
                (p.cantidad_c + p.cantidad_b + p.cantidad_a + 
                 p.cantidad_aa + p.cantidad_aaa + p.cantidad_jumbo) as total_huevos
            FROM pedidos p
            WHERE p.cliente_id = ?
            ORDER BY p.fecha DESC, p.hora DESC
        """
        return self.db.execute_query(query, (cliente_id,))


class TrabajadoresRepository:
    """Repositorio para gestionar trabajadores"""
    
    def __init__(self, db):
        self.db = db
    
    def crear_trabajador(self, nombre: str, cargo: str = None) -> int:
        """Crea un nuevo trabajador"""
        query = "INSERT INTO trabajadores (nombre, cargo) VALUES (?, ?)"
        return self.db.execute_insert(query, (nombre, cargo))
    
    def obtener_trabajadores_activos(self) -> List[Dict]:
        """Obtiene todos los trabajadores activos"""
        query = "SELECT * FROM trabajadores WHERE activo = 1 ORDER BY nombre"
        return self.db.execute_query(query)
    
    def obtener_trabajador(self, trabajador_id: int) -> Dict:
        """Obtiene un trabajador específico"""
        query = "SELECT * FROM trabajadores WHERE id = ?"
        result = self.db.execute_query(query, (trabajador_id,))
        return result[0] if result else {}
    
    def actualizar_trabajador(self, trabajador_id: int, nombre: str, cargo: str = None) -> int:
        """Actualiza los datos de un trabajador"""
        query = "UPDATE trabajadores SET nombre = ?, cargo = ? WHERE id = ?"
        return self.db.execute_update(query, (nombre, cargo, trabajador_id))


class PreciosRepository:
    """Repositorio para gestionar precios de huevos"""
    
    def __init__(self, db):
        self.db = db
    
    def obtener_precio_actual(self) -> Dict:
        """Obtiene el precio activo actual"""
        query = "SELECT * FROM precios_huevos WHERE activo = 1"
        result = self.db.execute_query(query)
        return result[0] if result else {}
    
    def crear_nuevo_precio(self, fecha_vigencia: date,
                          precio_c: float, precio_b: float, precio_a: float,
                          precio_aa: float, precio_aaa: float, precio_jumbo: float) -> int:
        """
        Crea un nuevo precio (el trigger automáticamente desactiva el anterior)
        """
        query = """
            INSERT INTO precios_huevos 
            (fecha_vigencia, precio_c, precio_b, precio_a, precio_aa, precio_aaa, precio_jumbo, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """
        return self.db.execute_insert(query, (
            fecha_vigencia, precio_c, precio_b, precio_a, precio_aa, precio_aaa, precio_jumbo
        ))
    
    def obtener_historial_precios(self, limit: int = 10) -> List[Dict]:
        """Obtiene el historial de precios (limitado)"""
        query = f"SELECT * FROM precios_huevos ORDER BY fecha_vigencia DESC LIMIT {limit}"
        return self.db.execute_query(query)

class PedidosRepository:
    """Repositorio para gestionar pedidos y despachos"""
    
    def __init__(self, db):
        self.db = db
    
    def crear_pedido(self, cliente_id: int, fecha: date, hora: str,
                    canastillas_c: int, canastillas_b: int, canastillas_a: int,
                    canastillas_aa: int, canastillas_aaa: int, canastillas_jumbo: int,
                    precio_total: float, observaciones: str = None) -> int:
        """Crea un nuevo pedido (en canastillas)"""
        query = """
            INSERT INTO pedidos 
            (cliente_id, fecha, hora, canastillas_c, canastillas_b, canastillas_a, 
             canastillas_aa, canastillas_aaa, canastillas_jumbo, precio_total, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.db.execute_insert(query, (
            cliente_id, fecha, hora, canastillas_c, canastillas_b, canastillas_a,
            canastillas_aa, canastillas_aaa, canastillas_jumbo, precio_total, observaciones
        ))
    
    def obtener_pedidos_pendientes(self) -> List[Dict]:
        """Obtiene todos los pedidos pendientes con datos del cliente"""
        query = """
            SELECT 
                p.*,
                c.nombre as cliente_nombre,
                c.contacto as cliente_contacto,
                (p.canastillas_c + p.canastillas_b + p.canastillas_a + 
                 p.canastillas_aa + p.canastillas_aaa + p.canastillas_jumbo) as total_canastillas
            FROM pedidos p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.estado = 'pendiente'
            ORDER BY p.fecha ASC, p.hora ASC
        """
        return self.db.execute_query(query)
    
    def obtener_pedido(self, pedido_id: int) -> Dict:
        """Obtiene un pedido específico con datos del cliente"""
        query = """
            SELECT 
                p.*,
                c.nombre as cliente_nombre,
                c.contacto as cliente_contacto
            FROM pedidos p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = ?
        """
        result = self.db.execute_query(query, (pedido_id,))
        return result[0] if result else {}
    
    def actualizar_pedido(self, pedido_id: int, canastillas_c: int, canastillas_b: int,
                         canastillas_a: int, canastillas_aa: int, canastillas_aaa: int,
                         canastillas_jumbo: int, precio_total: float, observaciones: str = None) -> int:
        """Actualiza un pedido pendiente"""
        query = """
            UPDATE pedidos 
            SET canastillas_c = ?, canastillas_b = ?, canastillas_a = ?,
                canastillas_aa = ?, canastillas_aaa = ?, canastillas_jumbo = ?,
                precio_total = ?, observaciones = ?
            WHERE id = ? AND estado = 'pendiente'
        """
        return self.db.execute_update(query, (
            canastillas_c, canastillas_b, canastillas_a, canastillas_aa, 
            canastillas_aaa, canastillas_jumbo, precio_total, observaciones, pedido_id
        ))
    
    def cancelar_pedido(self, pedido_id: int) -> int:
        """Cancela un pedido"""
        query = "UPDATE pedidos SET estado = 'cancelado' WHERE id = ?"
        return self.db.execute_update(query, (pedido_id,))
    
    def despachar_pedido(self, pedido_id: int, fecha: date, hora: str,
                        canastillas_c: int, canastillas_b: int, canastillas_a: int,
                        canastillas_aa: int, canastillas_aaa: int, canastillas_jumbo: int,
                        observaciones: str = None) -> int:
        """
        Registra un despacho.
        El trigger automáticamente:
        - Descuenta el stock (canastillas * 30)
        - Marca el pedido como completado
        - Registra el ingreso
        """
        query = """
            INSERT INTO despachos 
            (pedido_id, fecha, hora, canastillas_c, canastillas_b, canastillas_a,
             canastillas_aa, canastillas_aaa, canastillas_jumbo, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.db.execute_insert(query, (
            pedido_id, fecha, hora, canastillas_c, canastillas_b, canastillas_a,
            canastillas_aa, canastillas_aaa, canastillas_jumbo, observaciones
        ))
    
    def obtener_historial_ventas(self, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """Obtiene el historial de ventas completadas en un período"""
        query = """
            SELECT 
                p.*,
                c.nombre as cliente_nombre,
                d.fecha as fecha_despacho,
                d.hora as hora_despacho,
                (p.canastillas_c + p.canastillas_b + p.canastillas_a + 
                 p.canastillas_aa + p.canastillas_aaa + p.canastillas_jumbo) as total_canastillas
            FROM pedidos p
            JOIN clientes c ON p.cliente_id = c.id
            LEFT JOIN despachos d ON p.id = d.pedido_id
            WHERE p.estado = 'completado' 
            AND p.fecha BETWEEN ? AND ?
            ORDER BY p.fecha DESC
        """
        return self.db.execute_query(query, (fecha_inicio, fecha_fin))

class InsumosRepository:
    """Repositorio para gestionar insumos y pagos"""
    
    def __init__(self, db):
        self.db = db
    
    def registrar_compra_insumo(self, nombre: str, categoria: str, cantidad: float,
                               unidad: str, costo_unitario: float, costo_total: float,
                               fecha_compra: date, proveedor: str = None) -> int:
        """
        Registra una compra de insumo.
        El trigger automáticamente registra el egreso y actualiza el stock.
        """
        query = """
            INSERT INTO insumos 
            (nombre, categoria, cantidad, unidad, costo_unitario, costo_total, fecha_compra, proveedor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.db.execute_insert(query, (
            nombre, categoria, cantidad, unidad, costo_unitario, costo_total, fecha_compra, proveedor
        ))
    
    def obtener_historial_compras(self, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """Obtiene el historial de compras en un período"""
        query = """
            SELECT * FROM insumos
            WHERE fecha_compra BETWEEN ? AND ?
            ORDER BY fecha_compra DESC
        """
        return self.db.execute_query(query, (fecha_inicio, fecha_fin))
    
    def obtener_compras_por_categoria(self, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """Obtiene el total de compras agrupado por categoría"""
        query = """
            SELECT 
                categoria,
                COUNT(*) as cantidad_compras,
                SUM(costo_total) as total_gastado
            FROM insumos
            WHERE fecha_compra BETWEEN ? AND ?
            GROUP BY categoria
            ORDER BY total_gastado DESC
        """
        return self.db.execute_query(query, (fecha_inicio, fecha_fin))
    
    def registrar_pago_trabajador(self, trabajador_id: int, fecha: date, hora: str,
                                 monto: float, concepto: str = None) -> int:
        """
        Registra un pago a trabajador.
        El trigger automáticamente registra el egreso.
        """
        query = """
            INSERT INTO pagos_trabajadores (trabajador_id, fecha, hora, monto, concepto)
            VALUES (?, ?, ?, ?, ?)
        """
        return self.db.execute_insert(query, (trabajador_id, fecha, hora, monto, concepto))
    
    def obtener_historial_pagos(self, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """Obtiene el historial de pagos en un período"""
        query = """
            SELECT 
                p.*,
                t.nombre as trabajador_nombre,
                t.cargo
            FROM pagos_trabajadores p
            JOIN trabajadores t ON p.trabajador_id = t.id
            WHERE p.fecha BETWEEN ? AND ?
            ORDER BY p.fecha DESC, p.hora DESC
        """
        return self.db.execute_query(query, (fecha_inicio, fecha_fin))
    
    def obtener_pagos_por_trabajador(self, trabajador_id: int, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """Obtiene el historial de pagos de un trabajador específico"""
        query = """
            SELECT * FROM pagos_trabajadores
            WHERE trabajador_id = ? AND fecha BETWEEN ? AND ?
            ORDER BY fecha DESC, hora DESC
        """
        return self.db.execute_query(query, (trabajador_id, fecha_inicio, fecha_fin))
    
    def obtener_total_pagos_trabajador(self, trabajador_id: int, fecha_inicio: date, fecha_fin: date) -> float:
        """Obtiene el total pagado a un trabajador en un período"""
        query = """
            SELECT COALESCE(SUM(monto), 0) as total
            FROM pagos_trabajadores
            WHERE trabajador_id = ? AND fecha BETWEEN ? AND ?
        """
        result = self.db.execute_query(query, (trabajador_id, fecha_inicio, fecha_fin))
        return result[0]['total'] if result else 0

class ReportesRepository:
    """Repositorio para generar reportes y análisis"""
    
    def __init__(self, db):
        self.db = db
    
    def obtener_balance_periodo(self, fecha_inicio: date, fecha_fin: date) -> Dict:
        """Obtiene el balance financiero de un período"""
        query = """
            SELECT 
                SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END) as total_ingresos,
                SUM(CASE WHEN tipo = 'egreso' THEN monto ELSE 0 END) as total_egresos,
                SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE -monto END) as balance
            FROM movimientos_financieros
            WHERE fecha BETWEEN ? AND ?
        """
        result = self.db.execute_query(query, (fecha_inicio, fecha_fin))
        return result[0] if result else {}
    
    def obtener_movimientos_por_categoria(self, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """Obtiene los movimientos agrupados por categoría"""
        query = """
            SELECT 
                tipo,
                categoria,
                SUM(monto) as total,
                COUNT(*) as cantidad_movimientos
            FROM movimientos_financieros
            WHERE fecha BETWEEN ? AND ?
            GROUP BY tipo, categoria
            ORDER BY tipo, total DESC
        """
        return self.db.execute_query(query, (fecha_inicio, fecha_fin))
    
    def obtener_todos_movimientos(self, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """Obtiene todos los movimientos de un período"""
        query = """
            SELECT * FROM movimientos_financieros
            WHERE fecha BETWEEN ? AND ?
            ORDER BY fecha DESC, created_at DESC
        """
        return self.db.execute_query(query, (fecha_inicio, fecha_fin))
    
    def obtener_resumen_produccion_ventas(self, fecha_inicio: date, fecha_fin: date) -> Dict:
        """Obtiene un resumen comparativo de producción vs ventas"""
        query = """
            SELECT 
                (SELECT SUM(tipo_c + tipo_b + tipo_a + tipo_aa + tipo_aaa + tipo_jumbo) 
                 FROM produccion_diaria WHERE fecha BETWEEN ? AND ?) as total_producido,
                (SELECT SUM((canastillas_c + canastillas_b + canastillas_a + 
                            canastillas_aa + canastillas_aaa + canastillas_jumbo) * 30)
                 FROM pedidos WHERE estado = 'completado' AND fecha BETWEEN ? AND ?) as total_vendido
        """
        result = self.db.execute_query(query, (fecha_inicio, fecha_fin, fecha_inicio, fecha_fin))
        return result[0] if result else {}
    
    def obtener_produccion_diaria_periodo(self, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """Obtiene la producción diaria agregada por fecha"""
        query = """
            SELECT 
                fecha,
                SUM(tipo_c) as tipo_c,
                SUM(tipo_b) as tipo_b,
                SUM(tipo_a) as tipo_a,
                SUM(tipo_aa) as tipo_aa,
                SUM(tipo_aaa) as tipo_aaa,
                SUM(tipo_jumbo) as tipo_jumbo,
                SUM(tipo_c + tipo_b + tipo_a + tipo_aa + tipo_aaa + tipo_jumbo) as total
            FROM produccion_diaria
            WHERE fecha BETWEEN ? AND ?
            GROUP BY fecha
            ORDER BY fecha
        """
        return self.db.execute_query(query, (fecha_inicio, fecha_fin))
    
    def obtener_ventas_diarias_periodo(self, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """Obtiene las ventas diarias agregadas por fecha"""
        query = """
            SELECT 
                fecha,
                COUNT(*) as cantidad_ventas,
                SUM(canastillas_c + canastillas_b + canastillas_a + 
                    canastillas_aa + canastillas_aaa + canastillas_jumbo) as total_canastillas,
                SUM(precio_total) as total_ingresos
            FROM pedidos
            WHERE estado = 'completado' AND fecha BETWEEN ? AND ?
            GROUP BY fecha
            ORDER BY fecha
        """
        return self.db.execute_query(query, (fecha_inicio, fecha_fin))
    
    def obtener_top_clientes(self, fecha_inicio: date, fecha_fin: date, limit: int = 10) -> List[Dict]:
        """Obtiene los top clientes por compras"""
        query = f"""
            SELECT 
                c.nombre,
                COUNT(p.id) as cantidad_compras,
                SUM(p.precio_total) as total_comprado,
                SUM(p.canastillas_c + p.canastillas_b + p.canastillas_a + 
                    p.canastillas_aa + p.canastillas_aaa + p.canastillas_jumbo) as total_canastillas
            FROM pedidos p
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.estado = 'completado' AND p.fecha BETWEEN ? AND ?
            GROUP BY c.id, c.nombre
            ORDER BY total_comprado DESC
            LIMIT {limit}
        """
        return self.db.execute_query(query, (fecha_inicio, fecha_fin))
    
    def obtener_ventas_por_categoria(self, fecha_inicio: date, fecha_fin: date) -> Dict:
        """Obtiene el total de canastillas vendidas por categoría"""
        query = """
            SELECT 
                SUM(canastillas_c) as total_c,
                SUM(canastillas_b) as total_b,
                SUM(canastillas_a) as total_a,
                SUM(canastillas_aa) as total_aa,
                SUM(canastillas_aaa) as total_aaa,
                SUM(canastillas_jumbo) as total_jumbo
            FROM pedidos
            WHERE estado = 'completado' AND fecha BETWEEN ? AND ?
        """
        result = self.db.execute_query(query, (fecha_inicio, fecha_fin))
        return result[0] if result else {}
    
    def calcular_costo_produccion_por_huevo(self, fecha_inicio: date, fecha_fin: date) -> float:
        """
        Calcula el costo de producción por huevo.
        Costo = (Total egresos en alimento + salarios) / Total huevos producidos
        """
        # Obtener egresos relacionados con producción
        query_egresos = """
            SELECT SUM(monto) as total_egresos
            FROM movimientos_financieros
            WHERE tipo = 'egreso' 
            AND fecha BETWEEN ? AND ?
            AND (categoria LIKE '%Alimento%' OR categoria LIKE '%trabajador%')
        """
        egresos = self.db.execute_query(query_egresos, (fecha_inicio, fecha_fin))
        total_egresos = egresos[0]['total_egresos'] if egresos and egresos[0]['total_egresos'] else 0
        
        # Obtener producción total
        query_produccion = """
            SELECT SUM(tipo_c + tipo_b + tipo_a + tipo_aa + tipo_aaa + tipo_jumbo) as total
            FROM produccion_diaria
            WHERE fecha BETWEEN ? AND ?
        """
        produccion = self.db.execute_query(query_produccion, (fecha_inicio, fecha_fin))
        total_producido = produccion[0]['total'] if produccion and produccion[0]['total'] else 0
        
        if total_producido > 0:
            return total_egresos / total_producido
        else:
            return 0
    
    def obtener_estadisticas_stock(self) -> Dict:
        """Obtiene estadísticas del stock actual"""
        query = """
            SELECT 
                (tipo_c + tipo_b + tipo_a + tipo_aa + tipo_aaa + tipo_jumbo) as total_huevos,
                tipo_c, tipo_b, tipo_a, tipo_aa, tipo_aaa, tipo_jumbo
            FROM stock_huevos
            WHERE id = 1
        """
        result = self.db.execute_query(query)
        return result[0] if result else {}
    
class GallinasRepository:
    """Repositorio para gestionar población de gallinas y consumo de alimento"""
    
    def __init__(self, db):
        self.db = db
    
    def registrar_poblacion(self, fecha: date, hora: str, cantidad_gallinas: int, 
                           descartes: int = 0, observaciones: str = None) -> int:
        """Registra la población de gallinas"""
        query = """
            INSERT INTO poblacion_gallinas (fecha, hora, cantidad_gallinas, descartes, observaciones)
            VALUES (?, ?, ?, ?, ?)
        """
        return self.db.execute_insert(query, (fecha, hora, cantidad_gallinas, descartes, observaciones))
    
    def obtener_poblacion_actual(self) -> Dict:
        """Obtiene el último registro de población"""
        query = """
            SELECT * FROM poblacion_gallinas 
            ORDER BY fecha DESC, hora DESC 
            LIMIT 1
        """
        result = self.db.execute_query(query)
        return result[0] if result else {'cantidad_gallinas': 0}
    
    def registrar_consumo_alimento(self, fecha: date, hora: str, 
                                  consumo_por_gallina: float, cantidad_gallinas: int,
                                  observaciones: str = None) -> int:
        """Registra el consumo de alimento del día"""
        consumo_total = consumo_por_gallina * cantidad_gallinas
        query = """
            INSERT INTO consumo_alimento 
            (fecha, hora, consumo_por_gallina, cantidad_gallinas, consumo_total, observaciones)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.db.execute_insert(query, (fecha, hora, consumo_por_gallina, cantidad_gallinas, consumo_total, observaciones))
    
    def obtener_historial_poblacion(self, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """Obtiene el historial de población"""
        query = """
            SELECT * FROM poblacion_gallinas
            WHERE fecha BETWEEN ? AND ?
            ORDER BY fecha DESC, hora DESC
        """
        return self.db.execute_query(query, (fecha_inicio, fecha_fin))
    
    def obtener_historial_consumo(self, fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """Obtiene el historial de consumo"""
        query = """
            SELECT * FROM consumo_alimento
            WHERE fecha BETWEEN ? AND ?
            ORDER BY fecha DESC, hora DESC
        """
        return self.db.execute_query(query, (fecha_inicio, fecha_fin))