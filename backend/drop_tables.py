from app.models import Base, engine
from sqlalchemy import text

def drop_all_tables():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS templates CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS template_groups CASCADE"))
        conn.commit()
    print("Dropped templates tables")

if __name__ == "__main__":
    drop_all_tables()
