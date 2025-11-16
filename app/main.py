from fastapi import FastAPI, UploadFile, File, Depends
from minio import Minio
from .utils import get_file_path
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .db.database import Base, engine, SessionLocal
from .db import crud, schemas, models
from typing import List
from .db.schemas import FileMetadataResponse
from datetime import timedelta
from fastapi import HTTPException
from fastapi import Query
from fastapi import Body
from app.json_ingestion.manager import ingest_json
from app.json_ingestion.retrieval import retrieve_sql_dataset, retrieve_nosql_dataset
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

def get_db():
    try:
        db = SessionLocal()
    except Exception as e:
        raise  # This lets FastAPI show the real exception
    try:
        yield db
    except Exception as e:
        raise
    finally:
        db.close()


# MinIO client setup
minio_client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

BUCKET = "files"

# Ensure bucket exists
if not minio_client.bucket_exists(BUCKET):
    minio_client.make_bucket(BUCKET)

@app.post("/upload")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename.lower()
    if filename.endswith(".json"):
        content = await file.read()

        try:
            parsed_json = json.loads(content)
        except Exception:
            raise HTTPException(400, "Invalid JSON file")

        # Hand over to JSON ingestion engine
        return ingest_json(db, parsed_json, original_name=file.filename)
    
    content = await file.read()                     # raw bytes
    object_path = get_file_path(file.filename)

    stream = BytesIO(content)                       # ✔ stream object

    minio_client.put_object(
        bucket_name=BUCKET,
        object_name=object_path,
        data=stream,
        length=len(content),
        content_type=file.content_type
    )

    metadata = schemas.FileMetadataCreate(
        original_name=file.filename,
        stored_path=object_path,
        mime_type=file.content_type,
        size_bytes=len(content)
    )
    saved = crud.save_file_metadata(db, metadata)

    return {
        "status": "success",
        "stored_as": object_path,
        "id": saved.id,
    }


@app.get("/files", response_model=List[FileMetadataResponse])
def list_files(db: Session = Depends(get_db)):
    return crud.get_all_files(db)
from typing import Any, Dict, List
from datetime import datetime

@app.get("/files/tree")
def get_file_tree(db: Session = Depends(get_db)):
    files = db.query(models.FileMetadata).all()

    tree: Dict[str, Any] = {}  # {category: {subfolder: [files]} or [files]}

    for f in files:
        if not f.stored_path:
            continue

        parts = f.stored_path.split("/")
        if not parts:
            continue

        category = parts[0]  # e.g. "media", "documents", "code", "json_data", "others"
        filename = parts[-1]
        subfolder: str | None = None

        # If path has at least 3 parts → category/subfolder/file
        if len(parts) >= 3:
            subfolder = parts[1]

        file_info = {
            "id": f.id,
            "name": f.original_name or filename,
            "stored_path": f.stored_path,
            "mime_type": f.mime_type,
            "size_bytes": f.size_bytes,
            "created_at": f.created_at.isoformat() if getattr(f, "created_at", None) else None,
        }

        if subfolder:
            # Ensure category is a dict
            if category not in tree or not isinstance(tree[category], dict):
                tree[category] = {}
            if subfolder not in tree[category]:
                tree[category][subfolder] = []
            tree[category][subfolder].append(file_info)
        else:
            # Category directly contains files
            if category not in tree or isinstance(tree[category], dict):
                # If it was mistakenly a dict, overwrite with list
                tree[category] = []
            tree[category].append(file_info)

    return tree




