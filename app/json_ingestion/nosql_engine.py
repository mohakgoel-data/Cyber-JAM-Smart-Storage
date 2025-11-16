from pymongo import MongoClient
from typing import Any, List, Dict

def store_nosql_dataset(mongo_uri: str, db_name: str, collection_name: str, data: Any) -> int:
    """
    Stores JSON data in MongoDB.
    Returns number of inserted documents.
    """

    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    # List inserts (e.g., [{"a":1},{"b":2}])
    if isinstance(data, list):
        result = collection.insert_many(data)
        return len(result.inserted_ids)

    # Single document (e.g., {"a":1})
    result = collection.insert_one(data)
    return 1
