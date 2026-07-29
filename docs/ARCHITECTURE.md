# System Architecture Documentation

## Overview
The **Pharmaceutical Sales Forecasting & Decision Intelligence Platform** is designed as a clean, decoupled 3-tier web application modeled after internal commercial analytics suites used by management consulting firms (e.g., Viscadia, IQVIA).

---

## High-Level Architecture Components

1. **Presentation Tier (Streamlit)**:
   - Interactive multipage user dashboard.
   - Interactive Plotly visualizations for EDA, forecast curves, and scenario sensitivity curves.
   - Built-in PDF report download trigger.

2. **Application & API Tier (FastAPI)**:
   - RESTful API endpoints for dataset upload, statistical EDA, ML forecast execution, scenario calculations, decision intelligence, and report generation.
   - Pydantic validation schemas.
   - Asynchronous execution and ORM database handling.

3. **Analytics Engine Tier**:
   - **Ingestion Engine**: Validates CSV schema, parses dates, imputes missing values, and loads normalized records.
   - **EDA Engine**: Computes revenue/volume aggregations, monthly trends, product & regional market shares, basic statistics, and seasonality decomposition.
   - **Forecasting Pipeline**:
     - *Prophet*: Decomposes annual seasonality and trend components.
     - *XGBoost*: Time-series lag feature engineering (lag 1, lag 2, rolling 3-month mean, price, marketing spend) with feature importance extraction.
   - **Scenario Sensitivity Engine**: Evaluates price elasticity (-0.85) and marketing spend elasticity (+0.25) to project modified volume and revenue curves.
   - **Decision Intelligence Engine**: Rule-based explainable recommendation rules evaluating inventory buffers, product portfolio trajectories, regional growth opportunities, marketing spend efficiency, and pre-Q4 stocking risks.
   - **Executive Reporting Engine**: Generates formatted PDF reports via ReportLab.

4. **Data & Persistence Tier**:
   - PostgreSQL / SQLAlchemy database storing `datasets`, `sales_records`, `forecast_runs`, `forecast_predictions`, and `reports`.

---

## Data Schema Summary

- **`datasets`**: Metadata on ingested CSV files.
- **`sales_records`**: Granular historical time-series entries (date, product, area, region, volume, price, marketing, revenue).
- **`forecast_runs`**: Trained model run metadata, evaluation metrics (MAE, RMSE, MAPE), and feature importances.
- **`forecast_predictions`**: Horizon forecast points with confidence lower/upper bounds and revenue estimates.
- **`reports`**: Output PDF document storage references.
