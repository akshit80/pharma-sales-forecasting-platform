from backend.services.eda_service import EDAService

def test_eda_metrics_calculation(db_session, sample_dataset):
    metrics = EDAService.get_eda_metrics(db_session, sample_dataset.id)

    assert metrics["dataset_id"] == sample_dataset.id
    assert metrics["total_records"] > 0
    assert metrics["total_revenue"] > 0
    assert metrics["total_sales_units"] > 0
    assert len(metrics["products"]) == 5
    assert len(metrics["regions"]) == 4
    assert len(metrics["monthly_sales"]) > 0
    assert "basic_stats" in metrics
    assert "seasonality" in metrics
