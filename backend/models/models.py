import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Date, JSON, Text
from sqlalchemy.orm import relationship
from backend.database.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    total_records = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    sales_records = relationship("SalesRecord", back_populates="dataset", cascade="all, delete-orphan")
    forecast_runs = relationship("ForecastRun", back_populates="dataset", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="dataset", cascade="all, delete-orphan")


class SalesRecord(Base):
    __tablename__ = "sales_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    product_name = Column(String, nullable=False, index=True)
    therapeutic_area = Column(String, nullable=True)
    region = Column(String, nullable=False, index=True)
    sales_units = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    marketing_spend = Column(Float, default=0.0)
    revenue = Column(Float, nullable=False)

    dataset = relationship("Dataset", back_populates="sales_records")


class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False, index=True)
    model_name = Column(String, nullable=False)  # Prophet or XGBoost
    horizon_months = Column(Integer, nullable=False)
    mae = Column(Float, nullable=False)
    rmse = Column(Float, nullable=False)
    mape = Column(Float, nullable=False)
    feature_importance = Column(JSON, nullable=True)  # Store JSON dict for XGBoost
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="forecast_runs")
    predictions = relationship("ForecastPrediction", back_populates="forecast_run", cascade="all, delete-orphan")


class ForecastPrediction(Base):
    __tablename__ = "forecast_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    forecast_run_id = Column(String, ForeignKey("forecast_runs.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    predicted_units = Column(Float, nullable=False)
    lower_bound_units = Column(Float, nullable=True)
    upper_bound_units = Column(Float, nullable=True)
    predicted_revenue = Column(Float, nullable=False)

    forecast_run = relationship("ForecastRun", back_populates="predictions")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    file_path = Column(String, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="reports")
