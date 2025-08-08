from app.core.database import engine
from sqlalchemy import text

def check_alembic_version():
    with engine.connect() as conn:
        result = conn.execute(text('SELECT * FROM alembic_version'))
        print(result.fetchall())

if __name__ == '__main__':
    check_alembic_version()
