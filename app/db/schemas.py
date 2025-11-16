from pydantic import BaseModel
from datetime import datetime

class FileMetadataCreate(BaseModel):
    original_name: str
    stored_path: str
    mime_type: str
    size_bytes: int

class FileMetadataResponse(FileMetadataCreate):
    id: int
    uploaded_at: datetime

    class Config:
        orm_mode = True

class JsonDatasetCreate(BaseModel):
    storage_type: str          # "sql" or "nosql"
    sql_table_name: str | None = None
    mongo_collection_name: str | None = None
    original_name: str | None = None


class JsonDatasetResponse(JsonDatasetCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

