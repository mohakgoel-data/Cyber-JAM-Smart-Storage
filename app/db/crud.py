from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas

def save_file_metadata(db: Session, data: schemas.FileMetadataCreate):
    meta = models.FileMetadata(**data.dict())
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return meta

def get_all_files(db: Session):
    return db.query(models.FileMetadata).order_by(models.FileMetadata.id.desc()).all()


def search_files(db, query: str):
    return (
        db.query(models.FileMetadata)
        .filter(func.lower(models.FileMetadata.original_name).like(f"%{query.lower()}%"))
        .order_by(models.FileMetadata.id.desc())
        .all()
    )

def create_json_dataset(db: Session, dataset: schemas.JsonDatasetCreate):
    obj = models.JsonDataset(
        storage_type=dataset.storage_type,
        sql_table_name=dataset.sql_table_name,
        mongo_collection_name=dataset.mongo_collection_name,
        original_name=dataset.original_name
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_json_dataset(db: Session, dataset_id: int, data: dict):
    db.query(models.JsonDataset).filter(models.JsonDataset.id == dataset_id).update(data)
    db.commit()


def get_json_dataset(db: Session, dataset_id: int):
    return db.query(models.JsonDataset).filter(models.JsonDataset.id == dataset_id).first()

def search_json_datasets(db: Session, query: str):
    return db.query(models.JsonDataset).filter(
        models.JsonDataset.original_name.ilike(f"%{query}%")
    ).all()

def peek_next_json_dataset_id(db: Session) -> int:
    """
    Returns the next auto-increment ID *before* inserting a new JsonDataset row.
    Used to generate table/collection names safely.
    """
    last = (
        db.query(models.JsonDataset)
        .order_by(models.JsonDataset.id.desc())
        .first()
    )
    return (last.id + 1) if last else 1
