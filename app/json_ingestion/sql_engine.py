from sqlalchemy import Table, Column, MetaData, String, Integer, Float, Boolean
from sqlalchemy.sql import insert
from sqlalchemy.engine import Engine
from typing import List, Dict, Tuple

# Helper: detect Python → SQL type
def infer_sql_type(value):
    if isinstance(value, bool):
        return Boolean
    if isinstance(value, int):
        return Integer
    if isinstance(value, float):
        return Float
    # Default fallback type
        return String
    return String


def store_sql_dataset(engine: Engine, table_name: str, rows: List[Dict]) -> int:
    """
    Creates a new SQL table and inserts all rows.
    Returns number of inserted rows.
    """

    metadata = MetaData()

    # Build dynamic columns
    sample = rows[0]
    columns = []

    for key, value in sample.items():
        col_type = infer_sql_type(value)
        columns.append(Column(key, col_type))

    # Define the table
    table = Table(
        table_name,
        metadata,
        Column("_id", Integer, primary_key=True, autoincrement=True),
        *columns,
    )

    # Create table inside DB
    metadata.create_all(engine)

    # Insert rows
    with engine.connect() as conn:
        conn.execute(insert(table), rows)

    return len(rows)
