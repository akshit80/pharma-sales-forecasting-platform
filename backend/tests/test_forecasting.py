from backend.services.forecasting_service import ForecastingService

def test_prophet_forecast_training(db_session, sample_dataset):
    res = ForecastingService.run_forecast(db_session, sample_dataset.id, model_name="Prophet", horizon_months=6)

    assert res["model_name"] == "Prophet"
    assert res["horizon_months"] == 6
    assert res["mae"] >= 0.0
    assert res["rmse"] >= 0.0
    assert res["mape"] >= 0.0
    assert len(res["predictions"]) == 6
    assert res["predictions"][0]["predicted_units"] >= 0.0

def test_xgboost_forecast_training(db_session, sample_dataset):
    res = ForecastingService.run_forecast(db_session, sample_dataset.id, model_name="XGBoost", horizon_months=6)

    assert res["model_name"] == "XGBoost"
    assert res["horizon_months"] == 6
    assert res["mae"] >= 0.0
    assert res["rmse"] >= 0.0
    assert res["mape"] >= 0.0
    assert len(res["predictions"]) == 6
    assert res["feature_importance"] is not None
    assert "lag_1" in res["feature_importance"]

def test_model_comparison(db_session, sample_dataset):
    comp = ForecastingService.compare_models(db_session, sample_dataset.id, horizon_months=6)

    assert comp["dataset_id"] == sample_dataset.id
    assert len(comp["models"]) == 2
    assert comp["models"][0]["model_name"] == "Prophet"
    assert comp["models"][1]["model_name"] == "XGBoost"
    assert len(comp["prophet_forecast"]) == 6
    assert len(comp["xgboost_forecast"]) == 6
