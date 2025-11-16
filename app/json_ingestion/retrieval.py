from sqlalchemy import text
from sqlalchemy.orm import Session
from pymongo import MongoClient
from typing import Any, List, Dict


MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "json_ingestion"


def retrieve_sql_dataset(db: Session, table_name: str) -> List[Dict]:
    """
    Fetches all rows from a SQL dataset table and returns list of dicts.
    """
    query = text(f"SELECT * FROM {table_name}")
    result = db.execute(query)

    rows = result.fetchall()
    columns = result.keys()

    return [dict(zip(columns, row)) for row in rows]


def retrieve_nosql_dataset(collection_name: str) -> List[Dict]:
    """
    Fetches all documents from MongoDB collection and returns list of dicts.
    """
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    collection = db[collection_name]

    docs = list(collection.find({}, {"_id": 0})) 
    return docs
