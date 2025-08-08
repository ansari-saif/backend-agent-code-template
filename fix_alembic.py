from app.core.database import engine
from sqlalchemy import text

def fix_alembic_version():
    with engine.connect() as conn:
        # Update to the latest migration
        conn.execute(text("UPDATE alembic_version SET version_num = '570e3b109389'"))
        conn.commit()
        
        # Verify the update
        result = conn.execute(text('SELECT * FROM alembic_version'))
        print("New version:", result.fetchall())

if __name__ == '__main__':
    fix_alembic_version()
