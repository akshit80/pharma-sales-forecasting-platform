import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database.database import get_db
from backend.models.models import Dataset
from backend.schemas.schemas import DatasetSummary
from backend.services.ingestion_service import IngestionService

router = APIRouter(prefix="/datasets", tags=["Datasets"])

@router.post("/upload", response_model=DatasetSummary)
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Uploads CSV pharmaceutical sales dataset, validates schema, and stores in database."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")
    
    try:
        content = await file.read()
        dataset = IngestionService.process_csv_file(db, content, file.filename)
        return dataset
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def _do_upload_sample(db: Session):
    sample_path = "data/sample_pharma_sales.csv"
    if not os.path.exists(sample_path):
        from data.generate_sample_data import generate_sample_dataset
        generate_sample_dataset(sample_path)
    
    with open(sample_path, "rb") as f:
        content = f.read()
    
    return IngestionService.process_csv_file(db, content, "sample_pharma_sales.csv")

@router.post("/upload_sample", response_model=DatasetSummary)
def upload_sample_dataset_post(db: Session = Depends(get_db)):
    """Auto-loads built-in sample dataset for 1-click web demo (POST)."""
    return _do_upload_sample(db)

@router.get("/upload_sample", response_model=DatasetSummary)
def upload_sample_dataset_get(db: Session = Depends(get_db)):
    """Auto-loads built-in sample dataset for 1-click web demo (GET)."""
    return _do_upload_sample(db)

@router.get("/", response_model=List[DatasetSummary])
def list_datasets(db: Session = Depends(get_db)):
    """Lists all ingested datasets."""
    return db.query(Dataset).order_by(Dataset.uploaded_at.desc()).all()
