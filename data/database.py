import sqlite3
from contextlib import contextmanager
from pathlib import Path

class Database:
    """
    Clase para gestionar la conexión y creación de la base de datos SQLite.
    Implementa el patrón Context Manager para manejo seguro de conexiones.
    """
    
    def __init__(self, db_path='data/granja.db'):
        """
        Inicializa la base de datos.
        
        Args:
            db_path (str): Ruta al archivo de base de datos
        """
        self.db_path = db_path
        self._ensure_data_directory()
        self.init_db()
        self._run_migrations()  # ← añadir
        
    def _run_migrations(self):
        """
        Aplica migraciones necesarias a la BD existente.
        Se ejecuta en cada inicio pero solo hace cambios si son necesarios.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Migración 1: Corregir CHECK constraint de insumos (Canstillas → Canastillas)
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='insumos'")
            row = cursor.fetchone()
            if row and 'Canstillas' in row[0]:
                conn.executescript("""
                    PRAGMA foreign_keys=OFF;
                    CREATE TABLE insumos_nueva (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        categoria TEXT NOT NULL CHECK(categoria IN ('Alimento', 'Medicamento', 'Mantenimiento', 'Canastillas','Otros')),
                        cantidad REAL NOT NULL,
                        unidad TEXT NOT NULL CHECK(unidad IN ('kg', 'bultos', 'litros', 'unidades')),
                        costo_unitario REAL NOT NULL,
                        costo_total REAL NOT NULL,
                        fecha_compra DATE NOT NULL,
                        proveedor TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    INSERT INTO insumos_nueva SELECT * FROM insumos;
                    DROP TABLE insumos;
                    ALTER TABLE insumos_nueva RENAME TO insumos;
                    PRAGMA foreign_keys=ON;
                """)
                print("✅ Migración 1: tabla insumos corregida")

            # Migración 2: Consolidar stock_insumos por nombre
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='stock_insumos'")
            row = cursor.fetchone()
            if row and 'insumo_id' in row[0]:
                conn.executescript("""
                    CREATE TABLE stock_insumos_nueva (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL UNIQUE,
                        categoria TEXT NOT NULL,
                        unidad TEXT NOT NULL,
                        cantidad_actual REAL NOT NULL DEFAULT 0,
                        stock_minimo REAL DEFAULT 0,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    INSERT OR IGNORE INTO stock_insumos_nueva (nombre, categoria, unidad, cantidad_actual, stock_minimo)
                    SELECT i.nombre, i.categoria, i.unidad,
                        SUM(si.cantidad_actual), MAX(si.stock_minimo)
                    FROM stock_insumos si
                    JOIN insumos i ON si.insumo_id = i.id
                    GROUP BY i.nombre, i.categoria, i.unidad;
                    DROP TABLE stock_insumos;
                    ALTER TABLE stock_insumos_nueva RENAME TO stock_insumos;
                """)
                print("✅ Migración 2: stock_insumos consolidado")

            # Migración 3: Trigger correcto para register_egreso_after_insumo
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name='register_egreso_after_insumo'")
            row = cursor.fetchone()
            if not row or 'insumo_id' in row[0]:
                conn.executescript("""
                    DROP TRIGGER IF EXISTS register_egreso_after_insumo;
                    CREATE TRIGGER register_egreso_after_insumo
                    AFTER INSERT ON insumos
                    BEGIN
                        INSERT INTO movimientos_financieros (fecha, tipo, categoria, monto, descripcion, referencia_id, referencia_tabla)
                        VALUES (
                            NEW.fecha_compra, 'egreso', 'Compra de ' || NEW.categoria,
                            NEW.costo_total,
                            NEW.nombre || ' - ' || NEW.cantidad || ' ' || NEW.unidad,
                            NEW.id, 'insumos'
                        );
                        INSERT INTO stock_insumos (nombre, categoria, unidad, cantidad_actual, stock_minimo)
                        SELECT NEW.nombre, NEW.categoria, NEW.unidad, NEW.cantidad, 0
                        WHERE NOT EXISTS (SELECT 1 FROM stock_insumos WHERE nombre = NEW.nombre);
                        UPDATE stock_insumos
                        SET cantidad_actual = cantidad_actual + NEW.cantidad,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE nombre = NEW.nombre;
                    END;
                """)
                print("✅ Migración 3: trigger register_egreso_after_insumo corregido")

            # Migración 4: PRAGMA WAL
            cursor.execute("PRAGMA journal_mode=WAL")
            
    
    def _ensure_data_directory(self):
        """Crea el directorio 'data' si no existe"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """
        Context manager para obtener una conexión a la base de datos.
        Maneja automáticamente commit/rollback y cierre de conexión.
        
        Uso:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tabla")
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
        conn.execute("PRAGMA journal_mode=WAL")  # ← añadir esta línea
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_db(self):
        """
        Inicializa la base de datos ejecutando el schema completo.
        Lee el archivo schema.sql y lo ejecuta solo si es necesario.
        """
        # Verificar si la BD ya está inicializada
        db_exists = Path(self.db_path).exists()
        
        if db_exists:
            # Verificar si las tablas principales existen
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='produccion_diaria'
                """)
                if cursor.fetchone():
                    # La BD ya está inicializada
                    return
        
        # Si llegamos aquí, necesitamos crear las tablas
        schema_path = Path(__file__).parent / 'schema.sql'
        
        if not schema_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo schema.sql en {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
        
        print(f"✅ Base de datos inicializada correctamente en {self.db_path}")
    
    def execute_query(self, query, params=None):
        """
        Ejecuta una consulta SELECT y retorna los resultados.
        
        Args:
            query (str): Consulta SQL
            params (tuple): Parámetros de la consulta
            
        Returns:
            list: Lista de resultados como diccionarios
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Convertir Row objects a diccionarios
            columns = [description[0] for description in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
    
    def execute_insert(self, query, params=None):
        """
        Ejecuta una consulta INSERT y retorna el ID del registro insertado.
        
        Args:
            query (str): Consulta SQL INSERT
            params (tuple): Parámetros de la consulta
            
        Returns:
            int: ID del último registro insertado
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.lastrowid
    
    def execute_update(self, query, params=None):
        """
        Ejecuta una consulta UPDATE/DELETE y retorna el número de filas afectadas.
        
        Args:
            query (str): Consulta SQL UPDATE/DELETE
            params (tuple): Parámetros de la consulta
            
        Returns:
            int: Número de filas afectadas
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount
    
    def reset_database(self):
        """
        PELIGRO: Elimina y recrea la base de datos.
        Usar solo en desarrollo.
        """
        if Path(self.db_path).exists():
            Path(self.db_path).unlink()
            print(f"⚠️  Base de datos eliminada: {self.db_path}")
        
        self.init_db()
        print("✅ Base de datos recreada desde cero")


# Instancia global de la base de datos
db = Database()