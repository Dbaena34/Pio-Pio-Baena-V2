import pandas as pd

from data.database import db


class ExploradorRepository:

    def obtener_tablas(self):

        with db.get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)

            return [fila[0] for fila in cursor.fetchall()]


    def obtener_dataframe(self, tabla):

        with db.get_connection() as conn:

            return pd.read_sql(
                f"SELECT * FROM {tabla}",
                conn
            )