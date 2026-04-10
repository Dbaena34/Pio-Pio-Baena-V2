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