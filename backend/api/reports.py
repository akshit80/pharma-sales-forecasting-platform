import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.schemas.schemas import ReportResponse
from backend.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Executive Reports"])

@router.post("/generate", response_model=ReportResponse)
def generate_report(
    dataset_id: str = Query(...),
    model_name: str = Query("XGBoost"),
    horizon_months: int = Query(6),
    db: Session = Depends(get_db)
):
    """Generates an executive PDF report containing KPIs, forecasts, and recommendations."""
    try:
        return ReportService.generate_pdf_report(db, dataset_id, model_name, horizon_months)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/download/{report_id}")
def download_report(report_id: str, db: Session = Depends(get_db)):
    """Downloads generated PDF report file."""
    from backend.models.models import Report
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report PDF file not found.")
    
    return FileResponse(
        path=report.file_path, 
        filename=os.path.basename(report.file_path),
        media_type="application/pdf"
    )
