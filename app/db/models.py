from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base

class FileMetadata(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    original_name = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    

class JsonDataset(Base):
    __tablename__ = "json_datasets"

    id = Column(Integer, primary_key=True, index=True)

    # "sql" or "nosql"
    storage_type = Column(String, nullable=False)

    # Only used when SQL-like JSON is stored
    sql_table_name = Column(String, nullable=True)

    # Only used when NoSQL-like JSON is stored
    mongo_collection_name = Column(String, nullable=True)

    # Optional: the original filename if it came from a .json upload
    original_name = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

