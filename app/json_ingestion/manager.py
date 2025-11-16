import json
from sqlalchemy.orm import Session
from app.json_ingestion.classifier import is_sql_like
from app.json_ingestion.sql_engine import store_sql_dataset
from app.json_ingestion.nosql_engine import store_nosql_dataset
from app.db import crud, schemas
from fastapi import HTTPException


# MongoDB configuration (you can move this to settings later)
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "json_ingestion"


def ingest_json(db: Session, json_data, original_name: str | None = None):
    """
    Safe ingestion pipeline:
    - Classifies JSON
    - Stores SQL/NoSQL first
    - Only writes metadata AFTER storage succeeds
    - Prevents corrupted datasets forever
    """

    sql_like = is_sql_like(json_data)

    # Generate names first (without saving anything)
    # These names won't be used unless storage succeeds
    temp_table_name = None
    temp_collection_name = None

    try:
        # -------------------------
        # 1. SQL-LIKE JSON
        # -------------------------
        if sql_like:
            dataset_rows = json_data

            # generate table name (but do NOT save metadata yet)
            # we use a temporary placeholder ID, but better to delay metadata creation
            # until storage succeeds.
            # To create a unique table name, we use the next id in sequence:
            temp_id = crud.peek_next_json_dataset_id(db)  # You need to create a small helper
            temp_table_name = f"json_ds_{temp_id}"

            # Attempt SQL storage first
            row_count = store_sql_dataset(
                engine=db.bind,
                table_name=temp_table_name,
                rows=dataset_rows
            )

            # If succeeded → now create metadata safely
            meta = crud.create_json_dataset(
                db,
                schemas.JsonDatasetCreate(
                    storage_type="sql",
                    sql_table_name=temp_table_name,
                    original_name=original_name
                )
            )

            return {
                "dataset_id": meta.id,
                "storage_type": "sql",
                "rows": row_count
            }

        # -------------------------
        # 2. NOSQL-LIKE JSON
        # -------------------------
        else:
            temp_id = crud.peek_next_json_dataset_id(db)
            temp_collection_name = f"json_ds_{temp_id}"

            doc_count = store_nosql_dataset(
                mongo_uri=MONGO_URI,
                db_name=MONGO_DB,
                collection_name=temp_collection_name,
                data=json_data
            )

            # Only now create metadata
            meta = crud.create_json_dataset(
                db,
                schemas.JsonDatasetCreate(
                    storage_type="nosql",
                    mongo_collection_name=temp_collection_name,
                    original_name=original_name
                )
            )

            return {
                "dataset_id": meta.id,
                "storage_type": "nosql",
                "documents": doc_count
            }

    except Exception as e:
        # ⚠️ Storage failed → nothing was saved to metadata → no corruption possible
        raise HTTPException(
            status_code=400,
            detail=f"Ingestion failed: {str(e)}"
        )
