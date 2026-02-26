from app.core.database import SessionLocal
from sqlalchemy import text

def fix_alembic_version():
    db = SessionLocal()
    try:
        db.execute(text("UPDATE alembic_version SET version_num = '7dab872170df'"))
        db.commit()
        print("✅ Successfully reset database version to '7dab872170df'!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_alembic_version()