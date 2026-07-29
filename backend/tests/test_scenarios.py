from backend.services.scenario_service import ScenarioService

def test_scenario_recalculation(db_session, sample_dataset):
    scenario = ScenarioService.run_scenario(
        db_session,
        sample_dataset.id,
        model_name="XGBoost",
        horizon_months=6,
        price_change_pct=10.0,
        marketing_change_pct=20.0
    )

    assert scenario["dataset_id"] == sample_dataset.id
    assert scenario["price_change_pct"] == 10.0
    assert scenario["marketing_change_pct"] == 20.0
    assert scenario["baseline_units"] > 0
    assert scenario["recalculated_units"] > 0
    assert len(scenario["forecast_comparison"]) == 6
