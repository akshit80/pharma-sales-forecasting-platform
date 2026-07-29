# Pharmaceutical Sales Forecasting & Decision Intelligence Platform

A production-quality commercial analytics platform built for pharmaceutical brand managers and commercial consultants. This application enables users to analyze historical pharmaceutical sales, forecast demand using time-series machine learning models (Prophet & XGBoost), run what-if price/marketing scenarios, automatically generate explainable business recommendations, and export executive PDF reports.

---

## 📋 Problem Statement

Pharmaceutical commercial teams often struggle with fragmented sales spreadsheets, unpredictable demand fluctuations, and lack of explainability in forecasting models. Traditional enterprise ERPs are overly complex and lack decision-focused analytics.

This platform solves this challenge by providing an end-to-end analytics workflow:
1. **Validates & standardizes** raw pharmaceutical sales datasets.
2. **Explores** revenue trends, annual seasonality, and regional product contributions.
3. **Forecasts** future demand (3, 6, 12 months) with confidence intervals and model comparison.
4. **Explains** key driver features behind ML predictions (XGBoost Feature Importance).
5. **Simulates** dynamic What-If scenarios adjusting prices and promotional spend.
6. **Recommends** concrete inventory, portfolio, and marketing actions using explainable rule-based decision logic.
7. **Exports** executive PDF reports for executive decision-making.

---

## 🏛️ System Architecture

```
                                +-----------------------------------+
                                |     Streamlit Multipage UI        |
                                +-----------------+-----------------+
                                                  |
                                                  v
                                +-----------------+-----------------+
                                |        FastAPI REST API           |
                                +-----------------+-----------------+
                                                  |
     +-------------------+------------------------+------------------------+-------------------+
     |                   |                        |                        |                   |
     v                   v                        v                        v                   v
+----+----+    +---------+---------+    +---------+---------+    +---------+---------+    +----+----+
| Ingestion|    |   EDA Analytics |    | Forecasting Engine|    | Scenario Engine |    | PDF Report|
| Service |    |     Service     |    | (Prophet & XGBoost|    | & Decision Rules|    | Service |
+----+----+    +---------+---------+    +---------+---------+    +---------+---------+    +----+----+
     |                   |                        |                        |                   |
     +-------------------+------------------------+------------------------+-------------------+
                                                  |
                                                  v
                                +-----------------+-----------------+
                                |      PostgreSQL Database          |
                                | (SQLAlchemy ORM Data Schema)      |
                                +-----------------------------------+
```

---

## 💻 Tech Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn, Pydantic
- **Frontend**: Streamlit, Plotly
- **Database**: PostgreSQL 15, SQLAlchemy ORM
- **Machine Learning**: Prophet, XGBoost, Scikit-Learn, Pandas, NumPy
- **Reporting**: ReportLab
- **Testing**: Pytest
- **Containerization**: Docker, Docker Compose

---

## ✨ Features

- **Data Ingestion**: CSV dataset upload, automated schema validation, missing value imputation, database storage.
- **Exploratory Data Analysis (EDA)**: Interactive Plotly line/bar/pie charts for sales trends, annual seasonality, product breakdown, regional revenue share, missing values, and basic statistics.
- **Demand Forecasting Studio**: 3, 6, and 12-month demand projections with confidence bounds using Prophet or XGBoost; MAE, RMSE, and MAPE metrics; side-by-side model comparison.
- **XGBoost Feature Importance & Explainability**: Visual bar charts and clear explanations of key features (lags, rolling averages, marketing spend) driving predictions.
- **What-If Scenario Analysis**: Price (+/-%) and Marketing Spend (+/-%) elasticity sliders dynamically recalculating expected sales volume and revenue.
- **Rule-Based Decision Intelligence**: Explainable commercial recommendations covering inventory safety buffers, product portfolio trajectories, regional allocation, marketing spend efficiency, and pre-Q4 stocking warnings.
- **Executive PDF Report Export**: One-click generation of branded PDF reports with executive KPIs, forecast tables, and strategic recommendations.

---

## 🗄️ Database Schema

The database consists of 5 normalized tables:
- `datasets`: Ingested file metadata and record counts.
- `sales_records`: Normalized historical daily/monthly transaction records.
- `forecast_runs`: Model training metadata, parameters, MAE/RMSE/MAPE metrics, and feature importance JSON.
- `forecast_predictions`: Time-series forecast points with lower/upper confidence bounds.
- `reports`: Saved PDF report file paths and generation timestamps.

---

## ⚡ Quick Start & Installation

### Option 1: Run with Docker Compose (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/pharma-analytics-platform.git
   cd pharma-analytics-platform
   ```

2. Start the full stack (PostgreSQL, FastAPI Backend, Streamlit Frontend):
   ```bash
   docker compose up --build
   ```

3. Access the applications:
   - **Streamlit Frontend**: [http://localhost:8501](http://localhost:8501)
   - **FastAPI REST API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option 2: Run Locally (Python Virtual Environment)

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Generate sample pharmaceutical sales data:
   ```bash
   python data/generate_sample_data.py
   ```

4. Start the FastAPI backend:
   ```bash
   python -m backend.main
   ```

5. In a new terminal, launch the Streamlit frontend:
   ```bash
   streamlit run frontend/app.py
   ```

---

## 🧪 Running Unit Tests

Run the Pytest suite covering EDA metrics, ML forecasting, and scenario calculations:
```bash
python -m pytest backend/tests/ -v
```

---

## 🚀 Future Improvements

- Multi-tenant role-based permissions (Admin, Brand Manager, Executive Viewer).
- Automated hyperparameter optimization using Optuna.
- Cloud object storage integration (AWS S3 / Azure Blob) for model artifacts.
- Real-time prescription data streaming pipeline via Apache Kafka.

---

## 📄 License

MIT License. Designed for commercial analytics demonstration and portfolio evaluation.