@app.get("/view/{file_id}")
def view_file(file_id: int, db: Session = Depends(get_db)):
    # 1. Fetch metadata
    meta = db.query(models.FileMetadata).filter(models.FileMetadata.id == file_id).first()
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")

    # 2. Generate presigned GET URL
    try:
        url = minio_client.presigned_get_object(
            bucket_name=BUCKET,
            object_name=meta.stored_path,
            expires=timedelta(minutes=10)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating presigned URL: {str(e)}")

    # 3. Return URL to frontend
    return {
        "url": url,
        "mime_type": meta.mime_type
    }

@app.get("/download/{file_id}")
def download_file(file_id: int, db: Session = Depends(get_db)):
    # 1. Fetch metadata
    meta = db.query(models.FileMetadata).filter(models.FileMetadata.id == file_id).first()

    if not meta:
        raise HTTPException(status_code=404, detail="File not found")

    # Extract original name (for download filename)
    original_name = meta.original_name

    # 2. Generate a presigned URL with download headers
    try:
        url = minio_client.presigned_get_object(
            bucket_name=BUCKET,
            object_name=meta.stored_path,
            expires=timedelta(minutes=10),
            response_headers={
                "response-content-disposition": f'attachment; filename="{original_name}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate download URL: {str(e)}")

    # 3. Return download link + filename
    return {
        "url": url,
        "filename": original_name
    }

@app.delete("/delete/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db)):
    # 1. Fetch metadata
    meta = db.query(models.FileMetadata).filter(models.FileMetadata.id == file_id).first()
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")

    # 2. Delete file from MinIO
    try:
        minio_client.remove_object(
            bucket_name=BUCKET,
            object_name=meta.stored_path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing MinIO object: {str(e)}")

    # 3. Delete from DB
    try:
        db.delete(meta)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting metadata: {str(e)}")

    return {"status": "deleted", "id": file_id}


@app.get("/search", response_model=List[schemas.FileMetadataResponse])
def search_files(query: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    results = crud.search_files(db, query)
    return results

from fastapi import Form
@app.post("/json/file")
async def upload_json_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".json"):
        raise HTTPException(400, "Only .json files allowed")

    content = await file.read()
    try:
        parsed_json = json.loads(content)
    except Exception:
        raise HTTPException(400, "Invalid JSON file")

    return ingest_json(db, parsed_json, original_name=file.filename)

@app.post("/json/upload")
async def upload_json_body(
    json_body: dict | list = Body(...),
    db: Session = Depends(get_db)
):
    return ingest_json(db, json_body)

from sqlalchemy import or_

@app.get("/json/datasets")
def list_json_datasets(
    query: str = Query(default=""),

    db: Session = Depends(get_db)
):
    """
    List all JSON datasets stored in json_datasets table.
    Supports search by ID, SQL table name, or Mongo collection name.
    """
    q = db.query(models.JsonDataset)

    if query:
        like = f"%{query}%"
        conditions = [
            models.JsonDataset.sql_table_name.ilike(like),
            models.JsonDataset.mongo_collection_name.ilike(like)
        ]
        if query.isdigit():
            conditions.append(models.JsonDataset.id == int(query))

        q = q.filter(or_(*conditions))

    datasets = q.order_by(models.JsonDataset.id).all()

    out = []
    for ds in datasets:
        out.append({
            "id": ds.id,
            "storage_type": ds.storage_type,
            "sql_table_name": ds.sql_table_name,
            "mongo_collection_name": ds.mongo_collection_name,
            "created_at": ds.created_at.isoformat() if ds.created_at else None
        })

    return out

@app.get("/json/search")
def search_json_datasets(q: str, db: Session = Depends(get_db)):
    results = crud.search_json_datasets(db, q)
    return results

@app.get("/json/{dataset_id}")
def get_json_dataset(dataset_id: int, db: Session = Depends(get_db)):
    # 1. Get metadata
    meta = crud.get_json_dataset(db, dataset_id)
    if not meta:
        raise HTTPException(404, "Dataset not found")

    # 2. SQL dataset retrieval
    if meta.storage_type == "sql":
        if not meta.sql_table_name:
            raise HTTPException(500, "SQL table missing for dataset")
        data = retrieve_sql_dataset(db, meta.sql_table_name)
        return {
            "dataset_id": dataset_id,
            "storage_type": "sql",
            "data": data
        }

    # 3. NoSQL dataset retrieval
    if meta.storage_type == "nosql":
        if not meta.mongo_collection_name:
            raise HTTPException(500, "Mongo collection missing for dataset")
        data = retrieve_nosql_dataset(meta.mongo_collection_name)
        return {
            "dataset_id": dataset_id,
            "storage_type": "nosql",
            "data": data
        }

    raise HTTPException(500, "Invalid dataset configuration")

from sqlalchemy import text
from pymongo import MongoClient

@app.delete("/debug/reset-json-system")
def reset_json_system(db: Session = Depends(get_db)):
    """
    Completely clean all JSON ingestion data:
    - Drop SQL tables created for JSON datasets
    - Drop MongoDB collections created for JSON datasets
    - Clear json_datasets metadata table
    """

    # 1. Fetch all metadata
    datasets = db.query(models.JsonDataset).all()

    dropped_sql_tables = []
    dropped_mongo_collections = []

    # --- SQL cleanup ---
    for ds in datasets:
        if ds.storage_type == "sql" and ds.sql_table_name:
            try:
                db.execute(text(f'DROP TABLE IF EXISTS "{ds.sql_table_name}"'))
                dropped_sql_tables.append(ds.sql_table_name)
            except Exception as e:
                print("Error dropping SQL table:", e)

        # --- Mongo cleanup ---
        if ds.storage_type == "nosql" and ds.mongo_collection_name:
            try:
                client = MongoClient("mongodb://localhost:27017/")
                mongo_db = client["json_ingestion"]
                mongo_db.drop_collection(ds.mongo_collection_name)
                dropped_mongo_collections.append(ds.mongo_collection_name)
            except Exception as e:
                print("Error dropping Mongo collection:", e)

    # --- Clear metadata table ---
    db.query(models.JsonDataset).delete()
    db.commit()

    return {
        "status": "reset-complete",
        "dropped_sql_tables": dropped_sql_tables,
        "dropped_mongo_collections": dropped_mongo_collections,
        "metadata_cleared": True
    }



