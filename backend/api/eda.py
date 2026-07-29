from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.schemas.schemas import EDAResponse
from backend.services.eda_service import EDAService

router = APIRouter(prefix="/eda", tags=["Exploratory Data Analysis"])

@router.get("/{dataset_id}", response_model=EDAResponse)
def get_eda(dataset_id: str, db: Session = Depends(get_db)):
    """Returns EDA metrics, trends, missing values, statistics, and seasonality decomposition."""
    try:
        return EDAService.get_eda_metrics(db, dataset_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
