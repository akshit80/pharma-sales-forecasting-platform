from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.schemas.schemas import ScenarioRequest, ScenarioResponse
from backend.services.scenario_service import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["Scenario Analysis"])

@router.post("/run", response_model=ScenarioResponse)
def run_scenario(request: ScenarioRequest, db: Session = Depends(get_db)):
    """Runs what-if sensitivity analysis adjusting price and marketing spend."""
    try:
        return ScenarioService.run_scenario(
            db,
            request.dataset_id,
            request.model_name,
            request.horizon_months,
            request.price_change_pct,
            request.marketing_change_pct
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
