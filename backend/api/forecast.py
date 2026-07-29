from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.schemas.schemas import ForecastRequest, ForecastResponse, ModelComparisonResponse, DecisionIntelligenceResponse
from backend.services.forecasting_service import ForecastingService
from backend.services.decision_service import DecisionService

router = APIRouter(prefix="/forecast", tags=["Forecasting"])

@router.post("/run", response_model=ForecastResponse)
def run_forecast(request: ForecastRequest, db: Session = Depends(get_db)):
    """Triggers Prophet or XGBoost forecast model training and prediction."""
    try:
        return ForecastingService.run_forecast(
            db, 
            request.dataset_id, 
            request.model_name, 
            request.horizon_months
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/compare/{dataset_id}", response_model=ModelComparisonResponse)
def compare_models(
    dataset_id: str, 
    horizon_months: int = Query(6, ge=3, le=24),
    db: Session = Depends(get_db)
):
    """Compares performance of Prophet vs XGBoost models side-by-side."""
    try:
        return ForecastingService.compare_models(db, dataset_id, horizon_months)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/decision_intelligence/{dataset_id}", response_model=DecisionIntelligenceResponse)
def get_decision_intelligence(dataset_id: str, db: Session = Depends(get_db)):
    """Generates rule-based commercial decision intelligence recommendations."""
    try:
        recs = DecisionService.generate_recommendations(db, dataset_id)
        return {"dataset_id": dataset_id, "recommendations": recs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
