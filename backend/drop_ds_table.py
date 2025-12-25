from app.models import Base, engine
from sqlalchemy import text

def drop_datasources():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS data_sources"))
        conn.commit()
    print("Dropped data_sources table")

if __name__ == "__main__":
    drop_datasources()
