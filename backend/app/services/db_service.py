from sqlalchemy import create_engine, inspect, text
from typing import List, Dict, Any

class DbService:
    def __init__(self):
        pass

    def get_tables(self, db_url: str) -> List[Dict[str, Any]]:
        """
        Connects to the database and returns a list of tables with comments.
        """
        try:
            engine = create_engine(db_url)
            inspector = inspect(engine)
            tables = []
            for name in inspector.get_table_names():
                try:
                    comment = inspector.get_table_comment(name).get('text')
                except:
                    comment = None
                tables.append({"name": name, "comment": comment})
            return tables
        except Exception as e:
            raise Exception(f"Failed to connect to database: {str(e)}")

    def get_table_schema(self, db_url: str, table_name: str) -> Dict[str, Any]:
        """
        Returns schema information for a specific table.
        """
        try:
            engine = create_engine(db_url)
            inspector = inspect(engine)
            
            columns = []
            pk_constraint = inspector.get_pk_constraint(table_name)
            pk_columns = pk_constraint.get('constrained_columns', [])

            for col in inspector.get_columns(table_name):
                columns.append({
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "default": str(col["default"]) if col.get("default") else None,
                    "primary_key": col["name"] in pk_columns,
                    "comment": col.get("comment")
                })
            
            return {
                "table_name": table_name,
                "columns": columns
            }
        except Exception as e:
            raise Exception(f"Failed to inspect table {table_name}: {str(e)}")

db_service = DbService()
