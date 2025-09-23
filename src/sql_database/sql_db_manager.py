import sqlite3
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
from .schemas import SCHEMAS, INDEXES

class SQLDBManager:
    def __init__(self):
        self.path = Path('database/ff_sql.db')
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Register datetime adapter to fix Python 3.12 deprecation warning
        sqlite3.register_adapter(datetime, self._adapt_datetime)
        sqlite3.register_converter("timestamp", self._convert_timestamp)

        self.initialize_db()

    def _adapt_datetime(self, dt): # Fix Python3.12 DeprecationWarning
        return dt.isoformat()

    def _convert_timestamp(self, s): # Fix Python3.12 DeprecationWarning
        return datetime.fromisoformat(s.decode('utf-8'))

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = sqlite3.connect(
                self.path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
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
