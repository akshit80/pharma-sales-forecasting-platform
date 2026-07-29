import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.models.models import SalesRecord, ForecastRun, ForecastPrediction

# Machine Learning libraries
try:
    from prophet import Prophet
except ImportError:
    from fbprophet import Prophet

import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error

class ForecastingService:

    @staticmethod
    def _prepare_monthly_time_series(db: Session, dataset_id: str) -> pd.DataFrame:
        """Helper to aggregate dataset records into a clean monthly time series."""
        records = db.query(SalesRecord).filter(SalesRecord.dataset_id == dataset_id).all()
        if not records:
            raise ValueError("No records found for dataset.")

        df = pd.DataFrame([{
            "date": r.date,
            "sales_units": r.sales_units,
            "unit_price": r.unit_price,
            "marketing_spend": r.marketing_spend,
            "revenue": r.revenue
        } for r in records])

        df["date"] = pd.to_datetime(df["date"])
        # Aggregate by month start date
        monthly_df = df.groupby(pd.Grouper(key="date", freq="MS")).agg({
            "sales_units": "sum",
            "unit_price": "mean",
            "marketing_spend": "sum",
            "revenue": "sum"
        }).reset_index().sort_values("date")

        return monthly_df

    @classmethod
    def train_prophet_model(cls, df: pd.DataFrame, horizon_months: int):
        """Fits Prophet model and generates predictions with confidence intervals."""
        prophet_df = df[["date", "sales_units"]].rename(columns={"date": "ds", "sales_units": "y"})
        
        # Train/Test evaluation split (last 6 months or 20%)
        test_size = min(6, max(3, int(len(prophet_df) * 0.2)))
        train_df = prophet_df.iloc[:-test_size]
        test_df = prophet_df.iloc[-test_size:]

        # Train model on train set for evaluation metrics
        eval_model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        eval_model.fit(train_df)

        future_eval = eval_model.make_future_dataframe(periods=test_size, freq="MS")
        forecast_eval = eval_model.predict(future_eval)

        y_true = test_df["y"].values
        y_pred = forecast_eval.iloc[-test_size:]["yhat"].values

        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        mape = float(np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1))) * 100)

        # Full model fitting for future horizon
        full_model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        full_model.fit(prophet_df)

        future = full_model.make_future_dataframe(periods=horizon_months, freq="MS")
        forecast = full_model.predict(future)

        # Take only future dates
        future_forecast = forecast.iloc[-horizon_months:].copy()
        
        # Average unit price for revenue estimation
        avg_price = float(df["unit_price"].mean())

        predictions = []
        for _, row in future_forecast.iterrows():
            pred_units = max(0.0, float(row["yhat"]))
            lower_units = max(0.0, float(row["yhat_lower"]))
            upper_units = max(0.0, float(row["yhat_upper"]))
            predictions.append({
                "date": row["ds"].strftime("%Y-%m-%d"),
                "predicted_units": round(pred_units, 2),
                "lower_bound_units": round(lower_units, 2),
                "upper_bound_units": round(upper_units, 2),
                "predicted_revenue": round(pred_units * avg_price, 2)
            })

        return {
            "model_name": "Prophet",
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "mape": round(mape, 2),
            "feature_importance": None,
            "predictions": predictions
        }

    @classmethod
    def train_xgboost_model(cls, df: pd.DataFrame, horizon_months: int):
        """Builds time-series lag features, fits XGBoost Regressor, and forecasts future demand."""
        ts_df = df.copy()
        ts_df["month"] = ts_df["date"].dt.month
        ts_df["quarter"] = ts_df["date"].dt.quarter
        ts_df["year"] = ts_df["date"].dt.year
        
        # Lag and rolling features
        ts_df["lag_1"] = ts_df["sales_units"].shift(1)
        ts_df["lag_2"] = ts_df["sales_units"].shift(2)
        ts_df["rolling_3_mean"] = ts_df["sales_units"].shift(1).rolling(3).mean()

        ts_df = ts_df.dropna().reset_index(drop=True)

        features = ["month", "quarter", "year", "lag_1", "lag_2", "rolling_3_mean", "marketing_spend", "unit_price"]
        target = "sales_units"

        # Train / Test split
        test_size = min(6, max(3, int(len(ts_df) * 0.2)))
        X = ts_df[features]
        y = ts_df[target]

        X_train, X_test = X.iloc[:-test_size], X.iloc[-test_size:]
        y_train, y_test = y.iloc[:-test_size], y.iloc[-test_size:]

        model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=4, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        mae = float(mean_absolute_error(y_test, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        mape = float(np.mean(np.abs((y_test.values - y_pred) / np.maximum(y_test.values, 1))) * 100)

        # Retrain on full dataset
        full_model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=4, random_state=42)
        full_model.fit(X, y)

        # Feature importance dictionary
        importance = full_model.feature_importances_
        feature_importance = {features[i]: round(float(importance[i]), 4) for i in range(len(features))}
        # Sort feature importance descending
        feature_importance = dict(sorted(feature_importance.items(), key=lambda item: item[1], reverse=True))

        # Iterative recursive forecasting for future horizon
        last_row = ts_df.iloc[-1]
        last_date = last_row["date"]
        avg_price = float(ts_df["unit_price"].mean())
        avg_mkt = float(ts_df["marketing_spend"].mean())

        history_units = list(ts_df["sales_units"].values)
        predictions = []

        curr_date = last_date
        for i in range(horizon_months):
            curr_date = curr_date + pd.DateOffset(months=1)
            month_val = curr_date.month
            quarter_val = curr_date.quarter
            year_val = curr_date.year

            lag_1 = history_units[-1]
            lag_2 = history_units[-2] if len(history_units) >= 2 else lag_1
            rolling_3 = np.mean(history_units[-3:]) if len(history_units) >= 3 else lag_1

            feat_vector = pd.DataFrame([{
                "month": month_val,
                "quarter": quarter_val,
                "year": year_val,
                "lag_1": lag_1,
                "lag_2": lag_2,
                "rolling_3_mean": rolling_3,
                "marketing_spend": avg_mkt,
                "unit_price": avg_price
            }])

            pred_val = max(0.0, float(full_model.predict(feat_vector)[0]))
            history_units.append(pred_val)

            # Heuristic standard error for confidence interval bound simulation
            std_err = mae * (1 + 0.05 * i)
            predictions.append({
                "date": curr_date.strftime("%Y-%m-%d"),
                "predicted_units": round(pred_val, 2),
                "lower_bound_units": round(max(0.0, pred_val - 1.96 * std_err), 2),
                "upper_bound_units": round(pred_val + 1.96 * std_err, 2),
                "predicted_revenue": round(pred_val * avg_price, 2)
            })

        return {
            "model_name": "XGBoost",
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "mape": round(mape, 2),
            "feature_importance": feature_importance,
            "predictions": predictions
        }

    @classmethod
    def run_forecast(cls, db: Session, dataset_id: str, model_name: str, horizon_months: int):
        """Executes selected model training, saves run & predictions to DB, and returns response."""
        monthly_df = cls._prepare_monthly_time_series(db, dataset_id)

        if model_name.lower() == "prophet":
            result = cls.train_prophet_model(monthly_df, horizon_months)
        elif model_name.lower() == "xgboost":
            result = cls.train_xgboost_model(monthly_df, horizon_months)
        else:
            raise ValueError(f"Unsupported model_name: {model_name}. Choose Prophet or XGBoost.")

        # Store in database
        run = ForecastRun(
            dataset_id=dataset_id,
            model_name=result["model_name"],
            horizon_months=horizon_months,
            mae=result["mae"],
            rmse=result["rmse"],
            mape=result["mape"],
            feature_importance=result["feature_importance"]
        )
        db.add(run)
        db.flush()

        preds = []
        for p in result["predictions"]:
            preds.append(ForecastPrediction(
                forecast_run_id=run.id,
                date=datetime.strptime(p["date"], "%Y-%m-%d").date(),
                predicted_units=p["predicted_units"],
                lower_bound_units=p["lower_bound_units"],
                upper_bound_units=p["upper_bound_units"],
                predicted_revenue=p["predicted_revenue"]
            ))

        db.bulk_save_objects(preds)
        db.commit()
        db.refresh(run)

        result["forecast_run_id"] = run.id
        result["dataset_id"] = dataset_id
        result["horizon_months"] = horizon_months
        return result

    @classmethod
    def compare_models(cls, db: Session, dataset_id: str, horizon_months: int = 6):
        """Runs both Prophet and XGBoost to present side-by-side performance comparison."""
        monthly_df = cls._prepare_monthly_time_series(db, dataset_id)

        prophet_res = cls.train_prophet_model(monthly_df, horizon_months)
        xgboost_res = cls.train_xgboost_model(monthly_df, horizon_months)

        historical = [{
            "date": row["date"].strftime("%Y-%m-%d"),
            "sales_units": float(row["sales_units"]),
            "revenue": float(row["revenue"])
        } for _, row in monthly_df.iterrows()]

        return {
            "dataset_id": dataset_id,
            "horizon_months": horizon_months,
            "models": [
                {"model_name": "Prophet", "mae": prophet_res["mae"], "rmse": prophet_res["rmse"], "mape": prophet_res["mape"]},
                {"model_name": "XGBoost", "mae": xgboost_res["mae"], "rmse": xgboost_res["rmse"], "mape": xgboost_res["mape"]}
            ],
            "historical": historical,
            "prophet_forecast": prophet_res["predictions"],
            "xgboost_forecast": xgboost_res["predictions"]
        }
