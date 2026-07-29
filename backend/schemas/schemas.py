from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date, datetime

class DatasetSummary(BaseModel):
    id: str
    filename: str
    total_records: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

class EDAResponse(BaseModel):
    dataset_id: str
    total_records: int
    date_range: Dict[str, str]
    total_revenue: float
    total_sales_units: float
    products: List[str]
    regions: List[str]
    monthly_sales: List[Dict[str, Any]]
    product_sales: List[Dict[str, Any]]
    region_sales: List[Dict[str, Any]]
    missing_values: Dict[str, int]
    basic_stats: Dict[str, Dict[str, float]]
    seasonality: List[Dict[str, Any]]

class ForecastRequest(BaseModel):
    dataset_id: str
    model_name: str  # Prophet or XGBoost
    horizon_months: int  # 3, 6, or 12

class PredictionPoint(BaseModel):
    date: str
    predicted_units: float
    lower_bound_units: Optional[float] = None
    upper_bound_units: Optional[float] = None
    predicted_revenue: float

class ForecastResponse(BaseModel):
    forecast_run_id: str
    dataset_id: str
    model_name: str
    horizon_months: int
    mae: float
    rmse: float
    mape: float
    feature_importance: Optional[Dict[str, float]] = None
    predictions: List[PredictionPoint]

class ModelComparisonItem(BaseModel):
    model_name: str
    mae: float
    rmse: float
    mape: float

class ModelComparisonResponse(BaseModel):
    dataset_id: str
    horizon_months: int
    models: List[ModelComparisonItem]
    historical: List[Dict[str, Any]]
    prophet_forecast: Optional[List[PredictionPoint]] = None
    xgboost_forecast: Optional[List[PredictionPoint]] = None

class ScenarioRequest(BaseModel):
    dataset_id: str
    model_name: str = "XGBoost"
    horizon_months: int = 6
    price_change_pct: float = 0.0  # e.g., +10.0 or -5.0
    marketing_change_pct: float = 0.0  # e.g., +15.0 or -10.0

class ScenarioResponse(BaseModel):
    dataset_id: str
    price_change_pct: float
    marketing_change_pct: float
    baseline_units: float
    baseline_revenue: float
    recalculated_units: float
    recalculated_revenue: float
    units_diff: float
    revenue_diff: float
    units_pct_change: float
    revenue_pct_change: float
    forecast_comparison: List[Dict[str, Any]]

class DecisionRecommendation(BaseModel):
    category: str
    recommendation: str
    reasoning: str
    impact: str
    priority: str

class DecisionIntelligenceResponse(BaseModel):
    dataset_id: str
    recommendations: List[DecisionRecommendation]

class ReportResponse(BaseModel):
    report_id: str
    dataset_id: str
    file_path: str
    generated_at: datetime
