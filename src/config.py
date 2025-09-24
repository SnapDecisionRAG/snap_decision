from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC_DIR = ROOT / 'src'
DATA_DIR = ROOT / 'data'
DATABASE_DIR = ROOT / 'database'

SQL_DATA_DIR = DATA_DIR / 'sql'
VECTOR_DATA_DIR = DATA_DIR / 'vector'

WEATHER_DIR = SQL_DATA_DIR / 'weather'
PROJECTIONS_DIR = SQL_DATA_DIR / 'projections'
ACTUAL_SCORES_DIR = SQL_DATA_DIR / 'actual_scores'

SQLITE_DB_PATH = DATABASE_DIR / 'ff_sql.db'
CHROMA_DB_DIR = DATABASE_DIR / 'ff_vector'

def create_directories():
    directories = [
        DATA_DIR,
        SQL_DATA_DIR,
        VECTOR_DATA_DIR,
        WEATHER_DIR,
        PROJECTIONS_DIR,
        ACTUAL_SCORES_DIR,
        DATABASE_DIR
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    create_directories()
