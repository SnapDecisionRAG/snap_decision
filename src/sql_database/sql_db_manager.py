import sqlite3
from pathlib import Path
from contextlib import contextmanager
from .schemas import SCHEMAS, INDEXES

class SQLDBManager:
    def __init__(self):
        self.path = Path('database/ff_sql.db')
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.initialize_db()

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(self.path)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Database error: {e}")
            raise
        finally:
            if conn: conn.close()

    def initialize_db(self):
        if not self.path.exists():
            print(f"Creating SQLite DB at {self.path}")
            with self.get_connection() as conn:
                cursor = conn.cursor()

                for table_name, schema in SCHEMAS.items():
                    print(f'Creating table: {table_name}')
                    cursor.execute(schema)

                print('Creating indexes...')
                for index in INDEXES:
                    cursor.execute(index)

                conn.commit()
                print('Database initialization complete!')
        else:
            print(f'Using existing SQLite DB at {self.path}')
